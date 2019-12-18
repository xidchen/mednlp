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
import mednlp.text.pinyin as pinyin
from concurrent.futures import ThreadPoolExecutor
import copy
from ailib.client.ai_service_client import AIServiceClient
from ailib.client.cloud_solr import CloudSolr
import json
import traceback
import sys


class IndexGraphQlRelation(BaseIndex):
    index_filename = 'graphql_relation.json'
    core = 'graphql_relation'

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
        self.alias = self.kgd.load_entity_relation(self.inc_ids)
        self.relation_dict, self.relations = self.kgd.load_standard_relation(self.inc_ids)
        self.standard_type_dict = self.kgd.load_standard_type_dict()
        self.relation_attributes = self.kgd.load_relation_attribute(self.inc_ids)
        return self.relations

    def process_data(self, docs):
        self.logger.info('开始构建关系索引...')
        processed_docs = []
        for doc in docs:
            relation_obj = {}
            relation_obj['id'] = doc['id']
            relation_type_uuid = doc.pop('relation_type_uuid', None)
            relation_type = self.standard_type_dict['relation_type'].get(relation_type_uuid, {})
            if not relation_type:
                continue
            if doc.get('from_is_standard') != 1 or doc.get('to_is_standard') != 1:
                continue
            relation_obj['relation_type_s'] = relation_type.get('code', '')
            relation_obj['relation_name_s'] = relation_type.get('name', '')
            relation_obj['audit_status_s'] = doc.get('relation_status', '0')
            if doc.get('is_delete') and doc['is_delete'] == 1:
                relation_obj['solr_delete'] = 1
            # 放置From信息
            relation_obj['from_id_s'] = doc.get('from_id')
            relation_obj['from_name_s'] = doc.get('from_name')
            relation_obj['from_type_s'] = self.standard_type_dict['entity_type'].get(doc.get('from_type'), {}).get('code', '')
            # 放置To信息
            relation_obj['to_id_s'] = doc.get('to_id')
            relation_obj['to_name_s'] = doc.get('to_name')
            relation_obj['to_type_s'] = self.standard_type_dict['entity_type'].get(doc.get('to_type'), {}).get('code', '')
            relation_obj['relation_score_f'] = doc.get('relation_score', '')

            # TODO 加载关系属性数据

            processed_docs.append(relation_obj)
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

    def post_data(self, docs, interface='ai_graphql_relation', method='index', primary_key=None):
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
    indexer = IndexGraphQlRelation(global_conf, dev=True)
    indexer.index()
