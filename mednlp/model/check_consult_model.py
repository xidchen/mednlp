# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-07-08 星期日.
"""

import os
import sys
import time
import re
from ailib.model.base_model import BaseModel
from ailib.client.ai_service_client import AIServiceClient
from keras.preprocessing.sequence import pad_sequences
from keras.models import model_from_json
from os import path
import numpy as np
import mednlp.text.smartseg as smartseg
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser
from mednlp.text.vector import Char2vector, Check2Vector
import global_conf
from ailib.storage.db import DBWrapper

db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')


class CheckConsultModel(BaseModel):
    def initialize(self, model_version=0, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.load_model()
        self.char2vector = Char2vector(global_conf.dept_classify_char_dict_path)
        check2vector = Check2Vector(global_conf.dept_classify_check_consult_path)
        self.medical_word = self.char2vector.medical_word
        self.check_id = check2vector.check_id
        self.id_check = check2vector.id_check
        self.id_check_code = check2vector.id_check_code
        self.code_check_detail = check2vector.code_check_detail

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
        """对预测出的结果进行标准化"""
        sum_prob = 0
        for dept_name, pr in be_sort_result.items():
            sum_prob += pr
        normal_result = []
        for dept_name, pr in be_sort_result.items():
            normal_result.append([dept_name, pr / sum_prob])
        return normal_result

    def add_code_detail(self, sort_result):
        """根据排序之后的预测结果,加上规则说明"""
        for i in range(len(sort_result)):
            if sort_result[i][0] in self.code_check_detail:
                sort_result[i].append(self.code_check_detail[sort_result[i][0]])
            else:
                sort_result[i].append('')
        return sort_result

    def get_char_dict_vector(self, query, num=10):
        """输入要查询到文本,输出 词向量"""
        if not sys.version > '3':
            query = unicode(query).decode('utf-8')
        words = self.char2vector.get_char_vector(query)
        p = 0
        words_list = []
        while len(words[p:p + num]) == num:
            words_list.append(words[p:p + num])
            p += num
        if p != len(words):
            words_list.append(words[p:len(words)])
        return words_list

    def predict(self, query, sex=0, age=-1, level=1, num=100):
        """预测咨询内容对应的违反规则，以及规则说明,
        query-> 带预测的内容,输出 预测违反规则和概率"""
        words_list = self.get_char_dict_vector(query, num=num)
        if not words_list:
            return []
        predict_x = pad_sequences(words_list, maxlen=num)
        dept_values = self.model.predict(predict_x)
        res_dept = {}
        for dept_value in dept_values:
            for i, value in enumerate(dept_value):
                if self.id_check[i] not in res_dept:
                    res_dept[self.id_check_code[i]] = 0
                res_dept[self.id_check_code[i]] += value
        normal_result = self.new_normal(res_dept)
        normal_result.sort(key=lambda item: item[1], reverse=True)
        sort_result = self.add_code_detail(normal_result)
        return sort_result


def id_consult(id='0'):
    """
    通过订单order_id拿到医生的回复
    :param id: order_id
    :return: 返回医生的回复按照id进行排序
    """
    consults = []
    if not id:
        return consults
    table_id = int(id)/2000000
    sql = """ 
          select order_id,content,id
          from consult.consult_order_reply_{}
          where user_type = 1 and source != -2
          and order_id = '{}';
        """.format(table_id, id)
    rows = db.get_rows(sql)
    if rows:
        for row in rows:
            content = row['content']
            id = row['id']
            consults.append([content, id])
    consults = sorted(consults, key=lambda line: line[1])
    return consults


def get_contents(consults):
    """
    把医生的回复写成list形式
    :param consults: 医生的回复
    :return: 医生的回复list形式
    """
    content = []
    if consults:
        for line in consults:
            content.append(line[0])
    return content


def get_result(content):
    """
    医生的list回复，返回字符串形式
    :param content: 医生回复的list形式
    :return: 返回医生回复的字符串形式
    """
    result = ",".join(content)
    return result

