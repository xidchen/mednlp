# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/1/22 11:13
# @Auther:caoxg@guahao.com
# @File:knowledge_base_model.py
import json
import codecs
import global_conf


class KnowledgeBase():

    def __init__(self):
        self.file_path = global_conf.dict_path + 'knowledge_base.json'
        self.load_model()

    def load_model(self):
        """加载疾病和鉴别诊断和诊断依据的关系"""
        f = codecs.open(self.file_path, 'r', encoding='utf-8')
        self.model = json.load(f)

    def predict(self, query):
        """预测疾病所对应的鉴别诊断和诊断依据"""
        if not query:
            return {}
        disease = self.model.get('disease')
        for line in disease:
            if query == line.get('disease_name'):
                return line
        return {}
