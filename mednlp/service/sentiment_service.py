#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentiment_service.py -- the service of sentiment classification

Author: chenxd <chenxd@guahao.com>
Create on 2019-04-25 Thursday
"""

import json
import time
import global_conf
from ailib.utils.exception import ArgumentLostException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.sentiment_classify_lstm_model import SentimentClassifyLSTM


scm = SentimentClassifyLSTM(cfg_path=global_conf.cfg_path,
                            model_section='SENTIMENT_CLASSIFY_MODEL')


class SentimentService(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(SentimentService, self).initialize(runtime, **kwargs)

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
            query = decoded_json.get('query', [])
            sentiment = scm.predict(query=query)
            result = {'data': sentiment}
            result.update({'q_time': int((time.time() - start_time) * 1000)})
            return result


if __name__ == '__main__':
    handlers = [(r'/sentiment_service', SentimentService)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
