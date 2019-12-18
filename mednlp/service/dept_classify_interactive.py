#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dept_classify_interactive.py -- the interactive service of dept classify

Author: maogy <maogy@guahao.com>
Create on 2018-01-29 Monday.
"""


import os
import sys
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.exception import DeptClassifyException
from mednlp.model.dept_classify_model import DeptClassifyInteractiveModel
import global_conf


aisc = AIServiceClient(global_conf.cfg_path, 'AIService')
dcim = DeptClassifyInteractiveModel()


class DeptClassifyInteractive(BaseRequestHandler):

    def initialize(self, runtime=None,  **kwargs):
        super(DeptClassifyInteractive, self).initialize(runtime, **kwargs)

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query = str(self.get_q_argument('', limit=1000))
        age = self.get_argument('age', '-1')
        sex = self.get_argument('sex', '0')
        fl = self.get_argument('fl', 'dept_name')
        rows = self.get_argument('rows', 1)
        symptoms = self.get_argument('symptom', '')
        interactive = self.get_argument('interactive', 1)
        level = self.get_argument('level', 2)
        dept_set = self.get_argument('dept_set', 1)
        result = {}
        if not query:
            result = {'code': 1, 'message': 'query 参数不能为空'}
            return result
        if symptoms and symptoms != '-1':
            query = query + str(symptoms)
        params = {'q': query, 'rows': rows, 'fl': fl, 'age': age,
                  'sex': sex, 'level': level, 'dept_set': dept_set}
        # return params
        dept_result = aisc.query(params, 'dept_classify')
        depts = []
        if (dept_result and dept_result['data']):
            depts = dept_result['data']
        result_data = dcim.predict(query, sex, age, symptoms=symptoms,
                                   debug=self.debug, interactive=interactive)
        if not result_data:
            raise DeptClassifyException(query)
        result_data['totalCount'] = len(depts)
        result_data['depts'] = depts
        result = {'data': result_data, 'code': dept_result['code'], 'message': dept_result['message']}
        return result


if __name__ == '__main__':
    handlers = [(r'/dept_classify_interactive', DeptClassifyInteractive)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
