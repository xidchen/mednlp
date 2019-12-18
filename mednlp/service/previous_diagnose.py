#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
previous_diagnose.py -- previous diagnose service

Author: maogy <maogy@guahao.com>
Create on 2018-08-04 Saturday.
"""


import json
import yaml
import global_conf
from base_request_handler import BaseRequestHandler
from mednlp.dialog.dialog_manager import PreviousDiagnoseDialog
from ailib.utils.exception import ArgumentLostException
import mednlp.dialog.dialog_constant as constant


pd_dialog = PreviousDiagnoseDialog()


class PreviousDiagnose(BaseRequestHandler):

    def initialize(self, runtime=None,  **kwargs):
        super(PreviousDiagnose, self).initialize(runtime, **kwargs)

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
        query = yaml.safe_load(query_str)
        if not query.get('source'):
            raise ArgumentLostException(['lost source'])
        if 'input' not in query:
            raise ArgumentLostException(['lost input'])
        inputs = query.get('input')
        if not isinstance(inputs, list):
            raise TypeError('参数 input 应该是list类型 ！！')
        
        answer = pd_dialog.answer(inputs, biz=constant.BIZ_PRE_DIAGNOSE)
        # print(answer)
        result = {'data': answer}
        return result


if __name__ == '__main__':
    handlers = [(r'/previous_diagnose', PreviousDiagnose)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)        
