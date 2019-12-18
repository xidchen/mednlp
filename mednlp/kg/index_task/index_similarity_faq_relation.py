#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import json
import codecs
import global_conf
import numpy as np
import configparser
from ailib.storage.db import DBWrapper
from sklearn.feature_extraction.text import CountVectorizer
from scipy.linalg import norm
from mednlp.kg.index_task.base_index import BaseIndex
from ailib.client.ai_service_client import AIServiceClient


class QuestionAnswerManagerData():
    def __init__(self):
        self.db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')
        self.load_data()

    def load_data(self):
        self.db_id_question, self.db_id_answer, self.db_id_status, self.db_question_id = self.load_db_data()
        self.stand_id_question = self.load_standard_ask()

    def load_db_data(self):
        sql = """
            SELECT qq.question, qa.answer, qq.id, qq.status
            FROM ai_union.qa_question qq
            JOIN ai_union.qa_answer qa ON qq.id = qa.question_id
            WHERE qq.is_standard = 1
        """
        rows = self.db.get_rows(sql)
        db_id_question = {}
        db_id_answer = {}
        db_id_status = {}
        db_question_id = {}
        for row in rows:
            db_id_question[row['id']] = row['question']
            db_id_answer[row['id']] = row['answer']
            db_id_status[row['id']] = row['status']
            db_question_id[row['question']] = row['id']
        return db_id_question, db_id_answer, db_id_status, db_question_id

    def load_standard_ask(self):
        asks = {}
        with codecs.open(global_conf.standard_ask, 'r', 'utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('==')
                if len(items) == 2:
                    _id, question = items
                    asks[_id] = question
        return asks

    def make_relation(self, w=0.8):
        start_time = time.time()
        relation = []
        for std_id, std_question in self.stand_id_question.items():
            db_id = self.db_question_id.get(std_question)
            if db_id:
                relation.append({'id': std_id, 'question_id': db_id,
                                 'question': self.db_id_question.get(db_id),
                                 'answer': self.db_id_answer.get(db_id),
                                 'status': self.db_id_status.get(db_id)})
                continue
            max_sim = -1
            max_db_id = -1
            for db_id, db_question in self.db_id_question.items():
                sim_score = self.tf_similarity(std_question, db_question)
                if sim_score > max_sim:
                    max_sim = sim_score
                    max_db_id = db_id
            if max_sim > w:
                relation.append({'id': std_id, 'question_id': max_db_id,
                                 'question': self.db_id_question.get(max_db_id),
                                 'answer': self.db_id_answer.get(max_db_id),
                                 'status': self.db_id_status.get(max_db_id)})
        print('-' * 80)
        print('make relation success')
        print('{} relationships were established'.format(len(relation)))
        print('spend {} s'.format(time.time() - start_time))
        return relation

    def tf_similarity(self, s1, s2):
        def add_space(s):
            return ' '.join(list(s))
        s1, s2 = add_space(s1), add_space(s2)
        # 转化为TF矩阵
        cv = CountVectorizer(tokenizer=lambda s: s.split())
        corpus = [s1, s2]
        vectors = cv.fit_transform(corpus).toarray()
        # 计算TF系数
        return np.dot(vectors[0], vectors[1]) / (norm(vectors[0]) * norm(vectors[1]))


class IndexFaqRelation(BaseIndex):
    # index_filename = 'ai_question.xml'
    # core = 'ai_question'
    is_page = False

    def initialise(self, **kwargs):
        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'SEARCH_PLATFORM_SOLR')
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(global_conf.cfg_path)
        self.primaryKey = config.items('SEARCH_PLATFORM_SOLR')[7][1]

    def get_data_pre(self, **kwargs):
        self.qam = QuestionAnswerManagerData()

    def get_data(self):
        relations = self.qam.make_relation()
        return relations

    def process_data(self, docs):
        return docs

    def data_output(self, docs, close=True):
        if not docs:
            print('ai_similarity_faq_search 索引构建成功, 本回合无数据更新')
            return
        data = []
        params = {
            'cat': 'ai_similarity_faq_search',
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
            print('ai_similarity_faq_search error')
            res = {}
        if not res or res['code'] != 200:
            print('ai_similarity_faq_search index error')
        print('ai_similarity_faq_search index finish')


if __name__ == '__main__':
    indexer = IndexFaqRelation(global_conf, dev=True)
    indexer.index()
