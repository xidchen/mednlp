#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
underwriting_service.py -- the service of underwriting

"""

import json
import time
from ailib.utils.exception import ArgumentLostException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.underwriting_rule import UnderwritingRule


uw_rule = UnderwritingRule()


class UnderwritingService(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(UnderwritingService, self).initialize(runtime, **kwargs)

    def post(self, *args, **kwargs):
        self.get()

    def get(self, *args, **kwargs):
        self.write_result(self._get())

    def _get(self):
        start_time = time.time()
        if not self.request.body:
            if not self.get_q_argument('', limit=10000):
                return ArgumentLostException(['lost post data'])
        else:
            decoded_json = json.loads(self.request.body)
            query = decoded_json.get('query', {})
            result = uw_rule.decide(query=query)
            result.update({'q_time': int((time.time() - start_time) * 1000)})
            return result


if __name__ == '__main__':
    handlers = [(r'/underwriting_service', UnderwritingService)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
