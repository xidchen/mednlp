#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-04-08 星期三.
"""

import math
import codecs
import sys
import numpy as np
import global_conf

from mednlp.dept.common.result import DeptResults
from mednlp.utils.utils import unicode_python_2_3


class Score2Accuracy():
    def __init__(self, accuracy_path=global_conf.accuracy_path):
        self.accuracy_path = accuracy_path
        self.id_accuracy = self.load_score_accuracy()

    def _get_score_id(self, score):
        """
        生成模型预测概率和置信度之间的关系
        :param score: 模型预测概率
        :return: 返回该预测概率对应的置信度系数
        """
        score = float(score) * 100
        score_id = score / 2.0
        score_id = math.ceil(score_id)
        score_id = int(score_id) * 2
        score_id = unicode_python_2_3(score_id)
        return score_id

    def load_score_accuracy(self):
        """
        生成预测置信度系数和准确率之间的对应关系
        :return: 返回预测置信度系数和预测准确率之间的对应关系
        """
        accuracy_data = codecs.open(self.accuracy_path, 'r', encoding='utf-8')
        id_accuracy = {}
        for line in accuracy_data:
            line = line.strip().split('\t')
            id_accuracy[line[0]] = line[1]
        accuracy_data.close()
        return id_accuracy

    def get_accuracy(self, score):
        """
        给定预测结果概率，给出该评分下，模型的准确率
        :param score:科室分诊结果的预测概率 
        :return: 返回模型预测结果准确率
        """
        id = self._get_score_id(score)
        if not sys.version > '3':
            accuracy = '81%'.decode('utf-8')
        else:
            accuracy = '81%'
        if self.id_accuracy[str(id)]:
            accuracy = self.id_accuracy[str(id)]
        return accuracy

    def get_accuracy_list(self, depts):
        """
        :param depts: 科室预测结果
        :return: 返回科室替换准确率
        """
        for i in range(1, len(depts)):
            depts[i][3] = self.get_accuracy(depts[i][1])
        return depts

    def add_accuracy_to_result(self, results):
        assert isinstance(results, DeptResults)
        for dept in results[1:]:
            dept.accuracy = self.get_accuracy(dept.probability)


if __name__ == '__main__':
    scoretoaccuracy = Score2Accuracy()
    numbers = np.random.rand(100).astype('float')
    a = [float(number) for number in numbers]
    for number in a:
        print(number)
        print(scoretoaccuracy.get_accuracy(number))
