#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentence_similarity_entity_model.py -- 使用实体识别接口计算语句相似性模型

Author: caoxg <caoxg@guahao.com>
Create on 2018-10-11 星期四.
"""

from ailib.model.base_model import BaseModel
from ailib.client.ai_service_client import AIServiceClient
import global_conf
import codecs
import json
import re


class SentenceEntityModel(BaseModel):

    def initialize(self, **kwargs):
        self.aisc = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.pers = self.load_pers()

    def parse_age_sex(self, content):
        """
        :param query: 请求内容
        :return: 返回请求内容中包含的agline = '小孩女痢疾头疼吃阿莫西林，保宫治疗，心脏病'e_range，sex字段
        """
        result = {'age': [], 'sex': [], 'disease': [], 'symptom': [], 'medicine': [], 'treatment': []}
        params = {'q': content, 'property': 'age,sex'}
        try:
            entity_result = self.aisc.query(params, 'entity_extract')
        except:
            return result
        data = entity_result.get('data')
        if not data:
            return result
        type_list = ['disease', 'medicine', 'treatment']
        if data:
            for entity in data:
                if entity.get('type') == 'crowd':
                    property = entity.get('property')
                    if property.get('age'):
                        if property.get('age_range'):
                            if isinstance(property.get('age_range'), list):
                                result['age'].append(property.get('age_range'))
                        else:
                            try:
                                age = int(property.get('age'))
                                result['age'].append([age - 2, age + 2])
                            except:
                                print('age format is error')

                    if property.get('sex'):
                        result['sex'].append(property.get('sex'))
                type = entity.get('type')
                entity_name = entity.get('entity_name')
                if type == 'symptom':
                    if 'disease' in entity.get('type_all'):
                        if entity_name not in result['disease']:
                            result['disease'].append(entity_name)
                    else:
                        if entity_name not in result['symptom']:
                            result['symptom'].append(entity_name)
                elif type in type_list:
                    if entity_name not in result[type]:
                        result[type].append(entity_name)
        return result

    def check_age(self, age, age_ranges):
        """

        :param age: 传入参数年龄以天为单位
        :param age_ranges: 年龄所在的范围
        :return: 返回是否相违背 若为1  则年龄和age_ranges不匹配，
        """
        age_check = 0
        if not isinstance(age, int):
            try:
                age = int(age)
            except:
                return age_check

        if age < 0:
            return age_check
        if not age_ranges:
            return age_check
        for age_range in age_ranges:

            age_int = age / 365
            if age_int >= age_range[1] or age_int < age_range[0]:
                age_check = 1
        return age_check

    def check_sex(self, sex, sex_ranges):
        """

        :param sex: 性别
        :param sex_ranges: 性别标记
        :return: 返回是否匹配，若为1，则性别不匹配
        """
        sex_check = 0
        if not isinstance(sex, str):
            try:
                sex = str(sex)
            except:
                return sex_check
        if sex not in ['1', '2']:
            return sex_check
        if sex not in sex_ranges and sex_ranges:
            sex_check = 1
        return sex_check

    def compare_center_word(self, result1, result2):
        """
        :param result1: 句子A
        :param result2: 句子B
        :return: 返回句子A 和句子B中心词是否相同，判断逻辑依次为  疾病、症状、药品、治疗
        """
        center_label = 0
        if set(result1.get('disease')) and set(result2.get('disease')) and set(result1.get('disease')) == set(
                result2.get('disease')):
            center_label = 1
        elif set(result1.get('symptom')) and set(result2.get('symptom')) and set(result1.get('symptom')) == set(
                result2.get('disease')):
            center_label = 1
        elif set(result1.get('medicine')) and set(result2.get('medicine')) and set(result1.get('medicine')) == set(
                result2.get('medicine')):
            center_label = 1
        elif set(result1.get('treatment')) and set(result2.get('treatment')) and set(result1.get('treatment')) == set(
                result2.get('treatment')):
            center_label = 1
        else:
            center_label = 0

        return center_label

    def load_pers(self):
        """
        加载所有正则表达式
        :return: 正则表达式列表
        """
        file = codecs.open(global_conf.dict_path + 'navi.json', 'r', encoding='utf-8')
        data = json.load(file)
        pers = []
        pers.extend(data['disease'])
        pers.extend(data['medicine'])
        pers.extend(data['symptom'])
        pers.extend(data['check'])
        pers.extend(data['operation'])
        pers = set(pers)
        return pers

    def compare_navi_word(self, sentence1, sentence2):
        """
        :param sentence1: 句子A
        :param sentence2: 句子B
        :return: 句子A和句子B包含的导航词是否相同
        """
        label = 0
        for per in self.pers:
            if re.search(per, sentence1, re.M|re.I) and re.search(per, sentence2, re.M|re.I):
                label = 1
                if label == 1:
                    break
        return label

    def parse_sex_age_set(self, sentences, **kwargs):
        """
        :param sentences: 句子对
        :return: 返回句子对是识别识别中的身体部位实体词
        """
        age = -1
        sex = 0
        q = ""
        mode = 1
        if kwargs.get('age'):
            age = kwargs.get('age')
        if kwargs.get('sex'):
            sex = kwargs.get('sex')
        if kwargs.get('q'):
            q = kwargs.get('q')
        if kwargs.get('mode'):
            mode = kwargs.get('mode')

        bodies_age_sex = []
        bodies_center_navi = []
        for sentence in sentences:
            result = self.parse_age_sex(sentence)
            age_check = self.check_age(age, result.get('age'))
            sex_check = self.check_sex(sex, result.get('sex'))
            bodies_age_sex.append([age_check, sex_check])
            if mode == 2:
                result_q = self.parse_age_sex(q)
                center_label = self.compare_center_word(result_q, result)
                navi_label = self.compare_navi_word(q, sentence)
                bodies_center_navi.append([center_label, navi_label])
        return bodies_age_sex, bodies_center_navi

    def predict(self, sentences, **kwargs):
        """
        :param sentence: 句子
        :param sentences: 句子对
        :return: 返回句子和句子对在实体识别方面，特别是身体部位方面的相似度需求
        """
        age = -1
        sex = 0
        q = ""
        if kwargs.get('age'):
            age = kwargs.get('age')
        if kwargs.get('sex'):
            sex = kwargs.get('sex')
        if kwargs.get('q'):
            q = kwargs.get('q')
        if kwargs.get('mode'):
            mode = kwargs.get('mode')
        results, center_results = self.parse_sex_age_set(sentences, age=age, sex=sex, q=q, mode=mode)
        result = []
        center_result = []
        for line in results:
            if line[0]+line[1] > 1:
                result.append(0.25)
            elif line[0]+line[1] > 0:
                result.append(0.5)
            else:
                result.append(1)
        for line in center_results:
            if line[0] + line[1] == 2:
                center_result.append(1.5)
            else:
                center_result.append(1)
        return result, center_result
