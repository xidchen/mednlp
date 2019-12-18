#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_suggest_model.py -- the service of diagnose suggest model

Author: chenxd <chenxd@guahao.com>
Create on 2019-01-29 Tuesday
"""


import json
import time
import tornado.web
import ailib.service.base_service as base_service
from tornado.options import define, options
from ailib.utils.exception import ArgumentLostException
from mednlp.cdss.medical_record import MedicalRecordParser
from mednlp.cdss.suggest import DiagnoseSuggest
from mednlp.dao.kg_dao import KGDao
from mednlp.service.base_request_handler import BaseRequestHandler


class DiagnoseSuggestModel(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super().initialize()

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        if not self.request.body:
            if not self.get_q_argument('', limit=10000):
                return ArgumentLostException(['lost post data'])
        else:
            start_time = time.time()
            decoded_json = json.loads(self.request.body)
            source = decoded_json.get('source', '')
            chief_complaint = decoded_json.get('chief_complaint', '')
            medical_history = decoded_json.get('medical_history', '')
            pmh = decoded_json.get('past_medical_history', '')
            ins = decoded_json.get('general_info', '')
            pe = decoded_json.get('physical_examination', '')
            dept = decoded_json.get('department', '')
            sex = decoded_json.get('sex', '-1')
            age = decoded_json.get('age', '0')
            suggest_disease = decoded_json.get('diagnose_disease', [])
            field = decoded_json.get('suggest_type', '')
            field = field if field in ['symptom', 'inspection'] else ''
            if not field:
                return {}
            if medical_history:
                chief_complaint += '..' + medical_history
            medical_record = {'source': source,
                              'chief_complaint': chief_complaint,
                              'medical_history': medical_history,
                              'past_medical_history': pmh,
                              'inspection': ins,
                              'physical_examination': pe,
                              'department': dept,
                              'sex': sex, 'age': age}
            mr_parsed = mr_parser.parse(medical_record)
            match_symptom = set()
            symptom_synonym_group = set()
            if mr_parsed.get('chief_complaint'):
                symptom_synonym_group = mr_parsed[
                    'chief_complaint']['symptom_synonym']
            for synonym_group in symptom_synonym_group:
                for synonym_symptom_id in synonym_group:
                    match_symptom.add(synonym_symptom_id)

            if lstm_port:
                suggest = DiagnoseSuggest(suggest_disease, mr=medical_record,
                                          match_symptom=match_symptom,
                                          lstm_port=lstm_port)
            else:
                suggest = DiagnoseSuggest(suggest_disease, mr=medical_record,
                                          match_symptom=match_symptom)
            suggestion, api_code = suggest.model_suggest(field)
            result = {'data': suggestion}
            if api_code:
                result['code'] = 2
            result.update({'q_time': int((time.time() - start_time) * 1000)})
            return result


if __name__ == '__main__':
    define('lstm_port', default=None, help='run on the given port', type=int)
    tornado.options.parse_command_line()
    mr_parser = MedicalRecordParser(debug=False)
    kg = KGDao()
    lstm_port = ''
    if options.lstm_port:
        lstm_port = options.lstm_port
    handlers = [(r'/diagnose_suggest_model', DiagnoseSuggestModel)]
    base_service.run(handlers)
