#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
structure_service.py -- segment sentences by jieba which loads some entity dicts
Author: chenxd
Create on 2018.07.10
"""

import json
from ailib.utils.exception import ArgumentLostException
from mednlp.kg.drgs.pathology_report_structure import EntityCharRelation
from mednlp.kg.structure import StructuredModel, list_entity
from mednlp.service.base_request_handler import BaseRequestHandler


structured_model = StructuredModel()
pathology_structured_model = EntityCharRelation()


class MedicalRecord(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(MedicalRecord, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query_str = self.request.body
        if query_str:
            query = json.loads(query_str, encoding='utf-8')
            if not query.get('source'):
                raise ArgumentLostException(['lost source'])
            chief_complaint = query.get('chief_complaint', '')
            medical_history = query.get('medical_history', '')
            past_medical_history = query.get('past_medical_history', '')
            personal_history = query.get('personal_history', '')
            allergic_history = query.get('allergic_history', '')
            family_history = query.get('family_history', '')
            physical_examination = query.get('physical_examination', '')
            inspection = query.get('inspection', '')
            general_info = query.get('general_info', '')
            diagnose = query.get('diagnose', '')
            pathology_report= query.get('pathology_report', '')
            ## 添加 开关是否启用 mmseg对实体里的部位进行提取
            ## 当model=1 的时候 不进行提取，其余提取
            model = query.get('model', -1)
        else:
            query = self.get_q_argument('*:*')
            chief_complaint = self.get_argument('chief_complaint', '')
            medical_history = self.get_argument('medical_history', '')
            past_medical_history = self.get_argument('past_medical_history', '')
            personal_history = self.get_argument('personal_history', '')
            allergic_history = self.get_argument('allergic_history', '')
            family_history = self.get_argument('family_history', '')
            physical_examination = self.get_argument('physical_examination', '')
            inspection = self.get_argument('inspection', '')
            general_info = self.get_argument('general_info', '')
            diagnose = self.get_argument('diagnose', '')
            pathology_report = self.get_argument('pathology_report', '')
            model = self.get_argument('model', -1)

        is_entity_extract = False if model == '1' else True

        result = {}
        structured_result = {}
        pos_list = list_entity
        content_type = ['chief_complaint', 'medical_history',
                        'past_medical_history', 'personal_history',
                        'allergic_history', 'family_history',
                        'physical_examination', 'inspection',
                        'general_info', 'diagnose', 'pathology_report']
        for ct in content_type:
            if eval(ct):
                if ct == 'pathology_report':
                    structured_result[ct] = pathology_structured_model.structured_result(
                        eval(ct), ct, pos_list)
                else:
                    structured_result[ct] = structured_model.structured_method(
                        eval(ct), ct, pos_list, is_entity_extract)
        result['data'] = structured_result
        return result


if __name__ == '__main__':
    handlers = [(r'/medical_record', MedicalRecord)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
