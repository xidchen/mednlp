#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
segment_words.py -- segment sentence by jieba which load some etity dict
Author : yinwd
Create on 2018.06.27 
"""

from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.utils.exception import ArgumentLostException
from mednlp.kg.segment_words import words_segment


class WordSegment(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(WordSegment, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        result = {}
        query = self.get_q_argument('', escape=False, limit=1000)
        if not query:
            raise ArgumentLostException(['q'])

        result['data'] = words_segment(query)
        return result


if __name__ == '__main__':
    handlers = [(r'/word_segment', WordSegment)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
