#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sentence_vector_model.py -- model

Author: renyx <renyx@guahao.com>
Create on 2019-09-09 Monday
"""
import json
import global_conf
from ailib.utils.log import GLLog
from ailib.client.ai_service_client import AIServiceClient

ac = AIServiceClient(global_conf.cfg_path, 'AIService')
logger = GLLog('sentence_vector_input_output', level='info', log_dir=global_conf.log_dir).getLogger()


class SentenceVectorModel(object):
    """
    采用bert -1层的向量,通过bert_as_service这个开源系统获取
    """

    def __init__(self):
        self.embedding_dim = 768

    def bert(self, query):
        # bert
        result = {'dimension': 768, 'sentence': query}
        params = {
            "id": 123,
            "texts": [query]
        }
        vector = ac.query(json.dumps(params, ensure_ascii=False), 'bert/encode')
        if vector and isinstance(vector, dict) and vector.get('result'):
            result['feature'] = vector['result'][0]
        return result

    def get_vector(self, query):
        result = self.bert(query)
        self.embedding_dim = 768
        return result

if __name__ == '__main__':
    model = SentenceVectorModel()
    result = model.get_vector('发质、睡眠、眼睛 这些都能看气血状况')
    print(json.dumps(result, ensure_ascii=False))
    print('aa')