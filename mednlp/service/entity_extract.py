#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
entity_extract.py -- the service of entity extraction

Author: chenxd
Create on 2018-12-14.
"""

import re
import json
from ailib.utils.exception import ArgumentLostException
from mednlp.service.base_request_handler  import BaseRequestHandler
from mednlp.text.entity_extract import Entity_Extract


entity_extractor = Entity_Extract()


class EntityExtract(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(EntityExtract, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query = self.get_q_argument('', escape=False, limit=1000)
        if query:
            # print('method:get')
            is_stop_word = self.get_argument('stop_word', '0')
            type_str = self.get_argument('type', '')
            property_str = self.get_argument('property', '')
        else:
            # print('method:post')
            query_list = json.loads(self.request.body, encoding='utf-8')
            # print(type(query_str))
            query = query_list.get('q')
            is_stop_word = query_list.get('stop_word', '0')
            type_str = query_list.get('type', '')
            property_str = query_list.get('property', '')

        type_list = re.split('[，,]', type_str) if type_str else []
        property_list = re.split('[，,]', property_str) if property_str else []
        # print(property_str, property)
        if not query:
            raise ArgumentLostException(['q'])
        result = {'data': entity_extractor.result_filter(
            query, type_list, property_list, is_stop_word)}
        return result


if __name__ == '__main__':
    handlers = [(r'/entity_extract', EntityExtract)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
