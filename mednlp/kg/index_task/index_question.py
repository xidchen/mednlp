#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_doctor.py -- the index task of doctor to solr

Author: renyx <renyx@guahao.com>
Create on 2019-05-07 Tuesday.
"""
import sys
from mednlp.kg.index_task.base_index import BaseIndex
from ailib.storage.db import DBWrapper
import json
import traceback
import mednlp.utils.utils as utils
from ailib.client.ai_service_client import AIServiceClient
import global_conf
import configparser
import jieba

user_dict = global_conf.dict_path + './question_cut_word.dict'
stop_dict = global_conf.dict_path + './question_stop.dict'
jieba.load_userdict(user_dict)
stop_words = [line.strip() for line in open(stop_dict, 'r', encoding='utf-8').readlines()]

"""
1.加载信息,针对标准问句进行分词,添加tag
2.整理数据, post到solr
"""

class IndexQuestion(BaseIndex):
    index_filename = 'ai_question.xml'
    core = 'ai_question'
    is_page = True
    page_start = 0
    page_size = 1000

    def initialise(self, **kwargs):
        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'SEARCH_PLATFORM_SOLR')
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(global_conf.cfg_path)
        self.primaryKey = config.items('SEARCH_PLATFORM_SOLR')[7][1]

    def analyse_data(self, data):
        result = []
        for temp in data:
            question = temp[1]
            is_standard = temp[2]
            is_similar = temp[3]
            status = temp[4]
            standard_id = temp[5]
            temp_dict = {
                'id': str(int(temp[0])),
                'question': temp[1],
                'question_str': temp[1],
                'status': int(status)
            }
            result.append(temp_dict)
            if is_standard in (1, float(1)):
                temp_dict['is_standard'] = 1
                temp_dict['standard_id'] = str(int(temp[0]))
            if is_similar in (1, float(1)):
                temp_dict['is_similar'] = 1
                temp_dict['standard_id'] = str(int(standard_id))
            cut_words = jieba.cut(question)
            temp_dict['keyword'] = list(set([cut_temp for cut_temp in cut_words if len(
                cut_temp) > 1 and cut_temp not in stop_words]))
        return result

    def get_data_pre(self, **kwargs):
        r_path = global_conf.dict_path + 'similar_standard_question.xlsx'
        result = utils.load_xlsx_data(r_path=r_path, start=1)
        self.question = self.analyse_data(result)
        self.total_count = int(len(self.question) / self.page_size) + 1
        self.error_count = 0
        self.current_count = 0

    def get_data(self):
        question = self.question[self.page_start: self.page_start + self.page_size]
        if not question:
            self.page_status = 0
            return []
        self.page_start += self.page_size
        return question

    def process_data(self, docs):
        return docs

    def data_output(self, docs, close=True):
        if not docs:
            print('ai_doctor_search 索引构建成功, 本回合无数据更新')
            print('当前:%s, total:%s, error:%s' % (self.current_count, self.total_count, self.error_count))
            return
        data = []
        params = {
            'cat': 'ai_question_sentence',
            'primaryKey': self.primaryKey,
            'isAtomic': False,
            'pageDocs': data
        }
        for doc in docs:
            temp = {}
            for item in doc:
                if doc.get(item) is not None:
                    temp[item] = doc[item]
            data.append(temp)
        try:
            res = self.plat_sc.query(json.dumps(params, ensure_ascii=False), 'index/1.0', method='post')
        except Exception as err:
            print(err)
            print('ai_doctor_search error')
            res = {}
        if not res or res['code'] != 200:
            print('ai_doctor_search index error')
            self.error_count += 1
        self.current_count += 1
        if not close and self.current_count % 10 == 0:
            print('当前:%s, total:%s, error:%s' % (self.current_count, self.total_count, self.error_count))

if __name__ == '__main__':
    indexer = IndexQuestion(global_conf, dev=True)
    indexer.index()
