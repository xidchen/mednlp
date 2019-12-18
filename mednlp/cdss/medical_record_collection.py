#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-31 Wednesday
@Desc:	辅助问诊内容
"""

import json
import codecs
import global_conf
from mednlp.dao.kg_dao import KGDao


class MedicalRecordCollection():
    def __init__(self):
        self.load_data()
        self.kg_dao = KGDao()
        self.inquiry_fls = ['critical_situation', 'main_symptom', 'accompanying_symptoms', 'treatment_process',
                            'past_history',
                            'common_signs', 'general_info', 'examination',
                            # 'past_medical_history', 'surgical_history', 'allergy_history', 'blood_transfusion_history',
                            'menstrual_history', 'marital_history', 'personal_history', 'family_history']

    def load_data(self):
        with codecs.open(global_conf.medical_record_collection_data, 'r', 'utf-8') as f:
            self.symptom_ask_template = json.load(f)

    def get_common_symptom(self):
        """ 常见症状列表 """
        return self.kg_dao.find_body_part_symptom_relation()

    def get_inquiry_content(self, symptom, age, sex, fl):
        if symptom not in self.symptom_ask_template:
            return None

        fls = []
        if '*' in fl:
            fls = list(self.inquiry_fls)
        else:
            fls = fl.split(',')

        inquiry_content = {}
        for fl in fls:
            if fl in self.inquiry_fls:
                inquiry_content[fl] = self.get_inquiry_item(fl, symptom, age, sex)

        return inquiry_content

    def get_inquiry_item(self, fl, symptom, age, sex):
        res = []
        templates = self.symptom_ask_template.get(symptom, {}).get(fl, [])
        for template in templates:
            ask = {'name': template['name'], 'type': template['type'], 'options': []}
            for option in template['options']:
                if self._valid_age(age, option['age']) and self._valid_sex(sex, option['sex']):
                    ask['options'] = option['items']
                    # 以匹配到第一个为准
                    break
            # 只返回找到的选项
            if ask['options']:
                res.append(ask)
        return res

    def _valid_age(self, user_age, limit_age):
        """判别年龄是否匹配

        :user_age: 用户年龄，单位是天
        :limit_age: 要求的年龄，*表示无要求，形式：start-end|start-end
        :returns:

        """
        if limit_age == '*':
            return True
        for ran in limit_age.split('|'):
            s, e = ran.split('-')
            if int(s) <= int(user_age) <= int(e):
                return True
        return False

    def _valid_sex(self, user_sex, limit_sex):
        """判别性别是否匹配

        :user_sex: 用户性别
        :limit_sex: 要求的性别
        :returns:

        """
        if limit_sex == '*':
            return True
        if str(user_sex) == limit_sex:
            return True
        return False


if __name__ == '__main__':
    mrc = MedicalRecordCollection()
    # print(mrc.get_common_symptom())
    print(mrc.get_inquiry_content('腹痛', 1, 1, '*'))
