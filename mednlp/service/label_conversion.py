#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
entity_conversion.py -- the service of entity conversion

Author: chenxk <chenxk@guahao.com>
Create on 2019-04-29 tuesday.
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

class LabelConversion(BaseRequestHandler):

    not_none_field = ['target_label']
    entity_field_dict = {'name': {'type': '_s'}, 'type': {'type': '_s'}}

    def initialize(self, runtime=None, **kwargs):
        super(LabelConversion, self).initialize(runtime, **kwargs)

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
        row_count = 10
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
                ef.add('id')
            if not self.entity_field_dict.get(field):
                continue
            solr_field = field + self.entity_field_dict[field]['type']
            ef.add('%s:%s' % (field, solr_field))
        target_label = input_obj['target_label']
        ef.add('%s:_%s_label_s' % ('target_label_value', target_label))
        ef.add('label_set:label_set_ss')
        ef.add('type:type_s')
        ef.add('standard_name:standard_name_s')
        ef.add('alias:relation_set_ss')
        ef.add('disease_id:disease_id_s')
        fq_dict = {}
        first_fq_dict = {}  # 当有source_label字段时构造首次查询过滤参数
        fq_list = []
        entity_dict = {}
        search_names = []
        result = {'data': {}}
        entitys = []
        ids = set()
        id_filter = '(id:(%s) OR relation_set_id_ss:(%s))'
        name_filter = '(name_s:(%s) OR relation_set_ss:(%s))'
        # 过滤废弃的实体
        fq_dict['audit_status_i'] = '(0 1)'
        first_fq_dict['audit_status_i'] = '(0 1)'
        # id、name、source_label_value三个参数都为空时直接返回空
        if not (input_obj.get('id') or input_obj.get('name') or (input_obj.get('source_label') and input_obj.get('source_label_value'))):
            result['data']['entity'] = entitys
            return result
        if input_obj.get('id'):
            first_fq_dict['id'] = '(' + ' '.join(input_obj['id']) + ')'
            fq_list.append(id_filter % (' '.join(input_obj['id']), ' '.join(input_obj['id'])))
            row_count += len(input_obj['id'])
        if input_obj.get('name'):
            escape_names = self.deal_parameter(input_obj['name'])
            search_names = self.deal_parameter(input_obj['name'])
            escape_names = parameter.escape_solr_list(escape_names)
            first_fq_dict['name_s'] = '(' + ' '.join(escape_names) + ')'
            fq_list.append(name_filter % (' '.join(escape_names), ' '.join(escape_names)))
            row_count += len(input_obj['name'])
        if input_obj.get('type'):
            fq_dict['type_s'] = input_obj['type']
            first_fq_dict['type_s'] = input_obj['type']
        if input_obj.get('source_label'):  # 当指定source_label字段时先进行一次查询，获取到符合除target_label的条件
            source_label = input_obj['source_label']
            first_fq_dict['label_set_ss'] = source_label
            fl = 'id,type:type_s,name:name_s,relation_set_id:relation_set_id_ss,label_set:label_set_ss'
            fl += (',%s:_%s_label_s' % ('source_label_value', source_label))
            if input_obj.get('source_label_value'):
                first_fq_dict['_' + source_label + '_label_s'] = '(' + ' '.join(input_obj['source_label_value']) + ')'
                row_count += len(input_obj['source_label_value'])
            ef.add('%s:_%s_label_s' % ('source_label_value', source_label))
            try:  # 进行第一次搜索
                response = self.cloud_search.solr_search('*:*', 'ai_entity_knowledge_graph', first_fq_dict, timeout=0.3, rows=row_count, fl=fl)
            except:
                traceback.print_exc()
                raise Exception('solr exception')
            docs = response['data']
            for row in docs:
                for r in row.get('relation_set_id', []):
                    if r in entity_dict:  # 同一个实体有两个源标签时选择标签数量多的，一样多时选择第一个遍历到的
                        if len(row.get('label_set', [])) > entity_dict[r].get('label_set', []):
                            entity_dict[r] = row
                    else:
                        entity_dict[r] = row
                ids.add(row['id'])
        if input_obj.get('source_label'):
            if ids:  # 当第一次查询的返回不为空时重置fq_list,否则直接返回空
                fq_list = [id_filter % (' '.join(ids), ' '.join(ids))]
            else:
                result['data']['entity'] = entitys
                if self.get_argument('debug', False):
                    result['data']['res'] = response
                return result
        fq_dict['label_set_ss'] = target_label
        params['fl'] = ','.join(ef)
        try:
            response = self.cloud_search.solr_search(params['q'], 'ai_entity_knowledge_graph', fq_dict, fq_list=fq_list, timeout=0.3, **params)
        except:
            traceback.print_exc()
            raise Exception('solr exception')
        docs = response['data']
        filter_dict = {}
        for doc in docs:  # 处理在一个标签下同本体对应的不同名实体存在多个标签值
            if 'standard_name' not in doc:
                filter_dict[doc['name'] + '|' + doc['type']] = doc
                continue
            key = doc['standard_name'] + '|' + doc['type']
            if filter_dict.get(key):
                # escape_names为空或者两个实体名都在(或都不在)escape_names时比较标签数量
                if (not search_names) or (
                        doc['name'] in search_names and filter_dict[key]['name'] in search_names) or (
                        doc['name'] not in search_names and filter_dict[key]['name'] not in search_names):
                    # 标签数量多的优先级高,数量相等则先遍历到的优先级高
                    if len(doc.get('label_set', [])) > len(filter_dict[key].get('label_set', [])):
                        filter_dict[key] = doc
                elif doc['name'] in search_names:  # 实体名在搜索列表时优先级高
                    filter_dict[key] = doc
            else:
                filter_dict[doc['standard_name'] + '|' + doc['type']] = doc
        for doc in filter_dict.values():
            doc.pop('label_set')
            if 'source_label_value' not in doc and entity_dict.get(doc['id']):  # 当目标标签没有source_label时设置同本体其他实体的标签值
                doc['source_label_value'] = entity_dict[doc['id']].get('source_label_value', '')
            entity = {f: doc[f] for f in entity_field if doc.get(f)}
            entitys.append(entity)
        result['data']['entity'] = entitys
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
    handlers = [(r'/label_conversion', LabelConversion )]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
