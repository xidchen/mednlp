#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
entity_service.py -- the service of entity service

Author: chenxd
Create on 2019-02-16 Saturday.
"""


import json
import traceback
from ailib.client.ai_service_client import AIServiceClient
import ailib.service.parameter as parameter
from ailib.utils.exception import AIServiceException
import traceback
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.kg.conf import kg_conf
from mednlp.kg.conf import optional_conf
from mednlp.kg.inspection import Inspection
import global_conf
import collections



ENTITY_FIELD_DICT = {'id': {'type': ''}, 'name': {'type': '_s'},
                     'type': {'type': '_s'}, 'standard_name': {'type': '_s'}}
ENTITY_SOLR_QUERY_FIELD = """
name_s^10 relation_set_ss^9 name_eg^8 name_ng^1 
name_code_s^10 name_code_ng^1 name_code_eg^8 
name_py_s^11 name_py_ng^2 name_py_eg^9
"""
ENTITY_NORMAL_QUERY_FIELD = """
name_s^10 name_eg^5 name_ng^4 name_code_s^10 name_code_ng^4 name_code_eg^5 name_py_s^11 name_py_ng^5 name_py_eg^6
"""
ENTITY_FIELD_DICT.update(optional_conf)
for entity_conf in kg_conf['entity'].values():
    if entity_conf.get('label'):
        ENTITY_FIELD_DICT.update(entity_conf['label'])
    if entity_conf.get('attribute'):
        ENTITY_FIELD_DICT.update(entity_conf['attribute'])
    if entity_conf.get('relation'):
        ENTITY_FIELD_DICT.update(entity_conf['relation'])
aisc = AIServiceClient(global_conf.cfg_path, 'AIService')


class EntityService(BaseRequestHandler):

    not_none_field = []

    def initialize(self, runtime=None, **kwargs):
        super(EntityService, self).initialize(runtime, **kwargs)

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
        query = self.deal_parameter(input_obj.get('q', '*:*'))
        if query != '*:*':
            query = parameter.escape_solr(query)
        params = {
            'q': query,
            'qf': ENTITY_NORMAL_QUERY_FIELD,
            'start': input_obj.get('start', 0),
            'rows': input_obj.get('rows', 10)
        }
        entity_field = input_obj.get('ef', ['id'])
        if 'label' in entity_field:
            entity_field.remove('label')
        ef = set()
        for field in entity_field:
            if ENTITY_FIELD_DICT.get(field):
                solr_field = field + ENTITY_FIELD_DICT[field]['type']
                ef.add('%s:%s' % (field, solr_field))
            else:
                ef.add('%s:%s' % (field, field + '_ss'))
        detail_dict = {'symptom': 'symptom_detail',
                       'physical_examination': 'physical_examination_detail',
                       'inspection': 'inspection_json'}
        detail_field = set(detail_dict.keys()) & set(entity_field)
        if detail_field:
            solr_field = 'disease_id' + ENTITY_FIELD_DICT['disease_id']['type']
            ef.add('%s:%s' % ('disease_id', solr_field))
        if input_obj.get('status'):  # 支持检查检验大小项支持
            status = input_obj.get('status')
            status_solr_field = status + '_explanation'
            if ENTITY_FIELD_DICT.get(status_solr_field):
                status_explanation = status_solr_field + ENTITY_FIELD_DICT[status_solr_field]['type']
                ef.add('status_explanation:%s' % status_explanation)

        fq_dict = {}
        fq_list = []
        if input_obj.get('id'):
            if input_obj.get('match_alias') == 1:
                id_values = '(' + ' '.join(input_obj['id']) + ')'
                fq_list.append('(id:%s OR relation_set_id_ss:%s OR disease_id_s:%s)' % (id_values, id_values, id_values))
            else:
                id_values = '(' + ' '.join(input_obj['id']) + ')'
                fq_list.append('(id:%s OR disease_id_s:%s)' % (id_values, id_values))
        escape_names = []
        if input_obj.get('name'):
            escape_names = self.deal_parameter(input_obj['name'])
            escape_names = parameter.escape_solr_list(escape_names)
            if input_obj.get('match_alias') == 1:
                name_values = '(' + ' '.join(escape_names) + ')'
                fq_list.append('(name_s:%s OR relation_set_ss:%s)' % (name_values, name_values))
            else:
                fq_dict['name_s'] = '(' + ' '.join(escape_names) + ')'
        if input_obj.get('exclude_name'):
            exclude_name = self.deal_parameter(input_obj['exclude_name'])
            exclude_name = parameter.escape_solr_list(exclude_name)
            exclude_name = ['-'+name for name in exclude_name]
            if escape_names:
                exclude_name.extend(escape_names)
            fq_dict['name_s'] = '(' + ' '.join(exclude_name) + ')'
        if input_obj.get('type'):
            fq_dict['type_s'] = '(' + ' '.join(input_obj['type']) + ')'
        if input_obj.get('type_name'):
            fq_dict['type_name_s'] = '(' + ' '.join(input_obj['type_name']) + ')'
        if input_obj.get('audit_status'):
            fq_dict['audit_status_i'] = '(' + ' '.join(input_obj['audit_status']) + ')'
        if input_obj.get('is_standard'):
            fq_dict['is_standard_i'] = input_obj['is_standard']
            fq_dict['standard_audit_status_i'] = 1
        if input_obj.get('is_common') == '1':
            fq_dict['is_common_s'] = '是'
        if input_obj.get('label'):
            fq_dict['label_set_ss'] = '(' + ' '.join(input_obj['label']) + ')'
        if input_obj.get('label_intersection'):
            fq_dict['label_set_ss'] = '(' + ' AND '.join(input_obj['label_intersection']) + ')'
        label_field = input_obj.get('label_field')
        label = input_obj.get('label')
        label_intersection = input_obj.get('label_intersection')
        if label_field:
            ef.update(['_' + f+'_label_s' for f in label_field])
        params['fl'] = ','.join(ef)
        label_value = input_obj.get('label_value', [])


        if not input_obj.get('q'):
            if label:
                for f in label:
                    f_key = '_' + f+'_label_s'
                    if label_value:
                        f_value = '(' + " OR ".join(label_value) + ')'
                        fq_list.append(f_key + ':' + f_value)
                if fq_list:
                    fq_list = ['(' + " OR ".join(fq_list) + ')']
            elif label_intersection:
                for f in label_intersection:
                    f_key = '_' + f + '_label_s'
                    if label_value:
                        f_value = '(' + " OR ".join(label_value) + ')'
                        fq_list.append(f_key + ':' + f_value)
                if fq_list:
                    fq_list = ['(' + " AND ".join(fq_list) + ')']
        if input_obj.get('field_filter'):  # 自定义过滤字段
            for field, values in input_obj.get('field_filter').items():
                if not ENTITY_FIELD_DICT.get(field):
                    if values and isinstance(values, list):
                        fq_list.append('%s:%s' % (field+'_ss', '(' + ' AND '.join([str(value) for value in values]) + ')'))
                    elif values:
                        fq_list.append('%s:%s' % (field+'_ss', '(' + str(values) + ')'))
                    continue
                solr_field = field + ENTITY_FIELD_DICT[field]['type']
                if isinstance(values, list) and len(values) != 0:
                    fq_list.append('%s:%s' % (solr_field, '(' + ' AND '.join([str(value) for value in values]) + ')'))
                elif isinstance(values, str) and values != '':
                    if values == '*' and ENTITY_FIELD_DICT[field]['type'] in ['_i', '_f']:
                        values = '[* TO *]'
                    fq_list.append('%s:%s' % (solr_field, '(' + values + ')'))
                elif isinstance(values, int):
                    fq_list.append('%s:%s' % (solr_field, '(' + str(values) + ')'))
        if input_obj.get('match_alias') == 1:
            params['qf'] = ENTITY_SOLR_QUERY_FIELD  # 开启别名匹配
        if input_obj.get('sex'):
            sex = input_obj.get('sex')
            sex_field = ''
            if sex == 1:
                sex_field = 'male_rate'
            elif sex == 2:
                sex_field = 'female_rate'
            if sex_field and ENTITY_FIELD_DICT.get(sex_field):
                sex_field = sex_field + ENTITY_FIELD_DICT[sex_field]['type']
                fq_dict['-'+sex_field] = 0

        result = {'data': {}}
        params['bf'] = 'name_length_i'
        params['sort'] = collections.OrderedDict()
        if query == '*:*':  # 设置默认查询根据词频排序
            params['sort']['common_weight_f'] = 'desc'
            params['sort']['name_length_i'] = 'desc'
            name_score = '0'
        else:
            params['sort']['name_length_i'] = 'desc'
            params['sort']['common_weight_f'] = 'desc'
            name_score = 'field(name_length_i)'
        if input_obj.get('label_order'):  # 根据label_order设置打分规则
            bf = []
            for index, label_item in enumerate(input_obj.get('label_order')[::-1]):
                bf.append('if(exists(_%s_label_s),%d,0)' % (label_item, (index+1)*100))
            if bf:
                params['bf'] = 'sum(max(%s),%s,if(exists(common_weight_f),1,0))' % (','.join(bf), name_score)
                params['sort']['score'] = 'desc'
                params['sort'].move_to_end('score', last=False)
        if not fq_dict:
            fq_dict['id'] = '*'
        try:
            # response = self.solr.solr_search(params, 'entity', fq_dict, fq_list=fq_list, timeout=2)
            response = self.cloud_search.solr_search(params['q'], 'ai_entity_knowledge_graph', fq_dict, fq_list=fq_list, timeout=0.3,**params)
        except:
            traceback.print_exc()
            raise Exception('solr exception')
        docs = response['data']
        entitys = []
        std_disease_id = set()
        for doc in docs:
            entity = {}
            if label_field:
                doc_label = entity.setdefault('label', {})
                for label in label_field:
                    if doc.get('_' + label + '_label_s'):
                        doc_label[label] = doc['_' + label + '_label_s']

            for field in entity_field:
                if field in doc.keys():
                    entity[field] = doc.get(field)
            if detail_field and doc.get('disease_id'):
                entity['disease_id'] = doc.get('disease_id')
                std_disease_id.add(doc['disease_id'])
            if doc.get('relations'):  # 配置关系集合
                entity['relations'] = json.loads(doc.get('relations'))
            if 'attributes' in entity_field and doc.get('attributes'):  # 配置属性集合
                entity['attributes'] = json.loads(doc.get('attributes'))
            if doc.get('attribute_name_map'):  # 配置属性类型和名称的映射
                entity['attribute_name_map'] = json.loads(doc.get('attribute_name_map'))
            if doc.get('relation_name_map'):  # 配置关系类型和名称的映射
                entity['relation_name_map'] = json.loads(doc.get('relation_name_map'))

            entitys.append(entity)
        if detail_field:
            kg_fields = list(detail_dict.values())
            kg_fields.append('entity_id')
            res = aisc.query({'entity': ','.join(std_disease_id), 'fl': ','.join(kg_fields)}, 'knowledge_graph')
            if res and res.get('code') == 0 and res.get('data'):
                entity_dict = {}
                for doc in res['data']:
                    if not doc.get('entity_id'):
                        continue
                    entity_dict[doc['entity_id']] = doc
                for entity in entitys:
                    e_id = entity.get('disease_id')
                    if not e_id or e_id not in entity_dict:
                        continue
                    kg_entity = entity_dict[e_id]
                    for field in detail_field:
                        kg_detail_field = detail_dict[field]
                        if kg_entity.get(kg_detail_field):
                            if field == 'inspection':
                                try:
                                    inspects = json.loads(kg_entity[kg_detail_field])
                                    new_inspects = []
                                    for inspect in inspects:
                                        new_inspect = Inspection().build_entity(inspect)
                                        item = {'id': inspect['entity_id'],
                                                'name': new_inspect['entity_name'],
                                                'type': 'inspection'}
                                        new_inspects.append(item)
                                    entity['inspection'] = new_inspects
                                except Exception as e:
                                    traceback.print_exc()
                                    continue
                            else:
                                details = kg_entity[kg_detail_field]
                                new_details = []
                                for detail in details:
                                    d_id, d_name = detail.split('|')[0: 2]
                                    item = {'id': d_id, 'name': d_name,
                                    'type': field}
                                    new_details.append(item)
                                entity[field] = new_details
        result['data']['entity'] = entitys
        result['data']['entity_count'] = response['total']
        if self.get_argument('debug', False):
            result['data']['res'] = response
        return result

    def check_parameter(self, parameters):
        for field in self.not_none_field:
            if field not in parameters:
                raise AIServiceException(field)

    def deal_parameter(self, parameters):
        """
        根据传入类型处理字符串前后空格
        :param parameters: 字符或列表类型值
        :return: 处理后的入参
        """
        if isinstance(parameters, str):
            parameters = parameters.strip()
        elif isinstance(parameters, list):
            for index in range(len(parameters)):
                if isinstance(parameters[index], str):
                    parameters[index] = parameters[index].strip()
        return parameters


if __name__ == '__main__':
    handlers = [(r'/entity_service', EntityService)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
