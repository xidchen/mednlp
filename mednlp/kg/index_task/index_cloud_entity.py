#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_cloud_entity.py -- the index task of entity to cloud solr

Author: chenxk <chenxk@guahao.com>
Create on 2019-06-23 Sunday.
"""
import global_conf
from base_index import BaseIndex
from mednlp.dao.kg_dao import KGDBDao
from mednlp.dao.kg_dao import KGGraphqlDao
from mednlp.kg.db_conf import db_conf, entity_type_dict
from mednlp.kg.db_conf import medical_knowledge
from mednlp.kg.conf import kg_conf
from mednlp.kg.conf import optional_conf
import mednlp.text.pinyin as pinyin
from concurrent.futures import ThreadPoolExecutor
import copy
from ailib.client.ai_service_client import AIServiceClient
from ailib.client.cloud_solr import CloudSolr
import json
import traceback
import sys


class IndexCloudEntity(BaseIndex):
    index_filename = 'cloud_entity.json'
    core = 'cloud_entity'

    def initialise(self, **kwargs):
        self.kgd = KGDBDao(**kwargs)
        self.graph_kgd = KGGraphqlDao(**kwargs)
        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'CloudIndex')
        self.executor = ThreadPoolExecutor(max_workers=15)
        self.post_size = 256
        self.attribute_post_flag = True
        self.cloud_client = CloudSolr(global_conf.cfg_path)
        if self.config.has_section('CloudIndex'):
            section = 'CloudIndex'
            if self.config.has_option(section, 'IP'):
                self.cloud_ip = self.config.get(section, 'IP')
            if self.config.has_option(section, 'PORT'):
                self.cloud_port = self.config.get(section, 'PORT')
            if self.config.has_option(section, 'GROUP_PRIMARY_KEY'):
                self.primary_key = self.config.get(section, 'GROUP_PRIMARY_KEY')
        self.attr_db2field = {}
        self.label_db2field = {}
        self.relation_db2field = {}
        for entity in db_conf.values():
            if entity.get('attribute'):
                self.attr_db2field.update(entity['attribute'])
            if entity.get('label'):
                self.label_db2field.update(entity['label'])
            if entity.get('relation'):
                self.relation_db2field.update(entity['relation'])
        self.entity_field_dict = {}
        for entity_conf in kg_conf['entity'].values():
            if entity_conf.get('label'):
                self.entity_field_dict.update(entity_conf['label'])
            if entity_conf.get('attribute'):
                self.entity_field_dict.update(entity_conf['attribute'])
        self.entity_conf = kg_conf['entity']
        pinyin.load_pinyin_dic()

    def get_data_pre(self, **kwargs):
        if self.inc_sec:
            self.inc_ids = self.kgd.load_entity_id(self.inc_sec)

    def get_data(self):
        if self.inc_sec or self.inc_ids:
            if not self.inc_ids:
                return []
        self.logger.info('开始加载数据库数据...')
        self.attributes = self.kgd.load_entity_attribute(self.inc_ids)
        self.labels = self.kgd.load_entity_label(self.inc_ids)
        self.relations = self.kgd.load_entity_relation(self.inc_ids)
        self.standard_relations = self.kgd.load_standard_relation(self.inc_ids)
        self.standard_type_dict = self.kgd.load_standard_type_dict()
        self.auto_type_dict = self.graph_kgd.load_standard_type_dict()
        self.relation_attributes = self.graph_kgd.load_relation_attribute(self.inc_ids)
        self.medical_knowledge_disease = self.kgd.load_medical_knowledge_disease_info(self.inc_ids)
        self.medicine_enterprise = self.kgd.load_medicine_enterprise_info(self.inc_ids)
        self.entity_text_attributes = self.kgd.load_entity_text_attributes(self.inc_ids)
        return self.kgd.load_entity_info(self.inc_ids)

    def process_data(self, docs):
        self.logger.info('开始构建索引...')
        processed_docs = []
        intersection_code_value = {}  # 从json文件中加载检查检验的属性和属性值
        try:
            with open(global_conf.inspection_code_value_path, 'r', encoding='utf-8') as f:
                intersection_code_value = json.load(f)
        except Exception as err:
            self.logger.warning(traceback.format_exc())
        label_value = {'毒蛇咬伤': '40679', '异位妊娠': '44251'}
        for doc in docs:
            entity_name = doc.pop('name', '') # 删去key:name 获取key=name下的entitiy_name
            doc['name_s'] = entity_name
            standard_name = doc.pop('standard_name', '')  # 添加标准名
            doc['standard_name_s'] = standard_name
            is_standard = doc.pop('is_standard', 0)  # 添加是否标准名标志
            doc['is_standard_i'] = is_standard
            standard_audit_status = doc.pop('standard_audit_status', 0)
            doc['standard_audit_status_i'] = standard_audit_status
            entity_type_id = doc.pop('type', '')
            entity_type = self.auto_type_dict['entity_type'].get(entity_type_id, {}).get('code', '')
            if not entity_type:  # 兼容之前的方式
                entity_type = entity_type_dict.get(entity_type_id)
            audit_status = doc.pop('audit_status',0)
            if not entity_type:
                continue
            if doc.get('is_delete') and doc['is_delete'] == 1:
                doc['solr_delete'] = 1
            doc.pop('is_delete')
            doc['type_s'] = entity_type
            if optional_conf.get('type_name'):
                doc['type_name'+optional_conf['type_name'].get('type', '_s')] = self.standard_type_dict['entity_type'].get(entity_type_id, '')
            if optional_conf.get('audit_status'):
                doc['audit_status'+optional_conf['audit_status'].get('type', '_i')] = audit_status
            entity_id = doc['id']
            if intersection_code_value.get(entity_name):
                attribute = self.attributes.setdefault(entity_id, [])
                intersection_dict = intersection_code_value.get(entity_name)
                attribute_map = db_conf.get(entity_type, {})
                for key, value in attribute_map.get('attribute', {}).items():
                    if intersection_dict.get(value):
                        new_row = {'entity_id': entity_id, 'entity_name':entity_name, 'entity_type': entity_type_id}
                        new_row['attribute_type'], new_row['attribute_value'] = key, intersection_dict.get(value, '')
                        attribute.append(new_row)
            if self.medical_knowledge_disease.get(entity_id):
                origin_disease = self.medical_knowledge_disease.get(entity_id)
                disease_type = str(origin_disease.get('disease_type', '-1'))
                if disease_type in medical_knowledge.get('disease_type'):
                    addition_labels = self.labels.setdefault(entity_id, [])
                    for label_type in medical_knowledge['disease_type'].get(disease_type):
                        addition_labels.append({'entity_id': entity_id, 'label_type': label_type, 'label_value': origin_disease['disease_id']})

            if self.medicine_enterprise.get(entity_id) \
                    and self.entity_conf.get(entity_type)\
                    and self.entity_conf[entity_type].get('attribute'):  # 加载药品药店信息
                enterprise_ids = self.medicine_enterprise.get(entity_id)
                attr_conf = self.entity_conf[entity_type].get('attribute').get('supplier', {})
                if attr_conf.get('type'):
                    doc['supplier' + attr_conf['type']] = enterprise_ids

            if self.attributes.get(entity_id):
                # print('eagle')
                for attribute in self.attributes[entity_id]:
                    attribute_type_conf = self.entity_conf.get(entity_type, {}).get('attribute', {})
                    attr_code = self.auto_type_dict['attribute_type'].get(attribute.get('attribute_type', ''), {}).get('code', '')
                    if not attr_code:
                        attr_code = self.attr_db2field.get(attribute['attribute_type'])
                    if attr_code:
                        if self.entity_field_dict.get(attr_code):
                            doc[attr_code + self.entity_field_dict[attr_code]['type']] = attribute['attribute_value']
                        elif attribute.get('is_open') == 1:
                            doc.setdefault(attr_code + '_ss', []).append(attribute['attribute_value'])

            if self.attributes.get(entity_id):
                attributes = []
                attribute_dict = {}
                for index, attribute in enumerate(self.attributes[entity_id]):
                    attribute_obj = {}
                    if attribute['attribute_type'] in attribute_dict.keys():
                        attribute_obj = attributes[attribute_dict.get(attribute['attribute_type'])]
                        attribute_obj['value'].append(attribute['attribute_value'])
                    else:
                        if self.standard_type_dict.get('attribute_type'):
                            attribute_obj['name'] = self.standard_type_dict['attribute_type'].get(attribute['attribute_type'], '')
                            attribute_obj['value'] = [attribute['attribute_value']]
                            attribute_dict[attribute['attribute_type']] = len(attributes)
                            attributes.append(attribute_obj)
                if optional_conf.get('attributes'):
                    doc['attributes' + optional_conf['attributes']['type']] = json.dumps(attributes, ensure_ascii=False)
            # print('doc', doc)
            if self.labels.get(entity_id):
                label_conf = self.entity_conf.get(entity_type, {}).get('label', {})
                for label in self.labels[entity_id]:
                    label_code = label.get('open_code', '')
                    if not label_code:
                        label_code = self.label_db2field.get(label.get('label_type', ''), '')
                    if label_code in self.entity_field_dict:
                        doc[label_code + self.entity_field_dict[label_code]['type']] = label['label_value']
                    elif label.get('is_open') == 1:
                        doc.setdefault(label_code + '_ss', []).append(label['label_value'])
                if entity_type == 'disease' and label_value.get(entity_name):  # 修复错误标签值
                    doc['disease_id_s'] = label_value.get(entity_name)
            if self.labels.get(entity_id):
                label_type_set = set()
                for label in self.labels[entity_id]:
                    if not label.get('label_type'):
                        continue
                    doc['_' + label['label_type'] + '_label_s'] = label['label_value']
                    label_type_set.add(label['label_type'])
                doc['label_set_ss'] = list(label_type_set)
            if self.relations['entity_name'].get(entity_id):
                doc['relation_set_ss'] = list(self.relations['entity_name'].get(entity_id,[]))
                doc['relation_set_id_ss'] = list(self.relations['entity_id'].get(entity_id,[]))
            if self.standard_relations['from'].get(entity_id) or self.standard_relations['to'].get(entity_id):  # 构建关系字段
                standard_relation = []
                relation_conf = {}
                if self.entity_conf.get(entity_type) and self.entity_conf[entity_type].get('relation'):
                    relation_conf = self.entity_conf[entity_type].get('relation')
                for row in self.standard_relations['from'].get(entity_id, []):  # 加载from关系
                    relation_obj = dict()
                    relation_obj['id'] = row['to_id']
                    relation_obj['name'] = row['to_name']
                    relation_obj['entity_type'] = self.standard_type_dict['entity_type'].get(row['to_type'], '')
                    relation_type_name = self.standard_type_dict['relation_type'].get(row['relation_id'], '')
                    relation_type_name = '-'.join([self.standard_type_dict['entity_type'].get(entity_type_id, ''), relation_obj['entity_type'], relation_type_name])
                    relation_obj['relation_type'] = relation_type_name
                    relation_field = self.auto_type_dict['relation_type'].get(row['relation_id'], {}).get('code', '')
                    if not relation_field:
                        relation_field = self.relation_db2field.get(row['relation_id'], '')  # 设置关系字段
                    if relation_field:
                        entity_ids = doc.setdefault(relation_field + '_ss', [])
                        if row.get('to_is_standard', 0) == 1:
                            entity_ids.append(row['to_id'])
                    if self.relation_attributes.get(row['r_id']):  # 增加关系属性
                        relation_attributes = []
                        relation_attribute_dict = {}
                        for index, attribute_row in enumerate(self.relation_attributes.get(row['r_id'])):
                            relation_attribute = {}
                            if attribute_row['relation_type_attribute_uuid'] in relation_attribute_dict.keys():
                                relation_attribute = relation_attributes[relation_attribute_dict.get(attribute_row['relation_type_attribute_uuid'])]
                                relation_attribute['value'].append(attribute_row['relation_arrribute_value'])
                            else:
                                relation_attribute['name'] = attribute_row['relation_attribute_name']
                                relation_attribute['value'] = [attribute_row['relation_arrribute_value']]
                                relation_attribute_dict[attribute_row['relation_type_attribute_uuid']] = len(relation_attributes)
                                relation_attributes.append(relation_attribute)
                        relation_obj['attributes'] = relation_attributes
                    standard_relation.append(relation_obj)
                    if row['relation_score']:
                        doc[row['to_id'] + '_relation_score_f'] = row['relation_score']
                for row in self.standard_relations['to'].get(entity_id, []):  # 加载to关系
                    relation_obj = dict()
                    relation_obj['id'] = row['from_id']
                    relation_obj['name'] = row['from_name']
                    relation_obj['entity_type'] = self.standard_type_dict['entity_type'].get(row['from_type'], '')
                    relation_type_name = self.standard_type_dict['relation_type'].get(row['relation_id'], '')
                    relation_type_name = '-'.join([relation_obj['entity_type'], self.standard_type_dict['entity_type'].get(entity_type_id, ''), relation_type_name])
                    relation_obj['relation_type'] = relation_type_name
                    relation_field = self.auto_type_dict['relation_type'].get(row['relation_id'], {}).get('code', '')
                    if not relation_field:
                        relation_field = self.relation_db2field.get(row['relation_id'], '')  # 设置关系字段
                    if relation_field:
                        entity_ids = doc.setdefault(relation_field + '_ss', [])
                        if row.get('from_is_standard', 0) == 1:
                            entity_ids.append(row['from_id'])
                    if self.relation_attributes.get(row['r_id']):  # 增加关系属性
                        relation_attributes = []
                        relation_attribute_dict = {}
                        for index, attribute_row in enumerate(self.relation_attributes.get(row['r_id'])):
                            relation_attribute = {}
                            if attribute_row['relation_type_attribute_uuid'] in relation_attribute_dict.keys():
                                relation_attribute = relation_attributes[relation_attribute_dict.get(attribute_row['relation_type_attribute_uuid'])]
                                relation_attribute['value'].append(attribute_row['relation_arrribute_value'])
                            else:
                                relation_attribute['name'] = attribute_row['relation_attribute_name']
                                relation_attribute['value'] = [attribute_row['relation_arrribute_value']]
                                relation_attribute_dict[attribute_row['relation_type_attribute_uuid']] = len(relation_attributes)
                                relation_attributes.append(relation_attribute)
                        relation_obj['attributes'] = relation_attributes
                    standard_relation.append(relation_obj)
                    if row['relation_score']:
                        doc[row['from_id'] + '_relation_score_f'] = row['relation_score']
                standard_relation_type = []
                relation_type_dict = {}
                for relation_obj in standard_relation:
                    relation_name = relation_obj.pop('relation_type')
                    relation_type = {}
                    if relation_name in relation_type_dict.keys():
                        relation_type = standard_relation_type[relation_type_dict.get(relation_name)]
                        relation_type['value'].append(relation_obj)
                    else:
                        relation_type['name'] = relation_name
                        relation_type['value'] = [relation_obj]
                        relation_type_dict[relation_name] = len(standard_relation_type)
                        standard_relation_type.append(relation_type)
                if optional_conf.get('relations'):
                    doc['relations' + optional_conf['relations']['type']] = json.dumps(standard_relation_type, ensure_ascii=False)  # 设置关系集合
            doc['name_code_s'] = pinyin.get_pinyin(
                entity_name, mode='first', errors='default')
            doc['name_length_i'] = max((20-len(doc['name_s'])),1)
            doc['name_py_s'] = pinyin.get_pinyin(
                entity_name, mode='full', errors='default')
            if self.entity_text_attributes.get(entity_id):
                self.entity_text_attributes[entity_id]['name_s'] = doc['name_s']
                if doc.get('solr_delete'):
                    self.entity_text_attributes[entity_id]['solr_delete'] = doc['solr_delete']
                self.entity_text_attributes[entity_id]['name_code_s'] = doc['name_code_s']
                self.entity_text_attributes[entity_id]['name_length_i'] = doc['name_length_i']
                self.entity_text_attributes[entity_id]['name_py_s'] = doc['name_py_s']
                self.entity_text_attributes[entity_id]['type_s'] = doc['type_s']
            processed_docs.append(doc)
            # print(doc)
        return processed_docs

    def index_text_attribute(self, docs):
        self.logger.info('文本属性-开始构建索引...')
        if not docs:
            self.logger.info('文本属性-索引构建成功, 无数据更新')
            return
        delete_list = []
        index_list = []
        for doc in docs:
            doc['name_eg'] = doc.get('name_s', '')
            doc['name_ng'] = doc.get('name_s', '')
            doc['name_code_eg'] = doc.get('name_code_s', '')
            doc['name_code_ng'] = doc.get('name_code_s', '')
            doc['name_py_eg'] = doc.get('name_py_s', '')
            doc['name_py_ng'] = doc.get('name_py_s', '')
            if doc.get('solr_delete'):
                delete_list.append(doc.get('id'))
            else:
                index_list.append(doc)
        index_list = self.cloud_client.slice_docs(index_list)
        delete_list = self.cloud_client.slice_docs(delete_list)
        # 调用通用方法，接口名，key,初始单次上传大小，
        interface_list = ['ai_entity_text_knowledge' for i in index_list]
        methods = ['index' for i in index_list]
        result_index = self.executor.map(self.post_data, index_list, interface_list, methods)
        interface_list = ['ai_entity_text_knowledge' for i in delete_list]
        methods = ['delete' for i in delete_list]
        result_delete = self.executor.map(self.post_data, delete_list, interface_list, methods)
        for item in result_delete:
            if item:
                self.cloud_client.solr_delete(item, 'ai_entity_text_knowledge')
        failed_datas = []
        for item in result_index:
            if item:
                failed_datas.extend(item)
        if failed_datas:
            self.index_text_attribute(failed_datas)
        self.logger.info('文本属性-POST索引请求结束,更新总数：%d' % len(docs))

        self.executor.shutdown()

    def data_output(self, docs, close=True):
        if not docs:
            self.logger.info('index_cloud_entity 索引构建成功, 无数据更新')
            return
        index_params = []
        delete_params = []
        index_param = {
            'cat': 'ai_entity_knowledge_graph',
            'primaryKey': self.primary_key,
            'isAtomic': False,
            'pageDocs': []
        }
        delete_param = {
            'cat': 'ai_entity_knowledge_graph',
            'primaryKey': self.primary_key,
            'ids': []
        }
        self.logger.info('开始POST索引请求...')
        for doc in docs:
            doc['name_eg'] = doc.get('name_s', '')
            doc['name_ng'] = doc.get('name_s', '')
            doc['name_code_eg'] = doc.get('name_code_s', '')
            doc['name_code_ng'] = doc.get('name_code_s', '')
            doc['name_py_eg'] = doc.get('name_py_s', '')
            doc['name_py_ng'] = doc.get('name_py_s', '')
            if doc.get('solr_delete') and doc['solr_delete'] == 1:
                if not delete_params or sys.getsizeof(json.dumps(delete_params[-1], ensure_ascii=False)) >= self.post_size*1024 \
                        or len(delete_params[-1]['ids']) > 50:
                    delete_params.append(copy.deepcopy(delete_param))
                delete_params[-1]['ids'].append(doc.get('id', ''))
            else:
                if not index_params or sys.getsizeof(json.dumps(index_params[-1], ensure_ascii=False)) >= self.post_size*1024 \
                        or len(index_params[-1]['pageDocs']) > 50:
                    index_params.append(copy.deepcopy(index_param))
                index_params[-1]['pageDocs'].append(doc)

        result_delete = self.executor.map(self.post_delete, delete_params)
        result_index = self.executor.map(self.post_index, index_params)
        for item in result_delete:
            if item:
                self.post_delete(item)
        failed_datas = []
        for item in result_index:
            if item:
                failed_datas.extend(item.get('pageDocs', []))
        if failed_datas and self.post_size >= 64:
            self.post_size /= 2
            self.data_output(failed_datas, close=True)
        self.logger.info('POST索引请求结束,更新总数：%d' % len(docs))
        if self.attribute_post_flag:
            self.index_text_attribute(self.entity_text_attributes.values())
            self.attribute_post_flag = False
        self.executor.shutdown()
        pass

    def post_data(self, docs, interface, method='index', primary_key=None):
        try:
            if primary_key:
                if method == 'index':
                    res = self.cloud_client.solr_index(docs, interface, primary_key)
                elif method == 'delete':
                    res = self.cloud_client.solr_delete(docs, interface, primary_key)
            else:
                if method == 'index':
                    res = self.cloud_client.solr_index(docs, interface)
                elif method == 'delete':
                    res = self.cloud_client.solr_delete(docs, interface)
        except Exception as err:
            self.logger.info(err)
            res = {}
        if res and res['code'] == 200:
            self.logger.info('%s %s success - %d' % (interface, method, len(docs)))
            return None
        else:
            self.logger.info('%s %s error num:%d,size:%.2f' %
                             (interface,method, len(docs), sys.getsizeof(json.dumps(docs, ensure_ascii=False)) / 1024))
        return docs

    def post_index(self, param):
        try:
            res = self.plat_sc.query(json.dumps(param, ensure_ascii=False), 'index/1.0', method='post')
        except Exception as err:
            self.logger.info(err)
            res = {}
        if res and res['code'] == 200:
            self.logger.info('ai_entity_knowledge_graph index success - %d' % (len(param.get('pageDocs', []))))
            return None
        else:
            self.logger.info('ai_entity_knowledge_graph index error num:%d,size:%.2f' %
                             (len(param['pageDocs']), sys.getsizeof(json.dumps(param, ensure_ascii=False))/1024))
        return param

    def post_delete(self, param):
        try:
            res = self.plat_sc.query(json.dumps(param, ensure_ascii=False), 'delete/1.0', method='post')
        except Exception as err:
            print(err)
            res = {}
        if res and res['code'] == 200:
            self.logger.info('ai_entity_knowledge_graph delete success')
            return None
        else:
            self.logger.info('ai_entity_knowledge_graph delete error')
        return param


if __name__ == '__main__':
    indexer = IndexCloudEntity(global_conf, dev=True)
    indexer.index()
