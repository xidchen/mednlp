#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
rule_dao.py -- the dao of rule system

Author: chenxk <chenxk@guahao.com>
Create on 2019-11-02 Friday.
"""

import math
import global_conf
import ailib.utils.text as text
from ailib.client.ai_service_client import AIServiceClient
from ailib.client.solr import Solr
from ailib.utils.log import GLLog
from ailib.storage.db import DBWrapper
from mednlp.base.nlp import BaseNLP
from mednlp.kg.db_conf import inspection
from mednlp.kg.db_conf import entity_type_dict
from mednlp.kg.db_conf import db_conf
import mednlp.utils.utils as utils
from mednlp.utils.file_operation import get_disease_name
import traceback
import json


class RuleDBDao(BaseNLP):
    """
    The dao of knowledge graph for db.
    """

    def __init__(self, **kwargs):
        """
        初始化函数,遵循BaseNLP
        """
        super(RuleDBDao, self).__init__(**kwargs)
        self.db = DBWrapper(self.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')

    def load_condition_info(self, ids):
        """
        查询规则条件，这里只查询第一个触发节点的条件
        """
        sql = """
        SELECT
          rcd.id,
          rcd.conditions,
          rcd.rule_node_id rule_node_id_s,
          rcd.rule_case_id rule_case_id_s,
          rcd.organize_code organize_code_s,
          rcd.rule_id rule_id_s,
          rc.is_else_case is_else_case_s,
          r.name rule_name_s,
          r.rule_code rule_code_s,
          r.standard_entity_id standard_entity_id_s,
          r.type rule_type_s,
          r.is_deleted
        From ai_union.rule_condition rcd
        INNER JOIN ai_union.rule r ON rcd.rule_id=r.id
            AND rcd.is_deleted=0 AND r.rule_id IS NULL 
        INNER JOIN ai_union.rule_node rn ON rcd.rule_id=rn.rule_id
          AND rn.type=1 AND rn.is_deleted=0
        INNER JOIN ai_union.rule_case rc ON rn.id=rc.rule_node_id
            AND rc.next_rule_node_id=rcd.rule_node_id AND rc.is_deleted=0
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE rcd.rule_id in (%s)" % ",".join([str(_id) for _id in ids])
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        return list(rows)

    def load_rule_group_info(self, ids):
        """
        查询规则对应的规则组
        """
        sql = """
        SELECT
            r.id rule_id,
            GROUP_CONCAT(DISTINCT rg.name separator '|||') group_name
        FROM ai_union.rule r 
        INNER JOIN ai_union.rule_group_rel rgr ON r.id=rgr.rule_id
            AND r.is_deleted=0 AND rgr.is_deleted=0 AND r.rule_id IS NULL
        INNER JOIN ai_union.rule_group rg ON rgr.rule_group_id=rg.id
            AND rg.is_deleted=0
        %s
        GROUP BY r.id
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE r.id in (%s)" % ",".join([str(_id) for _id in ids])
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        rule_group = {}
        for row in rows:
            if row.get('rule_id'):
                rule_group[row['rule_id']] = row
        return rule_group

    def load_rule_entity_info(self, ids):
        """
        查询规则的应用主体
        """
        sql = """
        SELECT
            r.id rule_id,
            GROUP_CONCAT(DISTINCT e.entity_uuid separator '|||') entity_uuid,
            GROUP_CONCAT(DISTINCT e.entity_name separator '|||') entity_name
        FROM ai_union.rule r 
        INNER JOIN ai_union.rule_entity_rel rer ON r.id=rer.rule_id 
            AND rer.is_deleted=0 AND r.rule_id IS NULL
        INNER JOIN ai_union.entity e on rer.entity_uuid=e.entity_uuid
        %s
        GROUP BY r.id
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE r.id in (%s)" % ",".join([str(_id) for _id in ids])
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        rule_group = {}
        for row in rows:
            if row.get('rule_id'):
                rule_group[row['rule_id']] = row
        return rule_group

    def load_rule_question_code_info(self, ids):
        """
        查询规则中配置的全局问题code
        """
        sql = """
        SELECT
            rgq.rule_id,
            rgq.question_id,
            rgq.global_code
        FROM ai_union.rule_global_question rgq
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE rgq.is_deleted=0 AND rgq.rule_id in (%s)" % ",".join([str(_id) for _id in ids])
        else:
            inc_sql = "WHERE rgq.is_deleted=0 "
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        rule_question_code = {}
        for row in rows:
            if row.get('rule_id') and row.get('question_id') and row.get('global_code'):
                rule_question_code.setdefault(row['rule_id'], {})[row['question_id']] = row['global_code']
        return rule_question_code

    def load_rule_id(self, sec):
        """
        加载规则ID.
        """
        sql = """
        SELECT
            r.id id
        FROM ai_union.rule r 
        WHERE r.gmt_modified >= '%s' AND r.rule_id IS NULL
        """
        modify_time = utils.pasttime_by_seconds(sec)
        rows = self.db.get_rows(sql % modify_time)
        return [row['id'] for row in rows if row['id']]

    def load_delete_rule_info(self, ids):
        """
        查询需要删除的规则ID
        """
        sql = """
        SELECT
            rc.id
        FROM ai_union.rule_condition rc
        INNER JOIN ai_union.rule r ON rc.rule_id=r.id
          AND rc.is_deleted=1
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE rc.rule_id in (%s)" % ",".join([str(_id) for _id in ids])
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        if rows:
            return [row.get('id', '') for row in rows]
        return []

    def load_case_next_info(self, ids):
        """
        查询case对应的下个节点信息
        """
        sql = """
        SELECT
            rc.id,
            rn2.type
        FROM ai_union.rule_case rc INNER JOIN ai_union.rule_node rn2 
            ON rc.next_rule_node_id=rn2.id
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE rc.rule_id in (%s)" % ",".join([str(_id) for _id in ids])
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        result = {}
        if rows:
            for row in rows:
                if row.get('id') and row.get('type'):
                    result[row['id']] = row['type']
        return result
