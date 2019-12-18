#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
knowledge_graph.py -- the servce of knowledge graph

Author: maogy <maogy@guahao.com>
Create on 2017-09-12 Tuesday.
"""


import os
import sys
from mednlp.service.base_request_handler import BaseRequestHandler
import ailib.service.parameter as parameter
from ailib.client.cloud_solr import CloudSolr
import global_conf
import traceback

cloud_client = CloudSolr(global_conf.cfg_path)

ENTITY_SOLR_QUERY_FIELD = """name_s^10 name_eg^8 name_ng^1 name_code_s^10 name_code_ng^1 name_code_eg^8 name_py_s^11 name_py_ng^2 name_py_eg^9"""

class KnowledgeGraph(BaseRequestHandler):

    multi_field = {'type': 'type', 'entity': 'entity_id',
                   'has_disease_knowledge': 'has_disease_detail',
                   'first_char': 'first_char', 'entity_name': 'entity_name'}
    sort_dict = {
        'default': 'score DESC,entity_name_length ASC,entity_id ASC',
        'pinyin': 'entity_name_py_str ASC,entity_id ASC'
    }

    def initialize(self, runtime=None, **kwargs):
        super(KnowledgeGraph, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query = self.get_q_argument('*:*')
        fl = self.get_argument('fl', 'entity_id,entity_name')
        start = self.get_argument('start', 0, limit=5000)
        rows = self.get_argument('rows', 10, limit=5000)
        sort = self.get_argument('sort', 'default')
        new_version = self.get_argument('new_version', 0)
        original_names = []
        if new_version == '0':
            new_version = 0
        fl = 'entity_id,entity_name,type,' + fl
        params = {'q': query, 'fl': fl, 'start': start, 'rows': rows}
        if sort:
            params['sort'] = self.sort_dict[sort]
        fq_dict = {}
        new_fq = {}
        entity_names = []
        for field, solr_field in self.multi_field.items():
            values = self.get_argument(field, '-1')
            if not values or '-1' == values:
                continue
            if field == 'entity_name':
                entity_names.append(values)
                values = parameter.escape_solr(values)
            if field == 'type':
                if values == '1':
                    new_fq['type_s'] = 'disease'
                else:
                    new_fq['type_s'] = values
            if field == 'first_char':
                values = values.lower()
            fq_dict[solr_field] = parameter.get_parameter_split(values, limit=900)
        new_fl = ['type:type_s']
        for field in fl.split(','):
            if field == 'entity_id':
                new_fl.append('entity_id:id')
            elif field == 'entity_name':
                new_fl.append('entity_name:name_s')
            elif field == 'type':
                new_fl.append('type:type_s')
            else:
                new_fl.append('%s:%s_t'%(field, field))

        try:
            response = self.solr.solr_search(params, 'medical_entity', fq_dict, timeout=2)
        except Exception as e:
            traceback.print_exc()
            raise Exception('solr exception')
        total_count = response['response']['numFound']
        data = response['response']['docs']
        for doc in data:
            doc['version'] = 0
            if doc.get('entity_name'):
                entity_names.append(doc.get('entity_name'))
        if entity_names and new_version:
            if query == '*:*':
                query = '*'
            else:
                entity_names.extend(query.split(' '))
                entity_names.append(query)
            original_names.extend(entity_names)
            parameter.escape_chars.add(' ')
            for i in range(len(entity_names)):
                for c in parameter.escape_chars:
                    if entity_names[i] and c in entity_names[i]:
                        entity_names[i] = entity_names[i][0:entity_names[i].index(c)] + '*'
            new_fq['name_s'] = parameter.get_parameter_split(','.join(entity_names),900)
            try:
                response = cloud_client.solr_search('*', 'ai_entity_text_knowledge', new_fq, fl=','.join(new_fl), rows=10+len(entity_names),qf=ENTITY_SOLR_QUERY_FIELD)
            except Exception as e:
                traceback.print_exc()
                print('cloud search error')
            new_data = response['data']
            new_data_map = {}
            for doc in new_data:
                doc['version'] = 1
                if doc['type'] == 'disease':
                    doc['type'] = 1
                new_data_map[doc['entity_name']] = doc
            for i in range(len(data)):
                if data[i]['entity_name'] in new_data_map and new_data_map[data[i]['entity_name']].get('type') == data[i].get('type'):
                    new_data_map[data[i]['entity_name']]['disease_id'] = data[i]['entity_id']
                    data[i] = new_data_map[data[i]['entity_name']]
                    del new_data_map[data[i]['entity_name']]
            if new_data_map and not fq_dict.get('entity_id'):
                entity_name_str = ','.join(original_names)
                for key, value in new_data_map.items():
                    if key in entity_name_str:
                        data.insert(0, value)
        result = {'totalCount': total_count, 'data': data}
        return result


if __name__ == '__main__':
    handlers = [(r'/knowledge_graph', KnowledgeGraph)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
