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

    steps = [1, 3, 5]

    def __init__(self, cfg_path, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')
        self.sql = """
        SELECT
            mr.disease_name,
            mr.sex,
            mr.age,
            mr.chief_complaint,
            mr.medical_history,
            mr.past_medical_history,
            ins.inspection,
            pe.physical_exam
        FROM medical_data.medical_record_benchmark mr
        LEFT JOIN ai_medical_knowledge.medical_record_inspection ins
        ON mr.hospital_record_id = ins.hospital_record_id
        LEFT JOIN ai_medical_knowledge.medical_record_physical_exam pe
        ON mr.hospital_record_id = pe.hospital_record_id
        WHERE mr.is_deleted = 0
        """
        self.run_sql = """
        SELECT
            mr.disease_name,
            mr.sex,
            mr.age,
            mr.chief_complaint,
            mr.medical_history
        FROM medical_data.medical_record mr
        WHERE mr.state=1
        ORDER BY mr.disease_name
        """
        if kwargs.get('run'):
            self.sql = self.run_sql
        self.sql = self.sql + ' %s'
        c_params = {'debug': kwargs.get('debug', False)}
        if 'port' in kwargs:
            c_params['port'] = kwargs.get('port')
        if 'step' in kwargs:
            self.steps = [int(s) for s in kwargs['step'].split(',')]
        self.client = AIServiceClient(
            global_conf.cfg_path, 'AIService', **c_params)

    def run(self, disease=None):

        where_sql = loader.create_id_where_clause(
            disease, 'mr.disease_name')
        mr_sql = self.sql % where_sql
        rows = self.db.get_rows(mr_sql)
        step_info = {}
        for step in self.steps:
            step_info[step] = {
                'find_count': 0, 'not_find_count': 0,
                'find_chief_complaint': [], 'not_find_chief_complaint': [],
                'disease_count': {}}
        exception_count = 0
        wrong_prediction_count = 0
        for row in rows:
            for key in row.keys():
                if isinstance(row[key], bytes):
                    row[key] = str(row[key], encoding='utf-8')
            chief_complaint = row.get('chief_complaint', '')
            medical_history = row.get('medical_history', '')
            inspection = row.get('inspection', '')
            physical_exam = row.get('physical_exam', '')
            past_medical_history = row.get('past_medical_history', '')
            sex = row.get('sex', '-1')
            if sex in (1, '1'):
                sex = 2
            elif sex in (2, '2'):
                sex = 1
            else:
                sex = -1
            age = row.get('age', 1)
            if age and age > 0:
                if age == 1:
                    age = 1
                else:
                    age = int(age) * 365
            disease_name = str(row.get('disease_name', '').strip())
            if chief_complaint or medical_history:
                parameters = {'chief_complaint': chief_complaint,
                              'medical_history': medical_history,
                              'past_medical_history': past_medical_history,
                              'general_info': inspection,
                              'physical_examination': physical_exam,
                              'sex': sex}
                if age and age > 0:
                    parameters['age'] = age
                response = self.client.query(parameters, 'diagnose_service')
                self.client.clear_url()
                code = response.get('code')
                if code:
                    exception_count += 1
                    sys.exit(0)
                diagnose_data = response['data'][:5]
                diagnose_disease = [str(d['disease_name'])
                                    for d in diagnose_data]
                for step in self.steps:
                    step_disease = diagnose_disease[0: step]
                    info = step_info.get(step)
                    count_dict = info['disease_count'].setdefault(
                        disease_name, {'find': 0, 'not_find': 0})
                    content = chief_complaint + medical_history
                    if disease_name in step_disease:
                        info['find_count'] += 1
                        count_dict['find'] += 1
                        info['find_chief_complaint'].append(content)
                    else:
                        info['not_find_count'] += 1
                        count_dict['not_find'] += 1
                        info['not_find_chief_complaint'].append(content)
                        if step == 5:
                            if not chief_complaint:
                                chief_complaint = ''
                            if not medical_history:
                                medical_history = ''
                            if not past_medical_history:
                                past_medical_history = ''
                            if not inspection:
                                inspection = ''
                            if not physical_exam:
                                physical_exam = ''
                            content = '\t'.join([
                                chief_complaint, medical_history,
                                past_medical_history, physical_exam, inspection
                            ])
                            content += '\t'
                            sex = sex if sex else '0'
                            age = float(age / 365)
                            content += '\t'.join([str(sex), str(age)])
                            prediction = ', '.join(step_disease)
                            wrong_prediction_count += 1
                            print(wrong_prediction_count, '. ', content)
                            print('Predictions: ', prediction)
                            print('Actual Diagnose: ', disease_name)
                            print('\n')


if __name__ == '__main__':
    command = """\n python %s [-d -c config_file]""" % sys.argv[0]
    diseases = []
    parser = OptionParser(usage=command)
    parser.add_option('-c', '--config', dest='config', help='the config file',
                      metavar='FILE')
    parser.add_option('-d', '--disease', dest='disease', help='disease to test',
                      metavar='FILE')
    parser.add_option("-g", "--debug", action="store_true", dest="debug",
                      default=False, help="是否开启调试模式")
    parser.add_option("-r", "--run", action="store_true", dest="run",
                      default=False, help="开启普通运行模式")
    parser.add_option("-p", "--port", dest="port", help="测试服务端口")
    parser.add_option("-s", "--step", dest="step", help="测试step序列")
    (options, args) = parser.parse_args()
    if options.config is None:
        options.config = global_conf.cfg_path
    if options.disease is not None:
        diseases = options.disease.split(',')
    params = {}
    if options.run:
        params['run'] = 1
    if options.port:
        params['port'] = int(options.port)
    if options.step:
        params['step'] = options.step
    tester = DiagnoseServiceTest(options.config, debug=options.debug, **params)
    tester.run(disease=diseases)
