#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-30 Tuesday
@Desc:	中医辅助诊断测试程序
"""


import sys
import global_conf
import codecs
from optparse import OptionParser
from ailib.client.ai_service_client import AIServiceClient


class DiagnoseServiceTest(object):

    def __init__(self, test_file, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.test_file = test_file
        c_params = {'debug': kwargs.get('debug', False)}
        if 'port' in kwargs:
            c_params['port'] = kwargs.get('port')
        if 'step' in kwargs:
            self.steps = [int(s) for s in kwargs['step'].split(',')]

        self.client = AIServiceClient(global_conf.cfg_path, 'AIService', **c_params)

    def run(self, diagnose_type):
        test_data = []
        with codecs.open(self.test_file, 'r', 'utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('\t')
                if len(items) == 4:
                    test_data.append(items)

        accuracy = {s: 0 for s in self.steps}
        for td in test_data:
            para = {'source': 0, 'age': td[1], 'sex': td[2], 'chief_complaint': td[3]}
            if td[2] == '0':
                # 女
                sex = 1
            elif td[2] == '1':
                sex = 2
            else:
                sex = -1
            age = int(td[1]) * 365
            para['sex'] = sex
            para['age'] = age
            response = self.client.query(para, 'tcm_diagnose_service')
            self.client.clear_url()
            code = response.get('code')
            if code:
                print(para)
                sys.exit(0)
            if diagnose_type == '2':
                diagnose_data = response['data']['syndrome'][:3]
                diagnose_disease = [str(d['syndrome_name']) for d in diagnose_data]
            else:
                diagnose_data = response['data']['diseases'][:3]
                diagnose_disease = [str(d['disease_name']) for d in diagnose_data]

            for step in self.steps:
                step_disease = diagnose_disease[0: step]
                if td[0] in step_disease:
                    accuracy[step] += 1
        count = len(test_data)
        for i, v in accuracy.items():
            print('top{}\t{}\t{}'.format(i, v, v / count))


if __name__ == '__main__':
    command = """\n python %s [-d -c config_file]""" % sys.argv[0]
    diseases = []
    parser = OptionParser(usage=command)
    parser.add_option('-f', '--testfile', dest='test_file', help='test file', metavar='FILE')
    parser.add_option('-t', '--diagnose_type', dest='diagnose_type', default='1', help='diagnose type')
    parser.add_option("-g", "--debug", action="store_true", dest="debug", default=False, help="是否开启调试模式")
    parser.add_option("-p", "--port", dest="port", default='7788', help="测试服务端口")
    parser.add_option("-s", "--step", dest="step", default='1,2,3', help="测试step序列")
    (options, args) = parser.parse_args()
    params = {}
    if options.port:
        params['port'] = int(options.port)
    if options.step:
        params['step'] = options.step
    tester = DiagnoseServiceTest(options.test_file, debug=options.debug, **params)
    tester.run(options.diagnose_type)
