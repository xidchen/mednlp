# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
推荐治疗方案类

Author: chenxk <chenxk@guahao.com>
Create on 2019-10-15 星期三.
"""


import os
import sys
import time
import re
import copy
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.log import GLLog
import json
import traceback
from functools import wraps
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser


def print_exec_time(fn):
    """
    打印方法的运行时间
    :param fn:
    :return:
    """
    @wraps(fn)
    def measure_time(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        duration = time.time() - start
        if kwargs.get('logger'):
            kwargs.get('logger').info("函数:{},\t请求耗时：{} ms".format(fn.__name__, round(duration * 1000, 2)))
        else:
            print("函数:{},\t请求耗时：{} ms".format(fn.__name__, round(duration * 1000, 2)))
        return result
    return measure_time


class TreatmentPlanRecommendDao(object):
    def __init__(self, logger: GLLog=None):
        """
        初始化配置
        :return: 无
        """
        if not logger:
            logger = GLLog('treatment_plan_recommend', log_dir=global_conf.out_log_dir, level='info').getLogger()
        self.logger = logger
        self.config = ConfigParser.ConfigParser()
        self.config.read(global_conf.cfg_path)
        self.ai_service = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.questions = {'symptom': 'symptom', 'comorbidity': 'disease', 'complication': 'disease', 'examination': 'examination', 'inspection': 'inspection'}
        self.rule_label = []
        self.rule_code = ''
        if self.config.has_section('TREATMENT_PLAN_RECOMMEND'):
            section = 'TREATMENT_PLAN_RECOMMEND'
            if self.config.has_option(section, 'RULE_SYSTEM_LABEL'):
                rule_label = self.config.get(section, 'RULE_SYSTEM_LABEL')
                self.rule_label = rule_label.split(',')
            if self.config.has_option(section, 'STANDARD_RULE_CODE'):
                rule_code = self.config.get(section, 'STANDARD_RULE_CODE')
                self.rule_code = rule_code

    @print_exec_time
    def query_standard_name(self, entity_names: list=[], entity_type: list=[], logger=None, **kwargs) -> list:
        """
        获取标准的实体名称
        :param entity_names: 实体名称
        :param entity_type:  实体类型
        :return:
        """
        result = []
        if entity_names:
            param = {
                'q': '*:*',
                'name': entity_names,
                'rows': len(entity_names)*(len(entity_type) if len(entity_type) else 1),
                'ef': ['id', 'name', 'type', 'relation_set']
            }
            if self.rule_label:
                param['label'] = list(set(self.rule_label))
                param['label_field'] = list(set(self.rule_label))
                param['match_alias'] = 1
            res = {}
            param_str = json.dumps(param, ensure_ascii=False)
            try:
                res = self.ai_service.query(param_str, 'entity_service')
                self.logger.info('推荐治疗方案-查询实体标准名称成功，入参:{}'.format(param_str))
            except Exception as e:
                traceback.print_exc()
                self.logger.info('推荐治疗方案-查询实体标准名称失败，入参:{},错误:{}'.format(param_str, e))
            if res and res['code'] == 0 and res.get('data'):
                result = [entity for entity in res['data'].get('entity', []) if entity['type'] in entity_type]
        return result

    @print_exec_time
    def query_treatment_plan_id_by_condition(self, disease_names: list=[], logger=None, **kwargs) -> list:
        """
        根据诊断信息及辅助的诊疗信息从规则系统中获取治疗方案的ID
        包含的条件信息：
            主诊断
            症状
            合并症
            并发症
            检查
            检验
        :param disease_names: 主诊断名称
        :param kwargs
            -> symptom 症状集合
            -> examination 检查集合
            -> inspection 检验集合
            -> comorbidity 合并症
            -> complication 并发症集合
        :return: 治疗方案的ID
        """
        type_list = []
        name_list = []
        for question_code, entity_type in self.questions.items():
            question = kwargs.get(question_code, None)
            if question and isinstance(question, list) and isinstance(question[0], str):
                name_list.extend(question)
                type_list.append(entity_type)
            elif question and isinstance(question, list) and isinstance(question[0], dict):
                type_list.append(entity_type)
                for sub_question in question:
                    name_list.append(sub_question.get('name', ''))
        standard_entitys = self.query_standard_name(name_list, type_list, logger=logger)
        name_map = {}
        for entity in standard_entitys:
            tem_map = name_map.setdefault(entity['type'], {})
            for name in entity.get('relation_set', []):
                tem_map[name] = {'code': entity.get('label', {}).get(self.rule_label[0], ''), 'name': entity['name']}
            tem_map[entity['name']] = {'code': entity.get('label', {}).get(self.rule_label[0], ''), 'name': entity['name']}
        result = []
        if disease_names and self.rule_code:
            param = {
                'organizeCode': self.rule_code,
                'ruleGroupName': '治疗方案规则组',
                'ruleEntities': list(set(disease_names)),
                'initQuestionAnswer': []
            }
            for question_code, entity_type in self.questions.items():
                question = kwargs.get(question_code, None)
                if question and isinstance(question, list) and isinstance(question[0], str):
                    tem_question = [name_map[entity_type][name]['name'] if name_map.get(entity_type, {}).get(name) else name for name in question]
                    tem_question.extend(question)
                    answer = {
                        'questionCode': question_code,
                        'questionAnswer': list(set(tem_question)),
                        'questionAnswerUnit': ''
                    }
                    param['initQuestionAnswer'].append(answer)
                elif question and isinstance(question, list) and isinstance(question[0], dict):
                    for sub_question in question:
                        label_value = name_map.get(entity_type, {}).get(sub_question.get('name', ''), {}).get('code', '')
                        if label_value:
                            answer = {
                                'questionCode': label_value,
                                'questionAnswer': [sub_question.get('value', '')],
                                'questionAnswerUnit': ''
                            }
                            param['initQuestionAnswer'].append(answer)

            if param['initQuestionAnswer']:
                param_str = json.dumps(param, ensure_ascii=False)
                res = {}
                try:
                    res = self.ai_service.query(param_str, 'rule_engine')
                    self.logger.info('推荐治疗方案-查询规则系统成功，入参:{}'.format(param_str))
                except Exception as e:
                    traceback.print_exc()
                    self.logger.info('推荐治疗方案-查询规则系统失败，入参:{},错误:{}'.format(param_str, e))
                if res and res['code'] == '0' and res.get('data'):
                    rule_results = res['data'].get('ruleContents', [])
                    for rule_result in rule_results:
                        if rule_result.get('action') and rule_result.get('action').get('value'):
                            treatment_plan = json.loads(rule_result.get('action').get('value'))
                            result.append(treatment_plan)
        return result

    @print_exec_time
    def query_treatment_plan_by_id(self, ids: list=[], add_atc: list=[], remove_atc: list=[], logger=None, **kwargs) -> (list, list, dict):
        """
        根据治疗方案ID从知识图谱中获取治疗方案中包含的具体信息
        治疗方案中包含的信息：
            处方
                药品ATC编码
        :param ids: 治疗方案ID
        :param add_atc: 增加的药品ATC编码
        :param remove_atc: 减少的药品ATC编码
        :return: 治疗方案列表,全量ATC编码列表,ATC编码信息字典
        """
        all_atc_code = []
        treatment_map = {}
        prescription_map = {}
        atc_map = {}
        if ids:
            param = {
                'q': '*:*',
                'type': ['remedy_prescription'],
                'rows': len(ids)*10,
                'field_filter': {
                    'remedy_plan_prescription_relation': ' OR '.join([_id for _id in ids if _id])
                },
                'ef': ['id', 'name', 'remedy_prescription_atc_relation', 'remedy_plan_prescription_relation', 'type']
            }
            res = {}
            param_str = json.dumps(param, ensure_ascii=False)
            try:
                res = self.ai_service.query(param_str, 'entity_service')
                self.logger.info('推荐治疗方案-查询处方成功，入参:{}'.format(param_str))
            except Exception as e:
                traceback.print_exc()
                self.logger.info('推荐治疗方案-查询处方失败，入参:{},错误:{}'.format(param_str, e))
            if res and res['code'] == 0 and res.get('data'):
                tem_result = res['data'].get('entity', [])
                if tem_result:
                    atc_ids = []
                    for entity in tem_result:
                        for _id in entity.get('remedy_plan_prescription_relation', []):
                            if _id not in ids:
                                continue
                            if _id not in treatment_map:
                                treatment_map[_id] = {}
                            if entity.get('type') == 'remedy_prescription':
                                treatment_map[_id].setdefault('prescription', []).append(entity['id'])
                                atc_ids.extend(entity.get('remedy_prescription_atc_relation', []))
                    param = {
                        'q': '*:*',
                        'rows': len(atc_ids),
                        'id': atc_ids,
                        'type': ['medicine_atc_dir'],
                        'ef': ['id', 'name', 'type', 'atc_code', 'remedy_prescription_atc_relation']
                    }
                    res = {}
                    param_str = json.dumps(param, ensure_ascii=False)
                    try:
                        res = self.ai_service.query(param_str, 'entity_service')
                        self.logger.info('推荐治疗方案-查询ATC编码成功，入参:{}'.format(param_str))
                    except Exception as e:
                        traceback.print_exc()
                        self.logger.info('推荐治疗方案-查询ATC编码失败，入参:{},错误:{}'.format(param_str, e))
                    if res and res['code'] == 0 and res.get('data'):
                        tem_result = res['data'].get('entity', [])
                        for entity in tem_result:
                            atc_codes = entity.get('atc_code', [])
                            for _id in entity.get('remedy_prescription_atc_relation', []):
                                prescription_map.setdefault(_id, []).extend(atc_codes)
                            if atc_codes:
                                for code in atc_codes:
                                    atc_map[code] = entity
                    remove_treatment = set()
                    for treatment_key, treatment_value in treatment_map.items():
                        atc_codes = [code for code in add_atc]
                        for prescription_id in treatment_value['prescription']:
                            atc_codes.extend(prescription_map.get(prescription_id, []))
                        del treatment_value['prescription']
                        remove_list = []
                        for tem_code in atc_codes:
                            [remove_list.append(tem_code) for c in remove_atc if tem_code.startswith(c)]
                        atc_codes = set(atc_codes).difference(set(remove_list))
                        all_atc_code.extend(list(atc_codes))
                        if not treatment_value and not atc_codes:
                            remove_treatment.add(treatment_key)
                        else:
                            treatment_value['prescription'] = list(atc_codes)
                    [treatment_map.pop(key) for key in remove_treatment]
        self.logger.info('推荐治疗方案-治疗方案详情内容查询，结果:{}'.format(json.dumps(treatment_map, ensure_ascii=False)))
        return [value for value in treatment_map.values()], list(set(all_atc_code)), atc_map

    @print_exec_time
    def query_medicine_by_condition(self, all_atc_code: list=[], logger=None, **kwargs) -> dict:
        """"
        根据处方中的药品ATC编码和附加信息查询具体的药品
        条件：
            药品ATC编码
            医生用户ID
            患者ID
            药店ID列表
        :return: 按照ATC编码分组的药品列表
        """
        result = {}
        if all_atc_code:
            param = {
                'diagnosis': kwargs.get('standard_disease', []),
                'atcCodes': list(set(all_atc_code)),
                'doctorId': kwargs.get('doctor_user_id', ''),
                'patientId': kwargs.get('user_id', ''),
                'enterpriseId': kwargs.get('drug_store_id', ['-1']),
                'rows': kwargs.get('drug_number', 5)
            }
            res = {}
            param_str = json.dumps(param, ensure_ascii=False)
            try:
                res = self.ai_service.query(param_str, 'search_medicine')
                self.logger.info('推荐治疗方案-根据ATC编码查询药品成功，入参:{}'.format(param_str))
            except Exception as e:
                traceback.print_exc()
                self.logger.info('推荐治疗方案-根据ATC编码查询药品失败，入参:{},错误:{}'.format(param_str, e))
            if res and res.get('code') == '0':
                for medicines in res.get('data', []):
                    result[medicines.get('atcCode')] = []
                    for medicine in medicines.get('medicines', []):
                        tem_medicine = {
                            'medicine_id': medicine.get('medicineId', ''),
                            'medicine_name': medicine.get('medicineName', ''),
                            'common_preparation': medicine.get('commonPreparationName', ''),
                            'specification': medicine.get('specification', ''),
                            'dosage': medicine.get('dosage', None),
                            'dosage_unit': medicine.get('dosageUnit', ''),
                            'dosing_frequency': medicine.get('dosingFrequency', ''),
                            'manufacturer': medicine.get('factoryName', ''),
                            'drug_store_id': medicine.get('enterpriseId', ''),
                            'package_quantity': medicine.get('packageQuantity', None),
                            'administration_duration': medicine.get('administrationDuration', None),
                            'administration_route': medicine.get('administrationRoute', ''),
                            'medical_advice': medicine.get('medicalAdvice', ''),
                            'atc_code': medicine.get('atcCode', [])
                        }
                        result[medicines.get('atcCode')].append(tem_medicine)
        return result


if __name__ == '__main__':
    treatment_plan_recommend_dao = TreatmentPlanRecommendDao()
    print(treatment_plan_recommend_dao.query_standard_name(['呕吐', '头疼'], entity_type=['disease', 'symptom']))
    param = {
        "comorbidity": ["高血压","心脏病","脑外伤后综合征"],
        "complication": ["心脏病"],
        "symptom": ["腹泻", "腹痛"],
        "examination": [
            {
                "id": "123123",
                "code": "exam_1",
                "name": "心电图",
                "value": "异常",
                "unit": ""
            }
        ],
        "inspection": [
            {
                "id": "456456",
                "code": "insp_1",
                "name": "血钾",
                "value": "3.4",
                "unit": "mol/ml"
            }
        ]
      }
    print(treatment_plan_recommend_dao.query_treatment_plan_id_by_condition(['急性胃肠炎'], **param))
    treatment_plan_ids = ['2c094833-83bc-4fe2-b0ff-afe83242295d','38366ef7-b286-4156-ae5b-123de2cd9161','2c094833-83bc-4fe2-b0ff-afe83242295d','2c094833-83bc-4fe2-b0ff-afe83242295d','2c094833-83bc-4fe2-b0ff-afe83242295d']
    # add_atc = []
    add_atc = ['N01BB53']
    remove_atc = ['J01MA06']
    print(treatment_plan_recommend_dao.query_treatment_plan_by_id(treatment_plan_ids, add_atc=add_atc, remove_atc=remove_atc))

