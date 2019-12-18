#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
base_request_handler.py -- the base request handler to wrap some global object
for base_search

Author: maogy
Create on 2017-04-24 Monday.
"""


import json
import global_conf
from ailib.client.solr import Solr
from ailib.client.cloud_solr import CloudSolr
from ailib.service.base_service import BaseService


solr = Solr(global_conf.cfg_path)
cloud_search = CloudSolr(global_conf.cfg_path)


class BaseRequestHandler(BaseService):
    """
    Base Request Handler for CDSS
    """

    def data_received(self, chunk):
        pass

    def initialize(self, runtime=None, **kwargs):
        """
        init the global object and BaseSearch.initialize
        """
        if runtime is None:
            runtime = {}
        runtime['solr'] = solr
        runtime['cloud_search'] = cloud_search
        super(BaseRequestHandler, self).initialize(runtime, **kwargs)

    def parse_arguments(self, arguments):
        request_type = 'form'
        for key, val in arguments.items():
            arguments[key] = self.get_argument(key, val)

        query_str = self.request.body
        headers = self.request.headers
        content_type = headers.get('Content-type', None)
        if content_type and 'application/json' in content_type and query_str:
            request_type = 'body_json'
            query = json.loads(query_str, encoding='utf-8')
            for key, val in arguments.items():
                arguments[key] = query.get(key, val)

        return request_type
