#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
union_knowledge_service.py -- the service of graphql

Author: chenxk <chenxk@guahao.com>
Create on 2019-08-19 monday.
"""

import traceback
import json
import graphene
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.utils.exception import AIServiceException
from mednlp.dao.graphql_schema import Query

class UnionKnowledgeService(BaseRequestHandler):

    not_none_field = ['query_str']

    def initialize(self, runtime=None, **kwargs):
        super(UnionKnowledgeService, self).initialize(runtime, **kwargs)
        self.graphql_tool = graphene.Schema(query=Query, auto_camelcase=False)

    def post(self):
        try:
            if self.request.body:
                self.get(query_str=str(self.request.body, encoding='utf-8'))
        except Exception:
            raise AIServiceException(self.request.body)

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self, **kwargs):
        query_str = kwargs.get('query_str')
        # query_str = query_str.replace('\\', '')
        try:
            response = self.graphql_tool.execute(query_str)
        except:
            traceback.print_exc()
            raise Exception('graphql exception')

        return response

    def check_parameter(self, parameters):
        for field in self.not_none_field:
            if field not in parameters:
                raise AIServiceException(field)


if __name__ == '__main__':
    handlers = [(r'/union_knowledge', UnionKnowledgeService)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
