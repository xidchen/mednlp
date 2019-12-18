#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-29 Monday
@Desc:	业务质检模型
"""

import global_conf
import configparser
from mednlp.text.vector import Char2vector
from keras.preprocessing.sequence import pad_sequences
from onnet.arch.models.tf_serving.model import TFServeModel


class OrderCheckStandardModel(object):

    """业务质检模型服务（tf serving版）"""

    def __init__(self, cfg_path, check_type):
        """
        :param check_type: 业务质检类型：
        """
        if check_type not in ('is_proactive' 'is_detailed' 'is_clear' 'is_warm' 'is_review'):
            print('业务质检模型加载失败，不支持加载该类型模型')

        parser = configparser.ConfigParser()
        parser.read(cfg_path)

        serving_ip = parser.get('TFServing', 'IP')
        serving_port = parser.get('TFServing', 'PORT')
        part_url = parser.get('TFServing', 'BASE_URL')
        base_url = 'http://' + serving_ip + ':' + serving_port + '/' + part_url
        model_url = parser.get('ORDER_CHECK_STANDARD', check_type + '_url')
        url = base_url + '/' + model_url
        self.model = TFServeModel(url)
        self.char2vector = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)

    def get_char_dict_vector(self, query, num=10):
        """
        :param query: 输入预测文本
        :param num: 词向量长度
        :return: 词向量
        """
        words = self.char2vector.get_char_vector(query)
        p = 0
        words_list = []
        while len(words[p:p + num]) == num:
            words_list.append(words[p:p + num])
            p += num
        if p != len(words):
            words_list.append(words[p:len(words)])
        return words_list

    def normal_result(self, sub_results):
        """ 归一化预测结果

        :sub_results: 预测结果
        :returns: 归一化后的预测结果

        """
        score_sum = sum(sub_results.values())
        if score_sum:
            return [[i, v / score_sum] for i, v in sub_results.items()]
        return []

    def predict(self, query, num=600):
        """ 预测

        :query: 医生回答内容
        :num: 模型长度
        :returns: 模型预测结果[[标签 置信度]]

        """
        res = []
        query_vector = self.get_char_dict_vector(query, num=num)
        if not query_vector:
            return res
        query_pad = pad_sequences(query_vector, maxlen=num)
        predict_result = self.model.predict(query_pad)
        sub_results = {}
        for pr in predict_result:
            for i, v in enumerate(pr):
                if i not in sub_results:
                    sub_results[i] = 0
                sub_results[i] += v

        res = self.normal_result(sub_results)
        res.sort(key=lambda item: item[1], reverse=True)
        return res


if __name__ == '__main__':
    model = OrderCheckStandardModel(cfg_path=global_conf.cfg_path, check_type='is_proactive')
    line = '你好，你这样的情况一般是痔疮引起的，可以用马应龙痔疮栓塞肛门治疗有可能的'
    pred = model.predict(line, num=600)
    print(pred)
