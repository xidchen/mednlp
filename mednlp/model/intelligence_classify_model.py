#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
intelligence_classify_model.py

Author: caoxg <caoxg@guahao.com>
Create on 2017-11-22 星期三.
"""

from ailib.model.base_model import BaseModel
from keras.preprocessing.sequence import pad_sequences
from keras.models import model_from_json
from mednlp.text.vector import Char2vector, StandardAsk2Vector
import global_conf


class InterlligenceClassifyModel(BaseModel):
    def initialize(self, model_version=5, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.load_model()
        self.char2vector = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
        self.medical_word = self.char2vector.medical_word
        standardask = StandardAsk2Vector(global_conf.standard_ask)
        self.id_name, self.name_code = standardask.id_name, standardask.name_code

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        self.model = model

    def new_normal(self, be_sort_result):
        """
        :param be_sort_result: 预测出的结果
        :return: 对预测出的结果中的准确率进行标准化
        """
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
            if sort_result[i][0] in self.name_code:
                sort_result[i].append(self.name_code[sort_result[i][0]])
            else:
                sort_result[i].append('')
        return sort_result

    def get_char_dict_vector(self, query, num=10):
        """
        :param query: 输入预测文本
        :param num: 词向量长度
        :return: 词向量
        """
        words = self.char2vector.get_char_vector(query)
        p = 0
        words_list = []
        while len(words[p:p+num]) == num:
            words_list.append(words[p:p+num])
            p += num
        if p != len(words):
            words_list.append(words[p:len(words)])
        return words_list

    def predict(self, query, sex=0, age=-1, level=1, num=37):
        """
        :param query: 咨询的内容
        :param sex: 性别
        :param age: 年龄
        :param level: 置信度水平
        :param num: 输入模型的长度
        :return: [[科室，预测科室概率,科室id]]
        """
        words_list = self.get_char_dict_vector(query, num=num)
        if not words_list:
            return []
        predict_x = pad_sequences(words_list, maxlen=num)
        dept_values = self.model.predict(predict_x)
        res_dept = {}
        for dept_value in dept_values:
            for i, value in enumerate(dept_value):
                if self.id_name[i] not in res_dept:
                    res_dept[self.id_name[i]] = 0
                res_dept[self.id_name[i]] += value
        normal_result = self.new_normal(res_dept)
        normal_result.sort(key=lambda item: item[1], reverse=True)
        sort_result = self.add_dept_id(normal_result)
        return sort_result


if __name__ == '__main__':
    cnn_model = InterlligenceClassifyModel(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_TEXTCNN_MODEL')
    line = '绑卡后，我可以解绑或者更换其他银行卡吗'
    pred = cnn_model.predict(line, num=37)
    print(pred)
