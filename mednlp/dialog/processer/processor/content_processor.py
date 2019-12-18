#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.processer.processor.baike_processor import BaikeProcessor
from mednlp.dialog.processer.processor.post_processor import PostProcessor


class ContentProcessor(BasicProcessor):
    # 处理返回百科信息

    def __init__(self):
        super(ContentProcessor, self).__init__()
        self.baike_process = BaikeProcessor()      # 必须保证一定有intention_conf
        self.post_process = PostProcessor()

    def set_intention_conf(self, intention_conf):
        self.intention_conf = intention_conf
        self.baike_process.set_intention_conf(intention_conf)
        self.post_process.set_intention_conf(intention_conf)

    def process(self, query, **kwargs):
        result = {}
        baike_result = self.baike_process.process(query, **kwargs)
        if baike_result.get(constant.QUERY_KEY_BAIKE_SEARCH):
            result[constant.QUERY_KEY_BAIKE_SEARCH] = baike_result[constant.QUERY_KEY_BAIKE_SEARCH]
        post_result = self.post_process.process(query, **kwargs)
        if post_result.get(constant.QUERY_KEY_POST_SEARCH):
            result[constant.QUERY_KEY_POST_SEARCH] = post_result[constant.QUERY_KEY_POST_SEARCH]
        result['code'] = 0
        result['is_end'] = 1
        return result
