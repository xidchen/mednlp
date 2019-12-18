#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_medical_relation.py -- the index tool of medical relation

Author: maogy <maogy@guahao.com>
Create on 2017-07-07 Friday.
"""


import sys
import math
import datetime
import json
from base_index import BaseIndex
from ailib.storage.db import DBWrapper
import global_conf
import mednlp.text.pinyin as pinyin
from mednlp.dao.kg_dao import KGDao
from mednlp.text.synonym import Synonym
from mednlp.utils.utils import unicode_python_2_3

class IndexMedicalEntity(BaseIndex):

    index_filename = 'medical_entity.xml'
    core = 'medical_entity'

    def initialise(self, **kwargs):
        self.db = DBWrapper(self.cfg_path, 'mysql', 'AIMySQLDB')
        self.kgd = KGDao()
        pinyin.load_pinyin_dic()

    def get_data(self):
        entitys = self.kgd.load_disease_info(self.db)
        symptoms = self.kgd.load_symptom_info(self.db)
        self.symptom_dict = {s['entity_id']: s['entity_name'] for s in symptoms}
        entitys.extend(symptoms)
        self.symptom_dict = {}
        for symptom in symptoms:
            self.symptom_dict[symptom['entity_id']] = symptom['entity_name']
        self.disease_property = self.kgd.load_disease_property(self.db)
        self.disease_info = self.kgd.load_disease_relation_info(self.db)
        self.symptom_relation = self.kgd.load_symptom_parent(self.db)
        self._extend_symptom_weight()
        self.symptom_count = self._compute_weight_count()
        self.disease_detail = self.kgd.load_disease_detail(self.db)
        self.disease_medicine = self.kgd.load_disease_medicine(self.db)
        self.disease_std_dept = self.kgd.load_disease_std_dept(self.db)
        self.physical_examination = self.kgd.load_physical_examination_info(
            self.db)
        self.inspection = self.kgd.load_inspection_info(self.db)
        self.disease_insp = self.kgd.load_disease_inspection(self.db)
        return entitys

    def _extend_symptom_weight(self):
        """
        用同义词以及症状间的关系扩展症状权重.
        """
        # 同义词
        synonym = Synonym(['wy_symptom'])
        for disease_id, info in self.disease_info.items():
            symptom_id_set = info.get('symptom_id')
            symptom_weight = info.get('symptom_weight')
            if not symptom_id_set or not symptom_weight:
                continue
            # 同义词症状扩展
            extend_symptom_weight = {}
            for symptom_id, weight in symptom_weight.items():
                symptom_name, symptom_type = weight['name'], weight['type']
                s_weight = weight['weight']
                synonym_symptom = synonym.get_synonym(symptom_id)
                if not synonym_symptom:
                    extend_symptom_weight[symptom_id] = weight
                    continue
                max_weight = self._find_max_weight_symptom(synonym_symptom,
                                                           symptom_weight,
                                                           s_weight)
                weight['weight'] = max_weight
                extend_symptom_weight[symptom_id] = weight
                for s_symptom_id in synonym_symptom:
                    if s_symptom_id not in self.symptom_dict:
                        continue
                    item={'weight': max_weight, 'type': 2,
                          'name': self.symptom_dict[s_symptom_id]}
                    extend_symptom_weight[s_symptom_id] = item
                    symptom_id_set.add(s_symptom_id)
            info['symptom_weight'] = extend_symptom_weight
            # 父子症状扩展
            parent_extend_symptom_weight = {}
            for symptom_id, weight in extend_symptom_weight.items():
                symptom_name, symptom_type = weight['name'], weight['type']
                s_weight = weight['weight']
                parent_extend_symptom_weight[symptom_id] = weight
                parent_symptom = self.symptom_relation.get(symptom_id)
                if not parent_symptom:
                    continue
                for s_symptom_id in parent_symptom:
                    max_weight = self._find_max_weight_symptom(
                        [s_symptom_id], extend_symptom_weight, s_weight)
                    item={'weight': max_weight, 'type': 3,
                          'name': self.symptom_dict[s_symptom_id]}
                    parent_extend_symptom_weight[s_symptom_id] = item
                    symptom_id_set.add(s_symptom_id)
                
            info['symptom_weight'] = parent_extend_symptom_weight
            extend_symptom_weight = {}
            # 补充父子症状的同义词症状
            for symptom_id, weight in parent_extend_symptom_weight.items():
                symptom_name, symptom_type = weight['name'], weight['type']
                s_weight = weight['weight']
                extend_symptom_weight[symptom_id] = weight
                synonym_symptom = synonym.get_synonym(symptom_id)
                if not synonym_symptom:
                    extend_symptom_weight[symptom_id] = weight
                    continue
                max_weight = self._find_max_weight_symptom(
                    synonym_symptom, parent_extend_symptom_weight, s_weight)
                weight['weight'] = max_weight
                extend_symptom_weight[symptom_id] = weight
                for s_symptom_id in synonym_symptom:
                    if s_symptom_id not in self.symptom_dict:
                        continue
                    item={'weight': max_weight, 'type': 4,
                          'name': self.symptom_dict[s_symptom_id]}
                    extend_symptom_weight[s_symptom_id] = item
                    symptom_id_set.add(s_symptom_id)
            info['symptom_weight'] = extend_symptom_weight
        # 父子症状

        # 格式化症状权重(symptom_id, symptom_name, s_type, s_weight)
        for disease_id, info in self.disease_info.items():
            symptom_weight = info.get('symptom_weight')
            if not symptom_weight:
                continue
            symptom_weight_list = []
            for symptom_id, weight in symptom_weight.items():
                symptom_name, symptom_type = weight['name'], weight['type']
                s_weight = weight['weight']
                symptom_weight_list.append(
                    (symptom_id, symptom_name, symptom_type, s_weight))
            symptom_weight_list = sorted(
                symptom_weight_list, key=lambda s: s[3], reverse=True)
            info['symptom_weight'] = symptom_weight_list

    def _find_max_weight_symptom(self, synonym_symptom, symptom_weight,
                                 s_weight):
        max_weight = s_weight
        for symptom_id in synonym_symptom:
            weight_info = symptom_weight.get(symptom_id)
            if weight_info:
                weight = weight_info['weight']
                if weight > max_weight:
                    max_weight = weight
        return max_weight
                
    def _compute_weight_count(self):
        """
        计算症状与疾病之间的权重关系.
        参数:无
        返回值->症状的相关疾病词典,结构:{symptom_id, {disease_id,{disease_name, rate, weight}}}
        """
        symptom_count = {}
        for disease_id, info in self.disease_info.items():
            rate = self.disease_property[disease_id].setdefault('rate', 16)
            for weight_info in info.get('symptom_weight', []):
                symptom_id, symptom_name, s_type, s_weight = weight_info
                if symptom_id not in symptom_count:
                    symptom_count[symptom_id] = 0
                symptom_count[symptom_id] += s_weight * rate
            sex_weight = info.setdefault('sex_weight', {})
            for sex_i in range(1, 3):
                sex_i = str(sex_i)
                weight = sex_weight.setdefault(sex_i, 50)
            age_weight = info.setdefault('age_weight', {})
            for age_i in range(1, 7):
                age_i = str(age_i)
                weight = age_weight.setdefault(age_i, 20)
        self.symptom_count = symptom_count
        return symptom_count

    def process_data(self, docs):
        for doc in docs:
            entity_id = doc['entity_id']
            entity_type = doc['type']
            if 1 == entity_type:
                if self.disease_property.get(entity_id):
                    doc.update(self.disease_property[entity_id])
                is_general_treatment = doc.pop('is_general_treatment', None)
                if not is_general_treatment:
                    if self.disease_std_dept.get(entity_id):
                        std_dept = self.disease_std_dept[entity_id]
                        doc.update(std_dept)
                if self.disease_info.get(entity_id):
                    d_info = self.disease_info[entity_id]
                    doc.update(d_info)
                symptom_weight = doc.pop('symptom_weight', None)
                if symptom_weight and doc.get('common_level') == 1:
                    weight_list = doc.setdefault('symptom_weight', [])
                    # print 'sw:', symptom_weight
                    if not doc.get('rate'):
                        doc['rate'] = 16
                    for symptom_id, symptom_name, s_type, weight in symptom_weight:
                        # print 'dn:', doc['entity_name'], entity_id
                        rate = float(doc['rate'])
                        s_count = float(self.symptom_count[symptom_id])
                        d_weight = float(weight) * rate / s_count
                        # 负症状要考虑同义词,此处待改进
                        d_weight_nega = 1.0 - float(weight) / float(10000)
                        weight_list.append('%s|%s|%s|%s|%s' % (
                            symptom_id, symptom_name, s_type, d_weight,
                            d_weight_nega))
                sex_weight = doc.pop('sex_weight', {})
                if sex_weight:
                    sex_weight_list = doc.setdefault('sex_weight', [])
                    for sex_i in range(1, 3):
                        sex_i = str(sex_i)
                        weight = sex_weight.get(sex_i)
                        sex_weight_list.append(weight)
                age_weight = doc.pop('age_weight', None)
                if age_weight:
                    age_weight_list = doc.setdefault('age_weight', [])
                    for age_i in xrange(1, 7):
                        age_i = str(age_i)
                        weight = age_weight.get(age_i)
                        age_weight_list.append(weight)
                disease_history_weight = doc.pop('disease_history', None)
                if disease_history_weight:
                    disease_history_list = []
                    for disease_id, weight in disease_history_weight.items():
                        dh_weight = '%s|%s' % (disease_id, weight)
                        disease_history_list.append(dh_weight)
                    doc['disease_history'] = disease_history_list
                detail = self.disease_detail.get(entity_id)
                doc['has_disease_detail'] = 0
                if detail:
                    doc.update(detail)
                    doc['has_disease_detail'] = 1
                if self.disease_medicine.get(entity_id):
                    medicines = self.disease_medicine[entity_id]
                    doc['medicine_detail'] = [
                        '%(id)s|%(name)s' % m for m in medicines]
                    doc['has_disease_detail'] = 1
                symptom_disease_id = [entity_id]
                if doc.get('symptom_id'):
                    symptom_disease_id.extend(doc['symptom_id'])
                doc['disease_symptom_id'] = symptom_disease_id
                pe_set = doc.pop('physical_examination_detail', None)
                if pe_set:
                    pe_detail = set()
                    for pe in pe_set:
                        if pe not in self.physical_examination:
                            continue
                        pe_detail.add('%s|%s' % (
                            pe, self.physical_examination[pe]))
                    doc['physical_examination_detail'] = pe_detail
                inspection_set = doc.pop('inspection_detail', None)
                if inspection_set:
                    inspection_detail = set()
                    for inspection in inspection_set:
                        if inspection not in self.inspection:
                            continue
                        inspection_detail.add('%s|%s' % (
                            inspection, self.inspection[inspection]))
                    doc['inspection_detail'] = inspection_detail
                if entity_id in self.disease_insp:
                    doc['inspection_json'] = json.dumps(
                        self.disease_insp[entity_id], encoding='utf-8',
                        ensure_ascii=False)
            else:
                continue            

            entity_name = doc.get('entity_name')
            doc['entity_name_length'] = len(unicode_python_2_3(entity_name))
            doc['entity_name_code'] = pinyin.get_pinyin(entity_name,
                                                        mode='first')
            doc['entity_name_py'] = pinyin.get_pinyin(entity_name, mode='full',
                                                      errors='default')
            doc['first_char'] = doc['entity_name_py'][0].lower()
            if not doc.get('sex') or doc['sex'] in (0, '0'):
                doc['sex'] = ['1', '2']
            if doc.get('age_min'):
                doc['age_min'] = int(doc['age_min'])
            else:
                doc['age_min'] = 0
            if doc.get('age_max'):
                doc['age_max'] = int(doc['age_max'])
            else:
                doc['age_max'] = 5000000
        return docs


if __name__ == "__main__":
    indexer = IndexMedicalEntity(global_conf, dev=True)
    indexer.index()
