#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_lstm.py -- the service of diagnose using LSTM model in batch

Author: chenxd <chenxd@guahao.com>
Create on 2019-01-03 Thursday
"""

import json
import time
import global_conf
from ailib.utils.exception import ArgumentLostException
from mednlp.model.disease_classify_lstm_model import DiseaseClassifyLSTM
from mednlp.service.base_request_handler import BaseRequestHandler


dcm = DiseaseClassifyLSTM(cfg_path=global_conf.cfg_path,
                          model_section='DISEASE_CLASSIFY_MODEL')


class DiagnoseLSTM(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(DiagnoseLSTM, self).initialize(runtime, **kwargs)

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
            medical_record = decoded_json.get('medical_record', [])
            rows = decoded_json.get('rows', '10')
            try:
                rows = int(rows) if rows else 10
            except ValueError:
                rows = 10
            diagnosis = dcm.predict(medical_record=medical_record, rows=rows)
            result = {'diagnosis': diagnosis}
            result.update({'q_time': int((time.time() - start_time) * 1000)})
            return result


if __name__ == '__main__':
    handlers = [(r'/diagnose_lstm', DiagnoseLSTM)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
