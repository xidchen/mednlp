#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-05-17 Friday
@Desc: dept classify with merged char and pinyin model
"""

from keras.models import model_from_json
from ailib.model.base_model import BaseModel
from keras.preprocessing.sequence import pad_sequences
from mednlp.text.vector import Pinyin2vector, Char2vector, Dept2Vector
import global_conf


class DeptClassifyCharPinyin(BaseModel):
    def initialize(self, model_version=0, **kwargs):
        """
        初始化模型，加载相关字典文件
        """
        self.model_version = model_version
        self.pinyin_to_vector = Pinyin2vector(dept_classify_dict_path=global_conf.dept_classify_pinyin_dict_path)
        self.char_to_vector = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
        dept_to_vector = Dept2Vector(global_conf.dept_classify_dept_path)
        self.dept_dict = dept_to_vector.index2name
        self.dept_id = dept_to_vector.name2id
        self.load_model()

    def load_model(self):
        """
        加载模型
        """
        model_base_name = '{}.{}'.format(self.model_path, self.model_version)
        model_arch_name = '{}.arch'.format(model_base_name)
        model_weight_name = '{}.weight'.format(model_base_name)
        model = model_from_json(open(model_arch_name).read())
        model.load_weights(model_weight_name, by_name=True)
        self.model = model

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

    def predict(self, query, sex=0, age=-1, level=1, num=100):
        """预测科室
        :returns: 预测类别和概率
        """
        char_vector = [self.char_to_vector.get_char_vector(query, isIgnore=False)]
        padding_char_vector = pad_sequences(char_vector, maxlen=100)
        pinyin_vector = [self.pinyin_to_vector.get_pinyin_vector(query, isIgnore=False)]
        padding_pinyin_vector = pad_sequences(pinyin_vector, maxlen=100)

        # predict_result = self.model.predict([padding_char_vector, padding_pinyin_vector])
        dept_values = self.model.predict([padding_char_vector, padding_pinyin_vector])
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
