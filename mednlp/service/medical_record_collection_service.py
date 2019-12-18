#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-31 Wednesday
@Desc:  辅助问诊服务
"""

from ailib.utils.exception import AIServiceException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.cdss.medical_record_collection import MedicalRecordCollection
from mednlp.cdss.medical_record_backfill import BackFillTemplate

mrc = MedicalRecordCollection()
bt = BackFillTemplate()

class MedicalRecordCollectionService(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.write_result(self._get())

    def _get(self):
        arguments = {'source': None, 'sex': None, 'age': None, 'visit_type': 1, 'symptom': '',
                     'critical_situation': [], 'main_symptom': [], 'accompanying_symptoms': [],
                     'treatment_process': [], 'common_signs': [], 'past_history': [],
                     'surgical_history': [], 'allergy_history': [], 'blood_transfusion_history': [],
                     'family_history': [], 'personal_history': [], 'marital_history': [],
                     'menstrual_history': [], 'general_info': [], 'examination': [], 'check': [],
                     'fl': ''}
        self.parse_arguments(arguments)
        for must_arg in ('source', 'sex', 'age'):
            if arguments.get(must_arg) is None:
                return AIServiceException

        data = {}
        fl = arguments.get('fl')
        # 常见症状
        if '*' in fl or 'common_symptom' in fl:
            data['common_symptom'] = mrc.get_common_symptom()
        else:
            data['common_symptom'] = []
        # 问诊内容
        data['interrogation_content'] = mrc.get_inquiry_content(arguments['symptom'],
                                                                arguments['age'],
                                                                arguments['sex'],
                                                                arguments['fl'])
        data.update(bt.get_back_fill(arguments))
        result = {'code': 0, 'message': 'successful', 'data': data}
        # if arguments['visit_type'] in (2, '2'):
            # print('qwer')
            # print(arguments)
            # print('zxcv')
        return result


if __name__ == '__main__':
    handlers = [(r'/medical_record_collection', MedicalRecordCollectionService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
