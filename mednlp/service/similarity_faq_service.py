#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify.py -- the service of dept_classify

Author: maogy <maogy@guahao.com>
Create on 2017-06-19 星期一.
"""

from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.intelligence_classify_merge_model import MergeModel
import re
from mednlp.text.vector import StandardAsk2Vector
from sklearn.feature_extraction.text import CountVectorizer
from scipy.linalg import norm
from ailib.storage.db import DBWrapper
import global_conf
import json
import tensorflow as tf
from ailib.client.ai_service_client import AIServiceClient
import configparser


graph = tf.get_default_graph()


def classify(model, content):
    global graph
    with graph.as_default():
        predictions = model.predict(content)
    return predictions


mergemodel = MergeModel(cfg_path=global_conf.cfg_path, model_section='INTELLIGENCE_CLASSIFY_MODEL')
standardask = StandardAsk2Vector(global_conf.standard_answer)


class SimilarityFAQService(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(BaseRequestHandler, self).initialize(runtime, **kwargs)

        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'SEARCH_PLATFORM_SOLR')
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(global_conf.cfg_path)
        self.primaryKey = config.items('SEARCH_PLATFORM_SOLR')[7][1]

    def post(self):
        return self.get()

    def get(self):
        # self.write_result(self._get())
        self.asynchronous_get()

    def _get(self):
        result = {}
        data = result.setdefault('data', [])
        query = self.get_q_argument('', limit=2000)
        if query:
            fl = self.get_argument('fl')
            rows = self.get_argument('rows', 1)
            level = self.get_argument('level', 1)
        else:
            query_str = self.request.body
            try:
                querys = json.loads(query_str, encoding='utf-8')
                query = str(querys.get('q'))
                fl = querys.get('fl', '')
                rows = querys.get('rows', 1)
                level = querys.get('level', 1)
            except Exception:
                return result
        rows = int(rows)
        if not fl:
            fls = fl
        else:
            fls = re.split('[,，]', fl)
        try:
            level = int(level)
        except Exception:
            level = 1

        # 现阶段对外只支持level为1一种模式
        if level == 1:
            value = 0.5
        # level为0仅作为测试使用
        elif level == 0:
            value = 0
        else:
            value = 0.5
        # depts = mergemodel.predict(query)
        depts = classify(mergemodel, query)
        if not depts:
            result['totalCount'] = 0
            return result

        for line in depts[0:rows]:
            if float(line[1]) < value:
                continue
            train_id, score = line[2], line[1]
            temp_result = {}
            params = {
                'cat': 'ai_similarity_faq_search',
                'primaryKey': self.primaryKey,
                'filter': ['status:0'],
                'fl': 'question_id,question,answer',
                'query': 'id:{}'.format(train_id)
            }
            ask_id = None
            try:
                solr_result = self.plat_sc.query(json.dumps(params), 'search/1.0', method='post', timeout=0.3)
                if solr_result.get('code') != 200:
                    print('call solr response http code: {}'.format(solr_result.get('code')))
                else:
                    datas = solr_result.get('data', [])
                    if len(datas) == 0:
                        print('not search question id in solr')
                        continue
                    _data = datas[0]
                    ask_id = _data.pop('question_id', None)
                    similarity_ask = _data.pop('question')
                    answer = _data.pop('answer')
            except Exception:
                print('call solr Error')
                continue

            if not ask_id:
                print('not find in solr')
                print(line)
                if train_id in fls:
                    temp_result['score'] = score
                    temp_result['train_id'] = train_id
                    data.append(temp_result)
                continue

            if not fls:
                temp_result['score'] = score
                temp_result['similarity_ask'] = similarity_ask
                temp_result['ask_id'] = ask_id
                temp_result['answer'] = answer
            else:
                if 'similarity_ask' in fls:
                    temp_result['similarity_ask'] = similarity_ask
                if 'score' in fls:
                    temp_result['score'] = score
                if 'ask_id' in fls:
                    temp_result['ask_id'] = ask_id
                if 'answer' in fls:
                    temp_result['answer'] = answer
                if 'train_id' in fls:
                    temp_result['train_id'] = train_id
            data.append(temp_result)
        rows = min(len(data), rows)
        result['totalCount'] = rows
        return result


if __name__ == '__main__':
    handlers = [(r'/similarity_faq', SimilarityFAQService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
