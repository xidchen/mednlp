# !/usr/bin/env python
# encoding=utf-8

import json
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.processor.xwyz_post_processor import XwyzPostProcessor
import copy


class XwyzContentProcessor(BasicProcessor):

    def __init__(self):
        super(XwyzContentProcessor, self).__init__()
        self.post_process = XwyzPostProcessor()

    def set_intention_conf(self, intention_conf):
        self.intention_conf = intention_conf
        self.post_process.set_intention_conf(intention_conf)

    def process(self, query, **kwargs):
        result = {}
        if self.get_intention_conf().get_configuration().get_mode() == constant.VALUE_MODE_XWYZ:
            # xwyz 模式 1.查post 2.相似度 3.走科室
            post_data = self.post_process.process(query, **kwargs).get('data', [])
            title_list = [temp['title'] for temp in post_data if 'title' in temp]
            if title_list:
                # 有数据则调 相似度接口，把最相似的插入到第一个
                sentence_similarity_params = {
                    'q': self.input_params['input'].get('q'),
                    'contents': json.dumps(title_list, ensure_ascii=False)
                }


        else:
            # xwyz_doctor模式  1.查post， 2.分科+doctor ， 3.走post
            post_query = copy.deepcopy(query)
            ceil_process_info = post_query.setdefault(constant.PROCESS_FIELD_CEIL_PROCESS_INFO, {})
            ceil_process_info['match_type'] = 4
            post_data = self.post_process.process(post_query, **kwargs).get('data', [])
            title_list = [temp['title'] for temp in post_data if 'title' in temp]

        return result
