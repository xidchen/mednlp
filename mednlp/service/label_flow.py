#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
entity_service.py -- the service of entity service

Author: maogy <maogy@guahao.com>
Create on 2019-02-16 Saturday.
"""

import traceback
import json
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.kg.conf import kg_conf
from ailib.utils.exception import AIServiceException
import ailib.service.parameter as parameter

ENTITY_NORMAL_QUERY_FIELD = """
name_s^10 name_eg^5 name_ng^4 name_code_s^10 name_code_ng^4 name_code_eg^5 name_py_s^11 name_py_ng^5 name_py_eg^6
"""

class LabelFlow(BaseRequestHandler):

    not_none_field = ['target_label']
    entity_field_dict = {'name': {'type': '_s'}, 'type': {'type': '_s'}}

    def initialize(self, runtime=None, **kwargs):
        super(LabelFlow, self).initialize(runtime, **kwargs)

    def post(self):
        try:
            if self.request.body:
                input_obj = json.loads(self.request.body)
                self.get(input_obj=input_obj)
        except Exception:
            raise AIServiceException(self.request.body)

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self, **kwargs):
        input_obj = kwargs.get('input_obj')
        self.check_parameter(input_obj)
        params = {
            'q': input_obj.get('q', '*:*'),
            'qf': ENTITY_NORMAL_QUERY_FIELD,
            'start': input_obj.get('start', 0),
            'rows': input_obj.get('rows', 10)
        }
        entity_field = input_obj.get('ef', ['id'])
        if 'label' in entity_field:
            entity_field.remove('label')
        ef = set()
        for field in entity_field:
            if field == 'id':
                ef.add( '%s:%s' % ('original_id', field))
            if not self.entity_field_dict.get(field):
                continue
            solr_field = field + self.entity_field_dict[field]['type']
            ef.add('%s:%s' % (field, solr_field))
        target_label = input_obj['target_label']
        ef.add('%s:_%s_label_s' % ('id', target_label))
        source_label = input_obj['source_label']
        fq_dict = {'label_set_ss': target_label}
        if input_obj.get('id'):
            fq_dict['_' + source_label+'_label_s'] = '(' + ' '.join(input_obj['id']) + ')'
            ef.add('%s:name_s' % 'source_name')
            ef.add('%s:_%s_label_s' % ('source_id', source_label))
        if input_obj.get('name'):
            escape_names = parameter.escape_solr_list(input_obj['name'])
            fq_dict['name_s'] = '(' + ' '.join(escape_names) + ')'
            ef.add('%s:_%s_label_s' % ('source_id', source_label))
            ef.add('%s:name_s' % 'source_name')
        if input_obj.get('type'):
            fq_dict['type_s'] = '(' + ' '.join(input_obj['type']) + ')'
        params['fl'] = ','.join(ef)
        result = {'data': {}}
        try:
            response = self.cloud_search.solr_search(params['q'], 'ai_entity_knowledge_graph', fq_dict, timeout=0.3, **params)
        except:
            traceback.print_exc()
            raise Exception('solr exception')
        docs = response['data']
        entitys = []
        for doc in docs:
            entity = {f: doc[f] for f in entity_field if doc.get(f)}
            entitys.append(entity)
        result['data']['entity'] = entitys
        result['data']['entity_count'] = response['total']
        if self.get_argument('debug', False):
            result['data']['res'] = response
        return result

    def check_parameter(self, parameters):
        for field in self.not_none_field:
            if field not in parameters:
                raise AIServiceException(field)


if __name__ == '__main__':
    handlers = [(r'/label_flow', LabelFlow )]
    import ailib.service.base_service as base_service
    base_service.run(handlers)    
