#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_service.py -- the service of diagnosis

Author: chenxd
Create on 2017-07-10 Monday
"""

# import copy
import json
import time
import tornado.web
import traceback
import global_conf
import ailib.service.base_service as base_service
from tornado.options import define, options
from ailib.client.ai_service_client import AIServiceClient
from mednlp.cdss.aid_diagnose import AidDiagnose, RuleDiagnose
from mednlp.cdss.diagnose_range import merge_diagnose_range
from mednlp.cdss.medical_record_backfill import BackFillTemplate
# from mednlp.cdss.suggest import DiagnoseSuggest
from mednlp.dao.kg_dao import KGDao
from mednlp.kg.clinical_guide_disease import ClinicalGuideDisease
from mednlp.kg.inspection import Inspection
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.text.neg_filter import filter_negative
from mednlp.text.neg_filter import filter_physical_examination_negative
from mednlp.text.value_status_transformer import ValueStatusTransformer
from mednlp.utils.file_operation import get_disease_advice
from mednlp.utils.file_operation import get_disease_advice_code
from mednlp.utils.file_operation import get_disease_dept
from mednlp.utils.file_operation import get_kg_docs


ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')
dr_client = AIServiceClient(global_conf.cfg_path, 'AIService')
highlight_model = ClinicalGuideDisease()
back_fill_template = BackFillTemplate()
rule_diagnose = RuleDiagnose()


class DiagnoseService(BaseRequestHandler):

    disease_advice = get_disease_advice()
    disease_advice_code = get_disease_advice_code()
    disease_department = get_disease_dept()
    kg_docs = get_kg_docs()
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

    default_disease_list = ['44238',
                            '64406562-8643-11e7-b11b-1866da8f1f23',
                            '118786A18629FC4AE0500A0AC86471F9',
                            '6af282f3-31e1-11e6-804e-848f69fd6b70',
                            '1bab728c-31e0-11e6-804e-848f69fd6b70']
    splitter = '|'
    fl_in_mr_field = {
        'symptom_detail': 'chief_complaint',
        'inspection': 'inspection',
        'physical_examination': 'physical_examination'
    }

    def initialize(self, runtime=None, **kwargs):
        super(DiagnoseService, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        start_time = time.time()
        cc_times = [time.time()]

        arguments = {
            'source': '', 'chief_complaint': '', 'medical_history': '',
            'past_medical_history': '', 'general_info': '',
            'physical_examination': '', 'department': '', 'sex': '-1',
            'age': '0', 'body_temperature': '',
            'systolic_blood_pressure': '', 'diastolic_blood_pressure': '',
            'fl': 'entity_id,entity_name,'
                  'symptom_detail,physical_examination,inspection',
            'word_print': '', 'collected_medical_record': '',
            'disease_set': 0, 'start': '0', 'rows': '10', 'mode': '0'
        }
        self.parse_arguments(arguments)

        source = arguments['source']
        chief_complaint = arguments['chief_complaint']
        medical_history = arguments['medical_history']
        past_medical_history = arguments['past_medical_history']
        inspection = arguments['general_info']
        physical_examination = arguments['physical_examination']
        department = arguments['department']
        sex = arguments['sex']
        age = arguments['age']
        body_temperature = arguments['body_temperature']
        systolic_blood_pressure = arguments['systolic_blood_pressure']
        diastolic_blood_pressure = arguments['diastolic_blood_pressure']
        fl = arguments['fl']
        # word_print = arguments['word_print']
        collected_medical_record = arguments['collected_medical_record']
        disease_set_code = arguments['disease_set']
        start = arguments['start']
        rows = arguments['rows']
        confidence_mode = arguments['mode']

        try:
            start = int(start) if start else 0
        except ValueError:
            start = 0
        try:
            rows = int(rows) if rows else 10
            if rows < 0 or rows > 10:
                rows = 10
        except ValueError:
            rows = 10
        threshold = 0.4 if confidence_mode == '1' else 0
        disease_set_code = disease_set_code if disease_set_code in (1, 2) else 0

        if collected_medical_record:
            try:
                collected_mr_json = json.loads(collected_medical_record)
                medical_history = back_fill_template.make_medical_history(collected_mr_json)
            except Exception as e:
                print('make_medical_history error', e)
                print(collected_medical_record)

        sex = str(sex) if sex in ['1', '2', 1, 2, -1] else '-1'
        try:
            age = str(int(float(age) / 365 + 1)) if float(age) > 0 else '0'
        except ValueError:
            age = '0'
        if medical_history:
            chief_complaint += '..' + medical_history
        vst = ValueStatusTransformer()
        if body_temperature:
            body_temperature = vst.body_temperature_transform(body_temperature)
            if body_temperature:
                physical_examination += body_temperature
        if systolic_blood_pressure:
            systolic_blood_pressure = vst.systolic_transform(systolic_blood_pressure)
            if systolic_blood_pressure:
                physical_examination += systolic_blood_pressure
        if diastolic_blood_pressure:
            diastolic_blood_pressure = vst.diastolic_transform(diastolic_blood_pressure)
            if diastolic_blood_pressure:
                physical_examination += diastolic_blood_pressure
        inspection = inspection if inspection != 'None' else ''
        physical_examination = physical_examination if physical_examination != 'None' else ''
        chief_complaint = filter_negative(chief_complaint)
        past_medical_history = filter_negative(past_medical_history)
        inspection = filter_negative(inspection)
        physical_examination = filter_physical_examination_negative(physical_examination)
        medical_record = {'source': source,
                          'chief_complaint': chief_complaint,
                          'medical_history': medical_history,
                          'past_medical_history': past_medical_history,
                          'inspection': inspection,
                          'physical_examination': physical_examination,
                          'department': department,
                          'sex': sex, 'age': age}

        fl_set = set(fl.split(','))
        fl_set.update(['entity_id', 'entity_name'])
        fl = ','.join(fl_set)

        cc_times.append(time.time())
        disease_pop, match_symptom, api_code = ad.diagnose(medical_record)
        # critical_disease = ad.critical_disease_diagnose()
        # disease_pop, match_symptom, api_code, critical_disease = ad.diagnose_all(medical_record)
        cc_times.append(time.time())

        try:
            disease_pop = merge_diagnose_range(disease_pop)
        except Exception as e:
            print('diagnose range Error!', e)
            print(traceback.format_exc())

        # differential_diagnosis_disease = []
        # if collected_medical_record:
        #     try:
        #         optimize_type = 2 if source == '0' else 1
        #         disease_pop, differential_diagnosis_disease = rule_diagnose.optimize_diagnose(
        #             json.loads(collected_medical_record), disease_pop, optimize_type)
        #     except Exception as e:
        #         print('diagnose rule optimization error', e)
        #         print(traceback.format_exc())

        cc_times.append(time.time())
        if disease_pop and disease_pop[0].get('score', 0) < threshold:
            disease_pop = []
        # if disease_pop and disease_pop[0].get('score', 0):
        #
        #     try:
        #         # 请求diagnose_reliability接口获取诊断可靠性
        #         if rows < 5:
        #             update_accuracy_result = dr_client.query(
        #                 json.dumps({'diseases': disease_pop[:5]},
        #                            ensure_ascii=False), 'diagnose_reliability')
        #             if update_accuracy_result['code'] != 0:
        #                 raise ValueError
        #             disease_pop[:5] = update_accuracy_result['data'].get('diseases', [])
        #         else:
        #             update_accuracy_result = dr_client.query(
        #                 json.dumps({'diseases': disease_pop[:rows]},
        #                            ensure_ascii=False), 'diagnose_reliability')
        #             if update_accuracy_result['code'] != 0:
        #                 raise ValueError
        #             disease_pop[:rows] = update_accuracy_result['data'].get('diseases', [])
        #     except (BaseException, RuntimeError):
        #         print('diagnose_reliability_api error!')
        #
        #         confidence, accuracy = [], []
        #         if disease_pop and disease_pop[0].get('score', 0):
        #             for i in range(rows):
        #                 confidence.append(disease_pop[i].get('score', 0))
        #             accuracy = copy.copy(confidence)
        #             if rows > 0:
        #                 accuracy[0] *= 1.2
        #             if rows > 1:
        #                 accuracy[1] *= 1.1
        #             accuracy = [round(x / sum(accuracy), 4) for x in accuracy]
        #             for i in range(rows):
        #                 disease_pop[i]['accuracy'] = accuracy[i]

        cc_times.append(time.time())
        total_count = len(disease_pop)
        disease_pop_org = disease_pop
        disease_pop = disease_pop[start: start + rows]
        disease_set = set()
        disease_dict, docs = {}, []
        if disease_pop_org:
            for disease in disease_pop:
                disease_id = disease['disease_id']
                disease_set.add(disease_id)
                for doc in self.kg_docs:
                    if doc['entity_id'] == disease_id:
                        disease_dict[disease_id] = doc
                        docs.append(doc)
        else:
            docs = [doc for doc in self.kg_docs
                    if doc['entity_id'] in self.default_disease_list]
        # for disease in differential_diagnosis_disease:
        #     disease_set.add(disease['disease_id'])
        #     disease_dict[disease['disease_id']] = None
        # for disease in critical_disease:
        #     disease_set.add(disease['entity_id'])
        #     disease_dict[disease['entity_id']] = disease['entity_name']
        # fl = fl.replace('physical_examination', 'physical_examination_detail')
        # fl = fl.replace('inspection', 'inspection_json')
        # fl_extra = ['physical_examination_detail', 'inspection_json',
        #             'symptom_detail']
        # fl_inner = fl + ',' + ','.join(fl_extra)
        # fl_inner = fl_inner.replace('differential_diagnosis', 'DD')

        # disease_dict, docs, _ = kg.find_disease(
        #     disease_dict, fl=fl_inner, rows=rows, start=start)
        # cc_times.append(time.time())

        result = {'data': disease_pop}
        if api_code:
            result['code'] = 2
        if disease_pop == [] and (
                confidence_mode == '1' or chief_complaint != ''):
            result.update({'totalCount': 0, 'extend_data': {},
                           'q_time': int((time.time() - start_time) * 1000)})
            return result

        if not disease_pop_org:
            # total_count = 590
            for doc in docs[0: rows]:
                doc['disease_id'] = doc['entity_id']
                doc['disease_name'] = doc['entity_name']
                # doc['accuracy'] = 0.0
                doc['score'] = 0.0
                disease_pop.append(doc)
        # suggest_disease = disease_pop_org
        # if not suggest_disease:
        #     suggest_disease = docs[0: 5]
        # suggest = DiagnoseSuggest(suggest_disease)
        # cc_times.append(time.time())
        # extend_data = {
        #     'suggest_symptom': suggest.symptom_suggest(),
        #     'suggest_inspection': suggest.inspection_suggest(),
        #     'suggest_physical_examination':
        #         suggest.physical_examination_suggest()}

        delete_list = []
        for disease in disease_pop:
            self.update_disease(disease, disease_dict, fl, delete_list,
                                self.disease_advice, self.disease_advice_code,
                                self.disease_department, disease_set_code,
                                medical_record)
        for disease in delete_list:
            disease_pop.remove(disease)
        # # 过滤未找到相关疾病名称的疾病
        # disease_pop = [disease for disease in disease_pop if 'disease_name' in disease]
        #
        # delete_list = []
        # for disease in critical_disease:
        #     self.update_disease(disease, disease_dict, fl, delete_list,
        #                         self.disease_advice, self.disease_advice_code,
        #                         self.disease_department, disease_set_code)
        # for disease in delete_list:
        #     critical_disease.remove(disease)
        # # 未查寻到危重症相关信息，过滤该危重症
        # critical_disease = [cd for cd in critical_disease if cd.get('disease_name')]
        #
        # delete_list = []
        # for disease in differential_diagnosis_disease:
        #     self.update_disease(disease, disease_dict, fl, delete_list,
        #                         self.disease_advice, self.disease_advice_code,
        #                         self.disease_department, disease_set_code)
        # differential_diagnosis_disease = rule_diagnose.sort_differential_diagnosis(
        #     differential_diagnosis_disease)
        #
        # trans_disease_name_dict = {}
        # if disease_set_code:
        #     disease_names = [d.get('disease_name', '') for d in disease_pop
        #                      + critical_disease + differential_diagnosis_disease]
        #     trans_disease_name_dict = kg.get_disease_set(disease_names, disease_set_code)
        #     differential_diagnosis_disease = self._update_disease_set_name(
        #         differential_diagnosis_disease, trans_disease_name_dict, fl)
        # extend_data.update({'differential_diagnosis_merge': differential_diagnosis_disease})
        #
        # critical_d_list = []
        # for cd_dict in critical_disease:
        #     critical_d_list.append(cd_dict.get('disease_name', ''))
        #
        # critical_critical_d_str = ','.join(critical_d_list)
        # critical_clinical_data = self._disease_highlight(
        #     medical_record, critical_critical_d_str, word_print)
        # new_critical_disease = self._disease_clinical_guide(
        #     critical_disease, critical_clinical_data, fl)
        #
        # if disease_set_code:
        #     new_critical_disease = self._update_disease_set_name(
        #         new_critical_disease, trans_disease_name_dict, fl)
        # extend_data.update({'match_symptom': match_symptom,
        #                     'critical_disease': new_critical_disease})
        # extend_data.update(self.suggest_dict)
        #
        # for result_field, fields in self.suggest_filter_field.items():
        #     for field in fields:
        #         field_value = arguments.get(field, None)
        #         extend_data[result_field] = self._exist_entity_filter(
        #             field_value, extend_data.get(result_field, []))
        result.update({'totalCount': total_count,
                       # 'extend_data': extend_data,
                       'q_time': int((time.time() - start_time) * 1000)})
        # ## 添加fl开关
        # disease_list = [disease.get('disease_name', '') for disease in disease_pop]
        # disease_str = ','.join(disease_list)
        # cc_times.append(time.time())
        #
        # clinical_highlight_data = self._disease_highlight(
        #     medical_record, disease_str, word_print)
        # new_disease_pop = self._disease_clinical_guide(
        #     disease_pop, clinical_highlight_data, fl)
        #
        # if disease_set_code:
        #     new_disease_pop = self._update_disease_set_name(
        #         new_disease_pop, trans_disease_name_dict, fl)
        # result.update({'data': new_disease_pop})

        cc_times.append(time.time())
        if time.time() - start_time > 2:
            print(medical_record)
            print('zxcv\t' + '\t'.join([str(i) for i in cc_times]))

        return result

    def update_disease(self, disease, disease_dict, fl, delete_list,
                       disease_advice, disease_advice_code, disease_department,
                       disease_set_code, medical_record):
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
        symptom_detail = disease.pop('symptom_detail', None)
        if symptom_detail and 'symptom_detail' in fl:
            disease = self.split_property_detail(
                disease, symptom_detail, 'symptom_detail')
            if 'symptom_detail' in disease:
                disease = self.highlight_key_factor(
                    disease, 'symptom_detail', medical_record)
        physical_examination_detail = disease.pop(
            'physical_examination_detail', None)
        if physical_examination_detail and 'physical_examination' in fl:
            disease = self.split_property_detail(
                disease, physical_examination_detail, 'physical_examination')
            if 'physical_examination' in disease:
                disease = self.highlight_key_factor(
                    disease, 'physical_examination', medical_record)
        inspection_detail = disease.pop('inspection_json', None)
        if inspection_detail and 'inspection' in fl:
            inspection_detail = json.loads(inspection_detail)
            i_builder = Inspection()
            for detail in inspection_detail:
                detail.update(i_builder.build_entity(detail))
            disease['inspection'] = inspection_detail
            if 'inspection' in disease:
                disease = self.highlight_key_factor(
                    disease, 'inspection', medical_record)
        if disease_set_code:
            if disease_set_code == 1:
                query = dict()
                query['ef'] = ['id','name']
                query['name'] = [disease_detail.get('entity_name')]
                query['type'] = ['disease']
                query['source_label'] = 'pkCizO3q'
                query['target_label'] = 'F7ETJ8Go'
                query_return = ai_client.query(json.dumps(query), 'label_flow')
                if query_return and query_return['data']['entity']:
                    converted_id = query_return['data']['entity'][0]['id']
                    converted_name = query_return['data']['entity'][0]['name']
                else:
                    delete_list.append(disease)
                    return
                disease['disease_id'] = disease_id
                disease['disease_name'] = converted_name
                if 'disease_code' in fl:
                    disease['disease_code'] = converted_id
        return

    def split_property_detail(self, disease, property_detail, property_name):
        property_detail_list = disease.setdefault(property_name, [])
        for detail in property_detail:
            detail_list = detail.split(self.splitter)
            if len(detail_list) < 2:
                continue
            entity_id, entity_name = detail_list[0], detail_list[1]
            property_detail_list.append({'entity_id': entity_id,
                                         'entity_name': entity_name})
        return disease

    def highlight_key_factor(self, disease, property_name, medical_record):
        for property_detail in disease[property_name]:
            if property_detail['entity_name'] in medical_record[
                self.fl_in_mr_field[property_name]]:
                property_detail['highlight_mode'] = 1
            else:
                property_detail['highlight_mode'] = 0
        return disease

    def _update_disease_set_name(self, diseases, trans_disease_name_dict, fl):
        """转化为相应疾病名称集合中疾病名字和id"""
        trans_diseases = []
        for disease in diseases:
            if 'disease_name' not in disease:
                continue
            if disease['disease_name'] in trans_disease_name_dict:
                new_name = trans_disease_name_dict[disease['disease_name']]['name']
                new_id = trans_disease_name_dict[disease['disease_name']]['id']
                if new_name:
                    disease['disease_name'] = new_name
                    disease['disease_id'] = new_id
                    disease['entity_name'] = new_name
                    disease['entity_id'] = new_id
                    if '*' in fl or 'disease_code' in fl:
                        disease['disease_code'] = trans_disease_name_dict[
                            disease['disease_name']].get('code', '')
                    trans_diseases.append(disease)
        return trans_diseases

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

    def _disease_highlight(self, medical_record, disease_list, word_print):
        """
        获取临床指南的高亮显示
        :param medical_record:字典，用户输入的数据
        :param disease_list: 字符串（形如：disease1，disease2,,,,）
        :return: 临床指南和诊断依据高亮显示位置
        """
        content_input = medical_record.get('chief_complaint')
        content_highlight_data = highlight_model.get_disease_guide(
            content_input, disease_list, word_print)
        return content_highlight_data

    def _disease_clinical_guide(self, disease_pop, clinical_highlight_data, fl):
        """
        获取疾病对应的指南和高亮显示位置
        :param disease_pop: 预测的疾病列表
        :param clinical_highlight_data: 临床指南和诊断依据高亮显示位置
        :param fl: field_list
        :return:预测疾病列表
        """
        new_disease_data = []
        fl = fl.replace('DD', 'differential_diagnosis')
        if disease_pop:
            for index, dict_disease in enumerate(disease_pop):
                get_clinical_data = clinical_highlight_data[index]
                for new_item in ['medical_record_count',
                                 'medical_record_count_desc']:
                    if new_item in fl:
                        new_data = get_clinical_data.get(new_item)
                        if new_data:
                            dict_disease[new_item] = new_data

                for new_item2 in ['differential_diagnosis',
                                  'diagnosis_basis',
                                  'diagnosis_basis_highlight',
                                  'highlight_words']:
                    if new_item2 in fl:
                        new_data = get_clinical_data.get(new_item2.lower())
                        if new_data:
                            dict_disease[new_item2] = new_data
                new_disease_data.append(dict_disease)
        return new_disease_data


if __name__ == '__main__':
    define('lstm_port', default=None, help='run on the given port', type=int)
    define('cnn_port', default=None, help='run on the given port', type=int)
    tornado.options.parse_command_line()
    ad = AidDiagnose(debug=False,
                     lstm_port=options.lstm_port, cnn_port=options.cnn_port)
    kg = KGDao()
    handlers = [(r'/diagnose_service', DiagnoseService)]
    base_service.run(handlers)
