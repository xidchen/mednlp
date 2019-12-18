#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_reliability.py -- 诊断可靠性服务

Author: chaipf <chaipf@guahao.com>
Create on 2019-04-10
"""

import json
import time
from ailib.utils.exception import ArgumentLostException, AIServiceException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.diagnose_reliability_classifier import DiagnoseReliabilityClassifier
import global_conf


dr = DiagnoseReliabilityClassifier(cfg_path=global_conf.cfg_path, model_section='DIAGNOSE_RELIABILITY_MODEL')


class DiagnoseReliability(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(DiagnoseReliability, self).initialize(runtime, **kwargs)

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
            body = json.loads(self.request.body)
            diseases = body.get('diseases', [])
            try:
                newDiseases = dr.calc_accuracy(diseases)
            except:
                return AIServiceException()
            result = {'data': {'diseases': newDiseases}}
            result.update({'q_time': int((time.time() - start_time) * 1000)})
            return result


if __name__ == '__main__':
    handlers = [(r'/diagnose_reliability', DiagnoseReliability)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
