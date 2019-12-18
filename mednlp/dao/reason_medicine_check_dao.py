# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
合理用药检测类

Author: chenxk <chenxk@guahao.com>
Create on 2019-08-07 星期三.
"""


import os
import sys
import time
import re
import copy
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.log import GLLog
import json
import traceback
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser



class ReasonMedicineCheckDao(object):
    def __init__(self):
        """
        初始化配置
        :return: 无
        """
        self.logger = GLLog('reasonMedicineCheckDao', log_dir=global_conf.out_log_dir, level='info').getLogger()
        self.config = ConfigParser.ConfigParser()
        self.config.read(global_conf.cfg_path)
        self.local_data = self._load_data()
        self.ai_service = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.search_service = AIServiceClient(global_conf.cfg_path, 'SearchService')
        self.tip_level = {
            'info': [],
            'warning': [],
            'forbid': []
        }
        self.check_field = {
            'use_day_tip': self.check_use_day,
            'max_audit_day_tip': self.check_max_audit_day,
            'diagnose_tip': self.check_diagnose,
            'age_forbid_tip': self.check_children_forbid,
            'administration_route_tip': self.check_administration_route,
            'dose_unit_tip': self.check_dose_unit,
            'duplicate_principle_tip': self.check_duplicate_principle,
            'extreme_dose_tip': self.check_extreme_dose
        }

    def _load_data(self):
        """
        加载储存在本地文件中的合理用药数据
        :return:
        """
        reason_medicine_info = {}
        try:
            if self.config.has_section('REASON_MEDICINE'):
                section = 'REASON_MEDICINE'
                if self.config.has_option(section, 'FILE'):
                    file_name = self.config.get(section, 'FILE')
                    with open(os.path.join(global_conf.dict_path, file_name), 'r', encoding='utf-8') as f:
                        reason_medicine_info = json.load(f)
        except:
            self.logger.warning(traceback.format_exc())
        return reason_medicine_info

    def get_data_from_local(self, common_prescription_names, **kwargs):
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
        """
        从知识图谱中获取合理用药数据
        :param common_prescription_names 通用名制剂列表
        """
        result = {}
        # 请求知识图谱，获取并拼装数据，格式与local_data保持一致
        return result

    def get_medicine_info(self, medicineIds):
        """
        根据药品ID获取药品信息
        :param medicineIds:
        :return:
        """
        result = {}
        param = {
            'drug': ','.join(medicineIds),
            'fl': 'common_name,common_preparation_uuid,approval_no,manufacturer_name,ingredient,'
                  'specification,package_convert,name,use_unit,pill,pill_unit_name,dose,dose_unit_name,drug_id'
        }
        try:
            res = self.search_service.query(param, 'prescription_plat_drug',method='get')
        except:
            self.logger.warning(traceback.format_exc())
        if res and res.get('code') == 0:
            for data in res.get('data', []):
                if data.get('drug_id'):
                    result[data.get('drug_id')] = data
        return result

    def extract_symptom(self, content):
        """
        根据药品ID获取药品信息
        :param medicineIds:
        :return:
        """
        result = set()
        if content:
            param = {
                'q': content,
                'type': 'symptom',
                'fl': 'type,entity_id,entity_name'
            }
            res = {}
            try:
                res = self.ai_service.query(param, 'entity_extract', method='get')
            except:
                self.logger.warning(traceback.format_exc())
            if res and res.get('code') == 0:
                for data in res.get('data', []):
                    if data['type'] == 'symptom':
                        result.add(data.get('entity_name'))
        return list(result)

    def translate_dose(self, dose, unit, medicine):
        """
        将药品剂量单位转换为mg
        :param dose 剂量
        :param unit 单位
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

    def check_all_field(self, drug, medicine_infos, reason_medicine_infos, result=None, **kwargs):
        """
        检查所有配置项
        :param drug:  处方中药品信息
        :param medicine_infos: 根据药品ID查询到的药品信息
        :param reason_medicine_infos: 合理用药相关规范信息
        :param kwargs:
        :return:
        """
        if not result:
            result = {}
            for field in reason_medicine_check_dao.check_field.keys():
                result[field] = copy.deepcopy(self.tip_level)
        for key, func in self.check_field.items():
            tips = func(drug, medicine_infos, reason_medicine_infos, **kwargs)  # {'info':['提示信息']}
            if tips:
                for k, v in tips.items():
                    result[key][k].extend(v)
                    result[key][k] = list(set(result[key][k]))
        return result

    def check_use_day(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        检查药品的使用天数是否合理
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return: tip_object
        """
        tip_template = '警告！{} 药品 {} {} 对 {} 疾病治疗时间,请审查处方'
        common_name = drug.get('common_name', '')
        manufacturer = medicine_infos.get(drug.get('medicine_id', ''), {}).get('manufacturer_name')
        diseases = kwargs.get('diagnosis', [])
        result = copy.deepcopy(self.tip_level)
        days = drug.get('days', None)
        if days is not None and common_name in reason_medicine_infos:
            reason_medicine_info = reason_medicine_infos.get(common_name).get(manufacturer, {})
            if not reason_medicine_info:
                reason_medicine_info = reason_medicine_infos.get(common_name).get('_common_info_', {})
            for disease in diseases:
                usage_dosage = {}
                if disease in reason_medicine_info.get('usage_dosage', {}):
                    usage_dosage = reason_medicine_info.get('usage_dosage', {}).get(disease)
                else:
                    usage_dosage = reason_medicine_info.get('_common_usage_', {})
                if usage_dosage and usage_dosage.get('time_scope'):
                    for item in usage_dosage.get('time_scope', []):
                        source = item.get('source', '')
                        max_day = item.get('max', None)
                        min_day = item.get('min', None)
                        level = item.get('level', 'info')
                        if min_day and days < min_day and level in result:
                            result[level].append(tip_template.format(common_name, '低于', source, disease))
                        elif max_day and days > max_day:
                            result[level].append(tip_template.format(common_name, '高于', source, disease))
        return result

    def check_max_audit_day(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        检查药品的使用天数是否超过审方要求天数限制
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return: tip_object
        """
        common_name = drug.get('common_name', '')
        result = copy.deepcopy(self.tip_level)
        days = drug.get('days', None)
        if days:
            if isinstance(days, int) and days > 30:
                result['warning'].append('警告！ {} 药品开药天数超过审方要求限制天数(上限为30天)'.format(common_name))
        return result

    def check_diagnose(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        检查诊断和所开药品是否相符
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return: tip_object
        """
        common_name = drug.get('common_name', '')
        manufacturer = medicine_infos.get(drug.get('medicine_id', ''), {}).get('manufacturer_name')
        diseases = set(kwargs.get('diagnosis', []))
        symptoms = set(kwargs.get('symptoms', []))
        crowds = set(kwargs.get('crowd', []))
        allergens = set(kwargs.get('allergen', []))
        if kwargs.get('sex', '') == 1:
            crowds.add('女性')
        elif kwargs.get('sex', '') == 2:
            crowds.add('男性')
        if 0 <= kwargs.get('age', 100) <= 14:
            crowds.add('儿童')
        if kwargs.get('pregnancy_status') == 1:
            crowds.add('哺乳期')
        elif kwargs.get('pregnancy_status') == 2:
            crowds.add('怀孕')
        result = copy.deepcopy(self.tip_level)
        if common_name in reason_medicine_infos:
            reason_medicine_info = reason_medicine_infos.get(common_name).get(manufacturer, {})
            if not reason_medicine_info:
                reason_medicine_info = reason_medicine_infos.get(common_name).get('_common_info_', {})
            taboo_allergens = set(reason_medicine_infos.get(common_name, {}).get('allergen', []))
            if allergens.intersection(taboo_allergens):
                result['forbid'].append('拒绝！{} 药品与患者的过敏原 {} 禁忌,请审查处方'.format(common_name, '、'.join(taboo_allergens.intersection(allergens))))
            if diseases:
                # adaptation_disease = set(reason_medicine_info.get('adaptation_disease', {}).get('items', []))
                taboo_disease = set(reason_medicine_info.get('taboo_disease', {}).get('items', []))
                # if not adaptation_disease.intersection(diseases):  # 如果没有交集,发出警告提示诊断和用药不符
                #     result['warning'].append('警告！{} 药品使用和 {} 诊断不符,请审查处方'.format(common_name, '、'.join(diseases)))
                if taboo_disease.intersection(diseases):  # 如果有交集，发出拒绝提示用药和诊断有禁忌
                    result['forbid'].append('拒绝！{} 药品使用和 {} 诊断有禁忌,请审查处方'.format(common_name, '、'.join(taboo_disease.intersection(diseases))))
            if symptoms:
                taboo_symptom = set(reason_medicine_info.get('taboo_symptom', {}).get('items', []))
                if taboo_symptom.intersection(symptoms):  # 如果有交集，发出拒绝提示用药和症状有禁忌
                    result['forbid'].append('拒绝！{} 药品使用和 {} 症状有禁忌,请审查处方'.format(common_name, '、'.join(taboo_symptom.intersection(symptoms))))
            adaptation_symptom = set(reason_medicine_info.get('adaptation_symptom', {}).get('items', []))
            if adaptation_symptom and not adaptation_symptom.intersection(symptoms):
                result['info'].append('提示！{} 药品适用 {} 症状'.format(common_name, '、'.join(adaptation_symptom)))

            if crowds:
                taboo_crowd = set(reason_medicine_info.get('taboo_crowd', {}).get('items', []))
                if taboo_crowd.intersection(crowds):  # 如果有交集，发出拒绝提示用药和人群有禁忌
                    result['forbid'].append('拒绝！{} 药品使用和 {} 人群有禁忌,请审查处方'.format(common_name, '、'.join(taboo_crowd.intersection(crowds))))
            adaptation_crowd = set(reason_medicine_info.get('adaptation_crowd', {}).get('items', []))
            if adaptation_crowd and not adaptation_crowd.intersection(crowds):
                result['info'].append('提示！{} 药品适用 {} 人群'.format(common_name, '、'.join(adaptation_crowd)))

        return result

    def check_children_forbid(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        年龄禁用提示
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return:
        """
        common_name = drug.get('common_name', '')
        manufacturer = medicine_infos.get(drug.get('medicine_id', ''), {}).get('manufacturer_name')
        result = copy.deepcopy(self.tip_level)
        age = kwargs.get('age', -1)
        if common_name in reason_medicine_infos:
            reason_medicine_info = reason_medicine_infos.get(common_name).get(manufacturer, {})
            if not reason_medicine_info:
                reason_medicine_info = reason_medicine_infos.get(common_name).get('_common_info_', {})
            taboo_age = reason_medicine_info.get('taboo_age', {})
            if taboo_age and age >= 0:
                if taboo_age.get('min', 1000) <= age <= taboo_age.get('max', -1):
                    result['forbid'].append('拒绝！{} 药品与患者年龄禁忌,请审查处方'.format(common_name))
                elif 'min' in taboo_age and 'max' not in taboo_age and age >= taboo_age.get('min'):
                    result['forbid'].append('拒绝！{} 药品与患者年龄禁忌,请审查处方'.format(common_name))
                elif 'max' in taboo_age and 'min' not in taboo_age and age <= taboo_age.get('max'):
                    result['forbid'].append('拒绝！{} 药品与患者年龄禁忌,请审查处方'.format(common_name))
            if age < 0 or result['forbid']:
                if taboo_age.get('min'):
                    if taboo_age.get('max'):
                        result['info'].append('提示！ {} 药品禁忌年龄为{}至{}岁'.format(common_name, taboo_age.get('min'),taboo_age.get('max')))
                    else:
                        result['info'].append('提示！ {} 药品禁忌年龄为{}岁以上'.format(common_name, taboo_age.get('min')))
                elif taboo_age.get('max'):
                    result['info'].append('提示！ {} 药品禁忌年龄为{}岁以下'.format(common_name, taboo_age.get('max')))

        return result

    def check_administration_route(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        给药途径提示
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return:
        """
        common_name = drug.get('common_name', '')
        diseases = set(kwargs.get('diagnosis', []))
        manufacturer = medicine_infos.get(drug.get('medicine_id', ''), {}).get('manufacturer_name')
        result = copy.deepcopy(self.tip_level)
        administration_route = drug.get('administration_route', None)
        if administration_route and common_name in reason_medicine_infos:
            reason_medicine_info = reason_medicine_infos.get(common_name).get(manufacturer, {})
            if not reason_medicine_info:
                reason_medicine_info = reason_medicine_infos.get(common_name).get('_common_info_', {})
            for disease in diseases:
                usage_dosage = {}
                if disease in reason_medicine_info.get('usage_dosage', {}):
                    usage_dosage = reason_medicine_info.get('usage_dosage', {}).get(disease)
                else:
                    usage_dosage = reason_medicine_info.get('usage_dosage', {}).get('_common_usage_', {})
                if usage_dosage.get('route') and administration_route not in usage_dosage.get('route'):
                    result['warning'].append('警告！ {} 药品给药途径和推荐方式不符,请审查处方'.format(common_name))
                    break
        return result

    def check_dose_unit(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        剂量单位提示
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return:
        """
        common_name = drug.get('common_name', '')
        result = copy.deepcopy(self.tip_level)
        dose_unit = drug.get('dose_unit', None)
        medicine_info = medicine_infos.get(drug.get('medicine_id'), {})
        if not medicine_info:
            medicine_info['specification'] = drug.get('specification', '')
        if dose_unit and medicine_info and medicine_info.get('specification'):
            if dose_unit != medicine_info.get('pill_unit_name') and not medicine_info.get('specification', '').endswith(dose_unit):
                result['info'].append('提示！{} 药品所开剂量单位与规格不符，请审查处方'.format(common_name))
        return result

    def check_duplicate_principle(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        重复开药提示
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return:
        """
        result = copy.deepcopy(self.tip_level)
        common_prescription_names = kwargs.get('common_prescription_names', [])
        atc_5_code = set()  # atc
        for common_name in common_prescription_names:
            reason_medicine_info = reason_medicine_infos.get(common_name, {})
            if reason_medicine_info and reason_medicine_info.get('atc_code'):
                atc_code = reason_medicine_info.get('atc_code')
                if len(atc_code) > 5:
                    if atc_code[0:5] in atc_5_code:
                        result['warning'].append('警告！处方中的药品存在重复用药情况,请审查处方')
                        break
                    else:
                        atc_5_code.add(atc_code[0:5])
        return result

    def check_extreme_dose(self, drug={}, medicine_infos={}, reason_medicine_infos={}, **kwargs):
        """
        药品使用剂量提示
        :param drug:
        :param medicine_infos:
        :param reason_medicine_infos:
        :param kwargs:
        :return:
        """
        common_name = drug.get('common_name', '')
        drug_id = drug.get('medicine_id', '')
        manufacturer = medicine_infos.get(drug.get('medicine_id', ''), {}).get('manufacturer_name')
        weight = kwargs.get('weight', 60) * 1000
        dose = drug.get('dose', None)
        dose_unit = drug.get('dose_unit', None)
        frequency = drug.get('frequency', 1)
        dose = self.translate_dose(dose, dose_unit, medicine_infos.get(drug.get('medicine_id', ''), {}))
        if not isinstance(frequency, int) and not isinstance(frequency, float):  # 当传入频次为其他类型时默认频次为每天一次
            frequency = 1
        result = copy.deepcopy(self.tip_level)
        if dose and common_name in reason_medicine_infos:
            reason_medicine_info = reason_medicine_infos.get(common_name).get(manufacturer, {})
            if not reason_medicine_info:
                reason_medicine_info = reason_medicine_infos.get(common_name).get('_common_info_', {})
            active_principles = set(reason_medicine_infos.get(common_name).get('active_principle', []))
            # if reason_medicine_infos.get(common_name, {}).get('liver_damage') == 1:
            #     if kwargs.get('liver_damage') == 1:
            #         result['warning'].append('警告！患者肝功能损伤,{} 药品损伤肝功能'.format(common_name))
            #     elif kwargs.get('liver_damage') != 0:
            #         result['info'].append('提示！{} 药品受肝功能影响,请确认患者肝功能状态'.format(common_name))
            # if reason_medicine_infos.get(common_name, {}).get('renal_damage') == 1:
            #     if kwargs.get('renal_damage') == 1:
            #         result['warning'].append('警告！患者肾功能损伤,{} 药品损伤肾功能'.format(common_name))
            #     elif kwargs.get('renal_damage') != 0:
            #         result['info'].append('提示！{} 药品受肾功能影响,请确认患者肾功能状态'.format(common_name))
            if drug_id in reason_medicine_info and active_principles:
                medicine = reason_medicine_info.get(drug_id)
                for active_principle in active_principles:
                    active_principle_info = reason_medicine_infos.get(common_name).get(active_principle, None)
                    value = medicine.get(active_principle, {}).get('value', None)
                    if value and active_principle_info:
                        one_value = value * dose / (weight / 13)  # 单次剂量
                        day_value = frequency * one_value  # 日剂量
                        count_info = len(result['info'])
                        if active_principle_info.get('dead_concentration', {}).get('value', None):  # 致死剂量
                            concentration = active_principle_info.get('dead_concentration').get('value')
                            if one_value > concentration:
                                result['forbid'].append('禁止！{} 药品单次剂量达到致死量,请审查处方'.format(common_name))
                            if day_value > concentration:
                                result['forbid'].append('禁止！{} 药品单日剂量达到致死量,请审查处方'.format(common_name))
                            if result['forbid']:
                                break
                        if active_principle_info.get('toxic_concentration', {}).get('value', None):  # 中毒剂量
                            concentration = active_principle_info.get('toxic_concentration').get('value')
                            count_warning = len(result['warning'])
                            if one_value > concentration:
                                result['warning'].append('警告！{} 药品单次剂量达到最低药物中毒剂量,请审查处方'.format(common_name))
                            if day_value > concentration:
                                result['warning'].append('警告！{} 药品单日剂量达到最低药物中毒剂量,请审查处方'.format(common_name))
                            if len(result['warning']) > count_warning:
                                break
                        if active_principle_info.get('max_effective_concentration', {}).get('value', None):  # 最大有效剂量
                            concentration = active_principle_info.get('max_effective_concentration').get('value')
                            if one_value > concentration:
                                result['info'].append('提示！{} 药品单次剂量超出药物有效最大剂量,请审查处方'.format(common_name))
                            if day_value > concentration:
                                result['info'].append('提示！{} 药品单日剂量超出药物有效最大剂量,请审查处方'.format(common_name))
                            if len(result['info']) > count_info:
                                break
                        if active_principle_info.get('min_effective_concentration', {}).get('value', None):  # 最小有效剂量
                            concentration = active_principle_info.get('min_effective_concentration').get('value')
                            if one_value < concentration:
                                result['info'].append('提示！{} 药品单次剂量低于药物有效最小剂量,请审查处方'.format(common_name))
                            if day_value < concentration:
                                result['info'].append('提示！{} 药品单日剂量低于药物有效最小剂量,请审查处方'.format(common_name))
                            if len(result['info']) > count_info:
                                break
        return result



if __name__ == '__main__':
    reason_medicine_check_dao = ReasonMedicineCheckDao()
    reason_medicine_check_dao.get_data_from_local(['阿莫西林片'])
    reason_medicine_check_dao.get_data_from_web(['阿莫西林片'])
    reason_medicine_check_dao.get_medicine_info(['79b57d38-5ce8-4d09-ae5e-84596f512270'])
    reason_medicine_check_dao.extract_symptom('我头痛')
    reason_medicine_check_dao.check_all_field({}, {}, {})
