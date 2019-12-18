#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
bayes.py -- the bayes model for aid diagnose

Author: chenxd
Create on 2018-02-09 Friday.
"""


import math
import global_conf
from mednlp.dao.kg_dao import KGDao
from ailib.utils.log import GLLog
from mednlp.kg.disease import DiseaseEntity


class Bayes(object):

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', True)
        self.logger_level = 'info'
        if self.debug:
            self.logger_level = 'debug'
        self.logger = GLLog('bayes', log_dir=global_conf.log_dir,
                            level=self.logger_level).get_logger()
        self.kg = KGDao(debug=self.debug)
        self.de = DiseaseEntity()

    def get_condition_info(self, symptoms, mr_parsed):
        """
        获取条件相关信息集.
        参数:
        symptoms->条件症状集合.
        返回值->症状及相关疾病信息集合,格式:[{entity_id:,entity_name:,disease_detail:}]
        """
        sex = mr_parsed.get('sex')
        age = mr_parsed.get('age')
        # print '$$$$$$$$$$$', symptoms
        return self.kg.find_disease_with_symptom(
            symptoms, sex, age, mr_parsed['past_medical_history'].keys())

    def prepare_weight_info(self, diseases, symptom_all, mr_parsed,
                            disease_id_dept, dept_score):
        """
        准备权重信息.
        参数:
        diseases->疾病实体信息集合,格式:[{entity_id:,entity_name:,symptom_weight:}]
        disease_id_dept->疾病科室字典,格式:{disease_id, dept_name}
        dept_score->科室分数字典,格式:{dept_name, score}
        mr_lstm_score->病例LSTM分类字典,格式:{disease_name, score}
        返回值->疾病及相关症状的权重信息
        格式:{disease_id:{symptom_id:{positive:,negative:}}}
        """
        disease_weight = {}
        debug_symptom_disease_weight = {}
        other_weight = {}
        disease_pop = {}
        for disease in diseases:
            disease_id = disease['entity_id']
            disease_pop[disease_id] = math.pow(disease['rate'], 4)
            symptom_weight_dict = disease_weight.setdefault(str(disease_id), {})
            d_symptom_weight = disease.get('symptom_weight', [])
            for s_weight in d_symptom_weight:
                weight_list = s_weight.split('|')
                if len(weight_list) != 5:
                    continue
                symptom_id, symptom_name, s_type, s_weight, s_weight_nega = weight_list
                symptom_weight_dict[symptom_id] = {
                    'symptom_id': symptom_id, 'symptom_name': symptom_name,
                    'type': s_type, 'positive': float(s_weight),
                    'negative': float(s_weight_nega)
                }
                if self.debug or True:
                    self._build_debug_info(
                        debug_symptom_disease_weight, disease,
                        symptom_weight_dict[symptom_id], symptom_all)
            weight_list = other_weight.setdefault(disease_id, [])
            age_weight = disease.get('age_weight')
            age = mr_parsed['age']
            if age_weight and age and age != '-1':
                if mr_parsed.get('age_seg'):
                    weight_list.append(age_weight[mr_parsed['age_seg'] - 1])
            sex_weight = disease.get('sex_weight')
            sex = mr_parsed['sex']
            if sex_weight and sex and sex != '-1':
                weight_list.append(sex_weight[int(sex) - 1])
            past_medical_history = mr_parsed['past_medical_history']
            self.de.format(disease)
            pmh_weight_list = self.de.disease_history_weight(
                disease, past_medical_history)
            weight_list.extend(pmh_weight_list)
            if past_medical_history:
                if disease_id in past_medical_history:
                    weight_list.append(300)
            biduous_time = mr_parsed.get('biduous_time')
            if biduous_time:
                acute_time = disease.get('acute')
                if acute_time and biduous_time > acute_time:
                    weight_list.append(10)
                    if biduous_time > acute_time * 10:
                        weight_list.append(10)
                chronic_time = disease.get('chronic')
                if chronic_time and biduous_time < chronic_time:
                    weight_list.append(10)
            dept_score = {str(k): v for k, v in dept_score.items()}
            score_set = set()
            if disease_id in disease_id_dept:
                for dept_name in disease_id_dept[disease_id]:
                    if dept_score.get(dept_name):
                        score_set.add(dept_score.get(dept_name) * 100)
                if score_set:
                    weight_list.append(max(score_set))

        if self.debug:
            for symptom_id, weight_info in debug_symptom_disease_weight.items():
                for w in weight_info:
                    print(w)
        return disease_weight, other_weight, disease_pop

    def _build_debug_info(self, weight, doc, symptom_weight, symptom_all):
        disease_id, disease_name = doc['entity_id'], doc['entity_name']
        if not symptom_weight:
            return
        symptom_id = symptom_weight['symptom_id']
        if symptom_id not in symptom_all:
            return
        symptom_name = symptom_weight['symptom_name']
        weight_posi = symptom_weight['positive']
        weight_nega = symptom_weight['negative']
        s_weight = weight.setdefault(symptom_id, [])
        s_weight.append('%s|%s|%s|%s|%s|%s' % (symptom_id, symptom_name,
                                               disease_id, disease_name,
                                               weight_posi, weight_nega))
        return

    def compute_probability(self, disease_weight, parsed_context, disease_pop,
                            match_symptom):
        """
        计算条件下各个疾病的概率.
        参数:
        disease_weight->各疾病对应各症状的权重.
        结构:{disease_id:{symptom_id:{'positive':,'negative':}}}
        """
        symptom_synonym_group = parsed_context['symptom_synonym']
        symptom_all = parsed_context['symptom_all']
        symptom_negative = parsed_context['symptom_negative']
        for disease, symptom_weight in disease_weight.items():
            pop = self._top_match_symptom_pop(symptom_synonym_group,
                                              symptom_negative,
                                              symptom_weight, match_symptom, 6)
            if disease not in disease_pop:
                disease_pop[disease] = 1.0
            disease_pop[disease] = disease_pop[disease] * pop
            pop, s_id = self._top_symptom_group_weight(symptom_weight,
                                                       symptom_all)
            # print 'disease weight lose:', disease, pop, s_id
            disease_pop[disease] = disease_pop[disease] * pop
        # self.logger.debug('match_symptom:%s' % str(match_symptom))
        return

    def compute_probability_normal(self, weight, disease_pop):
        """
        计算附加条件下的概率衰减.
        参数:
        weight->附加权重衰减.
        disease_pop->各个疾病的权重信息,结构:{disease_id:pop}
        返回值->新的disease_pop
        """
        for disease in disease_pop.keys():
            disease_pop[disease] = math.pow(disease_pop[disease], 0.25)
        new_disease_pop = {}
        # print disease_pop
        # print 'other weight:', weight
        for disease_id, pop in disease_pop.items():
            weight_list = weight.get(disease_id)
            new_disease_pop[disease_id] = pop
            t_pop = pop
            for w in weight_list:
                t_pop *= float(w)/float(100)
                new_disease_pop[disease_id] = t_pop
        # print new_disease_pop
        return new_disease_pop

    def _top_symptom_group_weight(self, symptom_weight, symptom_all):
        """
        该疾病主症状匹配程度衰减.
        参数:
        disease_weight->各疾病对应各症状的权重.
        match_symptom->匹配的症状.
        返回值->衰减系数.
        """
        # 同义词按负权重归并
        symptom_group = {}
        for symptom_id, weight in symptom_weight.items():
            symptoms = symptom_group.setdefault(str(weight['negative']),
                                                set())
            symptoms.add(symptom_id)
        # 选取负权重最高的症状
        symptom_list = []
        for weight_nega, symptom_ids in symptom_group.items():
            symptom_list.append((symptom_ids, str(weight_nega)))
        symptom_list = sorted(symptom_list, key=lambda s: s[1])
        count = 0
        s_id = None
        loss = 1.0
        for symptom_id, weight_nega in symptom_list[0: 5]:
            is_find = False
            s_id = symptom_id
            for s_id in symptom_id:
                if s_id in symptom_all:
                    is_find = True
                    break
            if is_find:
                break
            loss *= float(weight_nega)
            count += 1
        return loss, s_id

    def _top_symptom_weight(self, symptom_weight, symptom_all):
        """
        该疾病主症状匹配程度衰减.
        参数:
        disease_weight->各疾病对应各症状的权重.
        match_symptom->匹配的症状.
        返回值->衰减系数.
        """
        symptoms = []
        for symptom_id, weight in symptom_weight.items():
            symptoms.append((symptom_id, weight['positive'], weight['negative']))
        symptoms = sorted(symptoms, key=lambda s: s[2])
        count = 0
        s_id = None
        loss = 1.0
        for symptom_id, weight, weight_nega in symptoms[0: 2]:
            s_id = symptom_id
            if symptom_id in symptom_all:
                break
            loss *= float(weight_nega)
            count += 1
        return loss, s_id

    def _top_match_symptom_pop(self, symptom_synonym_group, symptom_negative,
                               symptom_weight, match_symptom, top_n):
        """
        选择该疾病概率最大的topN症状.
        """
        weight_list = []
        weight_negative = []
        for synonym_group in symptom_synonym_group:
            weight, t_match_symptom = self._select_optimal_synonym(
                synonym_group, symptom_weight)
            weight_list.append(weight['positive'])
            weight_negative.append(weight['negative'])
            match_symptom.update(t_match_symptom)
        sorted_weight = sorted(weight_list, reverse=True)
        pop = 1.0
        for t_pop in sorted_weight[0: top_n]:
            pop = pop * t_pop
        for symptom_id in symptom_negative:
            s_weight = symptom_weight.get(symptom_id)
            if s_weight:
                pop = pop * s_weight['negative']
        return pop

    def _select_optimal_synonym(self, synonym_group, symptom_weight, **kwargs):
        """
        选择同义词中最理想的.
        """
        min_weight = kwargs.get('min_weight', 0.00001)
        match_symptom = set()
        weight = {'positive': min_weight, 'negative': 1.0}
        weight_field = ('positive', 'negative')
        for synonym_symptom_id in synonym_group:
            t_weight = symptom_weight.get(synonym_symptom_id)
            if t_weight:
                match_symptom.add(synonym_symptom_id)
                for field in weight_field:
                    if t_weight[field] > weight[field]:
                        weight[field] = t_weight[field]
        return weight, match_symptom

    def filter_sex_age(self, disease_set, sex, age, operator_dict=None):
        suitable_disease = self.kg.filter_disease_by_age_sex(disease_set, sex,
                                                             age)
        for disease_id in (disease_set-suitable_disease):
            disease_id = str(disease_id)
            if operator_dict and disease_id in operator_dict:
                del operator_dict[disease_id]
        return operator_dict
