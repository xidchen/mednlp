#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_rule.py -- the index task of rule to cloud solr

Author: chenxk <chenxk@guahao.com>
Create on 2019-11-02
"""
import global_conf
from base_index import BaseIndex
import mednlp.text.pinyin as pinyin
import hashlib
from mednlp.dao.rule_dao import RuleDBDao
from concurrent.futures import ThreadPoolExecutor
import copy
from ailib.client.cloud_solr import CloudSolr
import json
import traceback
import sys


class IndexRuleCondition(BaseIndex):
    index_filename = 'rule.json'
    core = 'rule_condition'

    def initialise(self, **kwargs):
        self.rule_dao = RuleDBDao(**kwargs)
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
            self.inc_ids = self.rule_dao.load_rule_id(self.inc_sec)

    def get_data(self):
        if self.inc_sec or self.inc_ids:
            if not self.inc_ids:
                return []
        self.logger.info('开始加载数据库数据...')
        self.rule_group = self.rule_dao.load_rule_group_info(self.inc_ids)
        self.rule_entity = self.rule_dao.load_rule_entity_info(self.inc_ids)
        self.question_code = self.rule_dao.load_rule_question_code_info(self.inc_ids)
        self.delete_rule = self.rule_dao.load_delete_rule_info(self.inc_ids)
        self.next_case = self.rule_dao.load_case_next_info(self.inc_ids)
        return self.rule_dao.load_condition_info(self.inc_ids)

    def process_data(self, docs):
        self.logger.info('开始构建索引...')
        processed_docs = []
        if docs:
            processed_docs.extend([{'id': _id, 'solr_delete': 1} for _id in self.delete_rule])
        for doc in docs:
            rule_id = doc.get('rule_id_s', None)
            case_id = doc.get('rule_case_id_s')
            conditions = doc.pop('conditions', None)
            is_deleted = doc.pop('is_deleted', 0)
            if not rule_id:
                continue
            if doc['id'] in self.delete_rule:
                doc['solr_delete'] = 1
                processed_docs.append(doc)
                continue
            # 配置规则组名称
            if self.rule_group.get(rule_id):
                doc['rule_group_ss'] = [name for name in self.rule_group[rule_id].get('group_name', '').split('|||')]
            # 配置应用主体
            if self.rule_entity.get(rule_id):
                doc['rule_entity_ss'] = [name for name in self.rule_entity[rule_id].get('entity_name', '').split('|||')]
            # 配置当前condition对应的case的下个节点是否为最后一个节点
            if self.next_case.get(case_id):
                doc['next_node_type_s'] = self.next_case.get(case_id)
            # 配置条件
            condition_list = json.loads(conditions, encoding='utf-8')
            if self.question_code.get(rule_id):
                question_dict = self.question_code.get(rule_id)
                gad_condition_flag = True
                for condition in condition_list:
                    question_id = condition.get('question', {}).get('id')
                    question_symbol = condition.get('symbol', {}).get('text')
                    question_value = condition.get('value', '')
                    code = question_dict.get(question_id, None)
                    if code:
                        if question_symbol in ('等于', '包含') and question_value:
                            question_value = hashlib.md5(question_value.encode(encoding='utf8')).hexdigest()
                            doc['question_{}_{}_i'.format(code, question_value)] = 1
                            doc['question_total_i'] = doc.setdefault('question_total_i', 0) + 1
                            gad_condition_flag = False
                        else:
                            doc['question_{}_i'.format(code)] = 1
                            doc['question_total_i'] = doc.setdefault('question_total_i', 0) + 1
                if gad_condition_flag:
                    doc['gad_condition_s'] = '1'
            if not doc.get('question_total_i'):
                doc['question_total_i'] = 0

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
                index_docs.append(doc)
        delete_args = ((docs, 'ai_rule_condition_prefilter', 'delete') for docs in self.cloud_client.slice_docs(delete_docs))
        result_delete = self.executor.map(lambda p: self.post_data(*p), delete_args)
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

    def post_data(self, docs, interface='ai_rule_condition_prefilter', method='index', primary_key=None):
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
    indexer = IndexRuleCondition(global_conf, dev=True)
    indexer.index()
