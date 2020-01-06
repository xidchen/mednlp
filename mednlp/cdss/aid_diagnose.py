#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
aid_diagnose.py -- the class of aid diagnose

Author: chenxd
Create on 2017-09-07 Thursday.
"""

import re
import json
import time
import global_conf
import configparser
import traceback
from ailib.client.ai_service_client import AIServiceClient
from mednlp.cdss.medical_record import MedicalRecordParser
from mednlp.dao.kg_dao import KGDao
from mednlp.dao.data_loader import generate_disease_dept_name
from mednlp.model.utils import age_segment, normal_probability, sort
from mednlp.utils.file_operation import get_disease_id, get_disease_id_add
from mednlp.dao.loader import get_disease_sex_filter
from mednlp.dao.loader import get_disease_age_filter
from mednlp.utils.file_operation import get_disease_body_part_filter
from mednlp.utils.file_operation import get_disease_inspection_filter
from mednlp.utils.file_operation import get_disease_physical_exam_filter
from mednlp.utils.file_operation import get_disease_past_medical_history_filter
from mednlp.utils.file_operation import get_disease_symptom_filter
from mednlp.utils.file_operation import get_symptom_name
from ailib.client.cloud_solr import CloudSolr
from mednlp.dao.rule_service_dao import rule_condition_prefilter


LSTM_WEIGHT = 0.8
CNN_WEIGHT = 1 - LSTM_WEIGHT
DEPT_WEIGHT = 1.2


class AidDiagnose(object):

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.mr_parsed = {}
        self.mr_parser = MedicalRecordParser(debug=self.debug)
        self.kg = KGDao(debug=self.debug)
        self.disease_id_dept = generate_disease_dept_name(
            global_conf.disease_id_dept_path)
        self.d_name_id = get_disease_id()
        if kwargs.get('lstm_port'):
            self.dcm = AIServiceClient(global_conf.cfg_path, 'AIService',
                                       port=kwargs.get('lstm_port'))
        else:
            self.dcm = AIServiceClient(global_conf.cfg_path, 'AIService')
        if kwargs.get('cnn_port'):
            self.dcn = AIServiceClient(global_conf.cfg_path, 'AIService',
                                       port=kwargs.get('cnn_port'))
        else:
            self.dcn = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.disease_sex_prob = get_disease_sex_filter()
        self.disease_age_prob = get_disease_age_filter()
        self.disease_body_part_filter = get_disease_body_part_filter()
        self.disease_inspection_filter = get_disease_inspection_filter()
        self.disease_physical_exam_filter = get_disease_physical_exam_filter()
        self.disease_past_medical_history_filter = get_disease_past_medical_history_filter()
        self.disease_symptom_filter = get_disease_symptom_filter()
        self.body_part_name = []
        self.inspection_name = []
        self.physical_exam_name = []
        self.symptom_name = []
        self.body_part_discount = 0.9
        self.inspection_discount = 1
        self.physical_exam_discount = 1
        self.past_medical_history_discount = 1
        self.symptom_discount = 0.999
        self.past_medical_history = ''
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(global_conf.cfg_path)

    def diagnose(self, medical_record, **kwargs):
        """
        根据病历作出诊断.
        参数:
        medical_record->病历,格式:{sex:,age:,chief_complaint:}
        返回值->诊断疾病列表,格式:[{disease_id:,score:}].
        """
        sex = medical_record.get('sex', '-1')
        age = medical_record.get('age', '0')
        patient_inspection = medical_record.get('inspection', '')
        patient_physical_examination = medical_record.get('physical_examination', '')
        medical_record['inspection'] = medical_record.get('inspection', '')
        medical_record['physical_examination'] = medical_record.get('physical_examination', '')
        mr_parsed = self.mr_parser.parse(medical_record)
        self.mr_parsed = mr_parsed
        symptom_name, disease_name, body_part_name = [], [], []
        inspection_name, physical_exam_name = [], []
        for field in ['chief_complaint', 'inspection', 'physical_examination']:
            if mr_parsed.get(field) and mr_parsed.get(field).get('symptoms'):
                symptom_name += list(mr_parsed[field]['symptoms'].keys())
            if mr_parsed.get(field) and mr_parsed.get(field).get('diseases'):
                disease_name += list(mr_parsed[field]['diseases'].keys())
            if mr_parsed.get(field) and mr_parsed.get(field).get('body_parts'):
                body_part_name += list(mr_parsed[field]['body_parts'].keys())
            if mr_parsed.get(field) and mr_parsed.get(field).get('ins'):
                inspection_name += list(mr_parsed[field]['ins'].keys())
            if mr_parsed.get(field) and mr_parsed.get(field).get('pe'):
                physical_exam_name += list(mr_parsed[field]['pe'].keys())
        medical_entity = ','.join(symptom_name + disease_name + body_part_name)
        self.body_part_name = body_part_name
        self.inspection_name = inspection_name
        self.physical_exam_name = physical_exam_name
        self.past_medical_history = medical_record.get('past_medical_history', '')
        self.symptom_name = symptom_name

        if medical_entity == '':
            return [], set(), {}

        else:
            api_code = 0
            params = dict()

            params['medical_record'] = [medical_record]
            params_str = json.dumps(params)
            disease_mr_dcm_score = []
            try:
                disease_lstm = self.dcm.query(params_str, 'diagnose_lstm')
                disease_mr_dcm_score = disease_lstm['diagnosis'][0]['diseases']
            except (BaseException, RuntimeError):
                api_code = 1
            disease_pop = {}
            disease_dcm_pop = {}
            disease_dcn_pop = {}
            d_n_id_set = set()
            for name, score in disease_mr_dcm_score:
                disease_dcm_pop[self.d_name_id[name]] = score
                d_n_id_set.add(self.d_name_id[name])
            for d_id in d_n_id_set:
                dcm_pop = disease_dcm_pop.get(d_id, 0)
                dcn_pop = disease_dcn_pop.get(d_id, 0)
                disease_pop[d_id] = LSTM_WEIGHT * dcm_pop + CNN_WEIGHT * dcn_pop
            normal_probability(disease_pop)
            self.sex_filter(disease_pop, sex)
            self.age_filter(disease_pop, age)
            self.body_part_filter(disease_pop)
            self.inspection_filter(disease_pop, patient_inspection)
            self.physical_exam_filter(disease_pop, patient_physical_examination)
            self.past_medical_history_filter(disease_pop)
            self.symptom_filter(disease_pop)
            self.strong_rule_filter(disease_pop, medical_record)
            normal_probability(disease_pop)
            disease_pop = sort(disease_pop)

            match_symptom = set()
            symptom_synonym_group = set()
            if mr_parsed.get('chief_complaint'):
                symptom_synonym_group = mr_parsed['chief_complaint']['symptom_synonym']
            for synonym_group in symptom_synonym_group:
                for synonym_symptom_id in synonym_group:
                    match_symptom.add(synonym_symptom_id)
            return disease_pop, match_symptom, api_code

    def get_disease_dept_score(self, chief_complaint, department):
        dept_score = {}
        try:
            dept_score = self.kg.dept_classify(chief_complaint=chief_complaint)
        except (BaseException, RuntimeError):
            print('Dept_Classify_API Error!')
        std_department = []
        try:
            std_department = self.kg.std_dept_extract(q=department)
        except (BaseException, RuntimeError):
            print('Entity_Extract_API Error!')
        disease_dept_score = {}
        for d_id, dept_list in self.disease_id_dept.items():
            score_set = set()
            for dept in dept_list:
                if dept in dept_score:
                    score_set.add(dept_score.get(dept, 0))
                if dept in std_department:
                    score_set.add(dept_score.get(dept, 0) * DEPT_WEIGHT)
            if score_set:
                disease_dept_score[d_id] = max(score_set)
        return disease_dept_score

    def sex_filter(self, disease_pop, sex):
        if sex in ['1', '2']:
            for disease in disease_pop:
                if self.disease_sex_prob.get(disease):
                    if self.disease_sex_prob[disease].get(sex) is not None:
                        disease_pop[disease] *= self.disease_sex_prob[
                            disease][sex]
        return disease_pop

    def age_filter(self, disease_pop, age):
        if age not in ['0']:
            age_seg = age_segment(age)
            for disease in disease_pop:
                if self.disease_age_prob.get(disease):
                    if self.disease_age_prob[disease].get(age_seg) is not None:
                        disease_pop[disease] *= self.disease_age_prob[
                            disease][age_seg]
        return disease_pop

    def strong_rule_filter(self, disease_pop, medical_record):
        """
        血糖升高 -> 过滤低血糖症
        血糖降低 & 既往史中无糖尿病 -> 过滤糖尿病
        血压降低 & 既往史中无高血压 -> 过滤高血压、高血压性脑病
        """
        medical_history = medical_record.get('chief_complaint', '')
        past_medical_history = medical_record.get('past_medical_history', '')
        if '血糖升高' in medical_history:
            # 低血糖症
            disease_pop['1cbd1ed9-31e0-11e6-804e-848f69fd6b70'] *= 0.001
        if '血糖降低' in medical_history and '糖尿病' not in past_medical_history:
            # 糖尿病
            disease_pop['1bab728c-31e0-11e6-804e-848f69fd6b70'] *= 0.001
        if '血压降低' in medical_history and '高血压' not in past_medical_history:
            # 高血压、高血压性脑病
            disease_pop['44238'] *= 0.001
            disease_pop['05a63a4b-31e1-11e6-804e-848f69fd6b70'] *= 0.001
        return disease_pop

    def body_part_filter(self, disease_pop):
        for disease in disease_pop:
            if self.disease_body_part_filter.get(disease):
                for body_part in self.disease_body_part_filter[disease]:
                    if body_part in self.body_part_name:
                        disease_pop[disease] *= 1 - self.body_part_discount
        return disease_pop

    def inspection_filter(self, disease_pop, patient_inspection):
        # 病历检查项格式化
        mr_inspection = {}
        for find_inspection in re.split(r'[,;，；]', patient_inspection):
            find_ins_content = re.split(r'[:：]', find_inspection)
            if len(find_ins_content) != 2:
                continue
            find_ins_name, find_ins_value = find_ins_content[0].strip(), find_ins_content[1].strip()
            if ':' in find_ins_name or '：' in find_ins_name:
                find_ins_name = re.split(r'[:：]', find_ins_name)[-1].strip()
            mr_inspection[find_ins_name] = InspectionValue(find_ins_value)

        report_not_support_set = ('未见异常', '未见明显异常', '报告未见异常', '报告未见明显异常', '正常', '无殊')
        for disease in disease_pop:
            for inspection_rule in self.disease_inspection_filter.get(disease, []):
                is_discount = False
                # 检查项 关系 值
                items = inspection_rule.split(' ')
                if len(items) == 1:
                    # 只有检查项表示该检查不支持诊断
                    inspection = items[0].strip()
                    # 正常心电图的常见表述：
                    # 1. 正常心电图
                    # 2. 大致正常心电图
                    # 3. 窦性心律 （报告内容中，仅含“窦性心律”或出现“窦性心律；大致正常心电”，“窦性心律；正常心电图”）
                    if inspection == '心电图' and inspection in mr_inspection:
                        if mr_inspection[inspection].unit == '窦性心律':
                            is_discount = True
                        if '正常心电' in mr_inspection[inspection].unit:
                            is_discount = True
                    if inspection in mr_inspection:
                        if mr_inspection[inspection].unit in report_not_support_set:
                            is_discount = True
                if len(items) == 3:
                    inspection, op, value = items
                    inspection = inspection.strip()
                    if inspection in mr_inspection:
                        expect = InspectionValue(value)
                        actual = mr_inspection[inspection]
                        if op == '>':
                            if actual > expect:
                                is_discount = True
                        elif op == '<':
                            if actual < expect:
                                is_discount = True
                        elif op == '≥':
                            if actual >= expect:
                                is_discount = True
                        elif op == '≤':
                            if actual <= expect:
                                is_discount = True
                        elif op == '：':
                            if actual == expect:
                                is_discount = True
                        if mr_inspection[inspection].value in report_not_support_set:
                            is_discount = True
                if is_discount:
                    disease_pop[disease] *= 1 - self.inspection_discount
        return disease_pop

    def physical_exam_filter(self, disease_pop, physical_examination):
        for disease in disease_pop:
            if self.disease_physical_exam_filter.get(disease):
                for examination in self.disease_physical_exam_filter[disease]:
                    if examination in physical_examination:
                        disease_pop[disease] *= 1 - self.physical_exam_discount
        return disease_pop

    def past_medical_history_filter(self, disease_pop):
        for disease in disease_pop:
            past_medical_history = self.disease_past_medical_history_filter.get(disease)
            if past_medical_history:
                for pmh in past_medical_history:
                    if pmh in self.past_medical_history:
                        disease_pop[disease] *= 1 - self.past_medical_history_discount
        return disease_pop

    def symptom_filter(self, disease_pop):
        for disease in disease_pop:
            if self.disease_symptom_filter.get(disease):
                for symptom in self.disease_symptom_filter[disease]:
                    if symptom in self.symptom_name:
                        disease_pop[disease] *= 1 - self.symptom_discount
        return disease_pop

    def diagnose_all(self, medical_record):
        """
        疾病诊断，包含普通疾病诊断和危重病诊断
        """
        mr_parsed = self.mr_parser.parse(medical_record)
        disease_pop, match_symptom, api_code = self.diagnose_with_para(medical_record, mr_parsed)
        critical_disease = self.critical_disease_diagnose_with_para(mr_parsed)
        return disease_pop, match_symptom, api_code, critical_disease

    def diagnose_with_para(self, medical_record, mr_parsed):
        medical_entity = []
        for field in ('chief_complaint', 'inspection', 'physical_examination'):
            for item in ('symptoms', 'diseases', 'body_parts'):
                medical_entity.extend(list(mr_parsed.get(field, {}).get(item, {}).keys()))

        if len(medical_entity) == 0:
            return [], set(), {}
        else:
            api_code = 0
            params_str = json.dumps({'medical_record': [medical_record]})
            disease_mr_dcm_score = []
            try:
                disease_lstm = self.dcm.query(params_str, 'diagnose_lstm')
                disease_mr_dcm_score = disease_lstm['diagnosis'][0]['diseases']
            except (BaseException, RuntimeError):
                api_code = 1

            disease_pop = {}
            disease_dcm_pop = {}
            disease_dcn_pop = {}
            d_n_id_set = set()
            for name, score in disease_mr_dcm_score:
                disease_dcm_pop[self.d_name_id[name]] = score
                d_n_id_set.add(self.d_name_id[name])
            for d_id in d_n_id_set:
                dcm_pop = disease_dcm_pop.get(d_id, 0)
                dcn_pop = disease_dcn_pop.get(d_id, 0)
                disease_pop[d_id] = LSTM_WEIGHT * dcm_pop + CNN_WEIGHT * dcn_pop
            normal_probability(disease_pop)

            sex = medical_record.get('sex', '-1')
            age = medical_record.get('age', '0')
            self.sex_filter(disease_pop, sex)
            self.age_filter(disease_pop, age)
            disease_pop = sort(disease_pop)

            match_symptom = set()
            symptom_synonym_group = set()
            if mr_parsed.get('chief_complaint'):
                symptom_synonym_group = mr_parsed[
                    'chief_complaint']['symptom_synonym']
            for synonym_group in symptom_synonym_group:
                for synonym_symptom_id in synonym_group:
                    match_symptom.add(synonym_symptom_id)
            return disease_pop, match_symptom, api_code

    def critical_disease_diagnose_with_para(self, mr_parsed):
        return self.kg.find_critical_disease(
            mr_parsed['symptom_all'], mr_parsed['sex'], mr_parsed['age'])


class RuleDiagnose:

    def __init__(self):
        self.client = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.cloud_client = CloudSolr(global_conf.cfg_path)
        self.config = configparser.ConfigParser()
        self.config.read(global_conf.cfg_path)
        if self.config.has_section('TREATMENT_PLAN_RECOMMEND'):
            section = 'TREATMENT_PLAN_RECOMMEND'
            if self.config.has_option(section, 'STANDARD_RULE_CODE'):
                rule_code = self.config.get(section, 'STANDARD_RULE_CODE')
                self.organize_code = rule_code
        self.rule_group_name = '诊断优化规则组'
        # TODO: 问题字典、规则字典
        self.question_code_dict = self._load_question_code_dict()
        self.rule_code_dict = self._load_rule_code_dict()
        self.disease_id_name = get_disease_id()
        self.disease_id_name_add = get_disease_id_add()
        self.disease_id_name.update(self.disease_id_name_add)

    def _load_question_code_dict(self):
        res = {}
        with open(global_conf.diagnose_question_code_dict_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('\t')
                if len(items) == 2:
                    res[items[0]] = items[1]
        return res

    def _load_rule_code_dict(self):
        res = {}
        with open(global_conf.diagnose_rule_code_dict_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('\t')
                if len(items) == 2:
                    res[items[0]] = items[1]
        return res

    def make_question_answer(self, argument):
        question_answers = []

        age = argument.get('age')
        try:
            age = float(age) / 365
        except ValueError:
            age = 0
        sex = argument.get('sex')
        if sex in (1, '1'):
            sex = '女'
        elif sex in (2, '2'):
            sex = '男'
        else:
            sex = '未知'
        rule_entity = argument.get('symptom', '')
        question_answers.append(
            {'questionCode': self.question_code_dict.get('年龄'),
             'questionAnswer': [age], 'questionAnswerUnit': '岁'})
        question_answers.append(
            {'questionCode': self.question_code_dict.get('性别'),
             'questionAnswer': [sex], 'questionAnswerUnit': ''})
        question_answers.append(
            {'questionCode': self.question_code_dict.get('主症状'),
             'questionAnswer': [rule_entity], 'questionAnswerUnit': ''})

        # 危急提示
        code = self.question_code_dict.get('危急提示')
        if code:
            inquiry_content = argument.get('critical_situation')
            if inquiry_content:
                qa = self._trans_argument_qa(inquiry_content[0], code)
                if qa:
                    question_answers.append(qa)

        # 主症状描述
        for inquiry_content in argument.get('main_symptom', []):
            qa = self._trans_argument_qa(inquiry_content)
            if qa:
                question_answers.append(qa)
        # 伴随症状
        code = self.question_code_dict.get('伴随症状')
        if code:
            inquiry_content = argument.get('accompanying_symptoms')
            if inquiry_content:
                qa = self._trans_argument_qa(inquiry_content[0], code)
                if qa:
                    question_answers.append(qa)
        # 诊治过程
        code = self.question_code_dict.get('诊治过程')
        if code:
            inquiry_content = argument.get('treatment_process')
            if inquiry_content:
                qa = self._trans_argument_qa(inquiry_content[0], code)
                if qa:
                    question_answers.append(qa)
        # 体格检查
        inquiry_content = argument.get('common_signs', [])
        for content in inquiry_content:
            code = self.question_code_dict.get(
                '体格检查' + '_' + content.get('name', ''))
            if code:
                qa = self._trans_argument_qa(content, code)
                if qa:
                    question_answers.append(qa)

        # 既往史
        for inquiry_content in argument.get('past_history', []):
            qa = self._trans_argument_qa(inquiry_content)
            if qa:
                question_answers.append(qa)
        # 婚育史
        for inquiry_content in argument.get('menstrual_history', []):
            qa = self._trans_argument_qa(inquiry_content)
            if qa:
                question_answers.append(qa)
        # 家族史
        for inquiry_content in argument.get('family_history', []):
            qa = self._trans_argument_qa(inquiry_content)
            if qa:
                question_answers.append(qa)
        # 检验
        examination = argument.get('examination')
        if examination:
            for exam in examination[0].get('value', []):
                for detail in exam.get('details', []):
                    name = exam.get('content', '') + '_' + detail.get('name', '')
                    code = self.question_code_dict.get(name)
                    if code:
                        answer = detail.get('answer', [])
                        unit = detail.get('unit', '')
                        if answer:
                            question_answers.append({'questionCode': code,
                                                     'questionAnswer': answer,
                                                     'questionAnswerUnit': unit})
        # 检查
        check = argument.get('check', [])
        for item in check:
            code = self.question_code_dict.get(item['name'] + '_检查所见')
            if code:
                question_answers.append({'questionCode': code,
                                         'questionAnswer': item['finding'],
                                         'questionAnswerUnit': ''})
            code = self.question_code_dict.get(item['name'] + '_检查结论')
            if code:
                question_answers.append({'questionCode': code,
                                         'questionAnswer': item['conclusion'],
                                         'questionAnswerUnit': ''})
        return question_answers

    def _trans_argument_qa(self, inquiry_content, code=None):
        code = code if code else self.question_code_dict.get(inquiry_content['name'])
        if not code:
            return None
        answer = inquiry_content.get('answer', '[]')
        unit = inquiry_content.get('unit') or ''
        if answer:
            return {'questionCode': code,
                    'questionAnswer': answer,
                    'questionAnswerUnit': unit}
        else:
            return None

    def _make_params(self, question_answers, rule_ids):
        params = {
            'organizeCode': self.organize_code,
            'ruleGroupName': self.rule_group_name,
            'ruleIds': rule_ids,
            'initQuestionAnswer': question_answers
        }
        return params

    def _get_matched_rule(self, params):
        matched_rule_names = []
        if not params['ruleIds']:
            return []
        try:
            re_response = self.client.query(
                json.dumps(params, ensure_ascii=False), 'rule_engine')
            if re_response['code'] not in [0, '0']:
                print('调用规则系统异常: ' + json.dumps(params, ensure_ascii=False))
                return
            re_res_data = re_response.get('data')
            if not re_res_data:
                print('调用规则系统异常: ' + json.dumps(params, ensure_ascii=False))
                return
            rule_contents = re_res_data.get('ruleContents', [])
            for rule_content in rule_contents:
                if rule_content.get('isEnd') == 1 and rule_content.get('status') == 0:
                    matched_rule_names.append(rule_content.get('ruleName'))
        except (BaseException, RuntimeError):
            print('调用规则系统异常: ' + json.dumps(params, ensure_ascii=False))
        return list(set(matched_rule_names))

    def _parse_rule_name(self, rule_name):
        m = re.match(r'(\w+)-(\w+)(-?.*)', rule_name)
        return m.groups() if m else '', '', ''

    def _trans_rule_name(self, rule_names):
        """
        :returns: {'disease_id': [应推荐, 怀疑, 拦截, 不建议]}
        """
        disease_rule = {}
        for name in rule_names:
            disease_name, classes, _ = self._parse_rule_name(name)
            if disease_name:
                disease_id = self.disease_id_name.get(disease_name)
                if not disease_id:
                    continue
                if disease_id not in disease_rule:
                    disease_rule[disease_id] = [False, False, False, False]
                if classes == '推出':
                    disease_rule[disease_id][0] = True
                elif classes == '怀疑':
                    disease_rule[disease_id][1] = True
                elif classes == '拦截':
                    disease_rule[disease_id][2] = True
                elif classes == '不建议':
                    disease_rule[disease_id][3] = True
        return disease_rule

    def _trans_rule_code(self, rule_codes):
        """
        :returns: {'disease_id': [应推荐, 怀疑, 拦截, 不建议]}
        """
        disease_rule = {}
        for code in rule_codes:
            m = re.match(r'(\w+)(\d+)', code)
            if m:
                disease_code, classes = m.groups()
                disease_name = self.rule_code_dict.get(disease_code)
                disease_id = self.disease_id_name.get(disease_name)
                if not disease_id:
                    continue
                if disease_id not in disease_rule:
                    disease_rule[disease_id] = [False, False, False, False]
                if classes == '1':
                    disease_rule[disease_id][0] = True
                elif classes == '2':
                    disease_rule[disease_id][1] = True
                elif classes == '3':
                    disease_rule[disease_id][2] = True
                elif classes == '4':
                    disease_rule[disease_id][3] = True
        return disease_rule

    def adjust_diagnose_result(self, diseases, disease_rule):
        # 推荐进top， 不推荐， 拦截， 鉴别诊断
        # recommend, not_recommend, deprecated, differential_diagnosis = [], [], [], []
        top_disease, normal_disease, tail_disease, differential_diagnosis = [], [], [], []
        for disease in diseases:
            if disease['disease_id'] not in disease_rule:
                normal_disease.append(disease)
            else:
                rule = disease_rule[disease['disease_id']]
                # 是否拦截该疾病
                if rule[2]:
                    tail_disease.append(disease)
                # 是否高度怀疑该疾病
                elif rule[0] and rule[1]:
                    top_disease.append(disease)
                # 是否不建议推出该疾病
                elif rule[3]:
                    normal_disease.append(disease)
                # 是否应推出该疾病
                elif rule[0]:
                    differential_diagnosis.append(disease)
                else:
                    normal_disease.append(disease)

        if len(top_disease) >= 3 and len(normal_disease) > 0:
            # 保证top1的score不超过1
            top1_score = min(normal_disease[0]['score'], 0.95)
            top_disease[0]['score'] = max(top1_score * 1.05, top_disease[0]['score'])
            top_disease[1]['score'] = max(top1_score * 1.02, top_disease[1]['score'])
            top_disease[2]['score'] = max(top1_score * 1.01, top_disease[2]['score'])
            # 取top3放入推荐诊断，其余放入鉴别诊断
            differential_diagnosis.extend(top_disease[3:])
        elif len(top_disease) == 2 and len(normal_disease) > 1:
            top1_score = normal_disease[0]['score']
            top2_score = normal_disease[1]['score']
            new_top2_score = (top1_score - top2_score) * 0.6 + top2_score
            new_top3_score = (top1_score - top2_score) * 0.3 + top2_score
            top_disease[0]['score'] = max(new_top2_score, top_disease[0]['score'])
            top_disease[1]['score'] = max(new_top3_score, top_disease[1]['score'])
        elif len(top_disease) == 1 and len(normal_disease) > 2:
            top2_score = normal_disease[1]['score']
            top3_score = normal_disease[2]['score']
            new_top3_score = (top2_score - top3_score) * 0.5 + top3_score
            top_disease[0]['score'] = max(new_top3_score, top_disease[0]['score'])
        min_score = normal_disease[-1]['score'] if normal_disease else 0
        for disease in tail_disease:
            disease['score'] = min_score * 0.9
        new_diseases = top_disease + normal_disease + tail_disease

        new_diseases = sorted(new_diseases, key=lambda d: d['score'], reverse=True)
        return new_diseases, differential_diagnosis

    def adjust_diagnose_result_v2(self, diseases, disease_rule):
        """诊断优化 - 医学优化规则v2"""
        # 推荐进top， 不推荐， 拦截， 鉴别诊断
        s_top_disease, top_disease, normal_disease, tail_disease = [], [], [], []
        for disease in diseases:
            if disease['disease_id'] not in disease_rule:
                normal_disease.append(disease)
            else:
                rule = disease_rule[disease['disease_id']]
                # 是否拦截该疾病
                if rule[2]:
                    tail_disease.append(disease)
                # 是否高度怀疑该疾病
                elif rule[0] and rule[1]:
                    s_top_disease.append(disease)
                # 是否应推出该疾病
                elif rule[0]:
                    top_disease.append(disease)
                else:
                    normal_disease.append(disease)

        # 只推前11个（5个疑似疾病+6个鉴别诊断）
        top_disease = s_top_disease + top_disease
        normal_disease = top_disease[11:] + normal_disease
        top_disease = top_disease[:11]
        weights = [i / 100 for i in range(105, 170, 5)]

        # 保证top1的score不超过1
        top_disease_len = len(top_disease)
        top1_score = min(
            normal_disease[0]['score'], int(0.99 / weights[top_disease_len]))
        top_disease_reverse = top_disease[::-1]
        for i in range(top_disease_len):
            top_disease_reverse[i]['score'] = top1_score * weights[i]
        top_disease = top_disease_reverse[::-1]

        min_score = normal_disease[-1]['score'] if normal_disease else 0
        for disease in tail_disease:
            disease['score'] = min_score * 0.9
        new_diseases = top_disease[:5] + normal_disease + tail_disease
        differential_diagnosis = top_disease[5:]

        new_diseases = sorted(new_diseases, key=lambda d: d['score'], reverse=True)
        return new_diseases, differential_diagnosis

    def sort_differential_diagnosis(self, differential_diagnosis):
        sorted_differential_diagnosis = []
        differential_diagnosis_dict = {
            dd.get('disease_name', ''): dd for dd in differential_diagnosis}
        params = {
            "ef": ["name", "incidence_rate"],
            "name": list(differential_diagnosis_dict.keys()),
            "type": ["disease"],
            "rows": 100
        }
        try:
            response = self.client.query(
                json.dumps(params, ensure_ascii=False), 'entity_service')
            if not response:
                return differential_diagnosis
            if response.get('code') not in (0, '0'):
                return differential_diagnosis
            entities = response.get('data', {}).get('entity', [])
            sorted_entities = sorted(entities, key=lambda d: int(
                d.get('incidence_rate', [0])[0]), reverse=True)
            for entity in sorted_entities:
                if entity.get('name') in differential_diagnosis_dict:
                    sorted_differential_diagnosis.append(
                        differential_diagnosis_dict[entity.get('name')])
        except Exception as e:
            print('sort differential diagnosis error', e)
            print(traceback.format_exc())
        return sorted_differential_diagnosis

    def filter_rule_ids(self, pre_no_matched, diseases):
        res = []
        disease_ids = [d['disease_id'] for d in diseases[:20]]
        for rule_id, info in pre_no_matched.items():
            name = info.get('name')
            disease_name, classes, _ = self._parse_rule_name(name)
            if classes:
                if classes in ('怀疑', '推出'):
                    res.append(rule_id)
                    continue
                disease_id = self.disease_id_name.get(disease_name)
                if disease_id in disease_ids:
                    res.append(rule_id)
        return res

    def optimize_diagnose(self, argument, diseases, optimization_type=1):
        """根据规则诊断结果优化
        :returns:
        """
        if not argument:
            return diseases, []
        if not diseases:
            return diseases, []

        # 补充诊断规则推荐出的新疾病
        for disease_id in self.disease_id_name_add.values():
            diseases.append({'disease_id': disease_id, 'score': 0})

        question_answers = self.make_question_answer(argument)
        rule_entities = [argument.get('symptom', '')]
        qa_code = {qa['questionCode']: qa['questionAnswer'] for qa in question_answers}
        pre_matched, pre_no_matched = rule_condition_prefilter(
            self.cloud_client, self.organize_code,
            self.rule_group_name, qa_code, rule_entities=rule_entities)

        rule_ids = self.filter_rule_ids(pre_no_matched, diseases)

        params = self._make_params(question_answers, rule_ids)

        st_time = time.time()
        matched_rule_names = self._get_matched_rule(params)
        print('rule engine spend time: {}; rule id num: {}'.format(
            time.time() - st_time, len(rule_ids)))

        matched_rule_names.extend([val['name'] for val in pre_matched.values()])
        # disease_rule = self._trans_rule_code(matched_rule_names)
        disease_rule = self._trans_rule_name(matched_rule_names)
        if optimization_type == 2:
            adjusted_diseases, differential_diagnosis = self.adjust_diagnose_result_v2(
                diseases, disease_rule)
        else:
            adjusted_diseases, differential_diagnosis = self.adjust_diagnose_result(
                diseases, disease_rule)
        return adjusted_diseases, differential_diagnosis


class InspectionValue:
    """检查检验项格式化 - 支持 < <= = >= > 操作运算符比较"""
    def __init__(self, value_str):
        m = re.match(r'([\d.]*)(.*)', value_str.strip())
        if m:
            try:
                self.value = float(m.group(1).strip())
            except ValueError:
                self.value = 0
            self.unit = m.group(2).strip()
        else:
            self.value = 0
            self.unit = ''
        self.trans_standard_unit()

    def trans_standard_unit(self):
        """转换为标准单位"""
        self.unit = self.unit
        self.value = self.value

    def __lt__(self, other):
        return (self.unit == other.unit) and (self.value < other.value)

    def __gt__(self, other):
        return (self.unit == other.unit) and (self.value > other.value)

    def __eq__(self, other):
        return (self.unit == other.unit) and (self.value == other.value)

    def __le__(self, other):
        return (self.unit == other.unit) and (self.value <= other.value)

    def __ge__(self, other):
        return (self.unit == other.unit) and (self.value >= other.value)

    def __str__(self):
        return '{}:{}'.format(self.value, self.unit)


if __name__ == '__main__':
    mr = {'chief_complaint': '头痛发烧', 'sex': 2}
    diagnose = AidDiagnose()
    print(diagnose.diagnose(mr))
