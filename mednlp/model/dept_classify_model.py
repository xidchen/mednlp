#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2017-11-22 星期三.
"""

import sys
from ailib.model.base_model import BaseModel
from ailib.client.ai_service_client import AIServiceClient
from keras.preprocessing.sequence import pad_sequences
from keras.models import model_from_json
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser
from mednlp.text.vector import Char2vector, Dept2Vector
import global_conf
from mednlp.model.AttentionLayer import AttentionLayer


class DeptClassifyModel(BaseModel):
    def initialize(self, model_version=7, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.load_model()
        self.char2vector = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
        dept2vector = Dept2Vector(global_conf.dept_classify_dept_path)
        self.dept_dict = dept2vector.index2name
        self.dept_id = dept2vector.name2id
        self.medical_word = self.char2vector.medical_word

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        # model = model_from_json(open(model_arch).read(), {'AttentionLayer':AttentionLayer})
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
        """
        :param sort_result: 排序以后的预测结果
        :return: 排序以后的预测结果每一项加上科室
        """
        for i in range(len(sort_result)):
            if sort_result[i][0] in self.dept_id:
                sort_result[i].append(self.dept_id[sort_result[i][0]])
            else:
                sort_result[i].append('')
        return sort_result

    def get_char_dict_vector(self, query, num=10):
        """
        :param query: 输入预测文本
        :param num: 词向量长度
        :return: 词向量
        """
        if not sys.version > '3':
            query = unicode(query).decode('utf-8')
        words = self.char2vector.get_char_vector(query)
        p = 0
        words_list = []
        while len(words[p:p+num]) == num:
            words_list.append(words[p:p+num])
            p += num
        if p != len(words):
            words_list.append(words[p:len(words)])
        return words_list

    def predict(self, query, sex=0, age=-1, level=1, num=100):
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
                if self.dept_dict[i] not in res_dept:
                    res_dept[self.dept_dict[i]] = 0
                res_dept[self.dept_dict[i]] += value
        normal_result = self.new_normal(res_dept)
        normal_result.sort(key=lambda item: item[1], reverse=True)
        sort_result = self.add_dept_id(normal_result)
        return sort_result


class DeptClassifyInteractiveModel(object):
    """
    科室分诊交互模型.
    """
    def __init__(self):
        """
        科室分诊交互模型构造函数.
        """
        dept_symptom_file = open(global_conf.dept_symptom_dict_path, 'r')
        dept_symptom_dict = {}
        count = 10
        symptom_list = []
        for line in dept_symptom_file:
            line = line.strip()
            item_list = line.split('|')
            if len(item_list) != 2:
                continue
            dept, symptom = item_list
            if dept not in dept_symptom_dict:
                symptom_list = dept_symptom_dict.setdefault(dept, [])
                count = 10
            if len(symptom_list) >= 10:
                continue
            symptom_list.append((symptom, count))
            count -= 1
        dept_symptom_file.close()
        self.symptom_rank = []
        symptom_rank_file = open(global_conf.symptom_rank_dict_path, 'r')
        for line in symptom_rank_file:
            line = line.strip()
            if line:
                self.symptom_rank.append(str(line))
        symptom_rank_file.close()
        self.dept_symptom_dict = dept_symptom_dict
        self.aisc = AIServiceClient(global_conf.cfg_path, 'AIService')

    def predict(self, query, sex=0, age=-1, symptoms='', debug=False, interactive='1'):
        """
        预测科室.
        参数:
        query->需要预测科室的主诉.
        """
        params = {'q': query, 'rows': 5, 'fl': 'dept_name,score',
                  'sex': sex, 'age': age}
        if debug:
            self.aisc.set_debug(True)
        dept_result = self.aisc.query(params, 'dept_classify')
        self.aisc.set_debug(False)
        result = {'isEnd': 0}
        if not dept_result and not dept_result['data']:
            return None
        depts = self._select_dept(dept_result['data'])
        issex_check, isage_check = self._check_age_sex(depts, sex, age)
        if interactive == '2':
            issex_valid, isage_valid = self.sex_age_valid(query, debug)
            result['isSex'] = max(issex_check, issex_valid)
            result['isAge'] = max(isage_check, isage_valid)
        else:
            result['isSex'] = issex_check
            result['isAge'] = isage_check
        result['isSymptom'], symptom_name = self._check_symptom(query)
        if (dept_result['data'][0]['dept_name'] != u'unknow' and dept_result['data'][0]['score'] > 0.6):
            if not result['isSex'] and not result['isAge'] and not result['isSymptom']:
                result['isEnd'] = 1
                return result
        if symptoms == '-1':
            result['isEnd'] = 1
            return result
        if symptoms:
            result['isEnd'] = 1
            return result
        symptoms = []
        dept_symptom = self._build_symptom(depts)
        if result['isSymptom'] == 1 and symptom_name:
            symptoms = self.cross_data(symptom_name, self.symptom_rank[0:20])
        elif depts and dept_symptom:
            symptoms = dept_symptom
        else:
            symptoms = self.symptom_rank[0:20]
        query_symptoms = self._parse_symptom(query)
        result['symptoms'] = [name for name in symptoms if name not in query_symptoms]
        return result

    def _select_dept(self, depts):
        """
        选择候选科室.
        参数:
        depts->候选科室列表.
        返回值->候选科室名称列表.
        """
        top_depts = depts[0: 5]
        selected_dept = []
        total_score = 0.0
        for dept in top_depts:
            if dept.get('score') and (dept['score'] > 0.1 or total_score < 0.5):
                total_score += dept['score']
                selected_dept.append(dept)
        return selected_dept

    def _build_symptom(self, depts):
        """
        构建补充症状集, 并按科室内顺序降序.
        参数:
        depts->症状集相关的科室名称列表.
        返回值->症状名称列表.
        """
        symptoms = []
        for dept in depts:
            if str(dept['dept_name']) not in self.dept_symptom_dict:
                continue
            for symptom_obj in self.dept_symptom_dict[str(dept['dept_name'])]:
                weight = float(symptom_obj[1]) * dept['score']
                symptoms.append((symptom_obj[0], weight))
        symptoms = sorted(symptoms, key=lambda dept: dept[1], reverse=True)
        symptom_name = []
        for symptom in symptoms:
            s_name = symptom[0]
            if s_name not in symptom_name:
                symptom_name.append(s_name)
        return symptom_name

    def _parse_symptom(self, query):
        """
        解析主诉中的症状.
        参数:
        query->主诉.
        返回值->症状名称列表.
        """
        params = {'q': query}
        entity_result = self.aisc.query(params, 'entity_extract')
        symptoms = []
        if not entity_result['data']:
            return symptoms
        for entity in entity_result['data']:
            if entity.get('type') == 'symptom':
                symptoms.append(entity.get('entity_name'))
        return symptoms

    def _check_age_sex(self, depts, sex, age):
        """
        检查是否需要性别和年龄.
        参数:
        depts->科室列表.
        返回值->是否需要性别和年龄的tuple,具体结构:(is_sex, is_age)
        """
        is_sex = 0
        is_age = 0
        for dept in depts:
            if str(dept['dept_name']) in {'妇科', '产科', '男科'}:
                if int(sex) not in (1, 2):
                    is_sex = 1
            if str(dept['dept_name']) == '儿科':
                if int(age) < 1:
                    is_age = 1
        return (is_sex, is_age)

    def _check_symptom(self, query):
        """
        :param query:主诉
        :return:返回是否需要症状，以及症状列表
        """
        is_symptom = 0
        params = {'q': query}
        entity_result = self.aisc.query(params, 'entity_extract')
        symptoms = []
        std_department = []
        disease = []
        body_part = []
        symptom_name = []
        if not entity_result['data']:
            return (is_symptom, symptom_name)
        for entity in entity_result['data']:
            if entity.get('type') == 'symptom':
                symptoms.append(entity.get('entity_name'))
            if entity.get('type') == 'std_department':
                std_department.append(entity.get('entity_name'))
            if entity.get('type') == 'disease':
                disease.append(entity.get('entity_name'))
            if entity.get('type') == 'body_part':
                body_part.append(entity.get('entity_name'))
        for dept in std_department:
            if str(dept) in self.dept_symptom_dict:
                for dept_symptom in self.dept_symptom_dict.get(str(dept)):
                    if dept_symptom[0] not in symptom_name:
                        symptom_name.append(dept_symptom[0])

        if std_department and not symptoms and not disease and not body_part:
            is_symptom = 1

        return (is_symptom, symptom_name)

    def cross_data(self, list_a, list_b):
        """
        把两部分结果交叉排序
        :param list_a: 第一部分结果以list存储
        :param list_b: 第二部分结果以list存储
        :return: 把两部分结果分开存储
        """
        len_max, len_min = max(len(list_a), len(list_b)), min(len(list_a), len(list_b))
        result = []
        for i in range(len_min):
            result.append(list_a[i])
            result.append(list_b[i])
        if len(list_b) > len(list_a):
            result.extend(list_b[len_min:])
        else:
            result.extend(list_a[len_max:])
        return result

    def sex_age_valid(self, query, debug=False):
        is_sex = 0
        is_age = 0
        params = {'q': query, 'fl': 'dept_name,score'}
        if debug:
            self.aisc.set_debug(True)
        depts = self.aisc.query(params, 'dept_classify')
        if depts and depts['data']:
            data = depts['data']
            for dept in data:
                if str(dept['dept_name']) in {'妇科', '产科', '男科'}:
                    is_sex = 1
                if str(dept['dept_name']) == '儿科':
                    is_age = 1
        return (is_sex, is_age)
