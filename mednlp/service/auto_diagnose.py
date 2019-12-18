#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
previous_diagnose.py -- previous diagnose service

Author: renyx <renyx@guahao.com>
Create on 2018-08-21 TuesDay.
"""


import json
import yaml
from base_request_handler import BaseRequestHandler
from mednlp.dialog.dialog_manager import AutoDiagnoseDialog
from ailib.utils.exception import ArgumentLostException
import mednlp.dialog.dialog_constant as constant


auto_dialog = AutoDiagnoseDialog()


class AutoDiagnose(BaseRequestHandler):

    def initialize(self, runtime=None,  **kwargs):
        super(AutoDiagnose, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query_str = self.request.body
        if not query_str:
            query_str = self.get_q_argument('', limit=10000)
            if not query_str:
                raise ArgumentLostException(['lost post data'])
        # query = yaml.safe_load(query_str)
        query = json.loads(query_str, encoding='utf-8')
        if not query.get('source'):
            raise ArgumentLostException(['lost source'])
        if 'input' not in query:
            raise ArgumentLostException(['lost input'])
        inputs = query.get('input')
        terminate = int(query.get(constant.BIZ_TERMINATE_FIELD, 0))
        dialogue = query.get('dialogue', {})
        if not isinstance(inputs, list):
            raise TypeError('参数 input 应该是list类型 ！！')
        answer = auto_dialog.answer(inputs, biz=constant.BIZ_AUTO_DIAGNOSE, terminate=terminate, dialogue=dialogue)
        # print(answer)
        result = {'data': answer}
        return result


if __name__ == '__main__':
    handlers = [(r'/auto_diagnose', AutoDiagnose)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
