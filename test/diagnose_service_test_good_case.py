#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_service_test.py -- test the diagnose service

Author: maogy <maogy@guahao.com>
Create on 2017-09-02 Saturday.
"""

import sys
from optparse import OptionParser
from ailib.storage.db import DBWrapper
from ailib.client.ai_service_client import AIServiceClient
import mednlp.dao.loader as loader
import global_conf as global_conf


class DiagnoseServiceTest(object):
    steps = [1]

    def __init__(self, cfg_path, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')
        self.sql = """
        SELECT
            mr.disease_name,
            mr.chief_complaint,
            mr.medical_history
        FROM medical_data.medical_record_benchmark mr
        WHERE mr.is_deleted=0
        """
        self.sql = self.sql + ' %s'
        c_params = {'debug': kwargs.get('debug', False)}
        if 'port' in kwargs:
            c_params['port'] = kwargs.get('port')
        if 'step' in kwargs:
            self.steps = [int(s) for s in kwargs['step'].split(',')]
        self.client = AIServiceClient(
            global_conf.cfg_path, 'AIService', **c_params)

    def run(self, disease=None):

        where_sql = loader.create_id_where_clause(disease, 'mr.disease_name')
        mr_sql = self.sql % where_sql
        rows = self.db.get_rows(mr_sql)
        exception_count = 0
        for row in rows:
            for key in row.keys():
                if isinstance(row[key], bytes):
                    row[key] = str(row[key], encoding='utf-8')
            disease_name = row.get('disease_name', '')
            chief_complaint = row.get('chief_complaint', '')
            medical_history = row.get('medical_history', '')
            if chief_complaint or medical_history:
                parameters = {'chief_complaint': chief_complaint,
                              'medical_history': medical_history}
                response = self.client.query(parameters, 'diagnose_service')
                self.client.clear_url()
                code = response.get('code')
                if code:
                    exception_count += 1
                    sys.exit(0)
                diagnose_data = response['data'][:5]
                diagnose_disease = [d['disease_name'] for d in diagnose_data]
                if disease_name in diagnose_disease[:1]:
                    print('{}\n'
                          '1.选中一条患者记录，点击“查看”按钮\n'
                          '2.在“主诉”一栏输入“{}”；'
                          '在“现病史”一栏内输入“{}”\n'.format(
                           disease_name, chief_complaint, medical_history))
                    break


if __name__ == '__main__':
    command = """\n python %s [-d -c config_file]""" % sys.argv[0]
    diseases = []
    parser = OptionParser(usage=command)
    parser.add_option('-c', '--config', dest='config',
                      help='the config file', metavar='FILE')
    parser.add_option('-d', '--diseases', dest='diseases',
                      help='diseases to test', metavar='FILE')
    parser.add_option("-g", "--debug", action="store_true", dest="debug",
                      default=False, help="是否开启调试模式")
    parser.add_option("-r", "--run", action="store_true", dest="run",
                      default=False, help="开启普通运行模式")
    parser.add_option("-p", "--port", dest="port", help="测试服务端口")
    parser.add_option("-s", "--step", dest="step", help="测试step序列")
    (options, args) = parser.parse_args()
    if options.config is None:
        options.config = global_conf.cfg_path
    params = {}
    if options.run:
        params['run'] = 1
    if options.port:
        params['port'] = int(options.port)
    if options.step:
        params['step'] = options.step
    tester = DiagnoseServiceTest(options.config, debug=options.debug, **params)
    import codecs

    for d_name in codecs.open(global_conf.train_data_path + 'disease_100.txt'):
        tester.run(disease=[d_name.strip()])
