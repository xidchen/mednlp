#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
breast_cancer_risk.py -- the service of diagnose Breast Cancer Risk

Author: chaipf <chaipf@guahao.com>
Create on 2019-04-23
"""

import json
import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.client.ai_service_client import AIServiceClient


class ArgumentException(Exception):
    code = 1
    message = 'Illegal Parameter'

class BusinessLogicException(Exception):
    code = 2
    message = 'Business logic exception'


aisc = AIServiceClient(global_conf.cfg_path, 'AIService')

class BreastCancerRisk(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(BreastCancerRisk, self).initialize(runtime, **kwargs)

    def post(self, *args, **kwargs):
        self.get()

    def get(self, *args, **kwargs):
        self.write_result(self._get())

    def _get(self):
        age = self.get_argument('age', '')
        biopsies_number = self.get_argument('biopsies_number', '')
        is_biopsy = self.get_argument('is_biopsy', '')
        menarchy_age = self.get_argument('menarchy_age', '')
        first_live_birth_age = self.get_argument('first_live_birth_age', '')
        brca_relatives_number = self.get_argument('brca_relatives_number', '')
        race = self.get_argument('race', '')

        query_str = self.request.body
        headers = self.request.headers
        content_type = headers.get('Content-type', None)
        if content_type and 'application/json' in content_type and query_str:
            query = json.loads(query_str, encoding='utf-8')
            age = query.get('age', '')
            biopsies_number = query.get('biopsies_number', '')
            is_biopsy = query.get('is_biopsy', '')
            menarchy_age = query.get('menarchy_age', '')
            first_live_birth_age = query.get('first_live_birth_age', '')
            brca_relatives_number = query.get('brca_relatives_number', '')
            race = query.get('race', '')

        requestData = {'age': str(age),
                       'biopsies_number': str(biopsies_number),
                       'is_biopsy': str(is_biopsy),
                       'menarchy_age': str(menarchy_age),
                       'first_live_birth_age': str(first_live_birth_age),
                       'brca_relatives_number': str(brca_relatives_number),
                       'race': str(race)}

        try:
            queryReturn = aisc.query(json.dumps(requestData), 'calculate_breast_cancer_risk')
        except Exception as e:
            print('Request calculate_breast_cancer_risk Error')
            print(e)
            return ArgumentException
        if len(queryReturn) == 4:
            if all(queryReturn):
                return {
                    'data': {
                        "user_risk_5": queryReturn[0],
                        "avg_risk_5": queryReturn[1],
                        "user_risk_90": queryReturn[2],
                        "avg_risk_90": queryReturn[3]
                    }
                }
            else:
                return ArgumentException
        else:
            return BusinessLogicException


if __name__ == '__main__':
    handlers = [(r'/breast_cancer_risk', BreastCancerRisk)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
