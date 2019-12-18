#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
doctor.py -- the processer of doctor search

Author: maogy <maogy@guahao.com>
Create on 2018-10-04 Thursday.
"""


from ailib.client.search_client import AIServiceClient
import global_conf


class DoctorProcesser(object):
    """
    医生搜索处理器.
    """

    entity_dict = {'hospital': 'hospital', 'department': 'department',
                   'doctor': 'doctor', 'disease': 'disease_name'}
    default_params = {'contract': '1', 'rows': '3', 'start': '0',
                      'do_spellcheck': '1', 'travel': '0',
                      'sort': 'general', 'secondsort': '0',
                      'aggr_field': 'contract_register', 'opensource': '9'}
    
    def __init__(self, **kwargs):
        self.search_client = AIServiceClient(global_conf.cfg_path, 'SearchService')
        self.ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')

    def process(self, inputs, dialog):
        query = ''
        city = ''
        province = ''
        std_department_name = ''
        for input_item in inputs:
            if input_item.get('q'):
                query += input_item['q']
            if input_item.get('std_department_name'):
                std_department_name = input_item['std_department_name']
            if input_item.get('city'):
                city = input_item['city']
            if input_item.get('province'):
                province = input_item['province']
        self.ai_client.set_debug(True)
        entity_res = self.ai_client.query({'q': str(query)}, 'entity_extract')
        self.ai_client.set_debug(False)
        entities = self._get_entitys(entity_res)
        q_list = set()
        for entity in entities:
            if entity['type'] in self.entity_dict:
                q_list.add(entity['entity_name'])
            for entity_type in entity['type_all']:
                if entity_type in self.entity_dict:
                    q_list.add(entity['entity_name'])
        if std_department_name:
            q_list.add(std_department_name)
        params = {'q': str(','.join(q_list))}
        params.update(self.default_params)
        if city:
            params['city'] = city
        if province:
            params['province'] = province
        self.search_client.set_debug(True)
        res = self.search_client.query(params,'doctor_search')
        self.search_client.set_debug(False)
        if res or city not in params:
            res['search_params'] = params
            return res
        del params['city']
        res = self.search_client.query(params,'doctor_search')
        res['search_params'] = params
        return res

    def _get_entitys(self, data):
        if data['code'] != 0:
            return None
        return data['data']
