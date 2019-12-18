#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-03-08 星期四.
"""

import sys
from keras.models import model_from_json
from ailib.model.base_model import BaseModel
from keras.preprocessing.sequence import pad_sequences
from mednlp.text.vector import Pinyin2vector, Dept2Vector
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser
import global_conf
from mednlp.model.AttentionLayer import AttentionLayer


class DeptClassifyPhonetic(BaseModel):
    def initialize(self, model_version=3,  **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.pinyin2vector = Pinyin2vector(dept_classify_dict_path=global_conf.dept_classify_pinyin_dict_path)
        self.load_model()
        dept2vector = Dept2Vector(global_conf.dept_classify_dept_path)
        self.dept_dict = dept2vector.index2name
        self.dept_id = dept2vector.name2id
        self.medical_word = self.pinyin2vector.medical_word

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        # model = model_from_json(open(model_arch).read(), {'AttentionLayer': AttentionLayer})
        model.load_weights(model_weight, by_name=True)
        self.model = model
    
    def new_normal(self, be_sort_result):
        """对预测出的结果进行标准化"""
        sum_prob = 0
        for dept_name, pr in be_sort_result.items():
            sum_prob += pr
        normal_result = []
        for dept_name, pr in be_sort_result.items():
            normal_result.append([dept_name, pr/sum_prob])
        return normal_result

    def add_dept_id(self, sort_result):
        """根据排序之后的预测结果,加上科室id"""
        for i in range(len(sort_result)):
            if sort_result[i][0] in self.dept_id:
                sort_result[i].append(self.dept_id[sort_result[i][0]])
            else:
                sort_result[i].append('')
        return sort_result

    def get_pinyin_dict_vector(self, query, num=10):
        """输入要查询到文本,输出 词向量"""
        if not sys.version > '3':
            query = unicode(query).decode('utf-8')
        words = self.pinyin2vector.get_pinyin_vector(query)
        p = 0
        words_list = []
        while len(words[p:p+num]) == num:
            words_list.append(words[p:p+num])
            p += num
        if p != len(words):
            words_list.append(words[p:len(words)])
        return words_list

    def predict(self, query, sex=0, age=-1, level=1, num=100):
        """预测咨询内容对应的科室,
        query-> 带预测的内容,输出 预测类别和概率"""
        words_list = self.get_pinyin_dict_vector(query, num=num)
        if not words_list:
            return []
        predict_x = pad_sequences(words_list, maxlen=num)
        dept_values = self.model.predict(predict_x)
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