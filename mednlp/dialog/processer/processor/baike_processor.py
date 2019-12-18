#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
import copy


class BaikeProcessor(BasicProcessor):
    # 处理返回百科信息
    default_rows = 1
    fl = []
    # 疾病 > 症状 > 药品 > 科室 > 治疗
    word_types = ['disease', 'symptom', 'medicine', 'std_department',
                  'hospital_department', 'treatment']
    word_template = {
        'disease': [],
        'symptom': [],
        'medicine': [],
        'std_department': [],
        'hospital_department': [],
        'treatment': []
    }

    def initialize(self):
        self.search_params = {
            'state': '2',
            'match_type': '1',
            'highlight': '1',
            'fl': 'introduction,word_id,name,name_highlight,type',
            'start': '0',
            'rows': '1'
        }

    def process(self, query, **kwargs):
        result = {}
        self.set_params(query)
        center_word = self.get_center_word()
        if center_word:
            self.search_params['q'] = center_word
            response = ai_search_common.query(self.search_params, self.input_params, 'baike_word')
            baike_data = self.deal_data(response)
            if baike_data:
                result[constant.QUERY_KEY_BAIKE_SEARCH] = baike_data
        self.set_dialogue_info(result)
        result['is_end'] = 1
        result['code'] = 0
        return result

    def deal_data(self, response):
        result = {}
        if response and response.get('data'):
            result = copy.deepcopy(response['data'])
            for temp in result:
                if len(temp['introduction']) > 40:
                    temp['introduction'] = temp['introduction'][:40]
        return result

    def set_rows(self):
        self.search_params['rows'] = super(
            BaikeProcessor, self).basic_set_rows(6, default_rows=self.default_rows)

    def get_center_word(self):
        # 得到百科中心词   疾病 > 症状 > 药品 > 科室 > 治疗
        result = None
        # 如果有q, 进行实体识别, 获取第一个词
        q = self.input_params['input'].get('q')
        if q:
            entity_result = constant.ai_server.query({'q': str(q)}, 'entity_extract')
            if entity_result and entity_result.get('data'):
                word_dict = copy.deepcopy(self.word_template)
                for entity_obj in entity_result.get('data'):
                    if entity_obj['type'] in self.word_types:
                        word_dict[entity_obj['type']].append(entity_obj['entity_name'])
                for word_type_temp in self.word_types:
                    if word_dict[word_type_temp]:
                        result = word_dict[word_type_temp][0]
                        break
        return result
