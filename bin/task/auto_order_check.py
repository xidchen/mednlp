#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import json
import traceback
import global_conf
import urllib.parse as urllib
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.log import GLLog
from ailib.storage.hivedb import HiveWrapper
from optparse import OptionParser
from mednlp.model.get_health_record import get_health_record_data,add_health_record_to_consult_info
from mednlp.service.order_check_standard import OrderCheckStandard
from mednlp.model.order_check_model import sex_idf,age_idf,disease_idf,online_case_idf,medical_logic_idf,name_idf,uncivilized_word_idf,chief_complaint_have_idf,chief_complaint_brief_idf,chief_complaint_compaire_disease,chief_complaint_loss_importance,first_reply_idf,end_reply_idf,drug_taboo_idf,antibiotic_idf

class OrderCheck():
    def __init__(self, check_type='2', debug=False):
        self.client_search_service = AIServiceClient(global_conf.cfg_path, 'SearchService')
        self.check_type = check_type
        if check_type == '1':
            self.order_check_standard_model = OrderCheckStandard()
        self.check_items = {'411': {'func': name_idf, 'score': 1, 'is_red_line': False},
                            '412': {'func': sex_idf, 'score': 2, 'is_red_line': False},
                            '413': {'func': age_idf, 'score': 2, 'is_red_line': False},
                            '421': {'func': disease_idf, 'score': 0, 'is_red_line': True},
                            '422': {'func': online_case_idf, 'score': 0, 'is_red_line': True},
                            '432': {'func': uncivilized_word_idf, 'score': 2, 'is_red_line': False},
                            '441': {'func': chief_complaint_have_idf, 'score': 3, 'is_red_line': False},
                            '442': {'func': chief_complaint_brief_idf, 'score': 2, 'is_red_line': False},
                            '443': {'func': chief_complaint_loss_importance, 'score': 5, 'is_red_line': False},
                            #'447': {'func': chief_complaint_compaire_disease, 'score': 0, 'is_red_line': True},
                            '461': {'func': medical_logic_idf, 'score': 0, 'is_red_line': True},
                            '621': {'func': first_reply_idf, 'score': 0, 'is_red_line': False},
                            '664': {'func': drug_taboo_idf, 'score': 0, 'is_red_line': False},
                            '666': {'func': antibiotic_idf, 'score': 0, 'is_red_line': False},
                            '671': {'func': end_reply_idf, 'score': 0, 'is_red_line': False}
                            }
        self.db = HiveWrapper(global_conf.cfg_path, 'HiveDB', GLLog('db_wrapper').getLogger())
        self.logger = GLLog('order_check').getLogger()
        self.debug = debug

    def check(self, start_time, end_time):
        self.logger.info('开始质检任务，时间范围：{} -> {}'.format(start_time, end_time))
        get_consult_data = self.get_consult_data(start_time, end_time)
        check_sum = 0
        for i, consult_infos in enumerate(get_consult_data):
            try:
                check_results = []
                # 检查订单是否已经质检
                consult_info_ids = [c.get('order_no') for c in consult_infos]
                not_in_db_ids = self.find_not_in_data_ids(consult_info_ids)
                # 用onder_no list去mongodb数据库拿取数据
                health_record_map = get_health_record_data(not_in_db_ids)
                for consult_info in consult_infos:
                    order_no = consult_info.get('order_no')
                    if order_no in not_in_db_ids:
                        #把健康单信息拼接到consult_info中
                        consult_info = add_health_record_to_consult_info(health_record_map,consult_info)
                        check_result = self.order_check(consult_info)
                        check_results.append(check_result)
                        check_sum += 1
                self.save_to_hive(check_results)
            except Exception as e:
                self.logger.error(e)
                traceback.print_stack()
                # self.logger.error('\n'.join(traceback.format_stack()))
        self.logger.info('质检任务完成，质检订单数：' + str(check_sum))

    def get_consult_data(self, start_time, end_time):
        fl = ['*']
        param = {'recent': 1,
                 'end_time_range': start_time + '|' + end_time,
                 'deep_page': 1,
                 'cursor_code': '*',
                 'rows': 100,
                 'sort': 'create_time',
                 'fl': ','.join(fl)}
        cursor_code = '*'
        pre_cursor_code = ''
        while cursor_code != pre_cursor_code:
            param['cursor_code'] = urllib.unquote(cursor_code)
            self.logger.info(json.dumps(param, ensure_ascii=False))
            response = self.client_search_service.query(param, 'admin_doctor_consult', method='get')
            if response['code'] == 0:
                yield response['data']
                pre_cursor_code, cursor_code = cursor_code, response['next_cursor_code']
            else:
                break
        return []

    def get_consult(self, order_no):
        fl = ['*']
        param = {'order_no': order_no,
                 'fl': ','.join(fl)}
        response = self.client_search_service.query(param, 'admin_doctor_consult', method='get')
        if response['code'] == 0:
            return response['data']
        return []

    def order_check(self, consult_info):
        """ 质检一条订单数据 """
        if self.check_type == '1':
            return self.order_check_standard(consult_info)
        if self.check_type == '2':
            return self.order_check_compliance(consult_info)

    def order_check_standard(self, consult_info):
        """ 业务质检 """
        order_id = consult_info.get('order_no')
        compliance_code, violation_code, unchecked_code = self.order_check_standard_model.order_check(consult_info)
        return {'order_id': order_id, 'biz_type': 2, 'check_type': 1,
                'check_status': 2, 'score': "''", 'violation_code': '|'.join(violation_code),
                'compliance_code': '|'.join(compliance_code), 'unchecked_code': '|'.join(unchecked_code)}

    def order_check_compliance(self, consult_info):
        """ 合规质检 """
        order_id = consult_info.get('order_no')
        score = 100
        violation_code = []
        compliance_code = []
        for code, check_item in self.check_items.items():
            try:
                func = check_item['func']
                if func(consult_info):
                    compliance_code.append(code)
                else:
                    if check_item['is_red_line']:
                        score = 0
                    else:
                        score -= check_item['score']
                    violation_code.append(code)
            except Exception as e:
                self.logger.error(e)
                traceback.print_stack()
                self.logger.error('\n'.join(traceback.format_stack()))
        if score < 0:
            score = 0
        return {'order_id': order_id, 'biz_type': 2, 'check_type': 2,
                'check_status': 2, 'score': score, 'violation_code': '|'.join(violation_code),
                'compliance_code': '|'.join(compliance_code), 'unchecked_code': ''}

    def find_not_in_data_ids(self, ids):
        sql_wrap_ids = ["'{}'".format(i) for i in ids]
        if sql_wrap_ids:
            sql = "select order_id from ai_opendata.ai_order_check where check_type = '{}' and order_id in ({})".format(self.check_type, ",".join(sql_wrap_ids))
            rows = self.db.get_rows(sql)
            db_order_ids = [row[0] for row in rows]
            return [i for i in ids if i not in db_order_ids]
        else:
            return []

    def save_to_hive(self, check_results):
        sql_values = []
        for check_result in check_results:
            value = "(0, '{order_id}', {biz_type}, {check_type}, {check_status}, {score}, '{violation_code}', '{compliance_code}', \
                now(), now(), 0, '{unchecked_code}')".format(**check_result)
            sql_values.append(value)
        if sql_values:
            sql = "insert into table ai_order_check values" + ",".join(sql_values)
            if self.debug:
                print(sql)
            else:
                self.db.execute(sql)


