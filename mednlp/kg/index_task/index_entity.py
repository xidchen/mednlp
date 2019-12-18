#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_entity.py -- the index task of entity to solr

Author: maogy <maogy@guahao.com>
Create on 2019-02-11 Monday.
"""


import global_conf
from base_index import BaseIndex
from mednlp.dao.kg_dao import KGDBDao
from mednlp.kg.db_conf import db_conf, entity_type_dict
from mednlp.kg.db_conf import medical_knowledge
from mednlp.kg.conf import kg_conf
from mednlp.kg.conf import optional_conf
import mednlp.text.pinyin as pinyin
import json
import traceback


class IndexEntity(BaseIndex):

    index_filename = 'entity.xml'
    core = 'entity'

    def initialise(self, **kwargs):
        self.kgd = KGDBDao(**kwargs)
        self.attr_db2field = {}
        self.label_db2field = {}
        self.relation_db2field = {}
        for entity in db_conf.values():
            if entity.get('attribute'):
                self.attr_db2field.update(entity['attribute'])
            if entity.get('label'):
                self.label_db2field.update(entity['label'])
            if entity.get('relation'):
                self.relation_db2field.update(entity['relation'])
        self.entity_conf = kg_conf['entity']
        pinyin.load_pinyin_dic()

    def get_data_pre(self, **kwargs):
        if self.inc_sec:
            self.inc_ids = self.kgd.load_entity_id(self.inc_sec)

    def get_data(self):
        if self.inc_sec or self.inc_ids:
            if not self.inc_ids:
                return []
        self.attributes = self.kgd.load_entity_attribute(self.inc_ids)
        self.labels = self.kgd.load_entity_label(self.inc_ids)
        self.relations = self.kgd.load_entity_relation(self.inc_ids)
        self.standard_relations = self.kgd.load_standard_relation(self.inc_ids)
        self.standard_type_dict = self.kgd.load_standard_type_dict()
        self.relation_attributes = self.kgd.load_relation_attribute(self.inc_ids)
        self.medical_knowledge_disease = self.kgd.load_medical_knowledge_disease_info(self.inc_ids)
        self.medicine_enterprise = self.kgd.load_medicine_enterprise_info(self.inc_ids)
        return self.kgd.load_entity_info(self.inc_ids)

    def process_data(self, docs):
        processed_docs = []
        intersection_code_value = {}  # 从json文件中加载检查检验的属性和属性值
        try:
            with open(global_conf.inspection_code_value_path, 'r', encoding='utf-8') as f:
                intersection_code_value = json.load(f)
        except Exception as err:
            self.logger.warning(traceback.format_exc())
        label_value = {'毒蛇咬伤': '40679', '异位妊娠': '44251'}
        for doc in docs:
            entity_name = doc.pop('name', '') # 删去key:name 获取key=name下的entitiy_name
            doc['name_s'] = entity_name
            standard_name = doc.pop('standard_name', '')  # 添加标准名
            doc['standard_name_s'] = standard_name
            is_standard = doc.pop('is_standard', 0)  # 添加是否标准名标志
            doc['is_standard_i'] = is_standard
            standard_audit_status = doc.pop('standard_audit_status', 0)
            doc['standard_audit_status_i'] = standard_audit_status
            entity_type_id = doc.pop('type', '')
            entity_type = entity_type_dict.get(entity_type_id)
            audit_status = doc.pop('audit_status',0)
            if not entity_type:
                continue
            if doc.get('is_delete') and doc['is_delete'] == 1:
                doc['solr_delete'] = 1
            doc.pop('is_delete')
            doc['type_s'] = entity_type
            if optional_conf.get('type_name'):
                doc['type_name'+optional_conf['type_name'].get('type', '_s')] = self.standard_type_dict['entity_type'].get(entity_type_id, '')
            if optional_conf.get('audit_status'):
                doc['audit_status'+optional_conf['audit_status'].get('type', '_i')] = audit_status
            entity_id = doc['id']
            if intersection_code_value.get(entity_name):
                attribute = self.attributes.setdefault(entity_id, [])
                intersection_dict = intersection_code_value.get(entity_name)
                attribute_map = db_conf.get(entity_type, {})
                for key, value in attribute_map.get('attribute', {}).items():
                    if intersection_dict.get(value):
                        new_row = {'entity_id': entity_id, 'entity_name':entity_name, 'entity_type': entity_type_id}
                        new_row['attribute_type'], new_row['attribute_value'] = key, intersection_dict.get(value, '')
                        attribute.append(new_row)
            if self.medical_knowledge_disease.get(entity_id):
                origin_disease = self.medical_knowledge_disease.get(entity_id)
                disease_type = str(origin_disease.get('disease_type', '-1'))
                if disease_type in medical_knowledge.get('disease_type'):
                    addition_labels = self.labels.setdefault(entity_id, [])
                    for label_type in medical_knowledge['disease_type'].get(disease_type):
                        addition_labels.append({'entity_id': entity_id, 'label_type': label_type, 'label_value': origin_disease['disease_id']})

            if self.medicine_enterprise.get(entity_id) \
                    and self.entity_conf.get(entity_type)\
                    and self.entity_conf[entity_type].get('attribute'):  # 加载药品药店信息
                enterprise_ids = self.medicine_enterprise.get(entity_id)
                attr_conf = self.entity_conf[entity_type].get('attribute').get('supplier', {})
                if attr_conf.get('type'):
                    doc['supplier' + attr_conf['type']] = enterprise_ids

            if (self.attributes.get(entity_id) and
                self.entity_conf.get(entity_type)
                and self.entity_conf[entity_type].get('attribute')):
                # print('eagle')
                attr_conf = self.entity_conf[entity_type]['attribute']
                # print('attr_conf', attr_conf) #attr_conf 包含哪些形如{'dosing_frequency': {'type': '_s'}}的key_value对
                for attribute in self.attributes[entity_id]:
                    if not attribute.get('attribute_type'):
                        continue
                    attr_field = self.attr_db2field.get(
                        attribute['attribute_type'])
                    if not attr_conf.get(attr_field):
                        continue
                    doc[attr_field + attr_conf[attr_field]['type']] = attribute['attribute_value']
            if self.attributes.get(entity_id):
                attributes = []
                attribute_dict = {}
                for index, attribute in enumerate(self.attributes[entity_id]):
                    attribute_obj = {}
                    if attribute['attribute_type'] in attribute_dict.keys():
                        attribute_obj = attributes[attribute_dict.get(attribute['attribute_type'])]
                        attribute_obj['value'].append(attribute['attribute_value'])
                    else:
                        if self.standard_type_dict.get('attribute_type'):
                            attribute_obj['name'] = self.standard_type_dict['attribute_type'].get(attribute['attribute_type'], '')
                            attribute_obj['value'] = [attribute['attribute_value']]
                            attribute_dict[attribute['attribute_type']] = len(attributes)
                            attributes.append(attribute_obj)
                if optional_conf.get('attributes'):
                    doc['attributes' + optional_conf['attributes']['type']] = json.dumps(attributes, ensure_ascii=False)
            # print('doc', doc)
            if (self.labels.get(entity_id)
                and self.entity_conf.get(entity_type)
                and self.entity_conf[entity_type].get('label')):
                label_conf = self.entity_conf[entity_type]['label']
                for label in self.labels[entity_id]:
                    if not label.get('label_type'):
                        continue
                    label_field = self.label_db2field.get(
                        label['label_type'])
                    # print(label_field)
                    if not label_conf.get(label_field):
                        continue
                    doc[label_field + label_conf[label_field]['type']] = label['label_value']
                if entity_type == 'disease' and label_value.get(entity_name):  # 修复错误标签值
                    doc['disease_id_s'] = label_value.get(entity_name)
            if self.labels.get(entity_id):
                label_type_set = set()
                for label in self.labels[entity_id]:
                    if not label.get('label_type'):
                        continue
                    doc['_' + label['label_type'] + '_label_s'] = label['label_value']
                    label_type_set.add(label['label_type'])
                doc['label_set_ss'] = label_type_set
            if self.relations['entity_name'].get(entity_id):
                doc['relation_set_ss'] = self.relations['entity_name'].get(entity_id,[])
                doc['relation_set_id_ss'] = self.relations['entity_id'].get(entity_id,[])
            if self.standard_relations['from'].get(entity_id) or self.standard_relations['to'].get(entity_id):  # 构建关系字段
                standard_relation = []
                relation_conf = {}
                if self.entity_conf.get(entity_type) and self.entity_conf[entity_type].get('relation'):
                    relation_conf = self.entity_conf[entity_type].get('relation')
                for row in self.standard_relations['from'].get(entity_id, []):  # 加载from关系
                    relation_obj = dict()
                    relation_obj['id'] = row['to_id']
                    relation_obj['name'] = row['to_name']
                    relation_obj['entity_type'] = self.standard_type_dict['entity_type'].get(row['to_type'], '')
                    relation_type_name = self.standard_type_dict['relation_type'].get(row['relation_id'], '')
                    relation_type_name = '-'.join([self.standard_type_dict['entity_type'].get(entity_type_id, ''), relation_obj['entity_type'], relation_type_name])
                    relation_obj['relation_type'] = relation_type_name
                    relation_field = self.relation_db2field.get(row['relation_id'], '')  # 设置关系字段
                    if relation_field and relation_conf.get(relation_field):
                        entity_ids = doc.setdefault(relation_field + relation_conf[relation_field]['type'], [])
                        if row.get('to_is_standard', 0) == 1:
                            entity_ids.append(row['to_id'])
                    if self.relation_attributes.get(row['r_id']):  # 增加关系属性
                        relation_attributes = []
                        relation_attribute_dict = {}
                        for index, attribute_row in enumerate(self.relation_attributes.get(row['r_id'])):
                            relation_attribute = {}
                            if attribute_row['attribute_type'] in relation_attribute_dict.keys():
                                relation_attribute = relation_attributes[relation_attribute_dict.get(attribute_row['attribute_type'])]
                                relation_attribute['value'].append(attribute_row['attribute_value'])
                            else:
                                relation_attribute['name'] = attribute_row['attribute_name']
                                relation_attribute['value'] = [attribute_row['attribute_value']]
                                relation_attribute_dict[attribute_row['attribute_type']] = len(relation_attributes)
                                relation_attributes.append(relation_attribute)
                        relation_obj['attributes'] = relation_attributes
                    standard_relation.append(relation_obj)
                    if row['relation_score']:
                        doc[row['to_id'] + '_relation_score_f'] = row['relation_score']
                for row in self.standard_relations['to'].get(entity_id, []):  # 加载to关系
                    relation_obj = dict()
                    relation_obj['id'] = row['from_id']
                    relation_obj['name'] = row['from_name']
                    relation_obj['entity_type'] = self.standard_type_dict['entity_type'].get(row['from_type'], '')
                    relation_type_name = self.standard_type_dict['relation_type'].get(row['relation_id'], '')
                    relation_type_name = '-'.join([relation_obj['entity_type'], self.standard_type_dict['entity_type'].get(entity_type_id, ''), relation_type_name])
                    relation_obj['relation_type'] = relation_type_name
                    relation_field = self.relation_db2field.get(row['relation_id'], '')  # 设置关系字段
                    if relation_field and relation_conf.get(relation_field):
                        entity_ids = doc.setdefault(relation_field + relation_conf[relation_field]['type'], [])
                        if row.get('from_is_standard', 0) == 1:
                            entity_ids.append(row['from_id'])
                    if self.relation_attributes.get(row['r_id']):  # 增加关系属性
                        relation_attributes = []
                        relation_attribute_dict = {}
                        for index, attribute_row in enumerate(self.relation_attributes.get(row['r_id'])):
                            relation_attribute = {}
                            if attribute_row['attribute_type'] in relation_attribute_dict.keys():
                                relation_attribute = relation_attributes[relation_attribute_dict.get(attribute_row['attribute_type'])]
                                relation_attribute['value'].append(attribute_row['attribute_value'])
                            else:
                                relation_attribute['name'] = attribute_row['attribute_name']
                                relation_attribute['value'] = [attribute_row['attribute_value']]
                                relation_attribute_dict[attribute_row['attribute_type']] = len(relation_attributes)
                                relation_attributes.append(relation_attribute)
                        relation_obj['attributes'] = relation_attributes
                    standard_relation.append(relation_obj)
                    if row['relation_score']:
                        doc[row['from_id'] + '_relation_score_f'] = row['relation_score']
                standard_relation_type = []
                relation_type_dict = {}
                for relation_obj in standard_relation:
                    relation_name = relation_obj.pop('relation_type')
                    relation_type = {}
                    if relation_name in relation_type_dict.keys():
                        relation_type = standard_relation_type[relation_type_dict.get(relation_name)]
                        relation_type['value'].append(relation_obj)
                    else:
                        relation_type['name'] = relation_name
                        relation_type['value'] = [relation_obj]
                        relation_type_dict[relation_name] = len(standard_relation_type)
                        standard_relation_type.append(relation_type)
                if optional_conf.get('relations'):
                    doc['relations' + optional_conf['relations']['type']] = json.dumps(standard_relation_type, ensure_ascii=False)  # 设置关系集合
            doc['name_code_s'] = pinyin.get_pinyin(
                entity_name, mode='first', errors='default')
            doc['name_length_i'] = max((20-len(doc['name_s'])),1)
            doc['name_py_s'] = pinyin.get_pinyin(
                entity_name, mode='full', errors='default')
            processed_docs.append(doc)
            # print(doc)
        return processed_docs

if __name__ == "__main__":
    indexer = IndexEntity(global_conf, dev=True)
    indexer.index()
