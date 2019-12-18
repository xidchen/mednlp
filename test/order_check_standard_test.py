#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-08-09 Friday
@Desc:	业务质检测试
"""

import json
import codecs
from mednlp.service.order_check_standard import OrderCheckStandard

BASE_PATH = '/home/chaipf/work/mednlp/data/testdata/order_check_standard/'

class OrderCheckStandardTest():

    def __init__(self):
        self.ocs = OrderCheckStandard()

    def load_test_data(self):
        test_data = []
        with codecs.open(BASE_PATH + 'test_data.txt', 'r', 'utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('\t')
                if len(items) == 2:
                    order_id, order_check = items
                    test_data.append({'id': order_id, 'check_result': json.loads(order_check)})
        return test_data

    def load_consult_info(self):
        with codecs.open(BASE_PATH + 'consult_info.json', 'r', 'utf-8') as f:
            consult_info = json.load(f)
        return consult_info

    def _show_consult_info(self, consult_info):
        print('order: ' + str(consult_info['order_no']))
        print('reply: ' + '#'.join(consult_info['doctor_reply_list']).replace('\n', ''))
        print('--' * 30)

    def test(self, check_codes):
        check_result = {code: {'TP': 0, 'TN': 0, 'FP': 0, 'FN': 0, 'total': 0} for code in check_codes}

        test_data = self.load_test_data()
        consult_info = self.load_consult_info()

        for data in test_data[:1000]:
            info = consult_info.get(data['id'])
            if info:
                compliance_codes, violation_codes = self.ocs.order_check(info, check_codes)
                for code in check_codes:
                    check_result[code]['total'] += 1
                    if data['check_result'][code] == '1':
                        if str(code) in compliance_codes:
                            check_result[code]['TP'] += 1
                        elif code in violation_codes:
                            check_result[code]['FN'] += 1
                    elif data['check_result'][code] == '0':
                        if str(code) in compliance_codes:
                            check_result[code]['FP'] += 1
                        elif str(code) in violation_codes:
                            check_result[code]['TN'] += 1

        for code, result in check_result.items():
            print(code)
            check_total = result['TP'] + result['TN'] + result['FP'] + result['FN']
            acc = (result['TP'] + result['TN']) / check_total
            recal = check_total / result['total']
            print('acc: {}\trecal: {}'.format(acc, recal))


if __name__ == '__main__':
    ocst = OrderCheckStandardTest()
    ocst.test(['2', '3', '4', '5', '6'])
