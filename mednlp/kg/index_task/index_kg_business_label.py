#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: FH <fenghui@guahao.com>
Created  on 2019/08/24 12:10
Modified on 2019/09/03 13:00
"""
import os
import json
import sys

from retry import retry

import global_conf
from mednlp.kg.index_task.base_index import BaseIndex
from ailib.client.cloud_solr import CloudSolr


class KgBusinessLabel(BaseIndex):

    index_filename = 'kg_business_label.xml'
    core = 'kg_business_label'

    def __init__(self, g_conf, **kwargs):
        super(KgBusinessLabel, self).__init__(g_conf, **kwargs)
        self.cloud_client = CloudSolr(global_conf.cfg_path)
        self.label_config_file_name = self.get_label_config_file_name()

    def get_label_config_file_name(self):
        """
        第一阶段使用配置文件
        获取业务标签配置文件的文件名称
        :return: 文件名称
        """
        file_name = ''
        section = 'KG_BUSINESS_LABEL'

        if self.config.has_section(section) \
                and self.config.has_option(section, 'LABEL_CONFIG_FILE_NAME'):
            file_name = self.config.get(section, 'LABEL_CONFIG_FILE_NAME')
        return file_name

    @staticmethod
    def read_from_file(file_path):
        """
        读取文件并返回文件内容
        :return: 文件内容
        """
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        return content

    def get_data(self, ids=None):
        """
        解析配置文件获取solr需要的原始数据
        :param ids: 通过sql更新索引使用
        :return: 返回一个字典列表，包含所有原始数据
        """
        if not self.label_config_file_name:
            raise Exception('获取业务标签配置文件异常')
        file_path = os.path.join(
            global_conf.kg_business_label_path, self.label_config_file_name
        )
        self.logger.info('更新或删除索引使用的配置文件路径为:{!r}'.format(file_path))
        file_content = self.read_from_file(file_path)
        json_data = json.loads(file_content)
        return json_data.get('data', []) if json_data else []

    def process_data(self, data):
        """
        data的结果来源于self.get_data()的结果
        处理上一步得到的data，然后处理成solr需要的格式
        :param data: self.get_data()
        :return: solr需要的结果
        """
        self.logger.info('>>>>>>开始构建索引')
        processed_docs = []
        for doc in data:
            _id = doc.get('id')
            org_id = doc.get('org_id')
            if not org_id:
                continue
            biz_id = doc.get('biz_id', '')
            biz_type = doc.get('biz_type', '')
            label = doc.get('label', '')
            is_deleted = doc.get('is_deleted', 1)
            modify_staffid = doc.get('modify_staffid', '')
            gmt_created = doc.get('gmt_created', '')
            gmt_modified = doc.get('gmt_modified', '')
            business_label_obj = {
                'id': _id,
                'org_id_s': org_id,
                'biz_id_s': biz_id,
                'biz_type_s': biz_type,
                'label_s': label,
                'is_deleted_i': is_deleted,
                'modify_staffid_s': modify_staffid,
                'gmt_created_s': gmt_created,
                'gmt_modified_s': gmt_modified
            }
            processed_docs.append(business_label_obj)
        return processed_docs

    def data_output(self, docs, close=True):
        if not docs:
            self.logger.info('>>>>>core：{0}对应的索引已构建成功,'
                             '无数据更新'.format(self.core))
            return

        # 更新索引，如果因为网络问题或其他未知问题会进行重试，重试3次
        update_num = 0
        for doc in docs:
            res = self.post_data([doc], interface='ai_kg_business_label2')
            update_num += 1 if res else update_num
        else:
            self.logger.info('POST索引成功,共更新数据:{:d}'.format(update_num))

    @retry(tries=3)
    def post_data(self, docs, interface, method='index', primary_key=None):
        """
        向solr提交数据，可更新或删除
        :param docs: 待提交到solr的数据
        :param interface: solr对应的collection
        :param method: 添加或删除索引
        :param primary_key: 一般为group key
        :return: 提交的数据
        """
        res = {}
        total_docs = len(docs)
        try:
            if method == 'index':
                res = self.cloud_client.solr_index(docs, interface, primary_key=primary_key)
            elif method == 'delete':
                doc_ids = [doc.get('id') for doc in docs]
                res = self.cloud_client.solr_delete(doc_ids, interface, primary_key=primary_key)
            else:
                raise Exception('The method: {} is not supported.'.format(method))
        except Exception as err:
            self.logger.info(err)

        if res and res['code'] == 200:
            self.logger.info('%s %s success - %d' % (interface, method, total_docs))
        else:
            self.logger.info('%s %s error num:%d,size:%.2f' %
                             (interface, method, total_docs,
                              sys.getsizeof(json.dumps(docs, ensure_ascii=False)) / 1024))
        return True if res else False


if __name__ == "__main__":
    indexer = KgBusinessLabel(global_conf, dev=True)
    indexer.index()
