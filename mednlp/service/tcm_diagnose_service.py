#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-30 Tuesday
@Desc:	中医诊断服务
"""

import json
import codecs
import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.tcm_diagnose_model import TCMDiagnoseModel
from ailib.utils.exception import AIServiceException


disease_diagnose_model = TCMDiagnoseModel(model_version=0, diagnose_type='1',
                                          cfg_path=global_conf.cfg_path, model_section='TCM_DIAGNOSE_MODEL')
disease_syndrome_dict = {}
with codecs.open(global_conf.tcm_disease_syndrome_path, 'r', 'utf-8') as f:
    disease_syndrome_dict = json.loads(f.readline())

class TCMDiagnoseService(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.write_result(self._get())

    def _get(self):
        arguments = {'source': None, 'sex': None, 'age': None, 'visits': '', 'chief_complaint': '',
                     'medical_history': '', 'past_medical_history': '', 'physical_examination': '',
                     'general_info': ''}
        self.parse_arguments(arguments)
        # 必传参数校验
        if not (arguments['source'] and arguments['sex'] and arguments['age']):
            return AIServiceException
        try:
            age = int(arguments['age'])
        except Exception:
            age = 0
        sex = arguments['sex']
        query = arguments['chief_complaint'] + arguments['medical_history'] + arguments['past_medical_history']
        predict_result = disease_diagnose_model.predict(query, age, sex)
        diseases = []
        for pr in predict_result:
            syndromes_result = []
            for syndrome in pr['syndromes']:
                prescription_result = []
                for prescription in syndrome['prescription']:
                    prescription_result.append({'prescription_name': prescription['entity_name'],
                                                'prescription_id': prescription['id'],
                                                'score': float(prescription['score'])})
                syndromes_result.append({'syndrome_name': syndrome['entity_name'],
                                         'syndrome_id': syndrome['entity_id'],
                                         'score': float(syndrome['score']),
                                         'prescription': prescription_result})
            diseases.append({'disease_name': pr['entity_name'],
                             'syndrome_id': pr['entity_id'],
                             'score': float(pr['score']),
                             'syndromes': syndromes_result})
        result = {'code': 0, 'message': 'successful'}
        result['data'] = {'totalCount': len(diseases), 'diseases': diseases}
        return result


if __name__ == '__main__':
    handlers = [(r'/tcm_diagnose_service', TCMDiagnoseService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
