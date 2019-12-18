#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: FH <fenghui@guahao.com>
Created on 2019/10/19 11:12
全科辅助诊断V1.2.1_合理用药
"""
import datetime
import os
import copy
import json
import traceback
import configparser

import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.log import GLLog


class PrescriptionScreeningDao:
    def __init__(self):
        self.logger = GLLog('PrescriptionScreeningDao',
                            log_dir=global_conf.out_log_dir,
                            level='info').getLogger()
        self.config = configparser.ConfigParser()
        self.config.read(global_conf.cfg_path)
        self.local_data = self._load_data()
        self.ai_service = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.search_service = AIServiceClient(global_conf.cfg_path, 'SearchService')
        self.tip_level = {
            'info': {},
            'warning': {},
            'forbid': {}
        }
        self.check_field = {
            'use_day_tip': self.check_use_day,
            'max_audit_day_tip': self.check_max_audit_day,
            'diagnose_tip': self.check_diagnose,
            'age_forbid_tip': self.check_children_forbid,
            'administration_route_tip': self.check_administration_route,
            'dose_unit_tip': self.check_dose_unit,
            'duplicate_principle_tip': self.check_duplicate_principle,
            'extreme_dose_tip': self.check_extreme_dose,
            'old_people_tip': self.check_old_people,
            'liver_renal_tip': self.check_liver_renal,
            'special_medication_tip': self.check_special_medication,
            'inspection_monitor_tip': self.check_inspection_monitor
        }
        self.max_audit_day = 30
        self.drug = {}
        self.medicine_infos = {}
        self.reason_medicine_infos = {}
        self.input_obj = {}
        self.common_name = ''
        self.pregnancy_status = 0
        self.patient_diagnosis = []
        self.assist_info = {}
        self.disease = []
        self.crowds = []
        self.gender = ''
        self.birth_year = 0

    def _load_data(self):
        """
        加载储存在本地文件中的合理用药数据
        :return:
        """
        reason_medicine_info = {}

        try:
            if self.config.has_section('Prescription_Screening'):
                section = 'Prescription_Screening'
                if self.config.has_option(section, 'FILE'):
                    file_name = self.config.get(section, 'FILE')
                    with open(os.path.join(global_conf.dict_path, file_name), 'r', encoding='utf-8') as f:
                        reason_medicine_info = json.load(f)
        except Exception as ex:
            traceback.print_exc()
            self.logger.error('从本地文件加载合理用药数据异常，原因是:{}'.format(ex))

        return reason_medicine_info

    def get_data_from_local(self, common_prescription_names):
        """
        从本地文件中获取合理用药数据
        :param common_prescription_names 通用名制剂列表
        """
        result = {}
        for name in common_prescription_names:
            if name in self.local_data:
                result[name] = self.local_data[name]
        return result

    def get_data_from_web(self, common_prescription_names, **kwargs):
        """从知识图谱中获取合理用药数据"""
        pass

    def get_medicine_info(self, medicine_ids):
        """
        根据药品ID获取药品信息
        :param medicine_ids:
        :return:
        """
        result = {}
        param = {
            'drug': ','.join(medicine_ids),
            'fl': 'common_name,common_preparation_uuid,approval_no,manufacturer_name,ingredient,'
                  'specification,package_convert,name,use_unit,pill,pill_unit_name,dose,dose_unit_name,drug_id'
        }
        try:
            res = self.search_service.query(param, 'prescription_plat_drug', method='get')
        except Exception as ex:
            traceback.print_exc()
            self.logger.error('从处方共享平台获取药品信息异常,原因是:{}'.format(ex))
        else:
            if res and res.get('code') == 0:
                for data in res.get('data', []):
                    if data.get('drug_id'):
                        result[data.get('drug_id')] = data
        return result

    def extract_symptom(self, content):
        """
        从【患者】主诉中获取症状
        :param content: 患者主诉信息
        :return: 主诉信息中包含的症状列表
        """
        result = set()
        if content:
            param = {
                'q': content,
                'type': 'symptom',
                'fl': 'type,entity_id,entity_name'
            }
            try:
                res = self.ai_service.query(param, 'entity_extract', method='get')
            except Exception as ex:
                traceback.print_exc()
                self.logger.error('从患者主诉信息中获取症状异常,原因是:{}'.format(ex))
            else:
                if res and res.get('code') == 0:
                    for data in res.get('data', []):
                        if data['type'] == 'symptom':
                            result.add(data.get('entity_name'))
        return list(result)

    def get_rule_info(self,
                      organize_code: str,
                      rule_group_name: str,
                      rule_entities: list,
                      question_answers_list: list) -> list:
        """
        通过规则引擎获取规则信息
        :param organize_code:
        :param rule_group_name:
        :param rule_entities:
        :param question_answers_list:
        :return:
        """
        result = []
        param = {
            "organizeCode": organize_code,
            "ruleGroupName": rule_group_name,
            "ruleEntities": rule_entities,
            "initQuestionAnswer": question_answers_list
        }
        try:
            res = self.ai_service.query(json.dumps(param, ensure_ascii=False), 'rule_engine')
        except Exception as ex:
            traceback.print_exc()
            self.logger.error('从规则引擎获取规则异常,原因是:{}'.format(ex))
        else:
            if res and res.get('code') == '0':
                rule_contents = res.get('data', {}).get('ruleContents', [])
                result.extend(rule_contents)
        return result

    def get_entity_info(self,
                        entities: list,
                        label: list,
                        label_field: list,
                        label_type: list,
                        rows: int = 40):
        """
        获取实体信息
        :param entities: 实体名称列表，例如：[溶血性贫血]
        :param label: 实体标签
        :param label_field: 实体标签
        :param label_type: 实体类型
        :param rows: 返回条数
        :return: 实体信息
        """
        result = []
        if entities:
            param = {
                "q": "*:*",
                "name": entities,
                "rows": rows,
                "ef": [
                    "id",
                    "name",
                    "type",
                    "relation_set"
                ],
                "type": label_type,
                "label": label,
                "label_field": label_field,
                "match_alias": 1
            }
            try:
                res = self.ai_service.query(json.dumps(param, ensure_ascii=False), 'entity_service')
            except Exception as ex:
                traceback.print_exc()
                self.logger.error('知识图谱(entity_service接口)异常,'
                                  '原因是:{}'.format(ex))
            else:
                if res and res.get('code') == 0:
                    data = res['data'].get('entity', [])
                    result.extend(data)
        return result

    @staticmethod
    def translate_dose(dose, unit, medicine):
        """
        将药品剂量单位转换为mg
        :param dose 剂量
        :param unit 单位
        :param medicine:
        :return: 以mg为单位的剂量
        """
        translate_weight = {
            'ug': 0.001,
            'mg': 1,
            'g': 1000,
            'kg': 1000000
        }
        pill_unit = medicine.get('pill_unit_name', None)
        dose_unit = medicine.get('dose_unit_name', None)
        dose_one = medicine.get('dose', None)
        if unit and pill_unit == unit:
            return dose
        if unit in translate_weight and dose_unit in translate_weight and dose_one:
            dose = dose * translate_weight[unit] / (translate_weight[dose_unit] * dose_one)
        else:
            dose = None
        return dose

    @staticmethod
    def check_number(number: int) -> int:
        """
        检测参数中的各种数字是否为数字
        如果为数字，则返回数字，否则，返回0
        :param number: 参数中的各种数字信息，比如：开药天数等
        :return: 返回对应的数字信息
        """
        if isinstance(number, int):
            value = number
        elif isinstance(number, str):
            try:
                value = int(number)
            except ValueError or TypeError:
                value = 0
        else:
            value = 0
        return value

    @staticmethod
    def get_age_range(age: int,
                      min_age: int,
                      max_age: int) -> str:
        """
        检测年龄范围
        :param age: 患者年龄
        :param min_age: 最小年龄
        :param max_age: 最大年龄
        :return: 年龄范围提示语
        """
        if age is None or age == 0:
            age_range = ''
        elif min_age is not None and max_age and min_age <= age <= max_age:
            age_range = '{}岁到{}岁'.format(min_age, max_age)
        elif min_age is not None and not max_age and age <= min_age:
            age_range = '{}岁以下'.format(min_age)
        elif min_age is None and max_age and age > max_age:
            age_range = '{}岁以上'.format(max_age)
        else:
            age_range = ''

        return age_range

    def get_patient_crowds(self):
        """
        获取患者所属人群
        :return:
        """
        age = self.check_number(self.input_obj.get('age'))
        sex = self.input_obj.get('sex', '')

        # 根据怀孕状态进行判断
        if self.pregnancy_status == 1:
            self.crowds.extend(['哺乳期', '哺乳期妇女'])
        elif self.pregnancy_status == 2:
            self.crowds.append('孕妇')

        # 根据性别进行判断
        if sex == 1:
            self.gender = '女性'
            self.crowds.append(self.gender)
        elif sex == 2:
            self.gender = '男性'
            self.crowds.append(self.gender)
        else:
            self.gender = '未知'

        # 根据出生日期和年龄进行判断
        birth_date = self.input_obj.get('birth_date')
        if birth_date:
            birth_date_time = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
            self.birth_year = (datetime.datetime.now() - birth_date_time).days / 365
            if 0 <= self.birth_year <= 3:
                self.crowds.append('婴幼儿')
            elif 0 <= self.birth_year <= 14:
                self.crowds.append('儿童')

        if age:
            if 0 <= age <= 3:
                self.crowds.append('婴幼儿')
            elif 0 <= age <= 14:
                self.crowds.append('儿童')

    def variable_access_logic(self):
        """
        变量取数逻辑
        1、通过患者诊断疾病和既往病史获取疾病编码
        2、通过检查检验的值去【规则引擎】里获取更精准的信息，比如：患者所属人群、疾病等
        """
        # 判断患者所属人群
        self.get_patient_crowds()

        # 根据患者诊断疾病、既往史、合并症、并发症及其疾病编码获取患者索还疾病
        past_medical_history = self.assist_info.get('past_medical_history', [])
        comorbidity = self.assist_info.get('comorbidity', [])
        complication = self.assist_info.get('complication', [])
        patient_diseases_list = self.patient_diagnosis + past_medical_history + comorbidity + complication
        self.disease.extend(patient_diseases_list)

        # 根据疾病获取疾病编码
        entities_infos = self.get_entity_info(patient_diseases_list,
                                              ["Rejuyokm", "a7bSzM9Q", "GKUUR01y"],
                                              ["Rejuyokm", "a7bSzM9Q", "GKUUR01y"],
                                              ['disease'])
        for entity_info in entities_infos:
            disease_code = entity_info.get('label', {}).get('a7bSzM9Q', '')
            if disease_code:
                self.disease.append(disease_code)

        # 根据检查、检验的项目构造规则引擎需要的请求体
        inspections_list = self.assist_info.get('inspection', [])
        examination_list = self.assist_info.get('examination', [])
        check_items_list = inspections_list + examination_list
        inspection_names = []
        inspections_dt = {}
        if check_items_list:
            for inspection in check_items_list:
                inspection_name = inspection.get('name', '')
                inspection_value = inspection.get('value', '')
                inspection_unit = inspection.get('unit', '')
                inspection_names.append(inspection_name)
                if inspection_name not in inspections_dt:
                    inspections_dt.setdefault(inspection_name,
                                              [inspection_value, inspection_unit])

            # 获取检查检验对应的规则引擎的code值
            entities_infos = self.get_entity_info(inspection_names, ["2tq7CO74"], ["2tq7CO74"], [])
            question_answer_list = []
            for entity_info in entities_infos:
                entity_name = entity_info.get('name', '')
                entity_type = entity_info.get('type', '')
                rule_code = entity_info.get('label', {}).get("2tq7CO74", '')
                item_value = inspections_dt.get(entity_name, [])

                if rule_code and (entity_type == 'inspection'
                                  or entity_type == 'examination') and item_value:
                    question_answer_dt = {
                        "questionCode": rule_code,
                        "questionAnswer": [item_value[0]],
                        "questionAnswerUnit": item_value[1]
                    }
                    question_answer_list.append(question_answer_dt)

            # 规则请求体添加性别等全局信息
            question_answer_dt = {
                "questionCode": 'sex',
                "questionAnswer": [self.gender],
                "questionAnswerUnit": ''
            }
            question_answer_list.append(question_answer_dt)

            # 获取organize_code与rule_group_name，然后从规则引擎获取配置好的规则
            if self.config.has_section('Prescription_Screening'):
                section = 'Prescription_Screening'
                if self.config.has_option(section, 'RULE_ENGINE_ORGANIZE_CODE'):
                    organize_code = self.config.get(section, 'RULE_ENGINE_ORGANIZE_CODE')
                    rule_group_name = self.config.get(section, 'RULE_ENGINE_RULE_GROUP_NAME')

                    # 从规则引擎获取规则
                    rule_results = self.get_rule_info(organize_code,
                                                      rule_group_name,
                                                      ["急性胃肠炎"],
                                                      question_answer_list)

                    # 处理从【规则引擎】获取到的结果，并把结果添加到人群与疾病列表中
                    for rule_result in rule_results:
                        action = rule_result.get('action')
                        if action:
                            rule_value = json.loads(action.get('value'))
                            rule_diseases = rule_value.get('disease', [])
                            rule_crowds = rule_value.get('crowd', [])
                            self.crowds.extend(rule_crowds)
                            self.disease.extend(rule_diseases)

    @staticmethod
    def get_intersection(set1: set, set2: set) -> set:
        """
        返回两个集合的交集
        :param set1: 集合1
        :param set2: 集合2
        :return: 交集
        """
        return set1.intersection(set2)

    def has_some_disease(self, tip_keyword: str) -> bool:
        """
        通过从规则引擎获取到的疾病判断患者是否患有某种疾病
        :param tip_keyword: 疾病的关键词，例如：肝或神
        :return: 患有某种疾病则返回True，否则返回False
        """
        patient_disease = '、'.join(self.disease)
        if tip_keyword in patient_disease:
            return True
        return False

    def check_all_field(self, **kwargs):
        """
        检查所有配置项
        :param kwargs: 包含入参信息字典、【合理用药】药品信息字典等
        :return: 返回【合理用药】的结果
        """
        # 获取【药品使用信息】(drug 对应参数中的medicine)、
        # 获取【药品信息】(medicine_infos 根据medicine_id从搜索云平台获取的药品结果)
        # 获取【合理用药信息】(reason_medicine_infos 从提前构造好的合理用药json中解析出的结果)
        # 获取所有【治疗方案-合理用药】接口所有的入参信息(input_obj)
        self.drug = kwargs.get('medicine', {})
        self.medicine_infos = kwargs.get('medicine_infos', {})
        self.reason_medicine_infos = kwargs.get('reason_medicine_infos', {})
        self.input_obj = kwargs.get('input_obj', {})

        # 获取药品信息名称、诊断疾病、检验项、既往疾病史、是否怀孕等状态
        self.common_name = self.drug.get('common_name', '')
        self.patient_diagnosis = self.input_obj.get('diagnosis', [])
        self.assist_info = self.input_obj.get('assist_info', {})
        self.pregnancy_status = self.input_obj.get('pregnancy_status', 0)
        self.disease = []
        self.crowds = []

        # 根据取数逻辑为患者添加所属人群与疾病信息
        # 主要在禁忌人群与禁忌疾病提示中使用
        try:
            self.variable_access_logic()
        except Exception as ex:
            self.logger.error('获取取数逻辑过程中出现异常，'
                              '原因是：{}'.format(ex))
            traceback.print_exc()

        # 检测所有【合理用药】需要检测的提示项，例如: 检查药品的使用天数是否合理等
        result = kwargs.get('result', {})
        if not result:
            result = copy.deepcopy(self.tip_level)
        for key, func in self.check_field.items():
            try:
                tips = func()
            except Exception as ex:
                traceback.print_exc()
                self.logger.info('检测是否合理用药中报错了'
                                 '(报错函数为:{!r})，'
                                 '原因是:{}'.format(func, ex))
            else:
                if tips:
                    for k, v in tips.items():
                        for k2, v2 in v.items():
                            k2_v2 = result.get(k, {}).get(k2, [])
                            if k2_v2:
                                result[k][k2].extend(v2)
                                result[k][k2] = list(set(result[k][k2]))
                            else:
                                result[k].setdefault(k2, v2)
        return result

    def generate_result(self, tip_name: str, **kwargs):
        """
        根据tip_name生产对应的【合理用药】的提示信息
        更多tip_name信息，请查看接口文档：
        http://confluence.guahao-inc.com/display/0124AI/Prescription_Screening_Api_Document

        :param tip_name: 【合理用药】提醒的名称，例如:use_day_tip（药品用药天数不规范提示信息）
        :return: 返回【合理用药】结果
        """
        result = copy.deepcopy(self.tip_level)
        forbid_tips_dt = result['forbid']
        warning_tips_dt = result['warning']
        info_tips_dt = result['info']

        ftl = kwargs.get('ftl', [])
        wtl = kwargs.get('wtl', [])
        itl = kwargs.get('itl', [])

        if ftl:
            forbid_tips_dt.setdefault(tip_name, ftl)
        if wtl:
            warning_tips_dt.setdefault(tip_name, wtl)
        if itl:
            info_tips_dt.setdefault(tip_name, itl)

        return result

    def check_use_day(self):
        """
        药品用药天数不规范提示信息
        1）根据传入 药品ID 查询药品的 通用名制剂 和 生产厂家 信息
        2）根据 通用名制剂 和 生产厂家 获取 对应疾病的推荐开药天数区间，和通用的 开药天数区间 信息
        3）当处方的开药天数 大于 2）中获取的最大开药天数 或者 小于 2）中获取的最小开药天数时，进行相应提醒
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        tip_template = '警告！{} 药品 {} {} 对 {} 疾病治疗时间,请审查处方'
        common_name = self.common_name
        diseases = self.input_obj.get('diagnosis', [])
        days = self.drug.get('days')

        if days is not None and common_name in self.reason_medicine_infos:
            reason_medicine_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})
            usage_dosage = reason_medicine_info.get('usage_dosage', {})
            for disease in diseases:
                common_usage = usage_dosage.get('_common_usage_', {})
                if common_usage and common_usage.get('time_scope'):
                    for item in common_usage.get('time_scope', []):
                        source = item.get('source', '')
                        max_day = self.check_number(item.get('max', 0))
                        min_day = self.check_number(item.get('min', None))

                        if min_day and days < min_day:
                            wtl.append(tip_template.format(common_name,
                                                           '低于',
                                                           source,
                                                           disease))
                        elif max_day and days > max_day:
                            wtl.append(tip_template.format(common_name,
                                                           '高于',
                                                           source,
                                                           disease))
        # 生成结果
        tip_name = 'use_day_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_max_audit_day(self):
        """
        药品超过审方最大开药天数提示信息
        1）根据处方中药品的开药天数，判断是否大于 30 天,当大于30天时，给出警告提示
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        days = self.check_number(self.drug.get('days', 0))

        if days > self.max_audit_day:
            tip = '警告！ {} 药品开药天数超过审方' \
                  '要求限制天数(上限为{:d}天)'.format(common_name, self.max_audit_day)
            wtl.append(tip)

        # 生成结果
        tip_name = 'max_audit_day_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_diagnose(self):
        """
        药品禁忌症和适应症提示信息
        1）根据传入 药品ID 查询药品的 通用名制剂 和 生产厂家 信息
        2）根据 通用名制剂 和 生产厂家 获取 对应的 适应疾病、症状、人群 和 对应的禁忌疾病、症状、人群、过敏原
        3）根据患者的年龄和性别添加隐藏人群信息， age<=14岁添加儿童人群，sex=男 添加男性人群， sex=女添加女性信息
        4）当患者的过敏原/疾病/症状/人群 存在于药品的禁忌信息中时，发出 拒绝 等级信息
        5）当诊断不在药品的适应疾病中时发出警告信息，提示药品使用和诊断不符
        6）当药品有 适应症状/人群 时，返回提示信息，提示药品的适应症状和人群
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        diseases = set(self.input_obj.get('diagnosis', []))
        # symptoms = set(kwargs.get('symptoms', []))
        crowds = set(self.input_obj.get('crowd', []))
        allergens = set(self.input_obj.get('allergen', []))

        # 添加根据规则引擎获取到的人群信息与疾病信息
        # 疾病信息包含疾病编码与疾病信息
        crowds.update(self.crowds)
        diseases.update(self.disease)

        if common_name in self.reason_medicine_infos:
            common_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})

            # 过敏原
            taboo_allergens = set(self.reason_medicine_infos.get(common_name, {}).get('allergen', []))
            check_result = '、'.join(self.get_intersection(allergens, taboo_allergens))
            if check_result:
                tip_template = '拒绝！{} 药品与患者的过敏原 {} 禁忌,请审查处方'
                ftl.append(tip_template.format(common_name, check_result))

            # 禁忌疾病
            if diseases:
                taboo_disease_list = common_info.get('taboo_disease', [])
                for taboo_disease in taboo_disease_list:
                    level = taboo_disease.get('level', 'info')
                    tip_word = taboo_disease.get('tip', '不推荐')
                    taboo_disease = taboo_disease.get('items', [])

                    # 判断诊断疾病是否在【治疗方案】中提地药品禁忌疾病中
                    taboo_disease = set(taboo_disease)
                    check_result = '、'.join(self.get_intersection(diseases, taboo_disease))

                    if check_result and tip_word:
                        tip_template = '对于{}患者，{}{}'
                        if level == 'forbid':
                            ftl.append(tip_template.format(check_result, tip_word, common_name))
                        elif level == 'warning':
                            wtl.append(tip_template.format(check_result, tip_word, common_name))
                        else:
                            itl.append(tip_template.format(check_result, tip_word, common_name))

            # 禁忌人群
            if crowds:
                taboo_crowd_list = common_info.get('taboo_crowd', {})
                for taboo_crowd in taboo_crowd_list:
                    level = taboo_crowd.get('level', 'info')
                    tip_word = taboo_crowd.get('tip', '不推荐')
                    taboo_crowd = taboo_crowd.get('items', [])

                    # 检测患者所属人群与合理用药中的用药人群是否有交集
                    check_result = '、'.join(self.get_intersection(crowds, taboo_crowd))

                    if check_result and tip_word:
                        tip_template = '对于{}患者，{}{}'
                        if level == 'forbid':
                            ftl.append(tip_template.format(check_result, tip_word, common_name))
                        elif level == 'warning':
                            wtl.append(tip_template.format(check_result, tip_word, common_name))
                        else:
                            itl.append(tip_template.format(check_result, tip_word, common_name))

        # 生成结果
        tip_name = 'diagnose_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_children_forbid(self):
        """
        年龄禁用提示
        1）根据传入 药品ID 查询药品的 通用名制剂 和 生产厂家 信息
        2）根据 通用名制剂 和 生产厂家 获取 药品的禁忌年龄区间
        3）根据患者年龄参数判断是否为药品的禁忌年龄区间，如果是，则返回 拒绝提示信息
        4）如果药品有禁忌年龄区间，返回禁忌年龄区间的提示信息
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        age = self.check_number(self.input_obj.get('age'))

        if common_name in self.reason_medicine_infos:
            reason_medicine_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})
            taboo_age = reason_medicine_info.get('taboo_age', {})

            min_age = taboo_age.get('min')
            min_age = self.check_number(min_age) if min_age is not None else min_age
            max_age = self.check_number(taboo_age.get('max'))
            age_range = self.get_age_range(age,
                                           min_age,
                                           max_age) or self.get_age_range(self.birth_year,
                                                                          min_age,
                                                                          max_age)

            # 根据年龄范围与提示语内容，添加对应的【合理用药】提示语
            if age_range:
                ftl.append('对于年龄{}患者，禁用{}'.format(age_range, common_name))

        # 生成结果
        tip_name = 'age_forbid_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_administration_route(self):
        """
        给药途径错误信息提示
        1）根据传入 药品ID 查询药品的 通用名制剂 ，生产厂家，最小剂量单位 ，包装规格 信息
        2）根据 通用名制剂 和 生产厂家 获取 药品对应指定疾病的给药途径 和通用的给药途径
        3）当处方的给药途径 和 2）中的不符时给出相应的警告信息
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取药品名称、给药途径
        common_name = self.common_name
        administration_route = self.drug.get('administration_route', '')

        # 检测是否符合要求
        if common_name:
            common_info = self.reason_medicine_infos.get(common_name, {}).get('_common_info_', {})
            usage_dosage = common_info.get('usage_dosage', {}).get('_common_usage_', {})
            usage_route = usage_dosage.get('route', [])
            if usage_route and administration_route not in usage_route:
                tip_template = '警告！ {} 药品给药途径和推荐方式不符,请审查处方'
                wtl.append(tip_template.format(common_name))

        # 生成结果
        tip_name = 'administration_route_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_dose_unit(self):
        """
        剂量单位提示
        根据传入 药品ID 查询药品的 通用名制剂 ，生产厂家，最小剂量单位 ，包装规格 信息
        当处方传入的剂量单位 不等于  1）中获取的最小剂量单位或者 包装规格中的剂量单位时，返回提示信息，提示药品剂量单位不符
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        dose_unit = self.drug.get('dose_unit')
        medicine_id = self.drug.get('medicine_id')
        specification = self.drug.get('specification', '')

        # 通过药品ID获取药品相关信息
        medicine_info = self.medicine_infos.get(medicine_id, {})

        # 判断剂量单位是否符合要求
        if medicine_info:
            common_name = common_name or self.medicine_infos.get('common_name')
            pill_unit_name = medicine_info.get('pill_unit_name', '')
            if dose_unit != pill_unit_name and not specification.endswith(dose_unit):
                tip_template = '提示！{} 药品所开剂量单位与规格不符，请审查处方'
                itl.append(tip_template.format(common_name))

        # 生成结果
        tip_name = 'dose_unit_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_duplicate_principle(self):
        """
        重复用药提示
        1）根据传入 药品ID 查询药品的 通用名制剂 ，生产厂家 信息
        2）根据通用名制剂获取到对应的药品ATC编码
        3）根据 2）中获取的ATC编码进行判断，如果存在ATC编码的前5位有重复，则判定为重复用药，给出警告提示
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 判断【治疗方案】中的所有通用制剂名称是否有重复开药
        # 主要通过ATC编码的前5位进行判断是否有重复的
        common_prescription_names = self.input_obj.get('common_prescription_names', [])
        atc_5_code = set()
        for common_name in common_prescription_names:
            reason_medicine_info = self.reason_medicine_infos.get(common_name, {})
            if reason_medicine_info and reason_medicine_info.get('atc_code'):
                atc_code = reason_medicine_info.get('atc_code')
                if len(atc_code) > 5:
                    if atc_code[0:5] in atc_5_code:
                        tip_template = '警告！处方中的药品存在重复用药情况,请审查处方'
                        wtl.append(tip_template)
                        break
                    else:
                        atc_5_code.add(atc_code[0:5])
        # 生成结果
        tip_name = 'duplicate_principle_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_extreme_dose(self):
        """
        药品使用剂量提示
        1）根据传入 药品ID 查询药品的 通用名制剂 ，生产厂家，药品的有效成分，药品的有效成分含量信息
        2）根据通用名制剂获取各有效成分的 最低有效浓度，最高有效浓度，中毒浓度，致死浓度
        3）根据处方的单次剂量计算单次剂量的浓度和单日剂量浓度
        公式为 单次剂量浓度=单次剂量 * 单片药品成分有效浓度 / (体重 / 13),体重单位为g，单日剂量浓度=单日频次 * 单次剂量浓度
        4）当 3）中的单次剂量浓度和单日剂量浓度 大于 2）中致死浓度时，发出拒绝信息，
        当大于 中毒浓度小于致死浓度时发出警告信息，当大于最大有效浓度小于中毒浓度时 或者低于最低有效浓度时发出提示信息
        5）当患者为 肝损伤/肾损伤 和药品为 肝损伤/肾损伤 时发出警告信息
        6）当处方未传 肝损伤/肾损伤 且药品为 肝损伤/肾损伤 时，返回提示信息
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        drug_id = self.drug.get('medicine_id', '')
        weight = self.check_number(self.input_obj.get('weight', 60)) * 1000
        dose = self.drug.get('dose')
        dose_unit = self.drug.get('dose_unit')
        frequency = self.drug.get('frequency', 1)
        dose = self.translate_dose(dose,
                                   dose_unit,
                                   self.medicine_infos.get(self.drug.get('medicine_id', ''), {}))

        # 当传入频次为其他类型时默认频次为每天一次
        if not isinstance(frequency, int) or not isinstance(frequency, float):
            frequency = 1

        # 判断药品使用剂量是否符合要求
        if dose and common_name in self.reason_medicine_infos:
            reason_medicine_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})
            active_principles = set(self.reason_medicine_infos.get(common_name).get('active_principle', []))

            if drug_id in reason_medicine_info and active_principles:
                medicine = reason_medicine_info.get(drug_id)
                for active_principle in active_principles:
                    active_principle_info = self.reason_medicine_infos.get(common_name).get(active_principle, None)
                    value = medicine.get(active_principle, {}).get('value', None)
                    if value and active_principle_info:
                        one_value = value * dose / (weight / 13)  # 单次剂量
                        day_value = frequency * one_value  # 日剂量
                        count_info = len(itl)

                        # 判断是否达到致死剂量
                        dead_concentration = active_principle_info.get('dead_concentration', {}).get('value', None)
                        if dead_concentration:
                            if one_value > dead_concentration:
                                ftl.append('禁止！{} 药品单次剂量'
                                           '达到致死量,请审查处方'.format(common_name))
                            if day_value > dead_concentration:
                                ftl.append('禁止！{} 药品单日剂量'
                                           '达到致死量,请审查处方'.format(common_name))
                            if ftl:
                                break

                        # 判断是否达到中毒剂量
                        toxic_concentration = active_principle_info.get('toxic_concentration', {}).get('value', None)
                        if toxic_concentration:
                            count_warning = len(wtl)
                            if one_value > toxic_concentration:
                                wtl.append('警告！{} 药品单次剂量'
                                           '达到最低药物中毒剂量,请审查处方'.format(common_name))
                            if day_value > toxic_concentration:
                                wtl.append('警告！{} 药品单日剂量'
                                           '达到最低药物中毒剂量,请审查处方'.format(common_name))
                            if len(wtl) > count_warning:
                                break

                        # 判断是否超出最大有效剂量
                        max_effective_concentration = active_principle_info.get('max_effective_concentration',
                                                                                {}).get('value', None)
                        if max_effective_concentration:
                            if one_value > max_effective_concentration:
                                itl.append('提示！{} 药品单次剂量'
                                           '超出药物有效最大剂量,请审查处方'.format(common_name))
                            if day_value > max_effective_concentration:
                                itl.append('提示！{} 药品单日剂量'
                                           '超出药物有效最大剂量,请审查处方'.format(common_name))
                            if len(itl) > count_info:
                                break

                        # 判断是否小于最小有效剂量
                        min_effective_concentration = active_principle_info.get('min_effective_concentration',
                                                                                {}).get('value', None)
                        if min_effective_concentration:
                            if one_value < min_effective_concentration:
                                itl.append('提示！{} 药品单次剂量'
                                           '低于药物有效最小剂量,请审查处方'.format(common_name))
                            if day_value < min_effective_concentration:
                                itl.append('提示！{} 药品单日剂量'
                                           '低于药物有效最小剂量,请审查处方'.format(common_name))
                            if len(itl) > count_info:
                                break
        # 生成结果
        tip_name = 'extreme_dose_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_old_people(self):
        """
        老年用药提示
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        age = self.check_number(self.input_obj.get('age'))

        if (age or self.birth_year) and common_name:
            common_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})
            elderly_medication_reminder = common_info.get('elderly_medication_reminder', [])

            tip_template = '对于年龄{}患者，{}'

            for each_reminder in elderly_medication_reminder:
                min_age = each_reminder.get('min')
                min_age = self.check_number(min_age) if min_age is not None else min_age
                max_age = self.check_number(each_reminder.get('max'))
                level = each_reminder.get('level', 'info')
                tip_content = each_reminder.get('tip', '').replace('此药', common_name)

                # 获取年龄范围
                # 根据年龄范围与提示语内容，添加对应的【合理用药】提示语
                age_range = self.get_age_range(age,
                                               min_age,
                                               max_age) or self.get_age_range(self.birth_year,
                                                                              min_age,
                                                                              max_age)
                if age_range and tip_content:
                    if level == 'forbid':
                        ftl.append(tip_template.format(age_range, tip_content))
                    elif level == 'warning':
                        wtl.append(tip_template.format(age_range, tip_content))
                    else:
                        itl.append(tip_template.format(age_range, tip_content))

        # 生成结果
        tip_name = 'old_people_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_liver_renal(self):
        """
        肝毒性、肾毒性提示
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name
        patient_liver_damage = self.input_obj.get('liver_damage')
        patient_renal_damage = self.input_obj.get('renal_damage')

        medicine_liver_damage = self.reason_medicine_infos.get(common_name, {}).get('liver_damage')
        medicine_renal_damage = self.reason_medicine_infos.get(common_name, {}).get('renal_damage')
        tip_template = '{common_name}具有{tip_keyword}毒性，有{tip_keyword}病者慎用，' \
                       '若使用此药，服药前请确认患者{tip_keyword}功能正常'

        # 通过从规则引擎获取到的疾病，判断患者是否患有肝或肾相关的疾病
        is_liver_damage = patient_liver_damage or self.has_some_disease('肝')
        is_renal_damage = patient_renal_damage or self.has_some_disease('肾')

        if is_liver_damage and medicine_liver_damage:
            itl.append(tip_template.format(common_name=common_name,
                                           tip_keyword='肝'))

        if is_renal_damage and medicine_renal_damage:
            itl.append(tip_template.format(common_name=common_name,
                                           tip_keyword='肾'))

        # 生成结果
        tip_name = 'liver_renal_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_special_medication(self):
        """
        特殊用药提示
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name

        # 获取【合理用药】中是否有对该药品的特殊用药提示
        if common_name:
            common_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})
            special_dosage_method = common_info.get('special_dosage_method', [])

            for each_method in special_dosage_method:
                level = each_method.get('level', 'info')
                tip_content = each_method.get('tip', '').replace('此药', common_name)

                if level == 'forbid':
                    ftl.append(tip_content)
                elif level == 'warning':
                    wtl.append(tip_content)
                else:
                    itl.append(tip_content)

        # 生成结果
        tip_name = 'special_medication_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result

    def check_inspection_monitor(self):
        """
        用药监测提示：
        规则20：盐酸小檗碱片_合理用药_药物=true & 合理用药知识库.用药监测.盐酸小檗碱片.B列对应字段.值≠null
        action20：使用此药，用药期间需监测：【合理用药知识库.用药监测.盐酸小檗碱片.B列对应字段.值】（多个内容顿号分割展示）
        """
        ftl, wtl, itl = [[] for _ in range(3)]

        # 获取通用信息
        common_name = self.common_name

        # 获取【合理用药】中是否有对该药品的用药监测提醒
        common_info = self.reason_medicine_infos.get(common_name).get('_common_info_', {})
        drug_monitoring = common_info.get('drug_monitoring', {}).get('items', [])
        if common_name and drug_monitoring:
            drug_monitoring_result = '、'.join(drug_monitoring)
            tip_template = '使用{}，用药期间需监测：{}'
            itl.append(tip_template.format(common_name, drug_monitoring_result))

        # 生成结果
        tip_name = 'inspection_monitor_tip'
        result = self.generate_result(tip_name, ftl=ftl, wtl=wtl, itl=itl)
        return result


if __name__ == '__main__':
    reason_medicine_check_dao = PrescriptionScreeningDao()
    reason_medicine_check_dao.get_data_from_local(['阿莫西林片'])
    reason_medicine_check_dao.get_data_from_web(['阿莫西林片'])
    reason_medicine_check_dao.get_medicine_info(['79b57d38-5ce8-4d09-ae5e-84596f512270'])
    reason_medicine_check_dao.extract_symptom('我头痛')
    reason_medicine_check_dao.check_all_field()
