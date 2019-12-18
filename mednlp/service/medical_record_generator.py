#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-05-27 Monday
@Desc:	病例辅助书写接口
"""

import json
import ailib.service.base_service as base_service
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.utils.exception import AIServiceException
from mednlp.kg.medical_record_generator import MedicalRecordGenerator

generator = MedicalRecordGenerator()

class MedicalRecordGeneratorServer(BaseRequestHandler):
    def initialize(self, runtime=None, **kwargs):
        super(MedicalRecordGeneratorServer, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        arguments = {'source': None, 'patient_user_id': '', 'patient_id': '', 'doctor_user_id': None,
                     'order_info_id': '', 'dialogue': [], 'fl': '', 'sex': None, 'age': None, 'chief_complaint': '',
                     'medical_history': '', 'allergy_history': '', 'past_medical_history': '',
                     'surgical_trauma_history': '', 'personal_history': '', 'family_history': '',
                     'body_temperature': 0.0, 'body_weight': 0.0, 'height': 0.0, 'heart_rate': 0.0,
                     'systolic_blood_pressure': 0.0, 'diastolic_blood_pressure': 0.0,
                     'physical_examination': '', 'general_info': '', 'mode': 0, 'disease_set': 0,
                     'department': '', 'diagnose': '', 'treatment_advice': '', 'disease_lable': []}
        self.parse_arguments(arguments)
        if arguments.get('source') is None:
            return AIServiceException
        if arguments.get('doctor_user_id') is None:
            return AIServiceException
        if arguments.get('sex') is None or arguments.get('age') is None:
            return AIServiceException

        # 获取问诊信息
        dialogue = arguments.get('dialogue')
        if isinstance(dialogue, str):
            dialogue = json.loads(dialogue)
        if len(dialogue) == 0:
            dialogue = generator.get_consult_message(arguments)
        arguments['dialogue'] = dialogue

        suggest_info = generator.get_suggest(arguments)
        diagnose_info, advices = generator.get_diagnose_info(arguments)

        treatment_advice = {'text': arguments.get('treatment_advice'), 'entities': []}
        for advice in advices:
            entity = {'content': '', 'entity_name': '', 'entity_id': '', 'time_endurance': '',
                      'type': '', 'relate_symptom': '', 'remark': '', 'time_happen': '',
                      'data_source': 1, 'status': -1, 'family_relation': ''}
            if advice not in treatment_advice['text']:
                entity['content'] = advice
                treatment_advice['entities'].append(entity)

        data = suggest_info
        data['diagnose'] = diagnose_info
        data['treatment_advice'] = treatment_advice
        for _f in arguments.get('fl').split(','):
            # 返回获取到的问诊对话内容
            if _f == 'dialogue':
                data['dialogue'] = arguments.get('dialogue')
        return {'data': data}


if __name__ == '__main__':
    handlers = [(r'/medical_record_generator', MedicalRecordGeneratorServer)]
    base_service.run(handlers)
