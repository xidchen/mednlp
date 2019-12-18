#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
suggest.py -- suggest for diagnose

Author: maogy <maogy@guahao.com>
Create on 2018-04-17 Tuesday.
"""


import copy
import json
import numpy
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from mednlp.dao.kg_dao import KGDao
from mednlp.kg.inspection import Inspection


class DiagnoseSuggest(object):
    """
    诊断相关提示.
    """
    suggest_data_field = ['entity_id', 'entity_name', 'symptom_detail',
                          'inspection_json', 'physical_examination_detail']

    def __init__(self, diseases, **kwargs):
        """
        构造函数.
        参数:
        diseases->疾病dict列表.
        kg->实例化了的kg.
        disease_docs->已取得结果的疾病详情.
        """
        self.disease_ids = []
        self.disease_dict = {}
        self.disease_names = []
        self.initial_scores = []
        self.rows = 5
        self.top_one_amount = 8
        self.coefficient = 0.5
        for d in diseases[:self.rows]:
            self.disease_ids.append(d.get('disease_id'))
            self.disease_dict[d.get('disease_id')] = d.get('disease_name')
            self.initial_scores.append(d.get('score'))
        self.disease_docs = kwargs.get('disease_docs')
        self.kg = KGDao()
        self.mr = kwargs.get('mr')
        self.match_symptom = kwargs.get('match_symptom')
        if kwargs.get('lstm_port'):
            self.dcm = AIServiceClient(global_conf.cfg_path, 'AIService',
                                       port=kwargs.get('lstm_port'))
        else:
            self.dcm = AIServiceClient(global_conf.cfg_path, 'AIService')
        if not self.disease_docs:
            fl = ','.join(self.suggest_data_field)
            # self.disease_docs, _, _ = self.kg.find_disease(set(self.disease_ids), fl=fl, rows=self.rows, start=0)
            self.disease_docs, _, _ = self.kg.find_disease(self.disease_dict, fl=fl, rows=self.rows, start=0)

    def symptom_suggest(self):
        """
        症状提示.
        返回值->症状提示实体列表.
        """
        return self.base_suggest('symptom')

    def physical_examination_suggest(self):
        """
        体征提示
        返回值->体征提示实体列表.
        """
        return self.base_suggest('physical_examination')

    def inspection_suggest(self):
        """
        检查检验提示.
        返回值->检查检验提示实体列表.
        """
        return self.base_suggest('inspection', detail_format='json',
                                 handler='_build_inspection')

    def base_suggest(self, field, detail_format=None, **kwargs):
        """
        基础提示方法.
        参数:
        field->需要提示的字段,可选值:symptom, physical_examination, inspection
        detail_format->该字段详细值格式,可选值,默认为None为竖杠分隔,可选值json
        handler->detail处理函数,可选值,默认为_build_split,可选值为:_build_inspection
        返回值->相应的提示内容.
        """
        field_dict = {
            'symptom': 'symptom_detail',
            'physical_examination': 'physical_examination_detail',
            'inspection': 'inspection_json'
        }
        suggest_entity_dict = {}
        disease_rank_weight = [0.45, 0.25, 0.15, 0.09, 0.05]
        handler_name = kwargs.get('handler', '_build_split')
        handler = getattr(self, handler_name)
        for index, disease_id in enumerate(self.disease_ids):
            if not disease_id:
                continue
            disease_doc = self.disease_docs.get(disease_id)
            if not disease_doc:
                continue
            field_detail = disease_doc.get(field_dict[field])
            if not field_detail:
                continue
            if 'json' == detail_format:
                field_detail = json.loads(field_detail)
            detail_len = len(field_detail)
            for detail_index, detail in enumerate(field_detail):
                entity_id, entity_name = handler(detail)
                rank_weight = 1.0 - float(detail_index)/float(detail_len)
                weight = rank_weight * 0.8 * disease_rank_weight[index]
                if entity_name not in suggest_entity_dict:
                    suggest_entity_dict[entity_name] = {
                        'entity_id': entity_id, 'entity_name': entity_name,
                        'weight': weight}
                elif weight > suggest_entity_dict[entity_name]['weight']:
                    suggest_entity_dict[entity_name]['weight'] = weight
        suggest_entity = suggest_entity_dict.values()
        if suggest_entity:
            return sorted(suggest_entity, key=lambda s: s['weight'],
                          reverse=True)
        return []

    def model_suggest(self, field, **kwargs):
        """
        模型提示方法.
        参数:
        field->需要提示的字段,可选值:symptom, inspection
        handler->detail处理函数,可选值:_build_inspection,_build_split
        返回值->相应的提示内容.
        方法逻辑：从Solr中获取传入诊断的症状，将每个症状缀在原病历字段后批量做诊断预测，
                比较症状所在疾病置信度上升幅度，兼顾原诊断排序位置，和症状发病率，给出新排序。
        """
        api_code = 0
        field_dict = {
            'symptom': 'symptom_detail',
            'inspection': 'inspection_json',
        }
        suggest_entity_dict = {}
        suggest_entity_list, suggest_combination = [], []
        entity_amount, entity_cum_amount = [], []
        self.disease_names = []

        if field:
            if field == 'inspection':
                handler_name = kwargs.get('handler', '_build_inspection')
            else:
                handler_name = kwargs.get('handler', '_build_split')
            handler = getattr(self, handler_name)
            for index, disease_id in enumerate(self.disease_ids):
                amount = self.top_one_amount - index
                if not disease_id:
                    continue
                disease_doc = self.disease_docs.get(disease_id)
                if not disease_doc:
                    continue
                self.disease_names.append(disease_doc.get('entity_name'))
                field_detail = disease_doc.get(field_dict[field])
                if not field_detail:
                    continue
                if field == 'inspection':
                    field_detail = json.loads(field_detail)
                entity_amount.append(len(field_detail[:amount]))
                for detail in field_detail[:amount]:
                    entity_id, entity_name = handler(detail)
                    if entity_name not in suggest_entity_dict:
                        if entity_id in self.match_symptom:
                            continue
                        suggest_entity_dict[entity_name] = {
                            'entity_id': entity_id, 'entity_name': entity_name}
                        _field = copy.copy(field)
                        suggest_mr = copy.copy(self.mr)
                        _field = 'chief_complaint' if _field == 'symptom' else _field
                        if (entity_name in self.mr[_field]
                                or entity_name in self.mr['chief_complaint']):
                            suggest_entity_dict.pop(entity_name)
                            continue
                        suggest_mr[_field] = self.mr[_field] + entity_name
                        suggest_entity_list.append(entity_name)
                        suggest_combination.append(suggest_mr)
        entity_cum_amount = numpy.cumsum(entity_amount)
        params = {'medical_record': suggest_combination, 'rows': self.rows}
        try:
            disease_lstm = self.dcm.query(json.dumps(params), 'diagnose_lstm')
            score_list = []
            for mr_id, diagnosis in enumerate(disease_lstm['diagnosis']):
                score_change = 0
                for index, amount in enumerate(entity_cum_amount):
                    if mr_id < amount:
                        new_index, disease_name, new_score = 0, '', 0
                        for new_index, (disease_name, new_score) in enumerate(
                                diagnosis['diseases']):
                            if disease_name == self.disease_names[index]:
                                score_change = (new_score -
                                                self.initial_scores[index])
                                break
                        rank_weight = (self.rows - index) * self.coefficient
                        weight = score_change + rank_weight
                        mr_score = (mr_id,
                                    weight,
                                    score_change,
                                    rank_weight,
                                    self.initial_scores[index],
                                    new_score,
                                    disease_name,
                                    index + 1,
                                    new_index + 1)
                        score_list.append(mr_score)
                        break
            for mr_score in score_list:
                suggest_entity_dict[suggest_entity_list[mr_score[0]]].update(
                    {'weight': mr_score[1],
                     'score_weight': mr_score[2],
                     'rank_weight': mr_score[3],
                     'initial_score': mr_score[4],
                     'new_score': mr_score[5],
                     'disease_name': mr_score[6],
                     'initial_rank': mr_score[7],
                     'new_rank': mr_score[8]})
        except (BaseException, RuntimeError):
            api_code = 1
        suggest_entity = list(suggest_entity_dict.values())
        if field == 'symptom':
            suggestion = {'symptom_suggestion': sorted(
                suggest_entity, key=lambda s: s['weight'], reverse=True)}
            return suggestion, api_code
        if field == 'inspection':
            suggestion = {'inspection_suggestion': sorted(
                suggest_entity, key=lambda s: s['weight'], reverse=True)}
            return suggestion, api_code
        return {}, api_code

    def _build_split(self, detail):
        detail_list = detail.split('|')
        return detail_list[0], detail_list[1]

    def _build_inspection(self, detail):
        i_builder = Inspection()
        i_builder.build_entity(detail)
        return detail['entity_id'], detail['entity_name']
