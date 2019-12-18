#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
kg_dao.py -- the dao of kg

Author: maogy <maogy@guahao.com>
Create on 2017-09-08 Friday.
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

def transform_text(content):
    return str(content, encoding='utf8').replace('\t', '') if isinstance(
        content, bytes) else content

class KGDBDao(BaseNLP):
    """
    The dao of knowledge graph for db.
    """

    def __init__(self, **kwargs):
        """
        初始化函数,遵循BaseNLP
        """
        super(KGDBDao, self).__init__(**kwargs)
        self.db = DBWrapper(self.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')

    def load_entity_info(self, ids):
        """
        加载实体信息.
        """
        sql = """
        SELECT
            e.entity_uuid id,
            e.entity_name name,
            e.entity_type type,
            e.audit_status,
            e.is_standard,
            e.is_delete,
            s.audit_status standard_audit_status,
            s.entity_name standard_name
        FROM ai_union.entity e LEFT JOIN ai_union.standard_entity s
            ON e.standard_uuid=s.entity_uuid
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        return list(rows)

    def load_entity_id(self, sec):
        """
        加载实体信息.
        """
        sql = """
        SELECT
            e.entity_uuid id
        FROM ai_union.entity e
        WHERE e.gmt_modified >= '%s'
        UNION
        SELECT e.entity_uuid id
        FROM ai_union.entity e INNER JOIN ai_union.entity t
            ON e.standard_uuid=t.standard_uuid
        WHERE t.gmt_modified >= '%s'
        """
        modify_time = utils.pasttime_by_seconds(sec)
        rows = self.db.get_rows(sql % (modify_time, modify_time))
        return [row['id'] for row in rows if row['id']]

    def load_entity_attribute(self, ids):
        """
        加载实体的属性信息
        """
        sql = """
        SELECT
            e.entity_uuid entity_id,
            e.entity_name,
            e.entity_type,
            sat.attribute_type,
            sat.is_open,
            CASE
                WHEN sa.attribute_value_type=1 THEN
                        sa.attribute_value
                WHEN sa.attribute_value_type=2 THEN
                        asi.attribute_value
                ELSE
                        st.context
            END attribute_value,
            sat.value_type
        FROM ai_union.entity e INNER JOIN ai_union.standard_attribute sa
            ON e.standard_uuid=sa.standard_uuid AND sa.is_delete=0
        INNER JOIN ai_union.entity_type et ON e.entity_type=et.type_uuid
            AND et.is_deleted=0
        INNER JOIN ai_union.standard_attribute_type sat
            ON sa.attribute_type=sat.attribute_type AND sat.is_deleted=0
            AND sat.value_type <> 4
        LEFT JOIN ai_union.standard_text st ON sa.attribute_value=st.id
            AND st.is_delete=0
        LEFT JOIN ai_union.attribute_select_item asi ON sa.attribute_value=asi.id
            AND asi.is_delete=0
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        entity_dict = {}
        for row in rows:
            entity_id = row['entity_id']
            if not entity_id:
                continue
            attribute = entity_dict.setdefault(entity_id, [])
            attribute.append(row)
        return entity_dict

    def load_entity_label(self, ids):
        """
        加载实体业务标签信息.
        """
        sql = """
        SELECT
            e.entity_uuid entity_id,
            elt.open_code,
            elt.is_open,
            el.label_type,
            el.label_value
        FROM ai_union.entity e
        INNER JOIN ai_union.entity_label el
            ON el.entity_uuid=e.entity_uuid AND el.audit_status <> 99 AND el.is_deleted=0
        INNER JOIN ai_union.entity_label_type elt ON el.label_type=elt.type_uuid AND elt.is_deleted=0
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        label_dict = {}
        for row in rows:
            entity_id = row['entity_id']
            if not entity_id:
                continue
            label = label_dict.setdefault(entity_id, [])
            label.append(row)
        return label_dict

    def load_entity_relation(self, ids):
        """
        加载实体别名信息.
        :param ids 集合或列表类型,包含需要加载别名信息的实体ID
        :return relation_dict 字典类型,value部分为不重复的别名集合{实体ID: {实体别名, 实体别名..}, ...}
        """
        sql = """
                SELECT
                    e1.entity_uuid id,
                    e2.entity_uuid alias_id,
                    e2.entity_name name
                FROM ai_union.entity e1
                INNER JOIN ai_union.entity e2 ON e1.standard_uuid = e2.standard_uuid
                        AND e1.entity_uuid != e2.entity_uuid AND e1.audit_status <> 99
                        AND e2.audit_status <> 99
                        AND e1.is_delete=0 AND e2.is_delete=0
                %s
                """
        inc_sql = ''
        relation_dict = {'entity_name': {}, 'entity_id': {}}
        if ids:
            inc_sql = "WHERE e1.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        for row in rows:
            entity_id = row['id']
            if not entity_id:
                continue
            relation_name = relation_dict['entity_name'].setdefault(entity_id, set())
            relation_name.add(row['name'])
            relation_id = relation_dict['entity_id'].setdefault(entity_id, set())
            relation_id.add(row['alias_id'])
        return relation_dict

    def load_standard_relation(self, ids):
        """
        加载实体对应本体关系信息.
        :param ids 集合或列表类型,包含需要加载本体关系信息的实体ID
        :return relation_dict 字典类型,value部分为不重复的别名集合{'from':{实体ID: {id, type, name}},'to':{...}}
        """
        sql = """
        SELECT
            e.entity_uuid from_id,
            e.entity_name from_name,
            e.is_standard from_is_standard,
            e.entity_type from_type,
            sr.id r_id,
            sr.relation_type_uuid relation_id,
            sr.relation_desc,
            CONVERT(sr.relation_score, char) relation_score,
            e_to.entity_uuid to_id,
            e_to.entity_name to_name,
            e_to.is_standard to_is_standard,
            e_to.entity_type to_type
        FROM ai_union.entity e
        INNER JOIN ai_union.standard_relation sr ON e.standard_uuid = sr.standard_from_uuid
                AND sr.stat <> 99 AND sr.is_deleted=0 AND e.is_delete=0
        INNER JOIN ai_union.entity e_to ON sr.standard_to_uuid = e_to.standard_uuid
                AND e_to.is_delete=0
        %s
        """
        inc_sql = ''
        relation_dict = {'from': dict(), 'to': dict()}
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s') OR e_to.entity_uuid in ('%s')" % ("','".join(ids), "','".join(ids))
        rows = self.db.get_rows(sql % inc_sql)
        for row in rows:
            from_id = row['from_id']
            if not from_id:
                continue
            relation_from = relation_dict['from'].setdefault(from_id, list())
            relation_from.append(row)
            to_id = row['to_id']
            if not to_id:
                continue
            relation_to = relation_dict['to'].setdefault(to_id, list())
            relation_to.append(row)
        return relation_dict

    def load_standard_type_dict(self):
        """
        加载本体的属性和本体关系属性的type:name映射关系
        :return: type_dict
        """
        sql = """
        select
            'relation_type'  tag,
            srt.relation_type_uuid type,
            srt.relation_desc name
        FROM ai_union.standard_relation_type srt
        UNION
        SELECT
            'attribute_type'  tag,
            sat.attribute_type type,
            sat.attribute_name name
        FROM ai_union.standard_attribute_type sat
        UNION
        SELECT
            'entity_type'  tag,
            et.type_uuid type,
            et.type_name name
        FROM ai_union.entity_type et
        """
        rows = self.db.get_rows(sql)
        type_dict = {}
        for row in rows:
            tag_dict = type_dict.setdefault(row['tag'], dict())
            tag_dict[row['type']] = row['name']
        return type_dict

    def load_relation_attribute(self, ids):
        """
        记载本体关系属性
        :return: 本体关系属性数据字典
        """
        sql = """
        SELECT
            ra.relation_id,
            sa.attribute_type,
            sat.attribute_name,
            sa.attribute_value
        FROM ai_union.relation_attribute ra
        INNER JOIN ai_union.standard_attribute sa ON ra.attribute_id=sa.id
        INNER JOIN ai_union.standard_attribute_type sat ON sa.attribute_type=sat.attribute_type
        %s
        """
        inc_sql = ''
        if ids:
            condition_sql = """
            SELECT
                sr.id
            FROM ai_union.entity e
            INNER JOIN ai_union.standard_relation sr ON e.standard_uuid=sr.standard_from_uuid
                AND sr.stat <> 99 AND sr.is_deleted=0 AND e.is_delete=0
            %s
            """
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
            condition_sql = condition_sql % inc_sql
            condition_row = self.db.get_rows(condition_sql)
            if condition_row:
                inc_sql = "WHERE ra.relation_id in ('%s')" % "','".join([str(row['id']) for row in condition_row])
            else:
                inc_sql = ''
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        attribute_dict = {}
        for row in rows:
            relation_id = row['relation_id']
            if not relation_id:
                continue
            attribute = attribute_dict.setdefault(relation_id, [])
            attribute.append(row)
        return attribute_dict

    def load_medical_knowledge_disease_info(self, ids):
        """
        根据原基础库疾病标签值连接medical_knowledge库的disease表，加载原业务库的疾病信息
        """
        sql = """
                SELECT
                    el.entity_uuid entity_id,
                    d.id disease_id,
                    d.disease_type
                FROM ai_union.entity_label el INNER JOIN medical_knowledge.disease d
                    ON el.label_value = d.id AND el.label_type='pkCizO3q' AND el.is_deleted=0
                    AND d.sort_code=0 AND d.state=1 AND el.audit_status <> 99
                %s
                """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE el.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        entity_dict = {}
        for row in rows:
            entity_id = row['entity_id']
            if not entity_id:
                continue
            entity_dict[entity_id] = row
        return entity_dict

    def load_medicine_enterprise_info(self, ids):
        """
        根据药品SKU标签中的药品ID加载药品库中medicine.medicine_enterprise_relation表中对应药品的药店列表信息
        """
        sql = """
        SELECT
            el.entity_uuid entity_id,
            GROUP_CONCAT(DISTINCT mer.enterprise_id SEPARATOR ',') as enterprise_ids
        FROM ai_union.entity_label el INNER JOIN medicine.medicine_enterprise_relation mer
            ON el.label_value = mer.medicine_id AND el.is_deleted=0
            AND mer.is_show=1 AND mer.is_delete=0 AND el.audit_status <> 99
        %s
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE el.entity_uuid in ('%s')" % "','".join(ids)

        sql = sql % (inc_sql, 'GROUP BY el.entity_uuid')
        rows = self.db.get_rows(sql)
        entity_dict = {}
        for row in rows:
            entity_id = row['entity_id']
            if not entity_id and not row['enterprise_ids']:
                continue
            enterprise_ids = row.get('enterprise_ids', '').split(',')
            entity_dict[entity_id] = enterprise_ids
        return entity_dict

    def load_entity_text_attributes(self, ids):
        """
        加载数据的长文本属性和富文本属性
        """
        sql = """
        SELECT
            e.entity_uuid id,
            e.entity_name name,
            e.audit_status,
            et.open_code entity_type,
            sat.open_code attribute_code,
            st.context attribute_value,
            e.is_delete
        FROM ai_union.entity e INNER JOIN ai_union.standard_attribute sa
            ON e.standard_uuid=sa.standard_uuid AND sa.is_delete=0
        INNER JOIN ai_union.entity_type et ON e.entity_type=et.type_uuid
            AND et.is_deleted=0 AND et.is_open=1
        INNER JOIN ai_union.standard_attribute_type sat
            ON sa.attribute_type=sat.attribute_type AND sat.is_deleted=0
            AND sat.is_open=1 AND sat.value_type in (3,4)
        INNER JOIN ai_union.standard_text st ON st.is_delete=0
            AND st.id=sa.attribute_value
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        entity_dict = {}
        for row in rows:
            entity_id = row['id']
            if not entity_id:
                continue
            attribute = entity_dict.setdefault(entity_id, {})
            attribute['id'] = row.get('id')
            attribute[row['attribute_code']+'_t'] = row.get('attribute_value')
        return entity_dict


class KGGraphqlDao(KGDBDao):
    """
    The dao of graphql for db.
    """

    def load_standard_relation(self, ids):
        """
        加载实体对应本体关系信息.
        :param ids 集合或列表类型,包含需要加载本体关系信息的实体ID
        :return relation_dict 字典类型,value部分为不重复的别名集合{'from':{实体ID: {id, type, name}},'to':{...}}
        """
        sql = """
        SELECT
            e.entity_uuid from_id,
            e.entity_name from_name,
            e.entity_type from_type,
            e.is_standard from_is_standard,
            sr.id,
            sr.is_deleted is_delete,
            sr.relation_type_uuid,
            sr.stat relation_status,
            sr.relation_desc,
            CONVERT(sr.relation_score, char) relation_score,
            e_to.entity_uuid to_id,
            e_to.entity_name to_name,
            e_to.entity_type to_type,
            e_to.is_standard to_is_standard
        FROM ai_union.entity e
        INNER JOIN ai_union.standard_relation sr ON e.standard_uuid = sr.standard_from_uuid
                AND sr.stat <> 99 AND sr.is_deleted=0 AND e.is_delete=0
        INNER JOIN ai_union.entity e_to ON sr.standard_to_uuid = e_to.standard_uuid
                AND e_to.is_delete=0
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s') OR e_to.entity_uuid in ('%s')" % ("','".join(ids), "','".join(ids))
        rows = self.db.get_rows(sql % inc_sql)
        relation_dict = {'from':{},'to':{}}
        for row in rows:
            from_id = row['from_id']
            if not from_id:
                continue
            relation_from = relation_dict['from'].setdefault(from_id, list())
            relation_from.append(row)
            to_id = row['to_id']
            if not to_id:
                continue
            relation_to = relation_dict['to'].setdefault(to_id, list())
            relation_to.append(row)
        return relation_dict, rows

    def load_relation_attribute(self, ids):
        """
        记载本体关系属性
        :return: 本体关系属性数据字典
        """
        sql = """
        select
                sr.id relation_id,
                srta.relation_type_attribute_uuid,
                srta.name relation_attribute_name,
                CASE
                        WHEN srtav.type=1 THEN
                                srtav.value
                        WHEN srtav.type=2 THEN
                                asi.attribute_value
                        ELSE
                                st.context
                END relation_arrribute_value,
                srta.value_type
        FROM ai_union.standard_relation sr
        INNER JOIN ai_union.relation_attribute ra ON
            sr.id=ra.relation_id AND sr.is_deleted=0
        INNER JOIN ai_union.standard_relation_type_attribute_value srtav ON
            ra.attribute_id=srtav.id AND srtav.is_deleted=0
        INNER JOIN ai_union.standard_relation_type_attribute srta ON
            srta.relation_type_attribute_uuid=srtav.relation_type_attribute_uuid
            AND srta.is_open=1 AND srta.open_code IS NOT NULL
        LEFT JOIN ai_union.standard_text st ON srtav.value=st.id
                AND st.is_delete=0
        LEFT JOIN ai_union.attribute_select_item asi on srtav.value=asi.id
                AND asi.is_delete=0
        %s
        """
        inc_sql = ''
        if ids:
            condition_sql = """
            SELECT
                sr.id
            FROM ai_union.entity e
            INNER JOIN ai_union.standard_relation sr ON e.standard_uuid=sr.standard_from_uuid
                AND sr.stat <> 99 AND sr.is_deleted=0 AND e.is_delete=0
            %s
            """
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
            condition_sql = condition_sql % inc_sql
            condition_row = self.db.get_rows(condition_sql)
            if condition_row:
                inc_sql = "WHERE sr.id in ('%s')" % "','".join([str(row['id']) for row in condition_row])
            else:
                inc_sql = ''
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        attribute_dict = {}
        for row in rows:
            relation_id = row['relation_id']
            if not relation_id:
                continue
            attribute = attribute_dict.setdefault(relation_id, [])
            attribute.append(row)
        return attribute_dict

    def load_standard_type_dict(self):
        """
        加载本体的属性和本体关系属性的type:name映射关系
        :return: type_dict
        """
        sql = """
        select
                'relation_type'  tag,
                srt.relation_type_uuid type,
                srt.relation_desc name,
                srt.open_code code,
                NULL value_type
        FROM ai_union.standard_relation_type srt
        WHERE srt.is_deleted=0 AND srt.is_open=1 AND srt.open_code IS NOT NULL
        UNION
        SELECT
                'attribute_type'  tag,
                sat.attribute_type type,
                sat.attribute_name name,
                sat.open_code code,
                sat.value_type value_type
        FROM ai_union.standard_attribute_type sat
        WHERE sat.is_deleted=0 AND sat.is_open=1 AND sat.open_code IS NOT NULL
        UNION
        SELECT
                'entity_type'  tag,
                et.type_uuid type,
                et.type_name name,
                et.open_code code,
                NULL value_type
        FROM ai_union.entity_type et
        WHERE et.is_deleted=0 AND et.is_open=1 AND et.open_code IS NOT NULL
        UNION
        SELECT
                'label_type'  tag,
                elt.type_uuid type,
                elt.type_name name,
                elt.open_code code,
                NULL value_type
        FROM ai_union.entity_label_type elt
        WHERE elt.is_deleted=0 AND elt.is_open=1 AND elt.open_code IS NOT NULL
        UNION
        select
                'relation_attribute_type' tag,
                srta.relation_type_attribute_uuid type,
                srta.name name,
                srta.open_code code,
                srta.value_type value_type
        FROM ai_union.standard_relation_type_attribute srta INNER JOIN ai_union.standard_relation_type srt
            ON srta.standard_relation_type_id=srt.id
        WHERE srta.is_deleted=0 AND srta.is_open=1 AND srta.open_code IS NOT NULL
        """
        rows = self.db.get_rows(sql)
        type_dict = {}
        for row in rows:
            tag_dict = type_dict.setdefault(row['tag'], dict())
            tag_dict[row['type']] = row
        return type_dict

    def load_entity_attribute(self, ids):
        """
        加载实体的属性信息
        """
        sql = """
        SELECT
            e.entity_uuid,
            sat.attribute_type,
            CASE
                WHEN sa.attribute_value_type=1 THEN
                        sa.attribute_value
                WHEN sa.attribute_value_type=2 THEN
                        asi.attribute_value
                ELSE
                        st.context
            END attribute_value,
            sat.value_type
        FROM ai_union.entity e INNER JOIN ai_union.standard_attribute sa
            ON e.standard_uuid=sa.standard_uuid AND sa.is_delete=0
        INNER JOIN ai_union.entity_type et ON e.entity_type=et.type_uuid
            AND et.is_deleted=0 AND et.is_open=1
        INNER JOIN ai_union.standard_attribute_type sat
            ON sa.attribute_type=sat.attribute_type AND sat.is_deleted=0
            AND sat.is_open=1
        LEFT JOIN ai_union.standard_text st ON sa.attribute_value=st.id
            AND st.is_delete=0
        LEFT JOIN ai_union.attribute_select_item asi ON sa.attribute_value=asi.id
            AND asi.is_delete=0
        %s
        """
        inc_sql = ''
        if ids:
            inc_sql = "WHERE e.entity_uuid in ('%s')" % "','".join(ids)
        sql = sql % inc_sql
        rows = self.db.get_rows(sql)
        entity_dict = {}
        for row in rows:
            entity_id = row['entity_uuid']
            if not entity_id:
                continue
            attribute = entity_dict.setdefault(entity_id, [])
            attribute.append(row)
        return entity_dict


class KGDao(object):
    """
    the dao of KG.
    """

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.log_level = 'info'
        if self.debug:
            self.log_level = 'debug'
        self.logger = GLLog('kg_dao', log_dir=global_conf.log_dir,
                            level=self.log_level).getLogger()
        self.logger.debug('kg dao debug mode:%s' % self.debug)
        self.solr = Solr(global_conf.cfg_path)
        self.ai_service_client = AIServiceClient(
            cfg_path=global_conf.cfg_path, service='AIService')
        self.disease_id_name_dict = get_disease_name()

    def set_level(self, debug):
        self.debug = debug

    def find_symptom_with_disease_detail(self, symptoms):
        """
        查询症状,获取相关的疾病.
        参数:
        symptoms->症状列表.
        返回值->症状文档列表.
        """
        if not symptoms:
            return []
        params = {'q': '*:*', 'rows': len(symptoms) * 2,
                  'fl': 'entity_id,entity_name,disease_detail'}
        # print total_names
        fq_dict = {'entity_id': '(' + ' OR '.join(symptoms) + ')',
                   'type': '2', 'disease_detail': '*'}
        # self.solr.set_debug(self.debug)
        response = self.solr.solr_search(
            params, 'medical_entity', fq_dict, method='post')
        self.solr.clear_url()
        # print response['response']['docs']
        return response['response']['docs']

    def find_disease_with_symptom(self, symptoms, diseases=None):
        """
        查询症状,获取相关的疾病.
        参数:
        symptoms->症状列表.
        返回值->症状文档列表.
        """
        params = {'q': '*:*', 'rows': 30000,
                  'fl': 'entity_id,entity_name,sex_weight,'
                        'age_weight,acute,chronic,rate'}
        fq_dict = {'type': '1', 'common_level': 1}
        disease_symptom_id = []
        if symptoms:
            disease_symptom_id.extend(symptoms)
        if diseases:
            disease_symptom_id.extend(diseases)
        if disease_symptom_id:
            fq_dict['disease_symptom_id'] = '(' + ' OR '.join(
                disease_symptom_id) + ')'
        response = self.solr.solr_search(
            params, 'medical_entity', fq_dict, method='post')
        self.solr.clear_url()
        # print response['response']['docs']
        return response['response']['docs']

    def filter_disease_by_age_sex(self, diseases, sex='-1', age='-1'):
        if not diseases:
            return set()
        fq_dict = {'entity_id': '(' + ' OR '.join(diseases) + ')',
                   'type': '1', 'common_level': 1}
        self.logger.debug('filter sex:%s, age:%s' % (sex, age))
        if sex and '-1' != sex:
            fq_dict['sex'] = sex
        if age and '-1' != age:
            fq_dict['age_min'] = '[* TO %s]' % age
            fq_dict['age_max'] = '[%s TO *]' % age
        params = {'start': 0, 'rows': len(diseases),
                  'fl': 'entity_id', 'q': '*:*'}
        self.logger.debug('filter age sex:%s, %s' % (str(params), str(fq_dict)))
        response = self.solr.solr_search(params, 'medical_entity', fq_dict)
        docs = response['response']['docs']
        if not docs:
            return set()
        suitable_disease = set()
        for doc in docs:
            if not doc:
                continue
            disease = doc.get('entity_id')
            if disease:
                suitable_disease.add(str(disease))
        self.logger.debug('after filter by age and sex:%s'
                          % str(suitable_disease))
        return suitable_disease

    def search(self, query, params, fq_dict):
        params['q'] = query
        response = self.solr.solr_search(params, 'medical_entity', fq_dict)
        return response

    def find_disease_symptom_etc(self, disease_ids):
        """获取知识图谱中疾病相关症状、体征

        :diseases: 疾病id列表
        :returns: 疾病信息

        """
        # 疾病id转名字
        diseases = {}
        for key, val in disease_ids.items():
            if not val:
                name = self.disease_id_name_dict.get(key)
                if name:
                    diseases[key] = name
            else:
                diseases[key] = val

        # 获取疾病相关的症状、体征id
        disease_symptom_etc = {}
        symptom_etc_ids = set()
        para = {'name': list(diseases.values()), 'type': ['disease'], 'rows': len(diseases),
                'ef': ['id', 'name', 'disease_symptom_clinical_relation', 'disease_physical_examination_clinical_relation']}
        response = self.ai_service_client.query(json.dumps(para, ensure_ascii=False), 'entity_service')
        if response.get('code') == 0:
            entities = response.get('data', {}).get('entity', [])
            for entity in entities:
                disease_symptom_etc[entity['name']] = {'entity_id': entity.get('id'),
                                                       'entity_name': entity.get('name'),
                                                       'symptom_detail': entity.get('disease_symptom_clinical_relation', []),
                                                       'physical_examination_detail': entity.get('disease_physical_examination_clinical_relation', []),
                                                       'inspection_json': []}
                symptom_etc_ids = symptom_etc_ids.union(entity.get('disease_symptom_clinical_relation', []))
                symptom_etc_ids = symptom_etc_ids.union(entity.get('disease_physical_examination_clinical_relation', []))
        # 根据id查找症状、体征
        symptom_dict = {}
        physical_e_dict = {}
        para = {'id': list(symptom_etc_ids), 'ef': ['name', 'type', 'id'], 'rows': len(symptom_etc_ids)}
        response = self.ai_service_client.query(json.dumps(para, ensure_ascii=False), 'entity_service')
        if response.get('code') == 0:
            entities = response.get('data', {}).get('entity', [])
            for entity in entities:
                if entity.get('type') == 'symptom':
                    symptom_dict[entity.get('id')] = entity.get('name')
                if entity.get('type') == 'physical_examination':
                    physical_e_dict[entity.get('id')] = entity.get('name')

        # 组合疾病、症状
        res = {}
        for _id, name in diseases.items():
            info = disease_symptom_etc.get(name)
            if not info:
                continue
            symptom_detail = []
            for sy in info['symptom_detail']:
                name = symptom_dict.get(sy)
                if name:
                    symptom_detail.append('{}|{}'.format(sy, name))
            info['symptom_detail'] = symptom_detail
            physical_examination = []
            for pe in info['physical_examination_detail']:
                name = physical_e_dict.get(pe)
                if name:
                    physical_examination.append('{}|{}'.format(pe, name))
            info['physical_examination_detail'] = physical_examination
            res[_id] = info

        return res

    def find_disease(self, diseases, **kwargs):
        default_disease_id = {'44238': '高血压', '64406562-8643-11e7-b11b-1866da8f1f23': '急性上呼吸道感染',
                              '118786A18629FC4AE0500A0AC86471F9': '急性胃肠炎',
                              '6af282f3-31e1-11e6-804e-848f69fd6b70': '胃十二指肠溃疡[消化性溃疡]',
                              '1bab728c-31e0-11e6-804e-848f69fd6b70': '糖尿病 NOS'}
        if diseases:
            symptom_etcs = self.find_disease_symptom_etc(diseases)
            diseases = list(diseases.keys())
        else:
            symptom_etcs = self.find_disease_symptom_etc(default_disease_id)
            default_disease_id = list(default_disease_id.keys())

        fl = kwargs.get('fl', 'entity_id,entity_name')
        params = {'fl': fl, 'q': '*:*', 'sort': 'rate desc'}
        fq_dict = {'type': '1'}
        if not diseases:
            params['start'] = kwargs.get('start', 0)
            params['rows'] = kwargs.get('rows', 10)
            fq_dict['entity_id'] = '(' + ' OR '.join(default_disease_id) + ')'
        else:
            params['start'] = 0
            params['rows'] = len(diseases)
            fq_dict['entity_id'] = '(' + ' OR '.join(diseases) + ')'
        docs = None
        response = None
        try:
            response = self.solr.solr_search(params, 'medical_entity', fq_dict,
                                             method='get', timeout=2)
            docs = response['response']['docs']
        except:
            traceback.print_exc()
        if not diseases:
            sorted_docs = []
            for ddi in default_disease_id:
                for doc in docs:
                    if doc.get('entity_id') == ddi:
                        sorted_docs.append(doc)
                        break
            docs = sorted_docs

        if not docs:
            return {}, [], 0
        doc_dict = {}
        for doc in docs:
            if not doc:
                continue
            disease = doc.get('entity_id')
            se = symptom_etcs.get(disease, {})
            symptom_detail = se.get('symptom_detail')
            if symptom_detail:
                doc['symptom_detail'] = symptom_detail
            physical_examination_detail = se.get('physical_examination_detail')
            if physical_examination_detail:
                doc['physical_examination_detail'] = physical_examination_detail
            doc_dict[disease] = doc
        return doc_dict, docs, response['response']['numFound']

    def find_critical_disease(self, symptom, sex=None, age=None, **kwargs):
        if not symptom:
            return []
        if len(symptom) > 100:
            symptom = list(symptom)[0: 100]
        fl = kwargs.get('fl', 'entity_id,entity_name')
        # print symptom
        fq_dict = {'symptom_id': '(' + ' OR '.join(symptom) + ')',
                   'is_critical_disease': '1'}
        if sex and '-1' != sex:
            fq_dict['sex'] = sex
        if age and '-1' != age:
            fq_dict['age_min'] = '[* TO %s]' % age
            fq_dict['age_max'] = '[%s TO *]' % age
        params = {'start': 0, 'rows': 1000, 'fl': fl, 'q': '*:*',
                  'sort': '$critical_weight desc,entity_id asc'}
        sub_q = ' '.join(symptom)
        match_weight = "query({!dismax qf=symptom_id_text^1 v='%s'}))" % sub_q
        critical_weight = "product(field(critical_rate), %s" % match_weight
        params['critical_weight'] = critical_weight
        docs = []
        try:
            response = self.solr.solr_search(params, 'medical_entity',
                                             fq_dict, timeout=2)
            docs = response['response']['docs']
        except Exception as e:
            traceback.print_exc()
        return docs

    def search_critical_disease(self, symptom_list, fl=None):
        """
        根据症状搜索疾病
        :param symptom_list: 症状列表
        :param fl: 返回的疾病字段
        :return:
        """
        if not fl:
            fl = ['entity_id:disease_id_s', 'entity_name:standard_name_s']
        params = dict()
        fq_dict = dict()
        fq_list = list()
        filter_query = dict()
        filter_query['standard_name_s'] = '(' + ' '.join(symptom_list) + ')'
        filter_query['type_s'] = 'symptom'
        res = None
        try:
            res = self.solr.solr_search({'q': '*:*', 'fl': 'id,standard_name_s'},
                                        'entity', filter_query,
                                        fq_list=None, timeout=100)
        except (BaseException, RuntimeError):
            traceback.print_exc()
        symptoms = [doc.get('id') for doc in res['response']['docs']]
        if not symptoms:
            return res['response']['docs']
        condition = [
            'if(gt(field(%s_relation_score_f),0),sum(field(%s_relation_score_f),0.2),0)'
            % (r_id, r_id) for r_id in symptoms]
        params['bf'] = 'sum(%s)' % ','.join(condition)
        fq_list.append('(' + ' '.join(
            ['%s_relation_score_f:*' % r_id for r_id in symptoms]) + ')')
        fq_dict['type_s'] = 'disease'
        fq_dict['disease_id_s'] = '*'
        params['sort'] = 'score desc'
        params['fl'] = ','.join(fl)
        params['q'] = '*:*'
        response = None
        try:
            response = self.solr.solr_search(params, 'entity', fq_dict,
                                             fq_list=fq_list, timeout=100)
        except (BaseException, RuntimeError):
            traceback.print_exc()
        docs = response['response']['docs']
        return docs

    def find_body_part_symptom_relation(self):
        """获取知识图谱中疾病常见症状和其对应的身体部位
        :returns: 症状身体部位信息
            example: [{'id':'123', 'symptom_part':'头部', 'symptoms':[{'id':'1','name':'头痛'}]}]
        """
        # 获取图谱中的常见症状
        param = {'is_common': '1', 'is_standard': '1', 'type': ['symptom'], 'rows': 200,
                 'ef': ['id', 'name', 'symptom_body_part_relation', 'is_common', 'common_weight']}
        response = {}
        result = []
        try:
            response = self.ai_service_client.query(json.dumps(param, ensure_ascii=False), 'entity_service')
        except:
            traceback.print_exc()
            self.logger.info('获取常见症状异常')
        if response.get('code') == 0:
            symptoms = response.get('data', {}).get('entity', [])
            body_part_id = []
            first_item = {'id': '', 'symptom_part': '常见症状', 'symptoms': []}
            for entity in symptoms:
                body_part_id.extend(entity.get('symptom_body_part_relation', []))
                first_item['symptoms'].append({'id': entity.get('id', ''), 'name': entity.get('name')})
            result.append(first_item)
            body_part_id = list(set(body_part_id))
            # 获取常见症状对应的身体部位
            if body_part_id:
                param = {'id': body_part_id, 'is_standard': '1', 'ef': ['id', 'name'], 'rows': len(body_part_id)}
                try:
                    response = self.ai_service_client.query(json.dumps(param, ensure_ascii=False), 'entity_service')
                except:
                    traceback.print_exc()
                    self.logger.info('获取身体部位异常')
                if response.get('code') == 0:
                    body_parts = response.get('data', {}).get('entity', [])
                    body_part_map = {}
                    for body_part in body_parts:
                        body_part_map[body_part.get('id')] = {'id': body_part.get('id'), 'symptom_part': body_part.get('name'), 'symptoms': []}
                    for entity in symptoms:
                        for _id in entity.get('symptom_body_part_relation', []):
                            if _id in body_part_map:
                                body_part_map[_id].get('symptoms').append({'id': entity.get('id', ''), 'name': entity.get('name', '')})
                    if body_part_map:
                        result.extend(body_part_map.values())
        return result

    def get_disease_set(self, disease_names, disease_set_code):
        '疾病名称集合转换'
        if disease_set_code == 2:
            # 国家临床2.0疾病标签
            label = 'pzmrT2hM'
            params = {
                'ef': ["id", "alias", "name", "source_label_value", "target_label_value", "disease_id"],
                'type': "disease",
                'target_label': label,
                'name': disease_names,
                'rows': 100
            }
            trans_dict = {}
            try:
                response = self.ai_service_client.query(json.dumps(params, ensure_ascii=False), 'label_conversion')
                if not response or response.get('code') != 0:
                    return {}
                entities = response.get('data', {}).get('entity', [])
                for entity in entities:
                    trans_name = entity.get('name', '')
                    trans_id = entity.get('disease_id') if entity.get('disease_id') else entity.get('id', '')
                    trans_code = entity.get('target_label_value', '')
                    trans_dict[trans_name] = {'name': trans_name, 'id': trans_id, 'code': trans_code}
                for entity in entities:
                    trans_name = entity.get('name', '')
                    trans_id = entity.get('disease_id') if entity.get('disease_id') else entity.get('id', '')
                    trans_code = entity.get('target_label_value', '')
                    for rs in entity.get('alias', []):
                        if rs not in trans_dict:
                            trans_dict[rs] = {'name': trans_name, 'id': trans_id, 'code': trans_code}
            except Exception:
                print('disease name trans error')
                print(traceback.format_exc())
            return trans_dict
        else:
            return {}

    def insert_symptom(self, db, symptoms, **kwargs):
        """
        插入症状.
        参数:
        db->数据库连接实例.
        symptoms->症状名称列表.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.symptom(symptom_uuid,symptom_name,
            is_deleted,gmt_created,gmt_modified)
        VALUES(uuid(),'%(name)s',0,now(),now())
        """
        self.insert_item(db, sql, symptoms)

    def insert_symptom_group(self, db, symptoms):
        """
        插入症状组.
        参数:
        db->数据库连接实例.
        symptoms->症状名称列表.
        """
        sql = """
        INSERT INTO medical_kg.symptom_synonym_group(words,is_deleted,
            gmt_created,gmt_modified)
        SELECT
            s.symptom_name,0,NOW(),NOW()
        FROM medical_kg.symptom s
        LEFT JOIN medical_kg.relation_info ri ON ri.entity_id_b=s.symptom_uuid
            AND ri.is_deleted=0
        WHERE ri.entity_id_a IS NULL AND s.symptom_name ='%(name)s'
        LIMIT 1
        """
        self.insert_item(db, sql, symptoms)

    def insert_symptom_group_group(self, db, words):
        """
        插入症状组.
        参数:
        db->数据库连接实例.
        symptoms->症状名称列表.
        """
        sql_group_select = """
        SELECT
            ssg.id,
            ssg.words
        FROM medical_kg.symptom_synonym_group ssg
        WHERE ssg.is_deleted=0 AND ssg.words='%(words)s'
        """
        rows = db.get_rows(sql_group_select % {'words': words})
        group_id = None
        if not rows:
            sql_insert = """
            INSERT INTO medical_kg.symptom_synonym_group(words,is_deleted,
                gmt_created,gmt_modified, `source`)
            VALUES('%(words)s',0,NOW(),NOW(), 10)
            """
            self.insert_item(db, sql_insert, [{'words': words}])
            rows = db.get_rows(sql_group_select % {'words': words})
            group_id = rows[0]['id']
        self.update_symptom_group(db, group_id, words.split(','))

    def update_symptom_group(self, db, group_id, words):
        """
        更新已有症状组的关系。
        参数：
        db->数据库连接实例.
        group_id->症状组ID.
        words->症状组元素数组.
        """
        wrap_words = []
        group_relation = []
        for w in words:
            wrap_words.append("'%s'" % w)
            group_relation.append({'group': group_id, 'name': w})
        sql_name_id_base = """
        SELECT
            s.symptom_uuid
        FROM medical_kg.symptom s
        WHERE s.symptom_name IN (%s) AND s.is_deleted=0
        """
        rows = db.get_rows(sql_name_id_base % ','.join(wrap_words))
        symptom_ids = []
        for row in rows:
            if not row['symptom_uuid']:
                continue
            symptom_ids.append("'%s'" % row['symptom_uuid'])
        sql_delete_base = """
        DELETE FROM medical_kg.relation_info
        WHERE relation_type=3000 AND entity_id_a='%s'
            AND entity_id_b NOT IN (%s)
        """
        sql_delete = sql_delete_base % (group_id, ','.join(symptom_ids))
        db.execute(sql_delete)
        sql_group_relation = """
        INSERT INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, is_deleted, gmt_created, gmt_modified,
            created_staffid, modify_staffid)
        SELECT '%(group)s', s.symptom_uuid, 3000, 0, NOW(), NOW(),
            'eagle', 'eagle'
        FROM medical_kg.symptom s
        LEFT JOIN medical_kg.relation_info ri
            ON ri.entity_id_b=s.symptom_uuid AND ri.relation_type=3000
            AND ri.is_deleted=0
        WHERE ri.id is NULL AND s.symptom_name='%(name)s'
        LIMIT 1
        """
        self.insert_item(db, sql_group_relation, group_relation)

    def insert_medical_synonym(self, db, words):
        """
        插入症状组.
        参数:
        db->数据库连接实例.
        symptoms->症状名称列表.
        """
        sql_group_select = """
        SELECT
            ms.id,
            ms.words
        FROM medical_kg.medical_synonym ms
        WHERE ms.is_deleted=0 AND ms.words='%(words)s'
        """
        rows = db.get_rows(sql_group_select % {'words': words})
        group_id = None
        if not rows:
            sql_insert = """
            INSERT INTO medical_kg.medical_synonym(words,is_deleted,
                gmt_created,gmt_modified, synonym_type)
            VALUES('%(words)s',0,NOW(),NOW(), 1)
            """
            self.insert_item(db, sql_insert, [{'words': words}])
            rows = db.get_rows(sql_group_select % {'words': words})
            group_id = rows[0]['id']
        self.update_medical_synonym(db, group_id, words.split(','))

    def update_medical_synonym(self, db, group_id, words):
        """
        更新已有症状组的关系。
        参数：
        db->数据库连接实例.
        group_id->症状组ID.
        words->症状组元素数组.
        """
        wrap_words = []
        group_relation = []
        for w in words:
            wrap_words.append("'%s'" % w)
            group_relation.append({'group': group_id, 'name': w})
        sql_name_id_base = """
        SELECT
            s.symptom_uuid
        FROM medical_kg.symptom s
        WHERE s.symptom_name IN (%s) AND s.is_deleted=0
        """
        rows = db.get_rows(sql_name_id_base % ','.join(wrap_words))
        symptom_ids = []
        for row in rows:
            if not row['symptom_uuid']:
                continue
            symptom_ids.append("'%s'" % row['symptom_uuid'])
        sql_delete_base = """
        DELETE FROM medical_kg.relation_info
        WHERE relation_type=9001 AND entity_id_a='%s'
            AND entity_id_b NOT IN (%s)
        """
        sql_delete = sql_delete_base % (group_id, ','.join(symptom_ids))
        db.execute(sql_delete)
        sql_group_relation = """
        INSERT INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, is_deleted, gmt_created, gmt_modified,
            created_staffid, modify_staffid)
        SELECT '%(group)s', s.symptom_uuid, 9001, 0, NOW(), NOW(),
            'eagle', 'eagle'
        FROM medical_kg.symptom s
        LEFT JOIN medical_kg.relation_info ri
            ON ri.entity_id_b=s.symptom_uuid AND ri.relation_type=9001
            AND ri.is_deleted=0
        WHERE ri.id is NULL AND s.symptom_name='%(name)s' AND s.is_deleted=0
        LIMIT 1
        """
        self.insert_item(db, sql_group_relation, group_relation)

    def insert_symptom_group_relation(self, db, symptoms):
        """
        插入症状症状组.
        参数:
        db->数据库连接实例.
        symptoms->症状名称列表.
        """
        sql = """
        INSERT INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, is_deleted, gmt_created, gmt_modified,
            created_staffid, modify_staffid)
        SELECT ssg.id, s.symptom_uuid, 3000, 0, NOW(), NOW(), 'eagle', 'eagle'
        FROM medical_kg.symptom s
        LEFT JOIN medical_kg.relation_info ri
            ON ri.entity_id_b=s.symptom_uuid AND ri.relation_type=3000
            AND ri.is_deleted=0
        LEFT JOIN medical_kg.symptom_synonym_group ssg
            ON s.symptom_name=ssg.words
        WHERE ri.id is NULL AND ssg.id IS NOT NULL AND s.symptom_name='%(name)s'
        LIMIT 1
        """
        self.insert_item(db, sql, symptoms)

    def insert_disease_symptom_relation(self, db, relations):
        """
        插入疾病症状关系.
        参数:
        db->数据库连接实例.
        relations->疾病症状关系,格式:[{disease_name:,symptom_name:,weight:}]
        """
        sql = """
        INSERT INTO medical_kg.relation_info(entity_id_a,
            entity_id_b, weight, relation_type, is_deleted, gmt_created,
            gmt_modified, created_staffid, modify_staffid)
        SELECT d.disease_uuid, s.symptom_uuid,%(weight)s, %(type)s, 0,
            NOW(), NOW(), 'eagle', 'eagle'
        FROM medical_kg.disease d
        INNER JOIN medical_kg.symptom s
            ON s.symptom_name='%(symptom_name)s' AND s.is_deleted=0
        LEFT JOIN medical_kg.relation_info ri ON ri.entity_id_a=d.disease_uuid
            AND ri.entity_id_b=s.symptom_uuid AND ri.relation_type=%(type)s
            AND ri.is_deleted=0
        WHERE d.disease_name='%(disease_name)s' AND d.is_deleted=0
            AND d.sort_code=0
        AND ri.id IS NULL
        """
        self.insert_item(db, sql, relations)

    def insert_disease_alias(self, db, diseases):
        """
        插入疾病之间的关系.
        参数:
        db->数据库连接实例.
        diseases->需要插入的疾病别名信息,格式:[{'disease_name':,'alias':, 'type':}]
        """
        sql = """
        INSERT IGNORE INTO medical_kg.disease_alias(disease_uuid,alias,
            alias_type,created_staffid,gmt_created,modify_staffid,gmt_modified)
        SELECT d.disease_uuid,'%(alias)s',%(type)s,'eagle',NOW(),'eagle',NOW()
        FROM medical_kg.disease d
        WHERE d.disease_name='%(disease_name)s' AND d.sort_code=0
            AND d.is_deleted=0
        """
        self.insert_item(db, sql, diseases)

    def insert_disease_sex_age_relation(self, db, relations):
        """
        插入疾病之间的关系.
        参数:
        db->数据库连接实例.
        relations->疾病之间的关系,结构:[{disease_name:,value:,type:}]
        """
        sql = """
        INSERT INTO medical_kg.relation_info(entity_id_a,
            entity_id_b, relation_type, is_deleted, gmt_created, gmt_modified,
            created_staffid,modify_staffid)
        SELECT d.disease_uuid, %(value)s, %(type)s, 0, NOW(), NOW(),
            'eagle', 'eagle'
        FROM medical_kg.disease d
        LEFT JOIN medical_kg.relation_info ri ON ri.entity_id_a=d.disease_uuid
            AND ri.entity_id_b=%(value)s AND ri.relation_type=%(type)s
            AND ri.is_deleted=0
        WHERE d.disease_name='%(disease_name)s' AND d.is_deleted=0
            AND d.sort_code=0 AND ri.id IS NULL
        """
        self.insert_item(db, sql, relations)

    def insert_disease_weight_relation(self, db, relations):
        """
        插入疾病之间的关系.
        参数:
        db->数据库连接实例.
        relations->疾病之间的关系,结构:[{disease_name:,value:,type:}]
        """
        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a,
            entity_id_b, relation_type, weight, is_deleted, gmt_created,
            gmt_modified, created_staffid, modify_staffid)
        SELECT d.disease_uuid, %(value)s, %(type)s, %(weight)s, 0, NOW(),
            NOW(),'eagle', 'eagle'
        FROM medical_kg.disease d
        WHERE d.disease_name='%(disease_name)s' AND d.is_deleted=0
            AND d.sort_code=0
        """
        self.insert_item(db, sql, relations)

    def insert_synonym_group(self, db, words):
        """
        插入同义词组,不检测重复,谨慎使用.
        参数:
        db->数据库连接实例.
        words->同义词列表.
        """
        sql = """
        INSERT INTO medical_kg.synonym_group(words,is_deleted,gmt_created,
            gmt_modified,created_staffid,modify_staffid)
        VALUES('%(words)s', 0, NOW(), NOW(), 'eagle', 'eagle')
        """
        self.insert_item(db, sql, words)

    def insert_disease_property(self, db, propertys):
        """
        插入疾病属性.
        参数:
        db->数据库连接实例.
        words->同义词列表.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.disease_property(disease_uuid,
            property_type, property_value, created_staffid, modify_staffid)
        SELECT d.disease_uuid, %(property_type)s,%(property_value)s,
            'mednlp', 'mednlp'
        FROM medical_kg.disease d
        WHERE d.disease_type=1 AND d.sort_code=0 AND d.is_deleted=0
            AND d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, propertys)

    def insert_symptom_property(self, db, propertys):
        """
        插入症状属性.
        参数:
        db->数据库连接实例.
        propertyss->症状属性列表.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.symptom_property(symptom_uuid,
            property_type, property_value, created_staffid, modify_staffid)
        SELECT s.symptom_uuid, %(property_type)s,%(property_value)s,
            'mednlp', 'mednlp'
        FROM medical_kg.symptom s
        WHERE s.is_deleted=0 AND s.symptom_name='%(symptom_name)s'
        """
        self.insert_item(db, sql, propertys)

    def insert_disease_property_by_alias(self, db, properties):
        """
        插入疾病属性.
        参数:
        db->数据库连接实例.
        words->同义词列表.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.disease_property(disease_uuid,
            property_type, property_value, created_staffid, modify_staffid)
        SELECT d.disease_uuid, %(property_type)s,'%(property_value)s',
            'mednlp', 'mednlp'
        FROM medical_kg.disease_alias da
        INNER JOIN medical_kg.disease d ON d.disease_uuid=da.disease_uuid
            AND d.disease_type=1 AND d.sort_code=0 AND d.is_deleted=0
        WHERE da.is_deleted=0 AND d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, properties)

    def insert_medical_record(self, db, records):
        """
        插入疾病属性.
        参数:
        db->数据库连接实例.
        words->同义词列表.
        """
        sql = """
        INSERT IGNORE INTO medical_data.medical_record(hospital_name,
            hospital_record_id, disease_name, disease_name_org, sex, age,
            `type`, chief_complaint, medical_history, state,gmt_created,
            gmt_modified,create_staff,modify_staff)
        VALUES('医务中心', %(count)s, '%(disease_name)s',
            '%(disease_name_org)s', %(sex)s, %(age)s, 3,
            '%(chief_complaint)s', '%(medical_history)s',1, NOW(),NOW(),
            'eagle','eagle')
        """
        self.insert_item(db, sql, records)

    def insert_medical_record_data(self, db, records):
        """
        插入疾病属性.
        参数:
        db->数据库连接实例.
        records->病历数据.
        """
        sql = """
        INSERT IGNORE INTO medical_data.medical_record_data(hospital_name,
            hospital_record_id, disease_name, disease_name_org, sex, age,
            medical_record_type, chief_complaint, medical_history,
            past_medical_history, personal_history, family_history,
            obstetrical_history, menstrual_history, is_deleted,gmt_created,
            gmt_modified,create_staff,modify_staff)
        VALUES('%(hospital_name)s', '%(hospital_record_id)s',
            '%(disease_name)s', '%(disease_name)s', %(sex)s, %(age)s, %(type)s,
            '%(chief_complaint)s', '%(medical_history)s',
            '%(past_medical_history)s', '%(personal_history)s',
            '%(family_history)s', '%(obstetrical_history)s',
            '%(menstrual_history)s', 0, NOW(),NOW(), 'eagle','eagle')
        """
        self.insert_item(db, sql, records)

    def insert_disease_detail(self, db, detail):
        """
        插入疾病属性.
        参数:
        db->数据库连接实例.
        detail->疾病属性
        """
        sql = """
        INSERT IGNORE INTO medical_kg.disease_detail_data(disease_name,
            disease_name_en, definition, cause, pathogenesis,
            pathophysiological, clinical_manifestation, complication,
            lab_check, other_check, diagnosis, differential_diagnosis,
            treatment, prevention, prognosis, is_deleted, created_staffid,
            modify_staffid, source)
        VALUES('%(disease_name)s', '%(disease_name_en)s', '%(definition)s',
            '%(cause)s', '%(pathogenesis)s', '%(pathophysiological)s',
            '%(clinical_manifestation)s', '%(complication)s', '%(lab_check)s',
            '%(other_check)s',
            '%(diagnosis)s', '%(differential_diagnosis)s', '%(treatment)s',
            '%(prevention)s', '%(prognosis)s', 0,'mednlp','mednlp', %(source)s)
        """
        self.insert_item(db, sql, detail)

    def insert_body_part(self, db, body_parts):
        """
        插入身体部位.
        参数:
        db->数据库连接实例.
        body_parts->需要插入的身体部位信息.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.body_part(body_part_uuid, body_part_name,
            gmt_created,gmt_modified)
        VALUES(uuid(), '%(body_part_name)s', NOW(),NOW())
        """
        self.insert_item(db, sql, body_parts)

    def insert_medical_word(self, db, medical_words):
        """
        插入身体部位.
        参数:
        db->数据库连接实例.
        medical_words->需要插入的医学词表信息.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.medical_word(word_uuid, medical_word,
            gmt_created,gmt_modified)
        VALUES(uuid(), '%(medical_word_name)s', NOW(),NOW())
        """
        self.insert_item(db, sql, medical_words)

    def insert_body_part_synonym_relation(self, db, words):
        """
        插入身体部位同义词关系.
        参数:
        db->数据库连接实例.
        words->需要插入的身体部位词组.
        """
        group_id_select_sql = """
        SELECT
            DISTINCT ri.entity_id_a group_id
        FROM medical_kg.body_part bp
        INNER JOIN medical_kg.relation_info ri
            ON ri.entity_id_b=bp.body_part_uuid AND bp.is_deleted=0
            AND ri.is_deleted=0 AND ri.relation_type=9002
        %(where_sql)s
        UNION ALL
        SELECT
            IFNULL(e.group_id, uuid()) group_id
        FROM (
            SELECT
                DISTINCT ri.entity_id_a group_id
            FROM medical_kg.body_part bp
            LEFT JOIN medical_kg.relation_info ri
                ON ri.entity_id_b=bp.body_part_uuid AND bp.is_deleted=0
                AND ri.is_deleted=0 AND ri.relation_type=9002
            %(where_sql)s
        ) e
        """
        if not words:
            return
        where_sql = text.create_id_where_clause(words, 'bp.body_part_name',
                                                wrap="'", operator='WHERE')
        if not where_sql:
            return
        group_id_select_sql = group_id_select_sql % ({'where_sql': where_sql})
        rows = db.get_rows(group_id_select_sql)
        if not rows:
            return
        group_id = rows[0]['group_id']
        print('group_id:', group_id)

        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        SELECT
            '%(group_id)s',
            bp.body_part_uuid,
            9002,
            NOW(),
            NOW(),
            'mednlp',
            'mednlp'
        FROM medical_kg.body_part bp
        WHERE bp.body_part_name='%(body_part_name)s' AND bp.is_deleted=0
        """
        for word in words:
            self.insert_item(db, sql, [{'body_part_name': word,
                                        'group_id': group_id}])
        synonym_sql = """
        REPLACE INTO medical_kg.medical_synonym(words, synonym_type,
            synonym_uuid, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        SELECT
            GROUP_CONCAT(bp.body_part_name),
            2,
            ri.entity_id_a,
            NOW(),
            NOW(),
            'mednlp',
            'mednlp'
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.body_part bp ON bp.body_part_uuid=ri.entity_id_b
            AND bp.is_deleted=0 AND ri.relation_type=9002
        WHERE ri.is_deleted=0 AND ri.relation_type=9002
            AND ri.entity_id_a='%(group_id)s'
        GROUP BY ri.entity_id_a
        """
        self.insert_item(db, synonym_sql, [{'group_id': group_id}])

    def insert_symptom_synonym_relation(self, db, words):
        """
        插入症状同义词关系.
        参数:
        db->数据库连接实例.
        words->需要插入的症状词组.
        """
        group_id_select_sql = """
        SELECT
            DISTINCT ri.entity_id_a group_id
        FROM medical_kg.symptom s
        INNER JOIN medical_kg.relation_info ri
            ON ri.entity_id_b=s.symptom_uuid AND s.is_deleted=0
            AND ri.is_deleted=0 AND ri.relation_type=9001
        %(where_sql)s
        UNION ALL
        SELECT
            IFNULL(e.group_id, uuid()) group_id
        FROM (
            SELECT
                DISTINCT ri.entity_id_a group_id
            FROM medical_kg.symptom s
            LEFT JOIN medical_kg.relation_info ri
                ON ri.entity_id_b=s.symptom_uuid AND s.is_deleted=0
                AND ri.is_deleted=0 AND ri.relation_type=9001
            %(where_sql)s
        ) e
        """
        if not words:
            return
        where_sql = text.create_id_where_clause(words, 's.symptom_name',
                                                wrap="'", operator='WHERE')
        if not where_sql:
            return
        group_id_select_sql = group_id_select_sql % ({'where_sql': where_sql})
        rows = db.get_rows(group_id_select_sql)
        if not rows:
            return
        group_id = rows[0]['group_id']
        print('group_id:', group_id)

        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        SELECT
            '%(group_id)s',
            s.symptom_uuid,
            9001,
            NOW(),
            NOW(),
            'mednlp',
            'mednlp'
        FROM medical_kg.symptom s
        WHERE s.symptom_name='%(symptom_name)s' AND s.is_deleted=0
        """
        for word in words:
            self.insert_item(db, sql, [{'symptom_name': word,
                                        'group_id': group_id}])
        synonym_sql = """
        REPLACE INTO medical_kg.medical_synonym(words, synonym_type,
            synonym_uuid, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        SELECT
            GROUP_CONCAT(s.symptom_name),
            1,
            ri.entity_id_a,
            NOW(),
            NOW(),
            'mednlp',
            'mednlp'
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.symptom s ON s.symptom_uuid=ri.entity_id_b
            AND s.is_deleted=0 AND ri.relation_type=9001
        WHERE ri.is_deleted=0 AND ri.relation_type=9001
            AND ri.entity_id_a='%(group_id)s'
        GROUP BY ri.entity_id_a
        """
        self.insert_item(db, synonym_sql, [{'group_id': group_id}])

    def insert_physical_examination(self, db, words):
        """
        插入体征.
        参数:
        db->数据库连接实例.
        words->需要插入的体征词.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.physical_examination(
            physical_examination_uuid, physical_examination_name,
            gmt_created,gmt_modified, create_staff, modify_staff)
        VALUES(uuid(), '%(physical_examination_name)s', NOW(),NOW(), 'mednlp',
            'mednlp')
        """
        self.insert_item(db, sql, words)

    def insert_physical_examination_property(self, db, words):
        """
        插入体征属性.
        参数:
        db->数据库连接实例.
        words->需要插入的体征属性信息.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.physical_examination_property(
            physical_examination_uuid, property_type, property_value,
            gmt_created, gmt_modified, create_staff, modify_staff)
        SELECT
            pe.physical_examination_uuid,
            %(property_type)s,
            '%(property_value)s',
            NOW(), NOW(), 'mednlp', 'mednlp'
        FROM medical_kg.physical_examination pe
        WHERE pe.is_deleted=0
            AND pe.physical_examination_name='%(physical_examination_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_physical_examination(self, db, words):
        """
        插入疾病体征关系.
        参数:
        db->数据库连接实例.
        words->需要插入的疾病体征关系信息.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        SELECT
            d.disease_uuid,
        pe.physical_examination_uuid,
        5000, now(), now(), 'mednlp', 'mednlp'
        FROM medical_kg.disease d
        LEFT JOIN medical_kg.physical_examination pe
            ON pe.physical_examination_name='%(physical_examination_name)s'
            AND pe.is_deleted=0
        WHERE d.is_deleted=0 AND d.common_level=1 AND d.sort_code=0
            AND d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_inspection_parent(self, db, word):
        """
        插入检查检验.
        参数:
        db->数据库连接实例.
        words->需要插入的检查检验词.结构[{'inspection_name':}]
        """
        sql = """
        INSERT IGNORE INTO medical_kg.inspection(inspection_uuid,
            inspection_name, gmt_created,gmt_modified, create_staff,
            modify_staff)
        VALUES(uuid(), '%(inspection_name)s', NOW(),NOW(), 'eagle', 'eagle')
        """
        self.insert_item(db, sql, [word])
        sql_id = """
        SELECT
            i.inspection_uuid
        FROM medical_kg.inspection i
        WHERE i.is_deleted=0 AND i.inspection_name='%(inspection_name)s'
        """
        rows = db.get_rows(sql_id % word)
        if rows:
            return rows[0]['inspection_uuid']
        return None

    def insert_inspection(self, db, word):
        """
        插入检查检验.
        参数:
        db->数据库连接实例.
        words->需要插入的检查检验词.
        结构[{'inspection_name':, 'inspection_name_parent':}]
        """
        sql = """
        INSERT IGNORE INTO medical_kg.inspection(inspection_uuid,
            inspection_name, parent, gmt_created,gmt_modified, create_staff,
            modify_staff)
        SELECT
            uuid(), '%(inspection_name)s', i.inspection_uuid,
            NOW(), NOW(), 'mednlp', 'mednlp'
        FROM medical_kg.inspection i
        WHERE i.is_deleted=0 AND i.inspection_name='%(inspection_name_parent)s'
        """
        self.insert_item(db, sql, [word])
        sql_id = """
        SELECT
            i.inspection_uuid
        FROM medical_kg.inspection i
        INNER JOIN medical_kg.inspection i2 ON i2.inspection_uuid=i.parent
            AND i2.is_deleted=0
            AND i2.inspection_name='%(inspection_name_parent)s'
        WHERE i.is_deleted=0 AND i.inspection_name='%(inspection_name)s'
        """
        rows = db.get_rows(sql_id % word)
        if rows:
            return rows[0]['inspection_uuid']
        return None

    def insert_inspection_property(self, db, words):
        """
        插入检查检验属性.
        参数:
        db->数据库连接实例.
        words->需要插入的检查检验属性信息.
        结构:[{'property_type':,'property_value':,'inspection_id':}]
        """
        sql = """
        INSERT IGNORE INTO medical_kg.inspection_property(inspection_uuid,
            property_type, property_value, gmt_created, gmt_modified,
            create_staff, modify_staff)
        VALUES(
            '%(inspection_id)s', %(property_type)s, '%(property_value)s',
            NOW(), NOW(), 'mednlp', 'mednlp')
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection(self, db, words):
        """
        插入疾病体征关系.
        参数:
        db->数据库连接实例.
        words->需要插入的疾病体征关系信息.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        SELECT
            d.disease_uuid,
        pe.inspection_uuid,
        6000, now(), now(), 'mednlp', 'mednlp'
        FROM medical_kg.disease d
        LEFT JOIN medical_kg.inspection pe
            ON pe.inspection_name='%(inspection_name)s'
            AND pe.is_deleted=0
        WHERE d.is_deleted=0 AND d.common_level=1 AND d.sort_code=0
            AND d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection_full(self, db, words):
        """
        插入完整的疾病体征关系，包含选项和数值文本。
        参数：
        db->数据库连接实例。
        words->需要插入的疾病体征关系信息.具体结构：
        [{'inspection_id':,'disease_name':, 'r_type':,'option:|min:|max:|unit'}]
        """
        self.insert_disease_inspection_alone(db, words)
        for word in words:
            if 6002 == word['r_type']:
                self.insert_disease_inspection_option(db, [word])
            if 6003 == word['r_type']:
                self.insert_disease_inspection_unit(db, [word])
                if 'min' in word:
                    self.insert_disease_inspection_value_min(db, [word])
                if 'max' in word:
                    self.insert_disease_inspection_value_max(db, [word])

    def insert_disease_inspection_value(self, db, words):
        """
        插入疾病体征关系，数值单位类型的值关系。
        参数：
        db->数据库连接实例。
        words->需要插入的疾病体征关系信息.
        具体结构：[{'inspection_id':,'disease_name':,}]
        """
        sql = """
        insert ignore into medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, weight, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        select
            ifnull(ri2.id, '-1'), ifnull(ri3.id, '-1'), 6110, ri.id,
            now(), now(), 'mednlp', 'mednlp'
        from medical_kg.inspection i
        inner join medical_kg.relation_info ri
            on ri.entity_id_b=i.inspection_uuid
            and ri.is_deleted=0 and ri.relation_type=6003
        inner join medical_kg.disease d on d.disease_uuid=ri.entity_id_a
            and d.is_deleted=0 and d.sort_code=0 and d.common_level=1
        left join medical_kg.relation_info ri2 on ri2.weight=ri.id
            and ri2.is_deleted=0 and ri2.relation_type=6120
        left join medical_kg.relation_info ri3 on ri3.weight=ri.id
            and ri3.is_deleted=0 and ri3.relation_type=6121
        where i.is_deleted=0 and i.inspection_uuid='%(inspection_id)s'
            and d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection_unit(self, db, words):
        """
        插入疾病体征关系，数值单位类型的单位关系。
        参数：
        db->数据库连接实例。
        words->需要插入的疾病体征关系信息.具体结构：[{'inspection_id':,'unit':}]
        """
        sql = """
        insert ignore into medical_kg.relation_info(entity_id_a, entity_id_b,
             relation_type, gmt_created, gmt_modified, created_staffid,
             modify_staffid)
        select
            ifnull(ip.id, ''), ri.id, 6122,
            now(), now(), 'mednlp', 'mednlp'
        from medical_kg.relation_info ri
        INNER JOIN medical_kg.inspection_property ip
            ON ip.inspection_uuid=ri.entity_id_b
            AND ip.is_deleted=0 AND ip.property_type=4
            AND ip.property_value='%(unit)s'
        where ri.is_deleted=0 and ri.relation_type=6003
            and ri.entity_id_b='%(inspection_id)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection_value_min(self, db, words):
        """
        插入疾病体征关系，数值单位类型的小值关系。
        参数：
        db->数据库连接实例。
        words->需要插入的疾病体征关系信息.
        具体结构：[{'inspection_id':,'disease_name':, 'min':,}]
        """
        sql = """
        insert ignore into medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        select
            '%(min)s', ri.id, 6120, now(), now(), 'mednlp', 'mednlp'
        from medical_kg.relation_info ri
        inner join medical_kg.disease d on d.disease_uuid=ri.entity_id_a
            and d.is_deleted=0 and d.sort_code=0 and d.common_level=1
        where ri.is_deleted=0 AND ri.relation_type=6003
            and ri.entity_id_b='%(inspection_id)s'
            and d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection_value_max(self, db, words):
        """
        插入疾病体征关系，数值单位类型的大值关系。
        参数：
        db->数据库连接实例。
        words->需要插入的疾病体征关系信息.
        具体结构：[{'inspection_id':,'disease_name':, 'max':,}]
        """
        sql = """
        insert ignore into medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        select
            '%(max)s', ri.id, 6121, now(), now(), 'mednlp', 'mednlp'
        from medical_kg.relation_info ri
        inner join medical_kg.disease d on d.disease_uuid=ri.entity_id_a
            and d.is_deleted=0 and d.sort_code=0 and d.common_level=1
        where ri.is_deleted=0 AND ri.relation_type=6003
            and ri.entity_id_b='%(inspection_id)s'
            and d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection_option(self, db, words):
        """
        插入疾病体征关系附加的选项。
        参数：
        db->数据库连接实例。
        words->需要插入的疾病体征关系信息.
        具体结构：[{'inspection_id':,'disease_name':, 'option':,...}]
        """
        sql = """
        insert ignore into medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
            modify_staffid)
        select
            ip.id, ri.id, 6100, now(), now(), 'mednlp', 'mednlp'
        from medical_kg.relation_info ri
        inner join medical_kg.disease d on d.disease_uuid=ri.entity_id_a
            and d.is_deleted=0 and d.sort_code=0 and d.common_level=1
        inner join medical_kg.inspection_property ip
            on ip.inspection_uuid=ri.entity_id_b
            and ip.is_deleted=0 and ip.property_type=5
            and ip.property_value='%(option)s'
        where ri.is_deleted=0 AND ri.relation_type=6002
            and ri.entity_id_b='%(inspection_id)s'
             and d.disease_name='%(disease_name)s'
        """
        self.insert_item(db, sql, words)

    def insert_disease_inspection_alone(self, db, words):
        """
        插入疾病体征关系不包含选项和数值文本.
        参数:
        db->数据库连接实例.
        words->需要插入的疾病体征关系信息.
        具体结构：[{'inspection_id':,'disease_name':, 'r_type':}]
        """
        sql = """
        insert ignore into medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created, gmt_modified, created_staffid,
             modify_staffid)
        select
            d.disease_uuid,
            i.inspection_uuid, %(r_type)s,
            now(), now(), 'mednlp', 'mednlp'
        from medical_kg.inspection i
        inner join medical_kg.disease d on d.disease_name='%(disease_name)s'
            and d.sort_code=0 and d.is_deleted=0 and d.common_level=1
        where i.inspection_uuid='%(inspection_id)s' and i.is_deleted=0
        """
        self.insert_item(db, sql, words)

    def insert_disease_complicated(self, db, words):
        """
        插入疾病并发征关系.
        参数:
        db->数据库连接实例.
        words->需要插入的疾病并发征关系信息.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, gmt_created,gmt_modified,created_staffid,
            modify_staffid, weight)
        SELECT
            d2.disease_uuid, d.disease_uuid, 1010,
            NOW(), NOW(), 'mednlp', 'mednlp', 200
        FROM medical_kg.disease d
        INNER JOIN medical_kg.disease d2
            ON d2.disease_name='%(disease_diagnose)s' AND d2.sort_code=0
            AND d2.is_deleted=0 AND d2.disease_type=1
        WHERE d.disease_name='%(disease_past)s' AND d.sort_code=0
            AND d.is_deleted=0 AND d.disease_type=1
        """
        self.insert_item(db, sql, words)

    def update_disease_common(self, db, diseases):
        """
        插入疾病通用级别属性.
        参数:
        db->数据库连接实例.
        疾病->疾病及属性
        """
        sql = """
        UPDATE medical_kg.disease d
        SET d.common_level=%(common_level)s,d.gmt_modified=NOW()
        WHERE d.disease_name='%(disease_name)s'
            AND d.disease_type=1 AND d.sort_code=0
        """
        self.insert_item(db, sql, diseases)

    def insert_item(self, db, sql, items, debug=False):
        for item in items:
            s = sql % item
            if debug:
                print(s)
            db.execute(s)
        db.commit()

    def update_synonym_relation(self, db):
        """
        根据同义词组表更新同义词关系.
        参数:
        db->数据库连接实例.
        """
        group_sql = """
        SELECT
            sg.id,
            sg.words
        FROM medical_kg.synonym_group sg
        WHERE sg.is_deleted=0
        """
        rows = db.get_rows(group_sql)
        word_group = {}
        for row in rows:
            group_id, words = row['id'], row['words']
            if not words or not group_id:
                continue
            word_list = words.split(',')
            for word in word_list:
                group_set = word_group.setdefault(word, set())
                group_set.add(group_id)
        relations = []
        for word, groups in word_group.items():
            for group_id in groups:
                relations.append({'group': group_id, 'word': word})
        self._insert_synonym_relation(db, relations)

    def _insert_synonym_relation(self, db, relations):
        """
        插入同义词关系.
        参数:
        db->数据库连接实例.
        relations->同义词关系列表.
        """
        sql = """
        INSERT IGNORE INTO medical_kg.relation_info(entity_id_a, entity_id_b,
            relation_type, is_deleted, gmt_created, gmt_modified,
            created_staffid, modify_staffid)
        VALUES('%(group)s', '%(word)s', 9000, 0, NOW(), NOW(),'eagle','eagle')
        """
        self.insert_item(db, sql, relations)

    def check_disease(self, db, disease_name):
        """
        检查该疾病是否存在.
        参数:
        db->数据库连接实例.
        disease_name->疾病名.
        """
        sql = """
        SELECT
            d.disease_name
        FROM medical_kg.disease d
        WHERE d.is_deleted=0 AND d.disease_type=1 AND d.sort_code=0
            AND d.disease_name='%s'
        """
        rows = db.get_rows(sql % disease_name)
        if rows and rows[0]['disease_name'] == disease_name:
            return True
        return False

    def check_disease_alias(self, db, disease_name):
        """
        检查该疾病别名是否存在.
        参数:
        db->数据库连接实例.
        disease_name->疾病名.
        """
        sql = """
        SELECT
            da.alias
        FROM medical_kg.disease_alias da
        INNER JOIN medical_kg.disease d ON d.disease_uuid=da.disease_uuid
            AND d.disease_type=1 AND d.sort_code=0 AND d.is_deleted=0
        WHERE da.is_deleted=0 AND da.alias = '%s'
        """
        rows = db.get_rows(sql % disease_name)
        if rows and rows[0]['alias'] == disease_name:
            return True
        return False

    def load_disease_info(self, db):
        """
        加载疾病信息.
        参数:
        db->数据库连接实例.
        返回值->疾病列表,格式:[{entity_id:,entity_name:,common_level:,type:}]
        """
        disease_sql = """
        SELECT
            d.disease_uuid entity_id,
            d.disease_name entity_name,
            d.common_level,
            1 type
        FROM medical_kg.disease d
        INNER JOIN (
        SELECT
            d.disease_uuid
        FROM medical_kg.disease d
        WHERE d.common_level=1
        UNION
        SELECT
            dp.disease_uuid
        FROM medical_kg.disease_property dp
        WHERE dp.property_type=1
        UNION
        SELECT
            dd.disease_uuid
        FROM medical_kg.disease_detail dd
        WHERE dd.is_deleted=0
        ) e ON e.disease_uuid=d.disease_uuid
        WHERE d.is_deleted=0
        """
        rows = db.get_rows(disease_sql)
        return list(rows)

    def load_disease_property(self, db):
        """
        加载疾病属性.
        参数:
        db->数据库连接实例.
        返回值->疾病属性词典,结构:{disease_id:{field:value}}
        """
        sql = """
        SELECT
            dp.disease_uuid,
            dp.property_type,
            dp.property_value
        FROM medical_kg.disease_property dp
        WHERE dp.is_deleted=0 AND dp.disease_uuid IS NOT NULL
        """
        rows = db.get_rows(sql)
        property = {}
        for row in rows:
            property_type = row['property_type']
            p_item = property.setdefault(row['disease_uuid'], {})
            # 是否危重病
            if 1 == property_type:
                p_item['is_critical_disease'] = 1
            # 危重病相对发病率
            elif 3 == property_type and row['property_value']:
                p_item['critical_rate'] = int(row['property_value']) * 10
            elif 4 == property_type:
                p_item['rate'] = int(
                    math.pow(4.0, float(row['property_value']) / 10.0))
            elif 5 == property_type:
                p_item['is_general_treatment'] = 1
            elif 6 == property_type:
                p_item['acute'] = row['property_value']
            elif 7 == property_type:
                p_item['chronic'] = row['property_value']
        return property

    def load_symptom_disease(self, db):
        """
        加载症状的相关疾病关系.
        参数:
        db->数据库连接实例.
        返回值->症状的相关疾病词典,结构:
        {symptom_id, {disease_id,{disease_name, rate, weight}}}
        """
        sql = """
        SELECT
            ri.entity_id_b symptom_id,
            d.disease_uuid disease_id,
            d.disease_name,
            IFNULL(dp.property_value, 1) rate,
            IFNULL(ri.weight, 1) weight
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.disease d ON d.disease_uuid=ri.entity_id_a
            AND d.is_deleted=0 AND d.common_level=1
        LEFT JOIN medical_kg.disease_property dp
            ON dp.disease_uuid=d.disease_uuid AND dp.is_deleted=0
            AND dp.property_type=4
        WHERE ri.relation_type=4 AND ri.is_deleted=0
        """
        rows = db.get_rows(sql)
        symptom_disease_weight = {}
        for row in rows:
            symptom_id = row.pop('symptom_id', None)
            disease_id = row.pop('disease_id', None)
            if not symptom_id or not disease_id:
                continue
            disease_dict = symptom_disease_weight.setdefault(symptom_id, {})
            disease_dict.setdefault(disease_id, row)
        return symptom_disease_weight

    def load_symptom_parent(self, db):
        """
        加载症状的父子关系.
        参数:
        db->数据库连接实例.
        返回值->症状的父症状,结构:{symptom_id, parent_symptom_id}
        """
        sql = """
        SELECT
            ri.entity_id_a symptom_id,
            ri.entity_id_b parent_symptom_id
        FROM medical_kg.relation_info ri
        WHERE ri.is_deleted=0 AND ri.relation_type=2001
        """
        rows = db.get_rows(sql)
        symptom_relation = {}
        for row in rows:
            symptoms = symptom_relation.setdefault(row['symptom_id'], set())
            symptoms.add(row['parent_symptom_id'])
        return symptom_relation

    def load_symptom_parent_by_name(self, db):
        """
        加载症状的父子关系.
        参数:
        db->数据库连接实例.
        返回值->症状的父症状,结构:{symptom_name, parent_symptom_name}
        """
        sql = """
        SELECT
            t2.symptom_name symptom_name,
            t3.symptom_name parent_symptom_name
        FROM medical_kg.relation_info t1
        LEFT JOIN medical_kg.symptom t2
        ON t1.entity_id_a = t2.symptom_uuid
        RIGHT JOIN medical_kg.symptom t3
        ON t1.entity_id_b = t3.symptom_uuid
        WHERE t1.relation_type = 2001;
        """
        rows = db.get_rows(sql)
        symptom_relation = {}
        for row in rows:
            symptoms = symptom_relation.setdefault(row['symptom_name'], set())
            symptoms.add(row['parent_symptom_name'])
        return symptom_relation

    def load_disease_relation_info(self, db):
        """
        加载疾病的相关信息.
        参数:
        db->数据库连接实例.
        返回值->症状的父症状,结构:{symptom_id, parent_symptom_id}
        """
        sql = """
        SELECT
            ri.entity_id_a disease_id,
            ri.entity_id_b,
            ri.relation_type,
            ri.weight,
            s.symptom_uuid,
            s.symptom_name,
            d.common_level
        FROM medical_kg.relation_info ri
        LEFT JOIN medical_kg.symptom s ON s.symptom_uuid=ri.entity_id_b
            AND ri.relation_type=4 AND s.symptom_name IS NOT NULL
        LEFT JOIN medical_kg.disease d ON d.disease_uuid=ri.entity_id_a
            AND d.is_deleted=0
        WHERE ri.is_deleted=0 AND ri.relation_type IN (4, 1101, 1102, 1202,
            1203, 1206, 1010, 5000, 6000)
        """
        rows = db.get_rows(sql)
        disease_info = {}
        for row in rows:
            disease_id = row.pop('disease_id')
            relation_type = row.pop('relation_type')
            info = disease_info.setdefault(disease_id, {})
            if 1010 == relation_type and row.get('common_level') != 1:
                del disease_info[disease_id]
            if 4 == relation_type:
                symptom = info.setdefault('symptom', [])
                item = {'symptom_id': row['symptom_uuid'],
                        'symptom_name': row['symptom_name'],
                        'weight': row['weight']}
                symptom.append(item)
            elif 1101 == relation_type:
                info['sex'] = row['entity_id_b']
                if info['sex'] in ('1', 1):
                    info['sex_weight'] = {'1': 100, '2': 0}
                elif info['sex'] in ('2', 2):
                    info['sex_weight'] = {'1': 0, '2': 100}
            elif 1102 == relation_type:
                sex_info = info.setdefault('sex_weight', {})
                sex_info[row['entity_id_b']] = int(row['weight'])
            elif 1202 == relation_type:
                info['age_min'] = row['entity_id_b']
            elif 1203 == relation_type:
                info['age_max'] = row['entity_id_b']
            elif 1206 == relation_type:
                sex_info = info.setdefault('age_weight', {})
                sex_info[row['entity_id_b']] = int(row['weight'])
            elif 1010 == relation_type and row.get('common_level') == 1:
                past_info = info.setdefault('disease_history', {})
                past_info[row['entity_id_b']] = int(row['weight'])
            elif 5000 == relation_type:
                physical_examinations = info.setdefault(
                    'physical_examination_detail', set())
                physical_examinations.add(row['entity_id_b'])
            elif 6000 == relation_type:
                inspections = info.setdefault('inspection_detail', set())
                inspections.add(row['entity_id_b'])
        for disease_id, info in disease_info.items():
            if not info:
                continue
            symptoms = info.pop('symptom', None)
            if not symptoms:
                continue
            symptoms = sorted(symptoms, key=lambda s: s['weight'],
                              reverse=True)
            detail = info.setdefault('symptom_detail', [])
            symptom_id = info.setdefault('symptom_id', set())
            symptom_weight = info.setdefault('symptom_weight', {})
            for symptom in symptoms:
                symptom_id.add(symptom['symptom_id'])
                detail.append('%s|%s' % (symptom['symptom_id'],
                                         symptom['symptom_name']))
                item = {'name': symptom['symptom_name'], 'type': 1,
                        'weight': symptom['weight']}
                symptom_weight[symptom['symptom_id']] = item
        return disease_info

    def load_physical_examination_info(self, db):
        """
        加载体征信息.
        参数:
        db->数据库连接实例.
        返回值->体征信息字典,{physical_examination_id: physical_examination_name}
        """
        physical_examination_sql = """
        SELECT
            pe.physical_examination_uuid uuid,
            pe.physical_examination_name name
        FROM medical_kg.physical_examination pe
        WHERE pe.is_deleted=0
        """
        rows = db.get_rows(physical_examination_sql)
        physical_examination = {}
        for row in rows:
            physical_examination[row['uuid']] = row['name']
        return physical_examination

    def load_inspection_info(self, db):
        """
        加载化验信息.
        参数:
        db->数据库连接实例.
        返回值->化验信息字典,{inspection_id: inspection_name}
        """
        inspection_sql = """
        SELECT
            i.inspection_uuid uuid,
            i.inspection_name name
        FROM medical_kg.inspection i
        WHERE i.is_deleted=0
        """
        rows = db.get_rows(inspection_sql)
        inspection = {}
        for row in rows:
            inspection[row['uuid']] = row['name']
        return inspection

    def load_disease_detail(self, db):
        """
        加载疾病知识库.
        参数:
        db->数据库连接实例.
        返回值->疾病知识,结构:{disease_id:{detail}}
        """
        sql = """
        SELECT
            dd.disease_uuid,
            dd.definition definition,
            dd.cause cause,
            dd.pathogenesis pathogenesis,
            dd.pathophysiological,
            dd.clinical_manifestation clinical_manifestation,
            dd.complication complication,
            dd.lab_check lab_check,
            dd.other_check other_check,
            dd.diagnosis diagnosis,
            dd.differential_diagnosis differential_diagnosis,
            dd.treatment treatment,
            dd.prognosis prognosis,
            dd.prevention prevention
        FROM medical_kg.disease_detail dd
        WHERE dd.is_deleted=0
        """
        rows = db.get_rows(sql)
        disease_detail = {}
        for row in rows:
            disease_id = row.pop('disease_uuid')
            if disease_id:
                disease_detail[disease_id] = row
        return disease_detail

    def load_top_symptom(self, db, top_n=0):
        """
        """
        sql_base = """
        SELECT
            s.symptom_name
        FROM medical_kg.symptom_property sp
        INNER JOIN medical_kg.symptom s ON s.symptom_uuid=sp.symptom_uuid
            AND s.is_deleted=0
        WHERE sp.is_deleted=0 AND sp.property_type=2
        ORDER BY CAST(sp.property_value as SIGNED) DESC
        %s
        """
        limit_sql = ''
        if top_n:
            limit_sql = 'limit %s' % top_n
        sql = sql_base % limit_sql
        rows = db.get_rows(sql)
        symptoms = []
        for row in rows:
            symptoms.append(row['symptom_name'])
        return symptoms

    def load_disease_medicine(self, db):
        """
        加载疾病的药品信息.
        参数:
        db->数据库连接实例.
        返回值->疾病药品对应字典,格式:{disease_id,[{id:, name:},]}
        """
        medicine_sql = """
        SELECT
            cdr.disease_uuid disease_id,
            cp.id medicine_id,
            cp.name medicine_name
        FROM medical_kg.cpreparation_disease_relation cdr
        LEFT JOIN medical_kg.common_preparation cp
            ON cp.id=cdr.common_preparation_uuid AND cp.is_delete=0
        WHERE cdr.is_delete=0
        """
        rows = db.get_rows(medicine_sql)
        disease_medicine = {}
        for row in rows:
            disease_id, medicine_id, medicine_name = (
                row['disease_id'], row['medicine_id'], row['medicine_name'])
            if not disease_id or not medicine_id or not medicine_name:
                continue
            medicines = disease_medicine.setdefault(disease_id, [])
            info = {'id': medicine_id, 'name': medicine_name}
            medicines.append(info)
        return disease_medicine

    def load_disease_std_dept(self, db):
        """
        加载疾病的科室信息.
        参数:
        db->数据库连接实例.
        返回值->疾病药品对应字典,格式:{disease_id,{id:, name:}}
        """
        std_dept_sql = """
        SELECT
            sddr.disease_id disease_id,
            sd.id std_dept_id,
            sd.name std_dept_name
        FROM medical_kg.std_depart_disease_relation sddr
        LEFT JOIN medical_kg.std_department sd
            ON sd.id=sddr.std_dept_id AND sd.state=0
        WHERE sddr.sort_code=1 AND sddr.state=0
        """
        rows = db.get_rows(std_dept_sql)
        disease_std_dept = {}
        for row in rows:
            disease_id, std_dept_id, std_dept_name = (
                row['disease_id'], row['std_dept_id'], row['std_dept_name'])
            if not disease_id or not std_dept_id or not std_dept_name:
                continue
            disease_std_dept[disease_id] = {'std_dept_id': std_dept_id,
                                            'std_dept_name': std_dept_name}
        return disease_std_dept

    def load_disease_inspection(self, db):
        """
        加载疾病的检查检验信息.
        参数:
        db->数据库连接实例.
        返回值->疾病检查检验信息字典,
        格式:{disease_id,{id:, name:}}
        """
        disease_insp_sql = """
        SELECT
            d.disease_uuid disease_id,
            i.inspection_uuid entity_id,
            i.inspection_name entity_name,
            ip.inspection_name parent_name,
            ipo.property_value option_value,
            rimin.entity_id_a min_value,
            ipu.property_value unit,
            rimax.entity_id_a max_value
        FROM medical_kg.disease d
        INNER JOIN medical_kg.relation_info ri ON ri.entity_id_a=d.disease_uuid
            AND ri.is_deleted=0 AND ri.relation_type IN (6001, 6002,6003)
        INNER JOIN medical_kg.inspection i ON i.inspection_uuid=ri.entity_id_b
            AND i.is_deleted=0
        LEFT JOIN medical_kg.inspection ip ON ip.inspection_uuid=i.parent
            AND ip.is_deleted=0
        LEFT JOIN medical_kg.relation_info rio ON rio.entity_id_b=ri.id
            AND rio.is_deleted=0 AND rio.relation_type=6100
        LEFT JOIN medical_kg.inspection_property ipo ON ipo.id=rio.entity_id_a
            AND ipo.is_deleted=0 AND ipo.property_type=5
        LEFT JOIN medical_kg.relation_info riu ON riu.entity_id_b=ri.id
            AND riu.is_deleted=0 AND riu.relation_type=6122
        LEFT JOIN medical_kg.inspection_property ipu ON ipu.id=riu.entity_id_a
            AND ipu.is_deleted=0 AND ipu.property_type=4
        LEFT JOIN medical_kg.relation_info rimin ON rimin.entity_id_b=ri.id
            AND rimin.is_deleted=0 AND rimin.relation_type=6120
        LEFT JOIN medical_kg.relation_info rimax ON rimax.entity_id_b=ri.id
            AND rimax.is_deleted=0 AND rimax.relation_type=6121
        WHERE d.is_deleted=0 AND d.common_level=1 AND d.sort_code=0
        """
        rows = db.get_rows(disease_insp_sql)
        disease_insp = {}
        for row in rows:
            disease_id = row.pop('disease_id')
            inspections = disease_insp.setdefault(disease_id, [])
            for field in row.keys():
                if row[field] is None:
                    del row[field]
            inspections.append(row)
        return disease_insp

    def dept_classify(self, chief_complaint=None, medical_history=None):
        """
        调用 Dept_Classify_API
        :param chief_complaint: 主诉 str
        :param medical_history: 病史 str
        返回值->dept_score: 科室分数 dict，格式：{dept_name: score}
        """
        params = dict()
        if chief_complaint and medical_history:
            params['q'] = str(chief_complaint) + str(medical_history)
        elif chief_complaint:
            params['q'] = str(chief_complaint)
        elif medical_history:
            params['q'] = str(medical_history)
        params['rows'] = 50
        params['mode'] = 2
        service = 'dept_classify'
        query_return = self.ai_service_client.query(params, service)
        dept_score = self.generate_dept_score(query_return)
        return dept_score

    def generate_dept_score(self, query_return):
        """
        生成科室和其分数的字典
        :param
        query_return: Dept_Classify_API 的返回值 dict，
        格式：{code:, message:, totalCount:, data:}
        返回值->department_score: dict {dept_name: score}
        """
        department_score = dict()
        if query_return['code'] == 0 and 'data' in query_return:
            for department in query_return['data']:
                if department.get('dept_name') != 'unknow':
                    department_score[
                        department.get('dept_name')] = department.get('score')
        return department_score

    def std_dept_extract(self, q=None):
        """
        调用 Entity_Extract_API
        :param q: 需要提取标准科室的文本 str
        :return: dept_name: list [dept_name]
        """
        params = dict()
        params['q'] = q
        service = 'entity_extract'
        query_return = self.ai_service_client.query(params, service)
        dept_name = []
        if query_return['code'] == 0 and 'data' in query_return:
            for entity in query_return['data']:
                if entity.get('type') == 'std_department' and entity.get('entity_id'):
                    dept_name.append(entity.get('entity_name'))
                if entity.get('std_department'):
                    dept_name.append(entity.get('std_department'))
        return dept_name

    def load_symptom_info(self, db):
        """
        加载症状信息.
        参数:
        db->数据库连接实例.
        返回值->症状信息列表:[{'entity_id':,'entity_name':, 'type':2}]
        """
        symptom_sql = """
        SELECT
            s.symptom_uuid entity_id,
            s.symptom_name entity_name,
            2 type
        FROM medical_kg.symptom s
        WHERE s.is_deleted=0
        """
        symptoms = list(db.get_rows(symptom_sql))
        return symptoms

    def load_jieba_user_dict(self, db):
        """
        加载jieba自定义词典
        :param db: 数据库实例
        :return: 词典
        """
        jieba_user_dict_sql = """
        SELECT symptom_name, 50000
        FROM medical_kg.symptom
        WHERE source = 1
        UNION
        SELECT disease_name, 50000
        FROM medical_kg.disease
        WHERE common_level = 1
        UNION
        SELECT body_part_name, 50000
        FROM medical_kg.body_part
        """
        rows = db.get_rows(jieba_user_dict_sql)
        return rows

    def load_disease_symptom(self, db, symptom_min_length):
        """
        加载疾病和症状出现率信息
        :param db: 数据库实例
        :param symptom_min_length: 症状数量最小值
        :return: 格式 {disease: {symptom: symptom_incidence}}
        """
        disease_symptom_sql = """
        SELECT d.disease_name AS disease,
         group_concat(DISTINCT concat(s.symptom_name, ': ', ri.weight)
         ORDER BY ri.weight DESC SEPARATOR ', ') AS symptoms
        FROM medical_kg.disease d
        INNER JOIN medical_kg.relation_info ri
        ON d.disease_uuid = ri.entity_id_a
        INNER JOIN medical_kg.symptom s
        ON ri.entity_id_b = s.symptom_uuid
        WHERE d.common_level = 1 AND ri.relation_type = 4
        GROUP BY d.disease_uuid
        ORDER BY d.disease_name
        """
        rows = db.get_rows(disease_symptom_sql)
        disease_symptom_dict = {}
        for row in rows:
            disease = transform_text(row['disease'])
            symptoms = transform_text(row['symptoms'])
            symptom_incidence_dict = {}
            symptom_incidence_list = symptoms.split(', ')
            if len(symptom_incidence_list) < symptom_min_length:
                continue
            for symptom_incidence in symptom_incidence_list:
                symptom = symptom_incidence.split(': ')[0]
                incidence = symptom_incidence.split(': ')[1]
                symptom_incidence_dict[symptom] = int(incidence)
            disease_symptom_dict[disease] = symptom_incidence_dict
        return disease_symptom_dict

    def load_disease_sex_prob_distribution(self, db):
        """
        加载疾病和性别的概率分布信息
        :param db: 数据库实例
        :return: 格式 {disease: {sex: probability}}
        """
        sql = """
        SELECT
            t4.disease_name AS disease,
            t1.entity_id_b AS sex,
            t1.weight / t4.wt_sum AS weight
        FROM medical_kg.relation_info t1
        INNER JOIN (
        SELECT t3.entity_id_a, t2.disease_name, SUM(t3.weight) AS wt_sum
        FROM medical_kg.relation_info t3
        INNER JOIN medical_kg.disease t2
        ON t3.entity_id_a = t2.disease_uuid
        WHERE t3.relation_type = 1102
        GROUP BY t2.disease_name) t4
        ON t1.entity_id_a = t4.entity_id_a
        WHERE t1.relation_type = 1102
        ORDER BY t4.disease_name, t1.entity_id_b;
        """
        rows = db.get_rows(sql)
        disease_sex_prob_dict = {}
        for row in rows:
            disease, sex, prob = (row['disease'], row['sex'], row['weight'])
            if disease not in disease_sex_prob_dict:
                disease_sex_prob_dict[disease] = {}
                disease_sex_prob_dict[disease][int(sex)] = float(prob)
            else:
                disease_sex_prob_dict[disease][int(sex)] = float(prob)
        return disease_sex_prob_dict

    def load_disease_age_prob_distribution(self, db):
        """
        加载疾病和年龄的概率分布信息
        :param db: 数据库实例
        :return: 格式 {disease: {age: probability}}
        """
        sql = """
        SELECT
            t4.disease_name AS disease,
            t1.entity_id_b AS age,
            IF(t1.entity_id_b=1, t1.weight/5, t1.weight) / t4.wt_sum AS weight
        FROM medical_kg.relation_info t1
        INNER JOIN
        (SELECT
            t3.entity_id_a,
            t2.disease_name,
            SUM(IF(t3.entity_id_b=1, t3.weight/5, t3.weight)) AS wt_sum
        FROM medical_kg.relation_info t3
        INNER JOIN medical_kg.disease t2
        ON t3.entity_id_a = t2.disease_uuid
        WHERE t3.relation_type = 1206
        GROUP BY t2.disease_name) t4
        ON t1.entity_id_a = t4.entity_id_a
        WHERE t1.relation_type = 1206
        ORDER BY t4.disease_name, t1.entity_id_b;
        """
        rows = db.get_rows(sql)
        disease_age_prob_dict = {}
        for row in rows:
            disease, age_seg, prob = (row['disease'], row['age'], row['weight'])
            if disease not in disease_age_prob_dict:
                disease_age_prob_dict[disease] = {}
                disease_age_prob_dict[disease][int(age_seg)] = float(prob)
            else:
                disease_age_prob_dict[disease][int(age_seg)] = float(prob)
                if int(age_seg) == 6:
                    precedent_sum = 0
                    for i in range(1, 6):
                        precedent_sum += disease_age_prob_dict[disease][i]
                    disease_age_prob_dict[disease][6] = 1 - precedent_sum
                    if precedent_sum > 1:
                        i = max(disease_age_prob_dict[disease],
                                key=disease_age_prob_dict[disease].get)
                        disease_age_prob_dict[disease][i] += 1 - precedent_sum
                        disease_age_prob_dict[disease][6] = 0
        return disease_age_prob_dict

    def load_disease_prevalence(self, db):
        """
        加载疾病和疾病发病率信息
        :param db: 数据库实例
        :return: 格式 {disease: disease_prevalence}
        """
        disease_prevalence_sql = """
        SELECT d.disease_name AS disease, dp.property_value AS prevalence
        FROM medical_kg.disease_property dp
        INNER JOIN medical_kg.disease d
        ON dp.disease_uuid = d.disease_uuid
        WHERE dp.property_type = 4
        AND d.common_level = 1
        ORDER BY d.disease_name
        """
        rows = db.get_rows(disease_prevalence_sql)
        disease_prevalence_dict = {}
        prevalence_sum = 0
        for row in rows:
            disease, prevalence = (row['disease'], row['prevalence'])
            prevalence = 2 ** (int(prevalence) / 10)
            disease_prevalence_dict[disease] = prevalence
            prevalence_sum += prevalence
        return disease_prevalence_dict, prevalence_sum

    def load_medical_record(self, db):
        """
        导入病历
        """
        sql = """
        SELECT
          replace(concat(trim(chief_complaint), '..',
            trim(medical_history)), '\t', '') AS query,
          CASE sex
            WHEN 1 THEN 2
            WHEN 2 THEN 1
            ELSE -1
          END AS sex,
          age,
          disease_name
        FROM medical_data.medical_record
        WHERE chief_complaint NOT IN ('取药','开药','咨询','体检','健康体检',
        '要求体检','健康查体','健康体查','健康咨询','便民开药','门诊开药','要求开药',
        '患者开药','便民查体','健康体查','健康体检.','健康查体，','无特殊不适','门特病复诊',
        '家人要求开药','要求健康查体','要求健康查体。','见特殊病历记录','门诊特病复诊开药')
        AND (chief_complaint <> ''
        OR medical_history <> '')
        UNION
        SELECT
          replace(concat(trim(chief_complaint), '..',
            trim(medical_history)), '\t', '') AS query,
          CASE sex
            WHEN 1 THEN 2
            WHEN 2 THEN 1
            ELSE -1
          END AS sex,
          age,
          disease_name
        FROM medical_data.medical_record_data
        WHERE chief_complaint NOT IN ('取药','开药','咨询','体检','健康体检',
        '要求体检','健康查体','健康体查','健康咨询','便民开药','门诊开药','要求开药',
        '患者开药','便民查体','健康体查','健康体检.','健康查体，','无特殊不适','门特病复诊',
        '家人要求开药','要求健康查体','要求健康查体。','见特殊病历记录','门诊特病复诊开药')
        AND (chief_complaint <> ''
        OR medical_history <> '')
        """
        rows = db.get_rows(sql)
        medical_record = []
        for row in rows:
            mr, sex, age, disease = (
                row['query'], row['sex'], row['age'], row['disease_name'])
            medical_record.append('\t'.join([mr, str(sex), str(age), disease]))
        return medical_record

    def load_medical_record_with_history(self, db):
        """
        Load medical record with past medical history
        :param db:
        :return:
        """
        sql = """
        SELECT
          replace(concat(trim(chief_complaint), '..',
            trim(medical_history)), '\t', '') AS query,
          CASE sex
            WHEN 1 THEN 2
            WHEN 2 THEN 1
            ELSE -1
          END AS sex,
          age, past_medical_history, disease_name
        FROM medical_data.medical_record
        WHERE chief_complaint NOT IN ('取药','开药','咨询','体检','健康体检',
        '要求体检','健康查体','健康体查','健康咨询','便民开药','门诊开药','要求开药',
        '患者开药','便民查体','健康体查','健康体检.','健康查体，','无特殊不适','门特病复诊',
        '家人要求开药','要求健康查体','要求健康查体。','见特殊病历记录','门诊特病复诊开药')
        AND (chief_complaint <> ''
        OR medical_history <> '')
        UNION ALL
        SELECT
          replace(concat(trim(chief_complaint), '..',
            trim(medical_history)), '\t', '') AS query,
          CASE sex
            WHEN 1 THEN 2
            WHEN 2 THEN 1
            ELSE -1
          END AS sex,
          age, past_medical_history, disease_name
        FROM medical_data.medical_record_data
        WHERE chief_complaint NOT IN ('取药','开药','咨询','体检','健康体检',
        '要求体检','健康查体','健康体查','健康咨询','便民开药','门诊开药','要求开药',
        '患者开药','便民查体','健康体查','健康体检.','健康查体，','无特殊不适','门特病复诊',
        '家人要求开药','要求健康查体','要求健康查体。','见特殊病历记录','门诊特病复诊开药')
        AND (chief_complaint <> ''
        OR medical_history <> '')
        """
        rows = db.get_rows(sql)
        return rows

    def load_medical_record_with_examination(self, db):
        """
        Load medical record with past history, inspection, and physical exam
        :param db:
        :return:
        """
        sql = """
        SELECT
          replace(concat(trim(chief_complaint), '..',
            trim(medical_history)), '\t', '') AS query,
          CASE sex
            WHEN 1 THEN 2
            WHEN 2 THEN 1
            ELSE -1
          END AS sex,
          age, past_medical_history,
          inspection, physical_exam, disease_name
        FROM medical_data.medical_record t1
        LEFT JOIN ai_medical_knowledge.medical_record_inspection t2
        ON t1.hospital_record_id = t2.hospital_record_id
        LEFT JOIN ai_medical_knowledge.medical_record_physical_exam t3
        ON t1.hospital_record_id = t3.hospital_record_id
        WHERE chief_complaint NOT IN ('取药','开药','咨询','体检','健康体检',
        '要求体检','健康查体','健康体查','健康咨询','便民开药','门诊开药','要求开药',
        '患者开药','便民查体','健康体查','健康体检.','健康查体，','无特殊不适','门特病复诊',
        '家人要求开药','要求健康查体','要求健康查体。','见特殊病历记录','门诊特病复诊开药')
        AND (chief_complaint <> ''
        OR medical_history <> '')
        UNION ALL
        SELECT
          replace(concat(trim(chief_complaint), '..',
            trim(medical_history)), '\t', '') AS query,
          CASE sex
            WHEN 1 THEN 2
            WHEN 2 THEN 1
            ELSE -1
          END AS sex,
          age, past_medical_history,
          '' AS inspection, '' AS physical_exam, disease_name
        FROM medical_data.medical_record_data
        WHERE chief_complaint NOT IN ('取药','开药','咨询','体检','健康体检',
        '要求体检','健康查体','健康体查','健康咨询','便民开药','门诊开药','要求开药',
        '患者开药','便民查体','健康体查','健康体检.','健康查体，','无特殊不适','门特病复诊',
        '家人要求开药','要求健康查体','要求健康查体。','见特殊病历记录','门诊特病复诊开药')
        AND (chief_complaint <> ''
        OR medical_history <> '');
        """
        rows = db.get_rows(sql)
        return rows

    def load_disease_alias(self, db):
        """
        导入疾病别名和标准名
        """
        sql = """
        SELECT disease_alias.alias, disease.disease_name
        FROM ai_medical_knowledge.disease_alias
        JOIN medical_kg.disease
        WHERE disease_alias.disease_uuid = disease.disease_uuid
        AND disease.common_level = 1
        UNION
        SELECT disease_alias.alias, disease.disease_name
        FROM medical_kg.disease_alias
        JOIN medical_kg.disease
        WHERE disease_alias.disease_uuid = disease.disease_uuid
        AND disease.common_level = 1
        ORDER BY disease_name;
        """
        rows = db.get_rows(sql)
        disease_alias = {}
        for row in rows:
            alias, disease_name = (row['alias'], row['disease_name'])
            disease_alias[alias] = disease_name
        return disease_alias

    def load_prod_xy_disease_alias(self, db):
        """
        导入线上数据库的疾病别名和标准名
        """
        sql = """
        SELECT DISTINCT t1.alias, t2.name
        FROM medical_knowledge.disease_alias t1
        JOIN medical_knowledge.disease t2
        WHERE t1.disease_uuid = t2.id;
        """
        rows = db.get_rows(sql)
        disease_alias = {}
        for row in rows:
            alias, disease_name = (row['alias'], row['name'])
            disease_alias[alias] = disease_name
        return disease_alias

    def load_prod_xy_diagnose_data(self, db, params):
        """
        导入线上数据库辅助诊断预测和医生诊断结论
        """
        date_from = params.get('date_from')
        date_till = params.get('date_till')
        sql = """
        SELECT *
        FROM ai_union.natural_medical_record
        WHERE gmt_modified > %s
        AND gmt_modified < %s
        AND (chief_complaint <> ''
        OR now_medical_history <> '');
        """
        sql = sql % (date_from, date_till)
        rows = db.get_rows(sql)
        return rows

if __name__ == '__main__':
    kg = KGDao()
    # print(kg.find_disease_symptom_etc({'123': '疾病恐怖', '124': '高血压'}))
    res = kg.find_body_part_symptom_relation()
    print(res)

