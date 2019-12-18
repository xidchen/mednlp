#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
consistency_model.py -- the servce of text's consistency model

Author: yinwd <yinwd@guahao.com>
Create on 2019-05-07.
"""

import re
import json
import global_conf
from mednlp.service.base_request_handler  import BaseRequestHandler
from ailib.utils.exception import ArgumentLostException
from mednlp.text.similar_model.consistency_model import ConsistencyModel

consistency_model = ConsistencyModel(cfg_path=global_conf.cfg_path, model_section='CONSISTENCY_MODEL')

class Consistency(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(Consistency, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query = self.get_q_argument('', escape=False, limit=1000)
        if query:
            # print('method:get')
            source = self.get_argument('source')
            content = self.get_argument('content')
            disease_name = self.get_argument('disease_name')
        else:
            # print('method:post')
            query_str = self.request.body
            query_list = json.loads(query_str, encoding='utf-8')
            source = query_list.get('source')
            content = query_list.get('content')
            disease_name = query_list.get('disease_name')

        if not source:
            raise ArgumentLostException(['source'])
        if not content:
            raise ArgumentLostException(['content'])
        if not disease_name:
            raise ArgumentLostException(['disease_name'])

        result = {}
        result['data'] = consistency_model.predict_probability(content, disease_name)
        return result


if __name__ == '__main__':
    handlers = [(r'/consistency_model', Consistency)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
