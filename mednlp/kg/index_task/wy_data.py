#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
data.py -- some funtion of data loader

Author: maogy <maogy@guahao.com>
Create on 2017-01-07 Saturday.
"""

import wylib.util.helper as helper


AREA_LOOKUP = {}
HOSPITAL_TYPE_LOOKUP = {}
HOSPITAL_TYPE_DETAIL_LOOKUP = {}
# standard departments to diseases mapping
STANDARD_DEPARTMENT_DISEASES = {}
# 地区维度来源开放规则
AREA_OPEN_RULE = {}
# 医院维度来源开放规则
HOSPITAL_OPEN_RULE = {}
if sys.version > '3':
    basestring = str
else:
    basestring = (str, unicode)


def load_data(db, sql_config=None, section=None, option=None, inc=None,
              **kwargs):
    """
    加载数据的通用方法.
    参数:
    db->数据库连接实例.
    section->sql_config的第一级分类.
    option->sql_config的第二级分类.
    inc->增量更新结构:(ids(增量ID), field(ID字段))
    sql->sql查询,可选,与sql_config,section,option必有一个,优先级高于sql_config
    operator->增量sql生成操作,默认为AND.
    wrap->增量ID字段包裹,默认字符串,单引号.
    data_builder->数据构建器.
    builder_argu->数据构建器参数.
    返回值->查询结果.
    """
    sql = ''
    if sql_config and section and option:
        sql = sql_config[section][option]
    if kwargs.get('sql'):
        sql = kwargs['sql']
    sql_inc = ''
    if inc:
        ids, field = inc
        sql_inc = helper.create_id_where_clause(ids, field, **kwargs)
    sql = sql % sql_inc
    rows = db.get_rows(sql)
    if not kwargs.get('data_builder'):
        return rows
    if kwargs.get('builder_argu'):
        return kwargs['data_builder'](rows, **kwargs['builder_argu'])
    else:
        return kwargs['data_builder'](rows)


def dict_data_builder(rows, key='id', **kwargs):
    """
    字典数据构建器.
    rows->数据集合(支持set,list,tuple).
    key->字典主键字段名,默认为:id.
    result->结果集,默认为新建.
    del_field->value需要删除的字段,默认为:key.
    multi_field->需要切分的多值字段.
    """
    result = kwargs.pop('result', {})
    if not rows:
        return {}
    del_field = kwargs.pop('del_field', [key])
    if isinstance(del_field, basestring):
        del_field = [del_field]
    multi_field = kwargs.pop('multi_field', [])
    if isinstance(multi_field, basestring):
        multi_field = [multi_field]
    for row in rows:
        key_value = row.get(key)
        if not row.get(key):
            continue
        for field in del_field:
            row.pop(field, None)
        if multi_field:
            for field in multi_field:
                if row[field]:
                    row[field] = row[field].split(',')
        result[key_value] = row
    return result


def load_hospital_type(db, hospital_id=None):
    """
    加载医院类型信息(标签,比如:男科等).
    db->数据库连接实例.
    hospital_id->增量更新时的医院ID.
    数据使用->见get_hospital_type和get_hospital_type_info方法.
    """
    global HOSPITAL_TYPE_LOOKUP
    global HOSPITAL_TYPE_DETAIL_LOOKUP
    sql = """
        SELECT
            ht.hospital_id AS hospital_uuid, ht.tag_id,
            t.tag_name AS tag_desc,
            CONCAT(ht.tag_id,'|',t.tag_name) tag_detail
        FROM
            hrs_std.hospital_tag ht
        LEFT JOIN
            hrs_std.tags t ON ht.tag_id = t.id
        %s
    """
    sql = sql % helper.create_id_where_clause(
        hospital_id, 'ht.hospital_id', operator='WHERE')
    rows = db.get_rows(sql)

    for row in rows:
        hospital_uuid = row['hospital_uuid']
        if hospital_uuid not in HOSPITAL_TYPE_LOOKUP:
            HOSPITAL_TYPE_LOOKUP[hospital_uuid] = []
        HOSPITAL_TYPE_LOOKUP[hospital_uuid].append(row['tag_id'])
        if hospital_uuid not in HOSPITAL_TYPE_DETAIL_LOOKUP:
            HOSPITAL_TYPE_DETAIL_LOOKUP[hospital_uuid] = {}

        detail_dict = {'hospital_type': 'tag_id',
                       'hospital_type_desc': 'tag_desc',
                       'hospital_type_detail': 'tag_detail'
                       }
        for key, value in detail_dict.items():
            if key not in HOSPITAL_TYPE_DETAIL_LOOKUP[hospital_uuid]:
                HOSPITAL_TYPE_DETAIL_LOOKUP[hospital_uuid][key] = set()
            if row[value]:
                HOSPITAL_TYPE_DETAIL_LOOKUP[hospital_uuid][key].add(row[value])


def get_hospital_type(hospital_uuid):
    """
    获取医院的类型(标签,比如:男科等).
    hospital_uuid->医院ID.
    返回值->医院的类型列表.
    """
    if hospital_uuid in HOSPITAL_TYPE_LOOKUP:
        return HOSPITAL_TYPE_LOOKUP[hospital_uuid]
    else:
        return []


def get_hospital_type_info(hospital_uuid):
    """
    获取医院的类型详情(标签,比如:男科等).
    hospital_uuid->医院ID
    返回值->医院详细列表,结构:
    """
    return HOSPITAL_TYPE_DETAIL_LOOKUP.get(hospital_uuid, {})


def load_area(db):
    global AREA_LOOKUP
    sql = """
        SELECT
            id          AS area_id,
            name        AS area_name,
            parent_id,
            type        AS area_type,
            national_code
        FROM
            hrsc_data.area
        WHERE is_delete = 0;
    """
    rows = db.get_rows(sql)
    for row in rows:
        row['area_name'] = helper.utf8_decode(row['area_name'])
        AREA_LOOKUP[row['area_id']] = row


def get_area_name(area_id):
    area = AREA_LOOKUP.get(area_id)
    if area:
        return area.get('area_name')
    return ''


def load_hospital_level_dict(db, is_reverse=False):
    """
    加载医院等级信息.
    参数:
    db->数据库连接实例.
    is_reverse->是否构建反向字典,默认为正向:key-字典值,value->字典值名称.
    """
    sql = """
    SELECT
        di.`VALUE` value,
        di.name
    FROM hrsc_data.dict_item di
    WHERE di.code='d_hosp_level'
    """
    rows = db.get_rows(sql)
    level_dict = {}
    for row in rows:
        if not row['value'] or not row['name']:
            continue
        if is_reverse:
            level_dict[row['name']] = row['value']
        else:
            level_dict[str(row['value'])] = row['name']
    return level_dict


def load_standard_department_diseases(db, is_common=False):
    global STANDARD_DEPARTMENT_DISEASES
    sql = """
        SELECT
            d.name as diseasename,
            sddr.std_dept_id departmentuuid
        FROM
            hrs_std.std_depart_disease_relation sddr,
            medical_knowledge.disease d
        WHERE
            sddr.disease_id = d.id
            AND sddr.sort_code = 1 AND d.state=1 AND d.sort_code=0
    """
    sql_common = """
        SELECT
            IFNULL(d.name_common, d.name) diseasename,
            sddr.std_dept_id departmentuuid
        FROM
            hrs_std.std_depart_disease_relation sddr
            INNER JOIN medical_knowledge.disease d ON d.id = sddr.disease_id
            AND d.state=1 AND d.sort_code=0
    """
    if is_common:
        sql = sql_common
    rows = db.get_rows(sql)
    for row in rows:
        department_uuid = row['departmentuuid']
        disease_name = row['diseasename']
        if not STANDARD_DEPARTMENT_DISEASES.get(department_uuid):
            STANDARD_DEPARTMENT_DISEASES[department_uuid] = []
        STANDARD_DEPARTMENT_DISEASES[department_uuid].append(disease_name)


def get_standard_department_diseases(standard_departments):
    global STANDARD_DEPARTMENT_DISEASES
    standard_department_diseases = []
    for department in standard_departments:
        if STANDARD_DEPARTMENT_DISEASES.get(department):
            standard_department_diseases.extend(
                STANDARD_DEPARTMENT_DISEASES[department])
    return standard_department_diseases


def load_hospital_source(db, hospital_id=None, expert_id=None):
    """
    加载医院维度的source开放规则.
    参数:
    db->数据库连接实例.
    hospital_id->用于增量更新的医院ID,默认None全量加载.
    expert_id->用于增量更新的医生ID,默认None全量加载.
    """
    # 医院维度来源开放规则:{hospital_id:{include:set,exclude:set}}
    hospital_source_rule = {}
    sql_base = """
    SELECT
        hpr.hosp_id hospital_id,
        hpr.channel_id source_id,
        hpr.include_or_exclude type
    FROM hrs_std.hosp_permission_rule hpr
    %s
    """
    expert_filter = """
    INNER JOIN hrs_std.hosp_dept_expert_relation hder
        ON hder.hospital_id=hpr.hosp_id AND hder.state=0
    %s
    """
    inc_sql = ''
    if hospital_id:
        inc_sql = helper.create_id_where_clause(
            hospital_id, 'hpr.hosp_id', operator='WHERE')
    if expert_id:
        inc_sql = expert_filter % helper.create_id_where_clause(
            expert_id, 'hder.expert_id', operator='WHERE')
    sql = sql_base % inc_sql
    rows = db.get_rows(sql)
    if not rows:
        return hospital_source_rule
    type_set = {'include', 'exclude'}
    for row in rows:
        hospital_id = row.pop('hospital_id')
        if not hospital_id:
            continue
        hospital_rule = hospital_source_rule.setdefault(hospital_id, {})
        if row['type'] in type_set and row['source_id']:
            hospital_rule.setdefault(row['type'], set()).add(row['source_id'])
    return hospital_source_rule


def get_hospital_source(hospital_source_rule, hospital_ids):
    """
    获取医院合并后的source开放规则.
    参数:
    hospital_ids->需要合并的医院ID.
    """
    include_source = set()
    exclude_source = set()
    if not hospital_ids:
        include_source.add('0')
        return include_source, exclude_source
    first_hospital = True
    open_all = False
    for hospital_id in hospital_ids:
        hospital_rule = hospital_source_rule.get(hospital_id, {})
        # 只要一个医院全部开放就全部开放
        if not hospital_rule.get('include'):
            include_source = set(['0'])
            open_all = True
        if not open_all:
            include_source.update(hospital_rule.get('include'))
        if first_hospital:
            exclude_source = hospital_rule.get('exclude', set())
            first_hospital = False
        # 所有医院都屏蔽才屏蔽
        exclude_source = exclude_source & hospital_rule.get('exclude', set())
    # 反向优先级高于正向
    include_source = include_source - exclude_source
    return include_source, exclude_source


def load_source_rule(db):
    global AREA_OPEN_RULE
    global HOSPITAL_OPEN_RULE
    sql = """
    SELECT
        ror.channel_id source_id,
        ror.area_id,
        ror.hosp_id hospital_id,
        ror.`SCOPE` `scope`,
        ror.include_or_exclude type
    FROM hrs_std.resource_open_rule ror
    """
    rows = db.get_rows(sql)
    rule = {}
    for row in rows:
        if row['scope'] == 1:
            rule = AREA_OPEN_RULE.setdefault(row['area_id'], {})
        elif row['scope'] == 2:
            rule = HOSPITAL_OPEN_RULE.setdefault(row['hospital_id'], {})
        rule.setdefault(row['type'], set()).add(row['source_id'])


def get_hospital_source_rule(hospital, area_path):
    """
    获取医院维度的source规则.
    hospital->医院ID.
    area_path->地区路径,数组结构,医院所在地区从最低到根节点.
    """
    rule = HOSPITAL_OPEN_RULE.get(hospital, {})
    exclude_source = rule.get('exclude', set())
    # 反向优先级高于正向
    include_source = rule.get('include', set()) - exclude_source
    if not area_path:
        if not include_source:
            include_source.add('0')
        return include_source, exclude_source
    area_exclude_source = set()
    area_include_source = set()
    for area in area_path:
        area_rule = AREA_OPEN_RULE.get(area)
        if not area_rule:
            continue
        t_exclude_source = area_rule.get('exclude')
        t_include_source = area_rule.get('include')
        if t_exclude_source:
            area_exclude_source.update(t_exclude_source)
        if t_include_source:
            area_include_source.update(t_include_source)
    # 反向优先级高于正向
    area_include_source = area_include_source - area_exclude_source
    # 医院维度的优先级高于地区维度
    area_include_source = area_include_source - exclude_source
    area_exclude_source = area_exclude_source - include_source
    exclude_source.update(area_exclude_source)
    include_source.update(area_include_source)
    if not include_source:
        include_source.add('0')
    return include_source, exclude_source


def get_standard_department_disease(std_dept_id):
    return STANDARD_DEPARTMENT_DISEASES.get(std_dept_id)


def load_doctor_technical_title(db):
    """
    加载医生的职称
    """
    DOCTOR_TECHNICAL_TITLE_ID_MAPPING = {}
    sql = """
    SELECT
        di.`VALUE` id,
        di.name
    FROM
        hrsc_data.dict_item di
    WHERE
        di.code = "d_expert_title"
    """
    rows = db.get_rows(sql)
    for row in rows:
        DOCTOR_TECHNICAL_TITLE_ID_MAPPING[int(row['id'])] = row['name']
    return DOCTOR_TECHNICAL_TITLE_ID_MAPPING
