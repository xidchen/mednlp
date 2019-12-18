#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
standardized_entity_name.py -- the service of standardized entity names

Author: raogj <raogj@guahao.com>
Create on 2019-08-02.
"""

import os
import global_conf
from ailib.storage.db import DBWrapper
from ailib.storage.hivedb import HiveWrapper
from ailib.utils.log import GLLog
from mednlp.text.entity_extract import Entity_Extract
from mednlp.dao.sql_standardized_entity_name import SQL_SEN
entity_extractor = Entity_Extract()

logger = GLLog('standardized_entity_name', log_dir=global_conf.out_log_dir, level='info').getLogger()


class StandardizedEntityNames():

    def __init__(self):
        self.db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')
        self.hive_db = HiveWrapper(global_conf.cfg_path, 'HiveDB', GLLog('db_wrapper').getLogger())
        self.type_dict = {'disease': 'disease', 'zsyr0fqA': 'symptom'}
        self.aliases_to_standard_name = self.load_dict()

    def standardized_processing(self, batch_size=10000, entity_type=[]):
        """
        从数据库获取数据，对数据处理后，更新数据库信息
        :param batch_size: 批处理大小
        :param entity_type: 需要获取的实体类别
        :return: 该词处理的数据量
        """
        if not entity_type:
            entity_type = self.type_dict.values()
        sql_select_context = SQL_SEN['standard_name']['context_select'] + ' LIMIT ' + str(batch_size)   # 获取文本sql
        text_num, entity_num = 0, 0
        self.delete_data()  # 从ai_opendata.wy_zny_examination_to_entity_df中删除处理完成的标记数据 context_id='end-tag'
        while True:
            try:
                context = self.hive_db.get_rows(sql_select_context)  # 从数据库获取待处理信息
            except Exception as e:
                logger.error(e)
                logger.error('数据库操作失败：数据读取异常！')
            else:
                logger.info('本次从wy_zny_examination_text_df中读取的数据量：' + str(len(context)))
            if not context:
                break
            standard_name_list = []
            for sentence in context:
                cut_result = entity_extractor.result_filter(sentence[1], [], [])
                standard_name = self.match_standard_name(cut_result, entity_type)
                standard_name_list.append(
                    {'context_id': sentence[0], 'context': sentence[1], 'entity_list': standard_name})
            self.insert_data(standard_name_list)
            # self.update_data(context, status='1')
            text_num += len(context)
            entity_num += len(standard_name_list)
        self.insert_data([{'context_id': 'end-tag', 'entity_list': []}])
        return "本次任务完成，处理数据量为：文本"+str(text_num)+"条，获取实体"+str(entity_num)+"个。"

    def match_standard_name(self, entities, entity_type):
        """
        根据别名与标准名字典，匹配实体标准名
        :param entities: 待处理的实体列表
        :param entity_type: 实体类型列表
        :return: 返回元素为{entity_name, standard_name, entity_type}字典的列表
        """
        if not entities:
            return []
        standard_name = []
        for entity in entities:
            for e_type in entity['type_all']:
                if e_type not in entity_type:
                    continue
                e_name = entity['entity_name']
                standard_name_dict = self.aliases_to_standard_name[e_type]
                if e_name in standard_name_dict:
                    standard_name.append({'entity_name': e_name,
                                          'standard_name': standard_name_dict[e_name],
                                          'entity_type': e_type
                                          })
                else:
                    standard_name.append({'entity_name': entity['entity_name'],
                                          'standard_name': entity['entity_name'],
                                          'entity_type': e_type
                                          })
        return standard_name

    def update_data(self, data, status="1", batchsize=1000):
        """
        更新数据库信息
        :param data: 待更新的数据
        :param status: 状态参数
        :return: 更新成功信息
        """
        if not data:
            return 'data is null'
        context_id_values = []
        for i in range(len(data)):
            if (i+1) % batchsize > 0:
                context_id_values.append("'{context_id}'".format(context_id=data[i][0]))
                if i != len(data) - 1:
                    continue
            if context_id_values:
                sql_update_status = SQL_SEN['standard_name']['status_update'].format(status=status) + "(" + ", ".join(
                    context_id_values) + ")"
                try:
                    self.hive_db.execute(sql_update_status)  # 更新wy_zny_examination_text_df中is_processed_id状态
                except Exception as e:
                    logger.error(e)
                    logger.error('数据库操作失败：数据更新异常,目的：更新is_processed_id为' + status)
            context_id_values = []
        logger.info('本次更新表wy_zny_examination_text_df中is_processed_id=' + status + '，更新数据量：' + str(len(data)))
        return "update done!"

    def insert_data(self, data):
        """
        向数据库插入数据
        :param data: 待插入的数据
        :return: 插入成功信息
        """
        if not data:
            return 'data is null'
        entity_values = []
        for line in data:
            if line['entity_list']:
                for e in line['entity_list']:
                    entity_val = "('{context_id}', '{entity_name}', '{standard_name}', '{entity_type}', now())".format(
                        context_id=line['context_id'], entity_name=e['entity_name'], standard_name=e['standard_name'],
                        entity_type=e['entity_type'])
                    entity_values.append(entity_val)
            else:
                entity_val = "('{context_id}', null, null, null, now())".format(context_id=line['context_id'])
                entity_values.append(entity_val)
        if entity_values:
            sql_insert_entity = SQL_SEN['standard_name']['entity_insert'] + ",".join(entity_values)
            try:
                self.hive_db.execute(sql_insert_entity)  # 向表 wy_zny_examination_to_entity_df 插入实体数据
            except Exception as e:
                logger.error(e)
                logger.error('数据库操作失败：数据插入异常！')
            else:
                logger.info('本次插入表wy_zny_examination_to_entity_df的数据量：' + str(len(entity_values)))
        return 'insert done!'

    def delete_data(self):
        """
        从ai_opendata.wy_zny_examination_to_entity_df中删除处理完成的标记数据 context_id='end-tag'
        :return:
        """
        sql_delete_end_tag = SQL_SEN['standard_name']['end_tag_delete']
        try:
            self.hive_db.execute(sql_delete_end_tag)
        except Exception as e:
            logger.error(e)
            logger.error('数据库操作失败：数据删除异常！')

    def load_dict(self):
        """
        加载数据库中实体别名和标准名到内存
        :return: 返回对应的别名和标准名字典
        """
        aliases_to_standard_name = {e_type: {} for e_type in self.type_dict.values()}
        sql = SQL_SEN['standard_name']['standard_name_select']
        try:
            query_results = self.db.get_rows(sql)
        except Exception as e:
            logger.error(e)
            logger.error('数据库操作异常，别名标准名字典查询异常！')
        for entity in query_results:
            e_type = self.type_dict[entity['entity_type']]
            if entity['entity_name'] in aliases_to_standard_name[e_type]:
                logger.warning(e_type+'中别名"' + entity['entity_name'] + '"重复出现！')
                continue
            aliases_to_standard_name[e_type][entity['entity_name']] = entity['standard_name']
        return aliases_to_standard_name


if __name__ == '__main__':
    file_lock = global_conf.RELATIVE_PATH + 'standardized_entity_name.lock'
    if os.path.exists(file_lock):
        logger.warning('已有一个进程在处理数据，当前进程退出执行。')
        exit(0)
    else:
        file = open(file_lock, "w")
        file.write("running...")
        file.close()
    try:
        standard_name_generator = StandardizedEntityNames()
        info_processed = standard_name_generator.standardized_processing(batch_size=10000)
    except Exception as accident:
        logger.error(accident)
        logger.error('程序意外结束！')
    else:
        logger.info(info_processed)
    finally:
        if os.path.exists(file_lock):
            os.remove(file_lock)
