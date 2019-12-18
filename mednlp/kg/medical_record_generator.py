#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-05-27 Monday
@Desc:	病例辅助书写接口
"""

import re
import sys
import json
import traceback
import collections
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.storage.db import DBWrapper
from mednlp.utils.utils import trans_to_digit
from mednlp.kg.db_conf import entity_type_dict, entity_label_dict
from mednlp.cdss.aid_diagnose import AidDiagnose
from mednlp.text.neg_filter import filter_negative
from mednlp.cdss.diagnose_range import merge_diagnose_range
from mednlp.utils.file_operation import get_disease_name
from mednlp.utils.file_operation import get_disease_advice


class MedicalRecordGenerator():
    def __init__(self):
        self.ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.ai_diagnose = AidDiagnose()
        self.liquor_id_dict = {'白酒': 1, '啤酒': 2, '红酒': 3, '黄酒': 4, '洋酒': 5, '其他': 99}
        self.db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')
        self.disease_id_name_dict = get_disease_name()
        self.disease_advice = get_disease_advice()
        self.load_kg_data()

    def load_kg_data(self):
        '加载知识图谱中的数据'
        self.common_data = {}
        # 既往史
        common_pmhs = self._get_by_type(entity_label_dict['past_medical_history'])
        self.common_data['past_medical_history'] = [
            {'entity_name': row['entity_name'], 'entity_id': row['entity_uuid']} for row in common_pmhs]
        # 家族史
        common_fh = self._get_by_type(entity_label_dict['family_history'])
        self.common_data['family_history'] = [
            {'entity_name': row['entity_name'], 'entity_id': row['entity_uuid']} for row in common_fh]
        # 手术外伤史
        common_sth = self._get_by_type(entity_label_dict['surgical_history']) + self._get_by_type(entity_label_dict['trauma_history'])
        self.common_data['surgical_trauma_history'] = [
            {'entity_name': row['entity_name'], 'entity_id': row['entity_uuid']} for row in common_sth]
        self.surgical_trauma_data = {row['entity_name']: row['entity_uuid'] for row in common_sth}

        common_allergy = self._get_by_type(entity_label_dict['allergy_history'])
        self.common_data['allergy_history'] = []
        self.allergy_data = {}
        for row in common_allergy:
            if row['label_value'].startswith("1"):
                _type = "medicine"
            elif row['label_value'].startswith("2"):
                _type = "food"
            else:
                _type = "contactant"

            _entity_id = row.get('label_value', row['entity_uuid'])
            self.common_data['allergy_history'].append({'entity_name': row['entity_name'],
                                                        'entity_id': _entity_id,
                                                        'type': _type})

            self.allergy_data[row['entity_name']] = [_entity_id, _type]

    def _get_by_type(self, label_type):
        sql = """
            SELECT e.entity_name, e.entity_uuid, el.label_value
            FROM `ai_union`.`entity_label` el
            JOIN `ai_union`.`entity` e ON e.entity_uuid = el.entity_uuid
            WHERE el.label_type = '{}' AND el.is_deleted = 0
        """.format(label_type)
        rows = self.db.get_rows(sql)
        return rows

    def get_consult_message(self, arguments):
        params = {"patientUserId": arguments.get('patient_user_id'),
                  "patientId": arguments.get('patient_id'),
                  "doctorUserId": arguments.get('doctor_user_id'),
                  "orderInfoId": arguments.get('order_info_id')}
        response = self.ai_client.query(json.dumps(params, ensure_ascii=False), 'get_consult_content')
        if response.get('code') == '0':
            data = json.loads(response.get('data'))
            return data.get('messages', [])
        else:
            print('get consult content error error_id:{} error_message{}'
                  .format(response.get('code'), response.get('message')))
            return []

    def disease_label_conversion(self,
                                 disease_set: str,
                                 disease_name: str,
                                 disease_id: str) -> tuple:
        """
        疾病根据业务标签进行流转
        :param disease_set: 流转的标签值，0 ICD10(协和版), 1 杭州医保, 2 国家临床版V2.0疾病库
        :param disease_id: 疾病ID
        :param disease_name 疾病名称
        :return: 对应标签值下的疾病名称
        """
        converted_name = ''
        converted_id = ''

        # 根据disease_set的值切换不同的疾病库
        if disease_set == 1:  # 杭州医保
            target_label = 'F7ETJ8Go'
        elif disease_set == 2:  # 国家临床版V2.0疾病库
            target_label = 'pzmrT2hM'
        else:  # 未指定切换版本，默认使用ICD10（协和版-1.0老的疾病库）
            target_label = ''

        # 根据目标标签值切换不同的疾病库
        if target_label:
            query = dict()
            query['ef'] = ["id", "name", "type", "source_label_value",
                           "target_label_value", "standard_name",
                           "alias", "disease_id"]
            query['name'] = [disease_name]
            query['type'] = 'disease'
            query['target_label'] = target_label
            query_return = self.ai_client.query(json.dumps(query), 'label_conversion')
            target_entities_list = query_return.get('data', {}).get('entity', [])
            if target_entities_list:
                target_name = target_entities_list[0].get('name', '')
                target_alias_list = target_entities_list[0].get('alias', [])
                target_disease_id = target_entities_list[0].get('disease_id', '')
                target_entity_id = target_entities_list[0].get('id', '')
                if target_name == disease_name:  # 完全匹配
                    converted_id = target_disease_id if target_disease_id else target_entity_id
                    converted_name = disease_name
                elif disease_name in target_alias_list:  # 别名匹配
                    converted_id = target_disease_id if target_disease_id else target_entity_id
                    converted_name = target_name
                else:  # 未匹配到别名
                    converted_name = converted_id = ''

        # 返回结果
        return converted_id, converted_name

    def get_diagnose_info(self, arguments):
        age = arguments.get('age', 0)
        sex = arguments.get('sex', -1)
        chief_complaint = arguments.get('chief_complaint', '')
        medical_history = arguments.get('medical_history', '')
        past_medical_history = arguments.get('past_medical_history', '')
        inspection = arguments.get('general_info', '')
        physical_examination = arguments.get('physical_examination', '')
        body_temperature = arguments.get('body_temperature', '')
        systolic_blood_pressure = arguments.get('systolic_blood_pressure', '')
        diastolic_blood_pressure = arguments.get('diastolic_blood_pressure', '')
        disease_set = arguments.get('disease_set', 0)

        try:
            age = str(int(float(age) / 365 + 1)) if float(age) > 0 else '0'
        except ValueError:
            age = '0'
        sex = str(sex) if sex in ['1', '2', 1, 2, -1] else '-1'
        chief_complaint = filter_negative(chief_complaint)
        past_medical_history = filter_negative(past_medical_history)
        inspection = inspection if inspection != 'None' else ''
        physical_examination = physical_examination if physical_examination != 'None' else ''
        if medical_history:
            chief_complaint += '..' + medical_history

        parameters = {
            'source': arguments.get('source', ''),
            'chief_complaint': chief_complaint,
            'medical_history': medical_history,
            'past_medical_history': past_medical_history,
            'inspection': inspection,
            'physical_examination': physical_examination,
            'department': arguments.get('department', ''),
            'sex': sex, 'age': age
        }
        # 若无主诉、现病史等信息，返回空
        if not parameters.get('chief_complaint') and not parameters.get('medical_history'):
            return [], []
        diagnose_data, _, _ = self.ai_diagnose.diagnose(parameters)

        try:
            diagnose_data = merge_diagnose_range(diagnose_data)
        except Exception as e:
            print('diagnose range Error!')
            print(traceback.format_exc())

        diagnose_result = []
        for disease in diagnose_data:
            _id = disease.get('disease_id')
            score = disease.get('score', 0)
            name = self.disease_id_name_dict.get(_id)
            if name:
                disease_res = {'disease_type': 2,
                               'score': score,
                               'accuracy': score}
                # 根据指定的疾病标签（如杭州医保）获取对应的疾病名称(获取参数中disease_set的值)
                if disease_set:
                    converted_id, converted_name = self.disease_label_conversion(disease_set, name, _id)
                    if converted_id and converted_name:
                        disease_res['disease_id'] = converted_id
                        disease_res['disease_name'] = converted_name
                        diagnose_result.append(disease_res)
                else:
                    disease_res['disease_id'] = _id
                    disease_res['disease_name'] = name
                    diagnose_result.append(disease_res)

            total_diagnose_result = len(diagnose_result)
            if total_diagnose_result >= 5:
                break

        disease_lable = arguments.get('disease_lable')
        if disease_lable:
            diagnose_result = self.tran_disease_name(diagnose_result, disease_lable)

        
        advices = []
        for disease in diagnose_result:
            name = disease['disease_name']
            advice = self.disease_advice.get(name)
            if advice and advice not in advices:
                advices.append(advice)

        return diagnose_result, advices

    def tran_disease_name(self, diagnose_data, disease_lable):
        disease_ls = [x.get('disease_name') for x in diagnose_data]
        # 获取原始的id,按照id排序
        params = {"name": disease_ls, "ef": ["id", "name", "standard_name"], "type": ["disease"]}
        entity_result = self.ai_client.query(json.dumps(params, ensure_ascii=False), 'entity_service')
        entity = entity_result.get('data', {}).get('entity', {})
        name_dict = {}
        for x in entity:
            name_dict[x.get('name')] = x.get('standard_name')

        params = {'name': disease_ls, 'ef': ['id', 'disease_id', 'name', 'type', 'standard_name'],
                  'label': disease_lable, 'label_field': disease_lable,
                  'rows': len(disease_lable) * len(disease_ls), 'match_alias': 1}

        entity_result = self.ai_client.query(json.dumps(params, ensure_ascii=False), 'entity_service')
        entity = entity_result.get('data', {}).get('entity', {})
        target_name_dict = {}
        for e in entity:
            if e.get('standard_name') in target_name_dict:
                if e.get('name') in disease_ls:
                    target_name_dict[e.get('standard_name')] = e
            else:
                target_name_dict[e.get('standard_name')] = e

        res = []
        for d in diagnose_data:
            standard_name = name_dict.get(d.get('disease_name'))
            if not standard_name:
                standard_name = d.get('disease_name')
            e = target_name_dict.get(standard_name)
            if not e:
                continue
            if not e.get('label'):
                continue
            _id = e.get('disease_id')
            if _id is None:
                _id = e.get('id')
            res.append({'disease_id': _id, 'disease_name': standard_name,
                        'disease_type': 2, 'score': d.get('score'), 'accuracy': d.get('accuracy'),
                        'label_value': e.get('label')})
        return res

    def add_common_values(self, entities):
        # 合并常见既往史
        entities = self._add_common_value(entities, 'past_medical_history')
        entities = self._add_common_value(entities, 'family_history')
        entities = self._add_common_value(entities, 'surgical_trauma_history')
        entities = self._add_common_value(entities, 'allergy_history')
        return entities

    def _add_common_value(self, entities, entity_type):
        entity_set = ([entity['entity_name'] for entity in entities[entity_type]])
        for common_entity in self.common_data[entity_type]:
            if common_entity not in entity_set:
                entity = {'content': '', 'entity_name': '', 'entity_id': '', 'time_endurance': '',
                          'type': '', 'relate_symptom': '', 'remark': '', 'time_happen': '',
                          'data_source': 2, 'status': 0, 'family_relation': ''}
                entity['entity_name'] = common_entity['entity_name']
                entity['entity_id'] = common_entity['entity_id']
                entity['content'] = common_entity['entity_name']
                entity['type'] = common_entity.get('type', '')
                entities[entity_type].append(entity)
        return entities

    def insert_deny_entity(self, entities):
        entity = {'content': '否认重大疾病', 'entity_name': '否认重大疾病', 'entity_id': '-1',
                  'time_endurance': '', 'type': '', 'relate_symptom': '', 'remark': '',
                  'time_happen': '', 'data_source': 2, 'status': 0, 'family_relation': ''}
        entities['past_medical_history'].insert(0, entity)

        entity = {'content': '否认家族遗传病史',
                  'entity_name': '否认家族遗传病史', 'entity_id': '-1', 'time_endurance': '',
                  'type': '', 'relate_symptom': '', 'remark': '', 'time_happen': '',
                  'data_source': 2, 'status': 0, 'family_relation': ''}
        entities['family_history'].insert(0, entity)

        entity = {'content': '否认手术外伤史', 'entity_name': '否认手术外伤史', 'entity_id': '-1',
                  'time_endurance': '', 'type': '', 'relate_symptom': '', 'remark': '',
                  'time_happen': '', 'data_source': 2, 'status': 0, 'family_relation': ''}
        entities['surgical_trauma_history'].insert(0, entity)

        entity = {'content': '未发现', 'entity_name': '未发现', 'entity_id': '-1',
                  'time_endurance': '', 'type': '', 'relate_symptom': '', 'remark': '',
                  'time_happen': '', 'data_source': 2, 'status': 0, 'family_relation': ''}
        entities['allergy_history'].insert(0, entity)

        return entities

    def get_suggest(self, arguments):
        dialogue = arguments.get('dialogue')
        records = self.get_medical_record(dialogue)
        entities = self.format_medical_record(records)
        entities = self.add_common_values(entities)
        entities = self.insert_deny_entity(entities)

        res = {}
        # 格式化字典并去重，忽略家族史（家族史中存在高血压史不同亲属，不易区分)
        for key in ('chief_complaint', 'medical_history', 'allergy_history', 'past_medical_history',
                    'surgical_trauma_history', 'family_history', 'treatment_advice'):
            _entities = []
            added_entity_set = set()
            for item in entities.get(key, []):
                # 去除已选实体
                if item['entity_name'] in arguments.get(key):
                    continue
                # 去除重复
                if item['entity_name'] not in added_entity_set:
                    added_entity_set.add(item['entity_name'])
                    _entities.append(item)
            res[key] = {'text': arguments.get(key), 'entities': _entities}
        res['personal_history'] = {'text': arguments.get('personal_history'),
                                   'entities': entities.get('personal_history', [])}
        return res

    def get_medical_record(self, dialogue):
        " 获取结构化病历 "
        # 现阶段只用用户对话内容
        request_data = "。".join([item[1].strip().replace('\n', '。') for item in dialogue if item and item[0] == '0'])
        if not request_data:
            return []
        response = self.ai_client.query(json.dumps({'source': '1', 'medical_history': request_data},
                                                               ensure_ascii=False), 'medical_record')
        if response['code'] != 0:
            raise ValueError
        return response['data']['medical_history']

    def format_medical_record(self, records):
        chief_complaint = []
        allergy_history = []
        disease_history = []
        surgical_trauma_history = []
        personal_history = []
        family_history = []

        for record in records:
            is_deny = False
            is_person_negative = False
            for prop in record.get('property', []):
                if prop.get('type') == 'status' and prop.get('value') == '无':
                    is_deny = True
            if is_deny:
                if '烟' in record.get('name') or '酒' in record.get('name'):
                    is_person_negative = True
                else:
                    continue

            entity = {'content': '', 'entity_name': '', 'entity_id': '', 'time_endurance': '',
                      'type': '', 'relate_symptom': '', 'remark': '', 'time_happen': '',
                      'data_source': 1, 'status': 0, 'family_relation': ''}

            prop_dict = {'time_endurance': '', 'immediate_family': [], 'allergen': '', 'time_happen': ''}
            for prop in record.get('property', []):
                t = prop.get('type')
                if t in prop_dict.keys():
                    if isinstance(prop_dict[t], list):
                        prop_dict[t].append(prop.get('text'))
                    else:
                        p = re.compile(r'([零一二三四五六七八九十百千万]+)([^几多来])')
                        text = prop.get('text')
                        text = p.sub(lambda m: str(trans_to_digit(m.group(1))) + m.group(2), text)
                        text = text.replace('两', '2')
                        prop_dict[t] = text

            record_name = record.get('name')
            record_type = record.get('type')
            entity['entity_id'] = record.get('uuid', '')
            entity['type'] = record.get('type', '')
            # 症状：主诉、现病史
            if record_type == 'symptom':
                # 个人既往史
                if '二手烟' in record_name:
                    entity['content'] = '二手烟'
                    entity['entity_name'] = '二手烟'
                    entity['status'] = 4
                    personal_history.append(entity)
                    continue

                if '烟' in record_name:
                    if is_person_negative:
                        entity['content'] = "无吸烟史"
                        entity['entity_name'] = "无吸烟史"
                        entity['status'] = 1
                    else:
                        entity['content'] = '烟龄{}'.format(prop_dict.get('time_endurance'))
                        entity['time_endurance'] = prop_dict.get('time_endurance')
                        entity['entity_name'] = record_name
                        entity['time_endurance'] = prop_dict.get('time_endurance')
                        entity['content'] = "有吸烟史"
                        if entity['time_endurance']:
                            entity['content'] += "，烟龄{}".format(entity['time_endurance'])
                        entity['status'] = 2
                    personal_history.append(entity)
                    continue

                if ('酒' in record_name and '毒' not in record_name):
                    if is_person_negative:
                        entity['content'] = "无饮酒史"
                        entity['entity_name'] = "无饮酒史"
                        entity['status'] = 1
                    else:
                        entity['time_endurance'] = prop_dict.get('time_endurance')
                        entity['entity_name'] = record_name
                        entity['time_endurance'] = prop_dict.get('time_endurance')
                        entity['content'] = "有饮酒史"
                        if entity['time_endurance']:
                            entity['content'] += "，酒龄{}".format(entity['time_endurance'])
                        entity['status'] = 2
                    personal_history.append(entity)
                    continue
                if record_name in self.surgical_trauma_data:
                    entity['content'] = "{}{}".format(prop_dict.get('time_happen'), record_name)
                    entity['entity_name'] = record_name
                    entity['entity_id'] = self.surgical_trauma_data.get(record_name, '')
                    entity['time_happen'] = prop_dict.get('time_happen')
                    surgical_trauma_history.append(entity)
                    continue
                # 疾病史
                if '年' in prop_dict.get('time_endurance') or '年' in prop_dict.get('time_happen'):
                    entity['content'] = '{}{}'.format(record_name, prop_dict.get('time_endurance'))
                    entity['entity_name'] = record_name
                    entity['time_happen'] = prop_dict.get('time_happen')
                    entity['time_endurance'] = prop_dict.get('time_endurance')
                    disease_history.append(entity)
                    continue

                # 主诉现病史
                try:
                    position = int(record.get('position')[0])
                except ValueError:
                    position = sys.maxsize
                entity['content'] = record_name + prop_dict.get('time_endurance')
                entity['entity_name'] = record_name
                entity['time_endurance'] = prop_dict.get('time_endurance')
                chief_complaint.append({'position': position, 'entity': entity})
            elif record.get('type') == 'disease':
                # 家族史
                if prop_dict.get('immediate_family'):
                    immediate_familys = prop_dict.get('immediate_family')
                    i_f = immediate_familys[0]
                    if len(immediate_familys) == 2 and '父亲' in immediate_familys and '母亲' in immediate_familys:
                        i_f = '父母亲'
                    entity['content'] = '{}({})'.format(record_name, i_f)
                    entity['entity_name'] = record_name
                    entity['family_relation'] = i_f
                    family_history.append(entity)
                    continue
                # 过敏史
                if prop_dict.get('allergen'):
                    text = prop_dict.get('allergen')
                    _id_type = self.allergy_data.get(text, [])
                    if _id_type:
                        entity['content'] = text
                        entity['entity_name'] = text
                        entity['entity_id'] = _id_type[0]
                        entity['relate_symptom'] = prop_dict.get('symptom', '')
                        entity['type'] = _id_type[1]
                        allergy_history.append(entity)
                    continue
                # 手术外伤史
                if record_name in self.surgical_trauma_data:
                    entity['content'] = "{}{}".format(prop_dict.get('time_happen'), record_name)
                    entity['entity_name'] = record_name
                    entity['entity_id'] = self.surgical_trauma_data.get(record_name, '')
                    entity['time_happen'] = prop_dict.get('time_happen')
                    surgical_trauma_history.append(entity)
                    continue
                # 疾病史
                if '年' in prop_dict.get('time_endurance') or '年' in prop_dict.get('time_happen'):
                    entity['content'] = '{}{}'.format(record_name, prop_dict.get('time_endurance'))
                    entity['entity_name'] = record_name
                    entity['time_happen'] = prop_dict.get('time_happen')
                    entity['time_endurance'] = prop_dict.get('time_endurance')
                    disease_history.append(entity)
                    continue
                try:
                    position = int(record.get('position')[0])
                except ValueError:
                    position = sys.maxsize
                entity['content'] = record_name + prop_dict.get('time_endurance')
                entity['entity_name'] = record_name
                entity['time_endurance'] = prop_dict.get('time_endurance')
                chief_complaint.append({'position': position, 'entity': entity})
            elif record.get('type') == 'treatment':
                # 手术外伤史
                if '术' in record_name:
                    entity['content'] = "{}{}".format(prop_dict.get('time_happen'), record_name)
                    entity['entity_name'] = record_name
                    entity['time_happen'] = prop_dict.get('time_happen')
                    surgical_trauma_history.append(entity)
                    continue
                if '烟' in record_name:
                    entity['content'] = "{}{}".format(record_name, prop_dict.get('time_endurance'))
                    entity['entity_name'] = record_name
                    entity['time_endurance'] = prop_dict.get('time_endurance')
                    entity['status'] = 3
                    personal_history.append(entity)
                    continue
                if ('酒' in record_name and '毒' not in record_name):
                    entity['content'] = "{}{}".format(record_name, prop_dict.get('time_endurance'))
                    entity['entity_name'] = record_name
                    entity['time_endurance'] = prop_dict.get('time_endurance')
                    entity['status'] = 3
                    personal_history.append(entity)
                    continue

        res = {}
        chief_complaint.sort(key=lambda item: item['position'])
        chief_complaint = [item['entity'] for item in chief_complaint]

        chief_complaint = self.remove_same_entity(chief_complaint)
        res['chief_complaint'] = chief_complaint
        res['medical_history'] = chief_complaint
        res['allergy_history'] = self.remove_same_entity(allergy_history)
        res['past_medical_history'] = self.remove_same_entity(disease_history)
        res['surgical_trauma_history'] = self.remove_same_entity(surgical_trauma_history)
        res['family_history'] = self.remove_same_entity(family_history)

        personal_history_set = {'烟': None, '酒': None}
        for entity in personal_history:
            if '烟' in entity['entity_name']:
                personal_history_set['烟'] = entity
            if '酒' in entity['entity_name']:
                personal_history_set['酒'] = entity
        res['personal_history'] = [entity for entity in personal_history_set.values() if entity is not None]
        return res

    def remove_same_entity(self, entities):
        entity_order_dict = collections.OrderedDict()
        for entity in entities:
            entity_order_dict[entity['entity_name']] = entity
        return list(entity_order_dict.values())


if __name__ == '__main__':
    environment = open(global_conf.cfg_path, 'r').readlines()
    model_ = MedicalRecordGenerator()
    advices = [{"disease_name":"高血压", "score":0.5, "accuracy":0.22},{"disease_name":"心脏病","score":0.2, "accuracy":0.72}]
    arguments = {"disease_lable": ['pkCizO3q']}
    res = model_.tran_disease_name(advices, arguments)
    print(res)
