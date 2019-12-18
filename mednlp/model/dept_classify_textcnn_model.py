#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: zhoulg1 <zhoulg1@guahao.com>
Create on 2018-03-08 星期四.
"""

import os
import sys
import time
import jieba
import pickle
import global_conf
import numpy as np
from keras.models import load_model
from ailib.model.base_model import BaseModel
from mednlp.utils.utils import unicode_python_2_3


class DeptClassifyCNN(BaseModel):
    def initialize(self, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        with open(global_conf.dept_classify_jiebacut_vocab_path, 'r') as f:
            vocab = pickle.load(f)
        self.w2i, self.i2w = vocab.get('w2i'), vocab.get('i2w')

        with open(global_conf.dept_labels_categorical_dict, 'r') as f:
            self.d2i = pickle.load(f)
        self.model = load_model(self.model_path)
        self.load_dept_dict()

    def pad_sentences(self, sentences, lenth=200, padding_word="<PAD>"):
        """
        把sentences pad成固定的length长度，缺少的部分用<PAD>填充
        :param sentences: 类型list 数据为jieba分词以后的数据
        :param lenth: pad成固定的长度
        :param padding_word: 填充的字符
        :return: 返回length长度的list
        """
        if lenth:
            sequence_length = lenth
        else:
            sequence_length = max(len(x) for x in sentences)
        padded_sentences = []
        for i in range(len(sentences)):
            sentence = sentences[i]
            num_padding = sequence_length - len(sentence)
            new_sentence = sentence + [padding_word] * num_padding
            padded_sentences.append(new_sentence)
        return padded_sentences

    def load_dept_dict(self):
        """主要是生成部门列表"""
        dept_dict = {}
        dept_id = {}
        for i, line in enumerate(open(global_conf.dept_classify_dept_path, 'r')):
            dept_name, dept_name_id = line.strip().split('=')
            j = self.d2i.get(unicode_python_2_3(dept_name))
            dept_dict[j] = dept_name
            dept_id[dept_name] = dept_name_id
        self.dept_dict = dept_dict
        self.dept_id = dept_id

    def new_normal(self, be_sort_result):
        """对预测出的结果进行标准化"""
        sum_prob = 0
        for dept_name, pr in be_sort_result.items():
            sum_prob += pr
            normal_result = []
        for dept_name, pr in be_sort_result.items():
            normal_result.append([dept_name, pr / sum_prob])
        return normal_result

    def add_dept_id(self, sort_result):
        """根据排序之后的预测结果,加上科室id"""
        for i in range(len(sort_result)):
            if sort_result[i][0] in self.dept_id:
                sort_result[i].append(self.dept_id[sort_result[i][0]])
            else:
                sort_result[i].append('')
        return sort_result

    def predict(self, query, sex=0, age=-1, level=1):
        """预测咨询内容对应的科室,
        query-> 带预测的内容,输出 预测类别和概率"""
        if not query:
            return []
        sens = [0]
        sens[0] = query
        sens = [jieba.lcut(s)[0:200] for s in sens]
        sens = self.pad_sentences(sens, lenth=200, padding_word="<PAD>")
        sens_int = [[self.w2i.get(w, 0) for w in sen] for sen in sens]
        dept_values = self.model.predict(np.array(sens_int))
        res_dept = {}
        for dept_value in dept_values:
            for i, value in enumerate(dept_value):
                if self.dept_dict[i] not in res_dept:
                    res_dept[self.dept_dict[i]] = 0
                res_dept[self.dept_dict[i]] += value
        normal_result = self.new_normal(res_dept)
        normal_result.sort(key=lambda item: item[1], reverse=True)
        sort_result = self.add_dept_id(normal_result)
        return sort_result
