#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: FH <fenghui@guahao.com>
Created on 2019/9/22 21:51

The script for classifying entities.(实体分类脚本)
"""
import traceback

from tqdm import tqdm

import global_conf
from ailib.utils.log import GLLog
from ailib.storage.hivedb import HiveWrapper
from mednlp.text.entity_extract import Entity_Extract


class ClassifyEntity:

    def __init__(self,
                 input_source,
                 output_source,
                 entity_type,
                 limit_number=-1,
                 debug_mode=False):
        self.input_source = input_source
        self.output_source = output_source
        self.entity_type = entity_type
        self.limit_number = limit_number
        self.debug_mode = debug_mode
        self.logger = GLLog('classify_entity').get_logger()
        self.conn_hive = HiveWrapper(global_conf.cfg_path,
                                     'SparkDB',
                                     GLLog('db_wrapper').getLogger())
        super(ClassifyEntity, self).__init__()

    def load_data_from_input_source(self):
        """
        从输入源加载数据
        :return: 待分类的实体数据集合
        """
        hql = """
        SELECT
            `entity_id`,
            `entity_name`,
            `entity_type`,
            `status` 
        FROM
            `ai_opendata`.`{input_source_name}` 
        WHERE
            `status`=0
        """

        if self.limit_number > 0:
            hql += ' LIMIT {limit_number}'
            hql = hql.format(input_source_name=self.input_source,
                             limit_number=self.limit_number,
                             entity_type=self.entity_type)
        else:
            hql = hql.format(input_source_name=self.input_source,
                             entity_type=self.entity_type)

        result = []
        try:
            result = self.conn_hive.get_rows(hql)
        except Exception as ex:
            self.logger.info('从输入源:{!r}中加载数据异常,'
                             '原因是:{!r}'.format(self.input_source, ex))
            traceback.print_exc()

        return result

    def output_data_to_output_source(self, processed_list: list):
        """
        分类后的数据存储到输出源
        该输出源会作为【实体归一化】脚本中的输入源进行实体归一化
        """
        processed_list = processed_list[:]
        sql_values = []
        for each_data in processed_list:
            value = "(0, " \
                    "'{entity_id}', " \
                    "'{entity_name}', " \
                    "'{entity_type}', " \
                    "{status})".format(**each_data)
            sql_values.append(value)
        hql = "insert into table ai_opendata.`{output_source}` values{sql_values}".format(
            output_source=self.output_source,
            sql_values=",".join(sql_values)
        )
        self.conn_hive.execute(hql)

    def classify_entity(self):
        """
        调用实体分类引擎进行实体分类
        :return: 获取分类结果并存储到输出源
        """
        # 从输入源加载数据
        input_source_data = self.load_data_from_input_source()
        if not input_source_data:
            self.logger.info('从输入源({!r})加载数据为空'.format(self.input_source))
            return

        # 对输入源中拿到的实体数据进行分类
        # 调用【实体分类引擎】进行实体分类
        processed_list = []
        entity_extractor = Entity_Extract()
        for each_data in tqdm(input_source_data):
            entity_id, entity_name, entity_type, input_status = each_data
            new_result_entities = entity_extractor.result_filter(entity_name, [], [])
            entity_type = self.get_entity_type(new_result_entities)
            output_status = 1 if entity_type else 2
            self.logger.info('源实体名称为:{!r},'
                             '分类后的类型为:{!r}'.format(entity_name, entity_type))

            processed_result = {
                'id': 0,
                'entity_id': entity_id,
                'entity_name': entity_name,
                'entity_type': entity_type,
                'status': output_status
            }
            processed_list.append(processed_result)

        # 输出结果到输出源
        if not self.debug_mode:
            try:
                self.output_data_to_output_source(processed_list)
                self.logger.info('输出实体分类结果到输出源({!r})结束,'
                                 '共输出{:d}条.'.format(self.output_source, len(processed_list)))
            except Exception as ex:
                self.logger.error('输出实体分类结果到输出源({!r})异常,'
                                  '原因是:{!r}'.format(self.output_source, ex))
                traceback.print_exc()
        else:
            self.logger.info('已开启Debug模式，'
                             '不输出结果到输出源({!r})'.format(self.output_source))

    def get_entity_type(self, result_entities: list) -> bool:
        """
        获取实体类型
        :param result_entities: 句子经过分类后的实体结果集
        :return: 返回实体类型，如果分类的结果符合传入的类型，则返回该类型，否则，返回空
        """
        entity_type = ''
        for each_entity in result_entities:
            type_all = each_entity.get('type_all', [])
            if self.entity_type not in type_all:
                continue
            else:
                entity_type = self.entity_type
                break
        return entity_type
