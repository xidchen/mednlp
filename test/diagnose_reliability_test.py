# -*- coding: utf-8 -*-

import sys
import global_conf
from optparse import OptionParser
from ailib.storage.db import DBWrapper
from ailib.client.ai_service_client import AIServiceClient

class DiagnoseReliabilityTest():
    "诊断可靠性接口测试"

    def __init__(self, cfg_path, **kwargs):
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
        c_params = {'debug': kwargs.get('debug', False)}
        if 'port' in kwargs:
            c_params['port'] = kwargs.get('port')
        self.client = AIServiceClient(global_conf.cfg_path, 'AIService', **c_params)

    def test(self):
        sql = self.sql
        rows = self.db.get_rows(sql)
        total, confirmedCount, correctCount, exceptionCount = 0, 0, 0, 0
        for row in rows[:10]:
            total += 1
            (response, diseaseName) = self.get_result(row)
            code = response.get('code')
            if code:
                exceptionCount += 1
            top1 = response['data'][0] if len(response['data']) > 0 else {}
            diagnoseResult = top1.get('disease_name', '')
            diagnoseResultAccuracy = float(top1.get('accuracy', '0'))
            if diagnoseResultAccuracy >= 0.9:
                confirmedCount += 1
                if diagnoseResult == diseaseName:
                    correctCount += 1

        if total == 0:
            print('total count is 0')
            return
        if confirmedCount == 0:
            print('confirmed count is 0')
            return
        print('request error: {}'.format(exceptionCount))
        print('total: {}\t confirmed: {}\t correct: {}\t'.format(total, confirmedCount, correctCount))
        print('fraction of coverage: {}'.format(confirmedCount / total))
        print('precision: {}'.format(correctCount / confirmedCount))

    def get_result(self, row):
        for k, v in row.items():
            if isinstance(v, bytes):
                row[k] = str(v, encoding="utf-8")
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
            age = 1 if age == 1 else int(age) * 365
        diseaseName = str(row.get('disease_name', '').strip())
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
        return (response, diseaseName)


if __name__ == '__main__':
    command = """\n python %s [-c config_file]""" % sys.argv[0]
    diseases = []
    parser = OptionParser(usage=command)
    parser.add_option('-c', '--config', dest='config', help='the config file',
                      metavar='FILE')
    parser.add_option("-p", "--port", dest="port", help="测试服务端口")
    (options, args) = parser.parse_args()
    if options.config is None:
        options.config = global_conf.cfg_path
    params = {}
    if options.port:
        params['port'] = int(options.port)

    drt = DiagnoseReliabilityTest(options.config, **params)
    drt.test()
