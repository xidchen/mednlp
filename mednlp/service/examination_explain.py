#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
examination_explain.py

Author: chenxd
Create on 2019-03-13 Wednesday.
"""

import json
import logging
from ailib.utils.exception import AIServiceException, ArgumentLostException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.kg.conf import kg_conf
from mednlp.kg.examination import ExaminationExplain

# from mednlp.kg.standard_entity import DataTrans
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

# data_model = DataTrans()
explain_model = ExaminationExplain()


class Examination(BaseRequestHandler):
    not_none_field = []

    def initialize(self, runtime=None, **kwargs):
        super(Examination, self).initialize(runtime, **kwargs)

    def post(self):
        try:
            if self.request.body:
                input_obj = json.loads(self.request.body)
                self.get(input_obj=input_obj)
        except Exception:
            raise AIServiceException(self.request.body)

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self, **kwargs):
        input_obj = kwargs.get('input_obj')
        source = input_obj.get('source')
        if not source:
            raise ArgumentLostException(['lost source'])
        fl = input_obj.get('fl')
        if not fl:
            raise ArgumentLostException(['lost source'])
        sex = input_obj.get('sex', '-1')  # 默认性别位置
        age = input_obj.get('age', '7300')  # 默认成年20岁
        organization = input_obj.get('organization')
        examination = input_obj.get('examination')
        # examination = data_model.data_trans(examination)
        # logging.info('fl的类型是：%s' % (",".join(fl)))
        logging.info('入参: ' + str(input_obj))
        result = {'data': {}}
        if examination:
            explain_result = explain_model.get_explain(fl, examination, gender=sex, age=age)
        else:
            explain_result = {}
        result['data'] = explain_result
        return result


if __name__ == '__main__':
    handlers = [(r'/medical_examination', Examination)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
