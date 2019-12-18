#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
sentence_similarity_test.py --  句子相似性测试程序

Author: caoxg <caoxg@guahao.com>
Create on 2018-08-16 星期三.
"""


import global_conf
from ailib.client.ai_service_client import AIServiceClient
import codecs
import pandas as pd
import os
import json


class Test(object):
    def __init__(self, port, test_file='', mode=1):
        self.mode = mode
        self.search = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService', port=port)
        self.querys = []
        self.labels = []
        self.test_file = test_file
        self.get_data()

    def get_data(self):
        """
        读取测试数据
        :return: 返回目标语句和语句列
        """
        labels = []
        querys = []
        with codecs.open(self.test_file, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('==')
                if len(items) == 2:
                    labels.append(items[0])
                    querys.append(items[1])
        self.labels = labels
        self.querys = querys

    def get_pred_count(self):
        """
        """
        pred_result = []
        for query in self.querys:
            query = str(query)
            query_data = {'q': query, 'fl': 'score,train_id', 'level': 0}
            t = self.search.query(json.dumps(query_data, ensure_ascii=False), service='similarity_faq')
            if t.get('data'):
                ask_id = t.get('data')[0].get('train_id')
                score = t.get('data')[0].get('score')
                pred_result.append([ask_id, score])
            else:
                pred_result.append(['', 0])
        return pred_result

    def compute_accuracy(self):
        confidences = [float(index) / 10 for index in range(10)]
        pred_result = self.get_pred_count()
        pred_count, true_count = [0 for _ in range(10)], [0 for _ in range(10)]
        for index, confidence in enumerate(confidences):
            for actual, [pred_id, score] in zip(self.labels, pred_result):
                if score:
                    if score > confidence:
                        pred_count[index] += 1
                        if actual == pred_id:
                            true_count[index] += 1

        total = len(self.labels) * 1.0
        accuracy = [round(tc / pc, 2) for tc, pc in zip(true_count, pred_count)]
        coverage = [round(pc / total, 2) for pc in pred_count]
        result = {'level': confidences,
                  'pred_count': pred_count,
                  'true_count': true_count,
                  'accuracy': accuracy,
                  'coverage': coverage}
        return result

    def save_result(self, save_path='similarity_faq_result.csv'):
        df = pd.DataFrame(self.compute_accuracy())
        df = df[['level', 'pred_count', 'true_count', 'accuracy', 'coverage']]
        df.to_csv(save_path, index=False, header=True)


if __name__ == '__main__':
    file = os.path.join('/home/chaipf/work/mednlp/data/traindata/similarity_faq', 'test.txt')
    test = Test(test_file=file, port=6447)
    test.save_result()