if __name__ == '__main__':
    command = '\npython %s [-t trainfile -v version -m model]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-m', dest='mode', default='0', help=('0 - 处理前12分钟数据；1-处理昨天一天的数据；2-处理指定时间范围的数据，范围由-r指定；'
                      '3-处理指定订单，订单号由-n指定'))
    parser.add_option('-r', dest='range', help='指定处理的时间(start,end)范围，时间格式为：%Y-%m-%dT%H:%M:%SZ')
    parser.add_option('-t', dest='check_type', default='2', help='质检类型')
    parser.add_option('-n', dest='order_no', help='指定重新处理订单号')
    parser.add_option('-d', action="store_true", dest="debug", help='开启debug模式')
    (options, args) = parser.parse_args()
    if options.mode == '1':
        today = datetime.date.today()
        today_zero = datetime.datetime(today.year, today.month, today.day)
        yesterday_zero = today_zero - datetime.timedelta(hours=24)
        start_time = yesterday_zero.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = today_zero.strftime('%Y-%m-%dT%H:%M:%SZ')
    elif options.mode == '2':
        start_time, end_time = options.range.split(',')
    elif options.mode == '3':
        order_no = options.order_no
    else:
        now = datetime.datetime.now()
        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        before = now - datetime.timedelta(minutes=12)
        start_time = before.strftime('%Y-%m-%dT%H:%M:%SZ')

    if options.debug:
        order_check = OrderCheck(check_type=options.check_type, debug=True)
    else:
        order_check = OrderCheck(check_type=options.check_type)

    if options.mode == '3':
        consult_info = order_check.get_consult(order_no)
        if len(consult_info) > 0:
            health_record_map = get_health_record_data([order_no])
            consult_info = add_health_record_to_consult_info(health_record_map, consult_info[0])
            res = order_check.order_check(consult_info)
            print(res)
    else:
        order_check.check(start_time, end_time)
