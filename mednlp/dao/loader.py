#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
loader.py -- some data loader from db

Author: maogy <maogy@guahao.com>
Create on 2017-09-07 Thursday.
"""

from mednlp.dao.sql_box import SQLS
import global_conf
from ailib.storage.db import DBWrapper
from mednlp.kg.db_conf import disease as conf_disease


def create_id_where_clause(value, field, **kwargs):
    """
    生成sql的where id过滤条件.
    参数:
    value:id值,单个id值或多个id列表(集合,元组).
    field:where筛选条件的字段.
    wrap:id值的首尾封装,默认无,一般字符串id需加单引号.
    首尾相同则直接传该字符串即可,否则首尾用逗号分隔,回避逗号封装.
    operator:逻辑操作符(and或or)
    返回值:对应的sql.
    """
    where_clause = ''
    if value:
        wrap = "'"
        if 'wrap' in kwargs:
            wrap = kwargs['wrap']
        value = string_wrapper(value, wrap)
        value_str = value
        if (isinstance(value, (list, tuple, set)) and
                isinstance(field, str)):
            value_str = ','.join(value)
        operator = 'AND'
        if 'operator' in kwargs:
            operator = kwargs['operator']
        clause_format = ' %s %s IN (%s) '
        if isinstance(field, str):
            where_clause = clause_format % (operator, field, value_str)
        else:
            clause_list = []
            for sql_field, id_field in field.items():
                value_id = value.get(id_field)
                if value_id:
                    value_str = ','.join(string_wrapper(value_id, wrap))
                    clause = clause_format % (operator, sql_field, value_str)
                    clause_list.append(clause)
            where_clause = ''.join(clause_list)
    return where_clause


def string_wrapper(elements, wrap="'"):
    """
    字符串首尾字符包裹.
    参数:
    elements->需要处理的字符串或字符串数组,列表,元组.
    wrap->首尾包裹的字符,默认为单引号.
    """
    if isinstance(elements, (list, set, tuple)):
        return ['%s%s%s' % (wrap, e, wrap) for e in elements]
    elif isinstance(elements, str):
        return '%s%s%s' % (wrap, elements, wrap)
    return elements


def load_mmseg_data(db, type_str):
    sql = SQLS['mmseg'][type_str]
    return db.get_rows(sql)


def load_synonym_data(db, type_str):
    sql = SQLS['synonym'][type_str]
    rows = db.get_rows(sql)
    group_dict = {}
    for row in rows:
        group_id, synonym_id = row['group_id'], row['synonym_id']
        synonym_set = group_dict.setdefault(group_id, set())
        synonym_set.add(synonym_id)
    return group_dict


def get_disease_sex_filter():
    male_id = ''
    for k, v in conf_disease.get('attribute', {}).items():
        if v == 'male_rate':
            male_id = k

    sql = """
        SELECT label_value, attribute_type, attribute_value
        FROM `ai_union`.`disease_sex_filter`
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')
    rows = db.get_rows(sql)
    dictionary = {}
    for row in rows:
        i = '2' if row['attribute_type'] == male_id else '1'
        disease_id = row['label_value']
        if disease_id not in dictionary:
            dictionary[disease_id] = {}
        dictionary[disease_id][i] = float(row['attribute_value'])
    print('load sex filter success, len is {}'.format(len(dictionary)))
    db.close()
    return dictionary


def get_disease_age_filter():
    age_types = {}
    for k, v in conf_disease.get('attribute', {}).items():
        for i in range(6):
            if v == 'age_scope_{}_rate'.format(i + 1):
                age_types[k] = str(i + 1)

    sql = """
        SELECT label_value, attribute_type, attribute_value
        FROM `ai_union`.`disease_age_filter`
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')
    rows = db.get_rows(sql)
    dictionary = {}
    for row in rows:
        i = age_types.get(row['attribute_type'])
        if i is not None:
            disease_id = row['label_value']
            if disease_id not in dictionary:
                dictionary[disease_id] = {}
            dictionary[disease_id][i] = float(row['attribute_value'])
    print('load age filter success, len is {}'.format(len(dictionary)))
    db.close()
    return dictionary
