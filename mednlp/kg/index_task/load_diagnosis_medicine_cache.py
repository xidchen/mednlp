#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import global_conf
import time
import datetime
import configparser
import json
from ailib.utils.text import string_wraper
from ailib.storage.db import DBWrapper
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.log import GLLog

config_parser = configparser.ConfigParser()
config_parser.optionxform = str
config_parser.read(global_conf.cfg_path)
cat_diagnosismedicine = config_parser.get('SEARCH_PLATFORM_SOLR', 'CAT_DIAGNOSISMEDICINE')
cat_diagnosismedicine_primarykey = config_parser.get('SEARCH_PLATFORM_SOLR', 'CAT_DIAGNOSISMEDICINE_PRIMARYKEY')

logger = GLLog('load_diagnosis_medicine_cache', level='info', log_dir=global_conf.log_dir).getLogger()


def load_data(start_page_no, page_size):
    logger.info('起始页码:{}，单页大小:{}'.format(start_page_no, page_size))
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')

    # 处方统计表总记录数SQL
    count_diagnosis_medicine_count_sql = """
    SELECT 
    COUNT(*) total_count
    FROM `dwservice`.user_doctor_diagnosis_medicine_statistics a
    """
    count_result = db.get_rows(count_diagnosis_medicine_count_sql)
    db_count = count_result[0].get('total_count', 0)
    count = db_count - (start_page_no - 1) * page_size
    logger.info('数据总量为:{}'.format(count))

    # 如果没有数据则直接终止
    if count < 1:
        return

    total_page = 0
    if (db_count % page_size) > 0:
        total_page = (db_count // page_size) + 1
    else:
        total_page = db_count // page_size

    logger.info('总查询页码数:{}'.format(total_page - start_page_no + 1))
    total_load_data = 0
    for num in range(start_page_no, (total_page + 1)):
        offset = (num - 1) * page_size

        # 处方统计表分页查询SQL
        diagnosis_medicine_rows_sql = """
        SELECT a.user_id, a.doctor_id, a.doctor_user_id, a.disease_name, a.disease_id, a.prescription_operation, a.sku_name,
        a.specification, a.common_preparation_name, a.medicine_id, a.medicine_name, a.factory_name, a.prescription_count,
        a.dosage, a.dosage_unit, a.dosing_frequency, a.administration_route, a.administration_duration, a.package_quantity,
        a.medical_advice, a.gmt_created, a.gmt_modified, a.date_id
        FROM `dwservice`.user_doctor_diagnosis_medicine_statistics a
        LIMIT %s,%s
        """
        diagnosis_medicine_rows_sql = diagnosis_medicine_rows_sql % (offset, page_size)
        diagnosis_medicine_rows = db.get_rows(diagnosis_medicine_rows_sql)
        logger.info('当前查询数据页码{}, offset:{}, page_size:{}, 结果记录数:{}'.format(num, offset, page_size,
                                                                     len(diagnosis_medicine_rows)))

        if diagnosis_medicine_rows is None or len(diagnosis_medicine_rows) < 1:
            logger.info('未查询到数据')
            continue

        medicine_id_list = []
        for diagnosis_medicine in diagnosis_medicine_rows:
            medicine_id_list.append(str(diagnosis_medicine.get('medicine_id')))
        # 药品ID去重
        medicine_id_list = list(set(medicine_id_list))

        medicine_enterprise_sql = """
        SELECT DISTINCT a.medicine_id, a.enterprise_id
        FROM `medicine`.medicine_enterprise_relation a
        WHERE a.is_delete=0 and a.medicine_id in (%s) 
        """

        medicine_id_condi = '%s' % ','.join(string_wraper(medicine_id_list))
        medicine_enterprise_sql = medicine_enterprise_sql % (medicine_id_condi)
        medicine_enterprise_rows = db.get_rows(medicine_enterprise_sql)
        # 未查询到药品供应商
        if medicine_enterprise_rows is None or len(medicine_enterprise_rows) < 1:
            continue

        # 提取药品到供应商
        medicine_enterprise_dict = {}
        for medicine_enterprise in medicine_enterprise_rows:
            if medicine_enterprise_dict.get(medicine_enterprise.get('medicine_id'), None) is None:
                enterprise_id_arr = []
                enterprise_id_arr.append(medicine_enterprise.get('enterprise_id'))
                medicine_enterprise_dict[medicine_enterprise.get('medicine_id')] = enterprise_id_arr
            else:
                exist_enterprise = medicine_enterprise_dict.get(medicine_enterprise.get('medicine_id'))
                exist_enterprise.append(medicine_enterprise.get('enterprise_id'))
                medicine_enterprise_dict[medicine_enterprise.get('medicine_id')] = exist_enterprise

        # 整合数据结果
        result_list = []
        for row in diagnosis_medicine_rows:
            enterprise = medicine_enterprise_dict.get(row.get('medicine_id'))
            if enterprise is not None and len(enterprise) > 0:
                convert_obj = convert_medicine_data(row)
                if convert_obj is None:
                    continue
                convert_obj['enterpriseId'] = enterprise
                result_list.append(convert_obj)

        http_client = AIServiceClient(cfg_path=global_conf.cfg_path, service='SEARCH_PLATFORM_SOLR')
        param_dict = {}
        param_dict['cat'] = cat_diagnosismedicine
        param_dict['primaryKey'] = cat_diagnosismedicine_primarykey
        param_dict['isAtomic'] = True
        param_dict['pageDocs'] = result_list
        index_result = http_client.query(json.dumps(param_dict, ensure_ascii=False), '/index/1.0', method='post')
        logger.info('本次缓存{}条数据，缓存结果:{} \n'.format(len(result_list), index_result))

        total_load_data += len(result_list)

    # 打印总记录数
    logger.info('装载总数据量为:{}'.format(total_load_data))

    # 删除老的无用数据
    if total_load_data > 0:
        delete_unused_data()


# 删除12小时前生成的数据
def delete_unused_data():
    pre_date = datetime.datetime.now() + datetime.timedelta(hours=-12)
    date_string = pre_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    delete_param = {}
    delete_param['cat'] = cat_diagnosismedicine
    delete_param['primaryKey'] = cat_diagnosismedicine_primarykey
    delete_param['query'] = '_timestamp_:[* TO ' + date_string + ']'
    http_client = AIServiceClient(cfg_path=global_conf.cfg_path, service='SEARCH_PLATFORM_SOLR')
    delete_result = http_client.query(json.dumps(delete_param, ensure_ascii=False), '/delete/1.0', method='post')
    logger.info('删除无用索引数据结果: {}'.format(delete_result))


def convert_medicine_data(db_obj):
    convert_obj = {}
    id_arr = []
    id_arr.append(str(db_obj.get('user_id', '')))
    id_arr.append(str(db_obj.get('doctor_id', '')))
    id_arr.append(str(db_obj.get('doctor_user_id', '')))
    id_arr.append(str(db_obj.get('disease_id', '')))
    id = '|'.join(id_arr)
    convert_obj['specification'] = db_obj.get('specification', '')
    dosage_unit = db_obj.get('dosage_unit', '')
    # 剔除剂量单位与规格不符的数据
    if convert_obj['specification'].find(dosage_unit) < 0:
        return None
    convert_obj['id'] = id
    convert_obj['userId'] = db_obj.get('user_id', '')
    convert_obj['doctorId'] = db_obj.get('doctor_id', '')
    convert_obj['doctorUserId'] = db_obj.get('doctor_user_id', '')
    convert_obj['diseaseId'] = db_obj.get('disease_id', '')
    convert_obj['diseaseName'] = db_obj.get('disease_name', '')
    convert_obj['prescriptionOperation'] = db_obj.get('prescription_operation', '')
    convert_obj['skuName'] = db_obj.get('sku_name', '')
    convert_obj['specification'] = db_obj.get('specification', '')
    convert_obj['commonPreparationName'] = db_obj.get('common_preparation_name', '')
    convert_obj['medicineId'] = db_obj.get('medicine_id', '')
    convert_obj['medicineName'] = db_obj.get('medicine_name', '')
    convert_obj['factoryName'] = db_obj.get('factory_name', '')
    convert_obj['prescriptionCount'] = db_obj.get('prescription_count', '')
    convert_obj['dosage'] = db_obj.get('dosage', '')
    convert_obj['dosageUnit'] = db_obj.get('dosage_unit', '')
    convert_obj['dosingFrequency'] = db_obj.get('dosing_frequency', '')
    convert_obj['administrationRoute'] = db_obj.get('administration_route', '')
    convert_obj['administrationDuration'] = db_obj.get('administration_duration', '')
    convert_obj['packageQuantity'] = db_obj.get('package_quantity', '')
    convert_obj['medicalAdvice'] = db_obj.get('medical_advice', '')

    gmt_created_time = time.strptime(str(db_obj.get('gmt_created')), '%Y-%m-%d %H:%M:%S')
    format_gmt_created = time.strftime("%Y-%m-%dT%H:%M:%SZ", gmt_created_time)
    convert_obj['gmtCreated'] = format_gmt_created

    gmt_midified_time = time.strptime(str(db_obj.get('gmt_modified')), '%Y-%m-%d %H:%M:%S')
    format_gmt_modified = time.strftime("%Y-%m-%dT%H:%M:%SZ", gmt_midified_time)
    convert_obj['gmtModified'] = format_gmt_modified

    date_id_time = time.strptime(str(db_obj.get('date_id')), '%Y-%m-%d')
    format_date_id = time.strftime("%Y-%m-%dT%H:%M:%SZ", date_id_time)
    convert_obj['dateId'] = format_date_id

    return convert_obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--page_no', type=int, default=1)
    parser.add_argument('--page_size', type=int, default=20000)
    args = parser.parse_args()
    # 装载数据
    load_data(args.page_no, args.page_size)
