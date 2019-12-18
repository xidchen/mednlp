#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: huhy
Create on 2018-08-17 Friday.
"""

import global_conf
from base_request_handler import BaseRequestHandler
from ailib.utils.exception import ArgumentLostException
import json
from mednlp.model.summary_extraction_model import SummaryExtractor

summary_extractor = SummaryExtractor(global_conf.text_rank_stopword_file)


class SummaryExtraction(BaseRequestHandler):
    def initialize(self, runtime=None,  **kwargs):
        super(SummaryExtraction, self).initialize(runtime, **kwargs)

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        data = {}
        if self.request.body:
            data_json = json.loads(self.request.body)
            query = data_json.get('q')
            source = data_json.get('source', '')
            sentence_limit = data_json.get('sentence_limit', 1)
            char_suggest = data_json.get('char_suggest', 0)
            char_limit = data_json.get('char_limit', 0)
        else:
            query = self.get_q_argument('', limit=5000)
            source = int(self.get_argument('source', ''))
            sentence_limit = int(self.get_argument('sentence_limit', '1'))
            char_suggest = int(self.get_argument('char_suggest', '0'))
            char_limit = int(self.get_argument('char_limit', '0'))

        if not query:
            raise ArgumentLostException(['q'])
        if not source:
            raise ArgumentLostException(['source'])
        if query != '':
            if isinstance(source, int) and isinstance(sentence_limit, int) and isinstance(char_suggest, int) and isinstance(char_limit, int):
                summary = summary_extractor.get_summary(query, sentence_limit, char_suggest, char_limit)
                data['summary'] = summary
                return {"code": 0, "message": "successful", "data": data}
            else:
                raise Exception('invalid input type')
        else:
            return {"code": 2, "message": "unsuccessful", "data": None}


if __name__ == '__main__':
    handlers = [(r'/summary_extraction', SummaryExtraction)]
    import ailib.service.base_service \
        as base_service
    base_service.run(handlers)

