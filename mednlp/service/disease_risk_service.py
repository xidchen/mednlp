#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease_risk_service.py -- the service of disease risk prediction

Author: chenxd
Create on 2020-02-18 Tuesday
"""

import json
import time
import global_conf
from ailib.utils.exception import ArgumentLostException
from mednlp.model.disease_risk_model import DiseaseRiskModel
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.utils.file_operation import get_param_list


drm = DiseaseRiskModel(cfg_path=global_conf.cfg_path,
                       model_section='DISEASE_RISK_MODEL')
param_list = get_param_list(global_conf.disease_risk_param_list_path)


class DiseaseRiskService(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(DiseaseRiskService, self).initialize(runtime, **kwargs)

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
            query_list = []
            for param in param_list:
                query_list.append(
                    str(json.loads(self.request.body).get(param, '')))
            result = {'data': drm.predict(query=query_list)}
            result.update({'q_time': int((time.time() - start_time) * 1000)})
            return result


if __name__ == '__main__':
    handlers = [(r'/disease_risk', DiseaseRiskService)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
