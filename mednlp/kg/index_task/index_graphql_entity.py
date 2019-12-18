#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_graphql_entity.py -- the index task of entity to cloud solr

Author: chenxk <chenxk@guahao.com>
Create on 2019-06-23 Sunday.
"""
import global_conf
from base_index import BaseIndex
from mednlp.dao.kg_dao import KGGraphqlDao
from mednlp.kg.db_conf import medical_knowledge
import mednlp.text.pinyin as pinyin
from concurrent.futures import ThreadPoolExecutor
import copy
from ailib.client.ai_service_client import AIServiceClient
from ailib.client.cloud_solr import CloudSolr
import json
import traceback
import sys


class IndexGraphQlEntity(BaseIndex):
    index_filename = 'graphql_entity.json'
    core = 'graphql_entity'

    def initialise(self, **kwargs):
        self.kgd = KGGraphqlDao(**kwargs)
        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'CloudIndex')
        self.executor = ThreadPoolExecutor(max_workers=15)
        self.post_size = 256
        self.cloud_client = CloudSolr(global_conf.cfg_path)
        if self.config.has_section('CloudIndex'):
            section = 'CloudIndex'
            if self.config.has_option(section, 'IP'):
                self.cloud_ip = self.config.get(section, 'IP')
            if self.config.has_option(section, 'PORT'):
                self.cloud_port = self.config.get(section, 'PORT')
            if self.config.has_option(section, 'GROUP_PRIMARY_KEY'):
                self.primary_key = self.config.get(section, 'GROUP_PRIMARY_KEY')
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
        self.alias = self.kgd.load_entity_relation(self.inc_ids)
        self.relation_dict, self.relations = self.kgd.load_standard_relation(self.inc_ids)
        self.standard_type_dict = self.kgd.load_standard_type_dict()
        self.relation_attributes = self.kgd.load_relation_attribute(self.inc_ids)
        self.medical_knowledge_disease = self.kgd.load_medical_knowledge_disease_info(self.inc_ids)
        self.medicine_enterprise = self.kgd.load_medicine_enterprise_info(self.inc_ids)
        return self.kgd.load_entity_info(self.inc_ids)

    def process_data(self, docs):
        self.logger.info('开始构建索引...')
        processed_docs = []
        for doc in docs:
            entity_name = doc.pop('name', '') # 删去key:name 获取key=name下的entitiy_name
            doc['name_s'] = entity_name
            standard_name = doc.pop('standard_name', '')  # 添加标准名
            doc['standard_name_s'] = standard_name
            is_standard = doc.pop('is_standard', 0)  # 添加是否标准名标志
            doc['is_standard_s'] = is_standard
            standard_audit_status = doc.pop('standard_audit_status', 0)
            doc['standard_audit_status_s'] = standard_audit_status
            entity_type_id = doc.pop('type', '')
            entity_type = self.standard_type_dict['entity_type'].get(entity_type_id, {}).get('code', None)
            audit_status = doc.pop('audit_status',0)
            if not entity_type:
                continue
            if doc.get('is_delete') and doc['is_delete'] == 1:
                doc['solr_delete'] = 1
            doc.pop('is_delete')
            doc['type_s'] = entity_type
            doc['audit_status_s'] = audit_status
            entity_id = doc['id']
            if self.medical_knowledge_disease.get(entity_id):  # 加载标签信息
                origin_disease = self.medical_knowledge_disease.get(entity_id)
                disease_type = str(origin_disease.get('disease_type', '-1'))
                if disease_type in medical_knowledge.get('disease_type'):
                    addition_labels = self.labels.setdefault(entity_id, [])
                    for label_type in medical_knowledge['disease_type'].get(disease_type):
                        addition_labels.append({'entity_id': entity_id, 'label_type': label_type, 'label_value': origin_disease['disease_id']})

            if self.medicine_enterprise.get(entity_id):  # 加载药品药店信息
                enterprise_ids = self.medicine_enterprise.get(entity_id)
                doc['supplier_ss'] = enterprise_ids

            # 构建别名信息
            if self.alias['entity_name'].get(entity_id):
                doc['relation_set_ss'] = list(self.alias['entity_name'].get(entity_id, []))
                doc['relation_set_id_ss'] = list(self.alias['entity_id'].get(entity_id, []))
                doc['relation_set_ss'].append(doc['name_s'])
                doc['relation_set_id_ss'].append(doc['id'])

            # 构建属性信息
            attributes = self.attributes.get(entity_id, [])
            for row in attributes:
                attribute_type = row.get('attribute_type')
                if self.standard_type_dict['attribute_type'].get(attribute_type):
                    type_row = self.standard_type_dict['attribute_type'].get(attribute_type)
                    if type_row.get('code') and row['attribute_value'] is not None:
                        if type_row.get('value_type') >= 3:
                            doc.setdefault(type_row.get('code') + '_tt', []).append(row['attribute_value'])
                        else:
                            if type_row.get('code') == 'common_weight':
                                doc['common_weight_f'] = row['attribute_value']
                            else:
                                doc.setdefault(type_row.get('code') + '_ss', []).append(row['attribute_value'])

            # 构建关系信息
            relations = self.relation_dict['from'].get(entity_id, [])
            for row in relations:
                relation_type = row.get('relation_type_uuid')
                if self.standard_type_dict['relation_type'].get(relation_type):
                    type_row = self.standard_type_dict['relation_type'].get(relation_type)
                    if type_row.get('code') and row['id'] is not None and row['id'] not in doc.setdefault(type_row.get('code') + '_ss', []):
                        doc.setdefault(type_row.get('code') + '_ss', []).append(row['id'])

            # 构建标签信息
            labels = self.labels.get(entity_id, [])
            for row in labels:
                label_type = row.get('label_type')
                if self.standard_type_dict['label_type'].get(label_type):
                    type_row = self.standard_type_dict['label_type'].get(label_type)
                    if type_row.get('code') and row['label_value'] is not None:
                        doc.setdefault(type_row.get('code') + '_ss', []).append(row['label_value'])
                if row['label_value'] is not None:
                    doc['_'+label_type+'_label_s'] = row['label_value']
                    doc.setdefault('label_set_ss', []).append(label_type)
            if doc.get('label_set_ss'):
                doc['label_set_ss'] = list(set(doc['label_set_ss']))

            doc['name_code_s'] = pinyin.get_pinyin(
                entity_name, mode='first', errors='default')
            doc['name_length_i'] = max((20-len(doc['name_s'])), 1)
            doc['name_py_s'] = pinyin.get_pinyin(
                entity_name, mode='full', errors='default')
            doc['name_ng'] = doc['name_s']
            doc['name_eg'] = doc['name_s']
            doc['name_code_ng'] = doc['name_code_s']
            doc['name_code_eg'] = doc['name_code_s']
            doc['name_py_ng'] = doc['name_py_s']
            doc['name_py_eg'] = doc['name_py_s']
            processed_docs.append(doc)
            # print(doc)
        return processed_docs

    def data_output(self, docs, close=True):
        if not docs:
            self.logger.info('index_cloud_entity 索引构建成功, 无数据更新')
            return
        index_docs = []
        delete_docs = []
        self.logger.info('开始POST索引请求...')
        for doc in docs:
            if doc.get('solr_delete') and doc['solr_delete'] == 1:
                delete_docs.append(doc.get('id'))
            else:
                if doc['type_s'] == 'disease':
                    index_docs.append(doc)

        result_delete = self.executor.map(self.post_data, self.cloud_client.slice_docs(delete_docs))
        result_index = self.executor.map(self.post_data, self.cloud_client.slice_docs(index_docs, self.post_size))
        for item in result_delete:
            if item:
                self.post_data(item)
        failed_datas = []
        for item in result_index:
            if item:
                failed_datas.extend(item)
        if failed_datas and self.post_size >= 64:
            self.post_size /= 2
            self.data_output(failed_datas, close=True)
        self.logger.info('POST索引请求结束,更新总数：%d' % len(index_docs))
        self.executor.shutdown()
        pass

    def post_data(self, docs, interface='ai_graphql_entity', method='index', primary_key=None):
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
            self.logger.info('%s %s error num:%d,size:%.2f res:%s' %
                             (interface, method, len(docs), sys.getsizeof(json.dumps(docs, ensure_ascii=False)) / 1024,
                              json.dumps(res, ensure_ascii=False)))
        return docs


if __name__ == '__main__':
    indexer = IndexGraphQlEntity(global_conf, dev=True)
    indexer.index()
