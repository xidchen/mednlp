#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_service.py -- the service of diagnose

Author: maogy <maogy@guahao.com>
Create on 2017-07-10 Monday.
"""

import json
import time
from mednlp.cdss.suggest import DiagnoseSuggest
from mednlp.kg.inspection import Inspection
from mednlp.text.neg_filter import filter_negative
from mednlp.utils.file_operation import get_disease_advice
from mednlp.utils.file_operation import get_disease_advice_code
from mednlp.utils.file_operation import get_disease_dept
from mednlp.utils.file_operation import get_disease_code_conversion
from ailib.client.ai_service_client import AIServiceClient
import global_conf


class DiagnoseServiceControl(object):

    def __init__(self):
        super(DiagnoseServiceControl, self).__init__()

    disease_advice = get_disease_advice()
    disease_advice_code = get_disease_advice_code()
    disease_department = get_disease_dept()
    disease_code_conversion = get_disease_code_conversion()
    suggest_dict = {
        'suggest_past_history_disease': [
            '高血压', '糖尿病', '冠心病', '脑血管病', '肺结核', '慢性肝病',
            '肾病', '肿瘤'],
        'suggest_past_history_operation': [
            '脑外伤', '心脏冠心搭桥术', 'PCI术', '器官切除', '器官移植'],
        'suggest_past_history_other': [
            '输血史', '疫苗接种史'],
        'suggest_person_history_medicine': [
            '阿司匹林', '法华林', '波立维', '糖皮质激素', '抗心律失常药物',
            '精神疾病药物', '非甾体抗炎药'],
        'suggest_person_history_hobby': ['吸烟', '嗜酒'],
        'suggest_family_history': [
            '糖尿病', '高血压', '冠心病', '脑卒中', '大肠癌', '癫痫', '肠息肉']}
    suggest_filter_field = {
        'suggest_symptom': ['chief_complaint', 'medical_history'],
        'suggest_past_history_disease': ['chief_complaint', 'medical_history',
                                         'past_medical_history'],
        'suggest_past_history_operation': ['chief_complaint', 'medical_history',
                                           'past_medical_history'],
        'suggest_past_history_other': ['chief_complaint', 'medical_history',
                                       'past_medical_history'],
        'suggest_person_history_medicine': ['chief_complaint',
                                            'medical_history',
                                            'personal_history'],
        'suggest_person_history_hobby': ['chief_complaint', 'medical_history',
                                         'personal_history'],
        'suggest_family_history': ['chief_complaint', 'medical_history',
                                   'family_history'],
        'suggest_physical_examination': ['chief_complaint', 'medical_history',
                                         'physical_examination'],
        'suggest_inspection': ['chief_complaint', 'medical_history',
                               'general_info']
    }
    for field, names in suggest_dict.items():
        suggest_dict[field] = []
        for name in names:
            suggest_dict[field].append({'entity_name': name})

    def control(self,query):
        start_time = time.time()

        #post json参数
        suggest_input={};dialogue={}
        print(1)

        print(2)
        # query_str = self.request.body
        # query = json.loads(query_str, encoding='utf-8')
        source=query.get('source','')
        chief_complaint=query.get('chief_complaint','')
        medical_history=query.get('medical_history','')
        past_medical_history=query.get('past_medical_history','')
        inspection=query.get('inspection','')
        physical_examination=query.get('physical_examination','')
        department=query.get('department','')
        sex=query.get('sex','-1')
        age=query.get('age','0')
        #问诊参数
        suggest_input=query.get('suggest_input',{})
        dialogue=query.get('dialogue',{})

        dialogue_suggest=AIServiceClient(global_conf.cfg_path,'AIService',port=12453)
        result={}
        result['data']=dialogue_suggest.query(json.dumps(query, indent=True),'diagnose_suggest',method='post')
        return result
    #post json参数

        sex = sex if sex in ['1', '2'] else '-1'
        try:
            age = str(int(float(age) / 365 + 1)) if float(age) > 0 else '0'
        except ValueError:
            age = '0'
        if medical_history:
            chief_complaint += '..' + medical_history
        if inspection and inspection != 'None':
            inspection = '检查检验：' + inspection
        if physical_examination and physical_examination != 'None':
            physical_examination = '体格检查：' + physical_examination
        chief_complaint = filter_negative(chief_complaint)
        past_medical_history = filter_negative(past_medical_history)
        physical_examination = filter_negative(physical_examination)
        medical_record = {'source': source,
                          'chief_complaint': chief_complaint,
                          'medical_history': medical_history,
                          'past_medical_history': past_medical_history,
                          'inspection': inspection,
                          'physical_examination': physical_examination,
                          'department': department,
                          'sex': sex, 'age': age}

        fl = self.get_argument('fl', 'entity_id,entity_name')
        fl_set = set(fl.split(','))
        fl_set.update(['entity_id', 'entity_name'])
        fl = ','.join(fl_set)
        disease_set_code = self.get_argument('disease_set', '')
        disease_set_code = disease_set_code if disease_set_code in ['1'] else ''
        start = self.get_argument('start', '0')
        try:
            start = int(start) if start else 0
        except ValueError:
            start = 0
        rows = self.get_argument('rows', '10')
        try:
            rows = int(rows) if rows else 10
        except ValueError:
            rows = 10
        confidence_mode = self.get_argument('mode', '0')
        threshold = 0.4 if confidence_mode == '1' else 0

        disease_pop, match_symptom, api_code = ad.diagnose(
            medical_record, rows=rows)
        critical_disease = ad.critical_disease_diagnose()
        if disease_pop and disease_pop[0].get('score', 0) < threshold:
            disease_pop = []
        total_count = len(disease_pop)
        disease_pop_org = disease_pop
        disease_pop = disease_pop[start: start + rows]
        disease_set = set()
        disease_dict = {}
        for disease in disease_pop:
            disease_set.add(disease['disease_id'])
            disease_dict[disease['disease_id']] = None
        for disease in critical_disease:
            disease_set.add(disease['entity_id'])
            disease_dict[disease['entity_id']] = disease['entity_name']
        fl = fl.replace('physical_examination', 'physical_examination_detail')
        fl = fl.replace('inspection', 'inspection_json')
        fl_extra = ['physical_examination_detail', 'inspection_json',
                    'symptom_detail']
        fl_inner = fl + ',' + ','.join(fl_extra)
        # disease_dict, docs, _ = kg.find_disease(disease_set, fl=fl_inner, rows=rows, start=start)
        disease_dict, docs, _ = kg.find_disease(disease_dict, fl=fl_inner, rows=rows, start=start)

        result = {'data': disease_pop}
        if api_code:
            result['code'] = 2
        if disease_pop == [] and (
                confidence_mode == '1' or chief_complaint != ''):
            result.update({'totalCount': 0, 'extend_data': {},
                           'q_time': int((time.time() - start_time) * 1000)})
            return result

        if not disease_pop_org:
            total_count = 590
            for doc in docs[0: rows]:
                doc['disease_id'] = doc['entity_id']
                doc['disease_name'] = doc['entity_name']
                disease_pop.append(doc)
        suggest_disease = disease_pop_org
        if not suggest_disease:
            suggest_disease = docs[0: 5]
        suggest = DiagnoseSuggest(suggest_disease, kg=kg)
        extend_data = {
            'suggest_symptom': suggest.symptom_suggest(),
            'suggest_inspection': suggest.inspection_suggest(),
            'suggest_physical_examination':
                suggest.physical_examination_suggest()}
        delete_list = []
        for disease in disease_pop:
            self.update_disease(disease, disease_dict, fl, delete_list,
                                self.disease_advice, self.disease_advice_code,
                                self.disease_department,
                                self.disease_code_conversion, disease_set_code)
        for disease in delete_list:
            disease_pop.remove(disease)
        delete_list = []
        for disease in critical_disease:
            self.update_disease(disease, disease_dict, fl, delete_list,
                                self.disease_advice, self.disease_advice_code,
                                self.disease_department,
                                self.disease_code_conversion, disease_set_code)
        for disease in delete_list:
            critical_disease.remove(disease)
        extend_data.update({'match_symptom': match_symptom,
                            'critical_disease': critical_disease})
        extend_data.update(self.suggest_dict)
        for result_field, fields in self.suggest_filter_field.items():
            for field in fields:
                extend_data[result_field] = self._exist_entity_filter(
                    self.get_argument(field, None),
                    extend_data.get(result_field, []))
        result.update({'totalCount': total_count,
                       'extend_data': extend_data,
                       'q_time': int((time.time() - start_time) * 1000)})
        return result

    def update_disease(self, disease, disease_dict, fl, delete_list,
                       disease_advice, disease_advice_code, disease_department,
                       disease_code_conversion, disease_set_code):
        disease_id = disease.get('disease_id')
        if not disease_id:
            disease_id = disease['entity_id']
            disease['disease_id'] = disease_id
        disease_detail = disease_dict.get(disease_id)
        if disease_detail:
            disease_name = disease_detail.get('entity_name')
            if disease_name:
                disease['disease_name'] = disease_name
            disease.update(disease_detail)
            if 'advice' in fl and disease_name in disease_advice:
                disease['advice'] = disease_advice[disease_name]
                disease['advice_code'] = disease_advice_code[disease_name]
            if 'advice_code' in fl and disease_name in disease_advice_code:
                disease['advice'] = disease_advice[disease_name]
                disease['advice_code'] = disease_advice_code[disease_name]
            if 'department' in fl and disease_name in disease_department:
                disease['department'] = disease_department[disease_name]
        if 'symptom_detail' not in fl:
            disease.pop('symptom_detail', None)
        physical_examination_detail = disease.pop(
            'physical_examination_detail', None)
        if physical_examination_detail and 'physical_examination' in fl:
            physical_examinations = disease.setdefault(
                'physical_examination', [])
            for detail in physical_examination_detail:
                detail_list = detail.split('|')
                if len(detail_list) < 2:
                    continue
                entity_id, entity_name = detail_list[0], detail_list[1]
                physical_examinations.append({'entity_id': entity_id,
                                              'entity_name': entity_name})
        inspection_detail = disease.pop('inspection_json', None)
        if inspection_detail and 'inspection' in fl:
            inspection_detail = json.loads(inspection_detail)
            i_builder = Inspection()
            for detail in inspection_detail:
                detail.update(i_builder.build_entity(detail))
            disease['inspection'] = inspection_detail
        if disease_set_code:
            if disease_set_code == '1':
                d_ins_id, d_ins_code, d_ins_name = disease_code_conversion
                if not d_ins_id.get(disease_id):
                    delete_list.append(disease)
                    return
                disease['disease_id'] = d_ins_id[disease_id]
                disease['disease_name'] = d_ins_name[disease_id]
                if 'disease_code' in fl:
                    disease['disease_code'] = d_ins_code[disease_id]
        return

    def _exist_entity_filter(self, content, entities):
        """
        已经存在的实体过滤.
        参数:
        content->已有文本.
        entities->原始实体,结构:[{'entity_id':,'entity_name':},]
        """
        if not content:
            return entities
        filtered_entities = []
        for entity in entities:
            if entity['entity_name'] not in content:
                filtered_entities.append(entity)
        return filtered_entities


if __name__ == '__main__':
    aa= DiagnoseServiceControl()
    query={
        "chief_complaint":"主诉",
        "medical_history":"现病史",
        "suggest_input":{
            "main_symptom":"朱症状"
        },
        "dialogue":{
            "step":1
        }
    }
    result=aa.control(query)
    print(result)
