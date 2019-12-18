# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-08-11 Sunday
@Desc:	病历采集接口中将医学研究员整理数据转换为配置文件
"""

import pandas as pd
import codecs
import json
import math
import re
import os
import global_conf

base_path = global_conf.RELATIVE_PATH + 'data/问诊模板/'

class TemplateExcel2Dict():
    """ 将excel格式的问诊模板转为自定义的配置文件 """

    def __init__(self):
        self.title_2_dict = {
            '快速转诊情况': 'critical_situation',
            '危急情况提示': 'critical_situation',
            '主症状描述': 'main_symptom',
            '伴随症状': 'accompanying_symptoms',
            '诊治经过': 'treatment_process',
            '既往史': 'past_history',
            '既往疾病史': 'past_medical_history',
            '既往手术史': 'surgical_history',
            '既往药物过敏史': 'allergy_history',
            '既往输血史': 'blood_transfusion_history',
            '月经婚育史': 'menstrual_history',
            '个人史': 'personal_history',
            '家族史': 'family_history'
        }
        self.option_type_dict = {
            '单选': 'single',
            '多选': 'multiple',
            '单项填空': 'text_select_unit',
            '日期': 'datetime',
            '用户自填': 'text_select_unit',
            '默认单位': 'text_default_unit',
            '其他': 'other'
        }
        self.dict_file_name = './medical_record_collection_data.json'
        self.accompanying_symptoms_details = self.load_detail(base_path + '伴随症状详情表.xlsx')
        self.past_medical_history_details = self.load_detail(base_path + '既往疾病史详情表.xlsx')
        self.personal_history_details = self.load_detail(base_path + '个人史详情表.xlsx')
        self.common_signs = self.load_common_signs()
        self.general_info = self.load_general_info()
        self.examination = self.load_examination()

    def is_null(self, item):
        if not item:
            return True
        if isinstance(item, float) and math.isnan(item):
            return True
        return False

    def trans_sex(self, sex_str):
        if sex_str == '女':
            return '1'
        if sex_str == '男':
            return '2'
        if isinstance(sex_str, float) and math.isnan(sex_str):
            return '*'
        return '*'

    def trans_age(self, age_str):
        if not age_str:
            return "*"
        if isinstance(age_str, float) and math.isnan(age_str):
            return "*"
        re_result = re.findall(r'(\d+)-(\d+)岁', age_str)
        if re_result:
            s, e = re_result[0]
            return "{}-{}".format(int(s) * 365, int(e) * 365)
        raise Exception()

    def trans_options(self, options_str, detail_str):
        options = [{"content": opt, "details": []} for opt in options_str.split('|||')]
        if not detail_str:
            return options
        if isinstance(detail_str, float) and math.isnan(detail_str):
            return options
        if "详见“伴随症状详情表”" in detail_str:
            for opt in options:
                opt['details'] = self.accompanying_symptoms_details.get(opt['content'], [])
            return options
        if "详见“既往疾病史详情表”" in detail_str:
            for opt in options:
                opt['details'] = self.past_medical_history_details.get(opt['content'], [])
        if "详见“个人史详情表”" in detail_str:
            for opt in options:
                opt['details'] = self.personal_history_details.get(opt['content'], [])
            return options

        re_find_result = re.findall(r'#+(.*)#{2,3}(.*)#{2,3}(.*)', detail_str)
        if re_find_result:
            name = re_find_result[0][0]
            detail_type = self.option_type_dict[re_find_result[0][1]]
            detail_options = re_find_result[0][2].split('|||')
            for opt in options:
                if opt['content'] in ('不详', '其他', '无'):
                    opt['details'] = []
                else:
                    opt['details'] = [{'name': name, 'type': detail_type, 'options': detail_options}]
            return options
        return options

    def load_common_signs(self):
        def get_options(content):
            re_find_result = re.findall('#+(.*)#{2,3}(.*)#{2,3}(.*)', content)
            if re_find_result:
                name = re_find_result[0][0]
                option_type = self.option_type_dict[re_find_result[0][1]]
                options = re_find_result[0][2]
            else:
                re_find_result = re.findall('#+(.*)#{2,3}(.*)', content)
                if re_find_result:
                    name = re_find_result[0][0]
                    option_type = 'multiple'
                    options = re_find_result[0][1]
                else:
                    return None
            return {'name': name, 'type': option_type, 'options': options.split('|||')}

        common_sign_detail = {}
        df = pd.read_excel(base_path + '常见异常体征详情表.xlsx', sheetname=0)
        for i in range(df.shape[0]):
            cs = df.iat[i, 0]
            for j in range(df.shape[1]):
                content = df.iat[i, j]
                details = get_options(content)
                if cs not in common_sign_detail:
                    common_sign_detail[cs] = []
                if details:
                    common_sign_detail[cs].append(details)

        res = []
        df = pd.read_excel(base_path + '常见异常体征.xlsx', sheetname=0)
        for i in range(df.shape[0]):
            content = df.iat[i, 0]

            re_find_result = re.findall('#+(.*)#{2,3}(.*)#{2,3}(.*)', content)
            if re_find_result:
                name = re_find_result[0][0]
                option_type = self.option_type_dict[re_find_result[0][1]]
                options = re_find_result[0][2]
            else:
                re_find_result = re.findall('#+(.*)#{2,3}(.*)', content)
                if re_find_result:
                    name = re_find_result[0][0]
                    if name == '其他':
                        option_type = 'other'
                    else:
                        option_type = 'multiple'
                    options = re_find_result[0][1]
                else:
                    continue
            options = [{'sex': '*', 'age': '*', 'items': [{"content": option, "details": common_sign_detail.get(option, [])} for option in options.split('|||')]}]
            res.append({'name': name, 'type': option_type, 'options': options})

        return res

    def load_examination(self):
        res = {'name': '检验指标', 'type': 'multiple'}
        items = []
        df = pd.read_excel(base_path + '检验指标.xlsx', sheetname=0)
        for i in range(df.shape[0]):
            name, option_name, option_type, options = df.iat[i, 0], df.iat[i, 1], df.iat[i, 2], df.iat[i, 3]
            if isinstance(options, float):
                options = ''
            detail = {"name": option_name, "type": self.option_type_dict[option_type], "options": options.split('|||')}
            if items:
                if items[-1]['content'] == name:
                    items[-1]['details'].append(detail)
                    continue
            items.append({"content": name, "details": [detail]})

        res['options'] = [{'age': '*', 'sex': '*', 'items': items}]
        return [res, {'name': '其他检验结果', 'type': 'other', 'options': [{'age': '*', 'sex': '*', 'items': [{'content': '', 'details': []}]}]}]

    def load_general_info(self):
        res = {'name': '心电图', 'type': 'multiple'}
        items = []
        for item in ('正常心电图', '窦性心动过缓', '窦性心动过速', '房室传导阻滞', '房早', '室早', '心房扑动', '房颤', '室速', '室扑', '室颤', '心肌梗死', '预激综合征'):
            items.append({'content': item, 'details': []})
        res['options'] = [{'age': '*', 'sex': '*', 'items': items}]
        return [res, {'name': '其他检查结果', 'type': 'other', 'options': [{'age': '*', 'sex': '*', 'items': [{'content': '', 'details': []}]}]}]

    def load_dict(self):
        '加载问诊模板字典数据'
        with codecs.open(self.dict_file_name, 'r', 'utf-8') as f:
            return json.load(f)

    def save_dict(self, data):
        with codecs.open(self.dict_file_name, 'w', 'utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False))

    def load_detail(self, file_name):
        '加载详情'
        res = {}
        df = pd.read_excel(file_name, sheetname=0)

        for i in range(df.shape[0]):
            key = df.iat[i, 1]
            for j in range(2, df.shape[1]):
                content = df.iat[i, j]
                if self.is_null(content):
                    continue
                re_find_result = re.findall('#+(.*)#{2,3}(.*)#{2,3}(.*)', content)
                if re_find_result:
                    name = re_find_result[0][0]
                    option_type = self.option_type_dict[re_find_result[0][1]]
                    options = re_find_result[0][2]
                    if '用户自填' in options:
                        options = options.replace('用户自填 ', '').strip()
                    if key not in res:
                        res[key] = []
                    res[key].append({'name': name, 'type': option_type, 'options': options.split('|||')})
                    name = name[0]
        return res

    def load_symptom_data(self, file_name):
        res = {}
        df = pd.read_excel(file_name, sheetname=0)

        before_title2, before_title3 = '', ''

        for i in range(df.shape[0]):
            title2 = self.title_2_dict[df.iat[i, 0].strip()]
            title3 = df.iat[i, 1]
            title3 = '' if isinstance(title3, float) and math.isnan(title3) else title3
            option_type = self.option_type_dict[df.iat[i, 2].strip()]
            age = self.trans_age(df.iat[i, 3])
            sex = self.trans_sex(df.iat[i, 4])
            opt1, opt2 = df.iat[i, 5], df.iat[i, 6]
            if isinstance(opt1, float):
                opt1 = ''
            if isinstance(opt2, float):
                opt2 = ''
            options = self.trans_options(opt1, opt2)

            if title2 not in res:
                res[title2] = []

            if (before_title2 == title2) and (before_title3 == title3):
                before_options = res[title2][-1]['options']
                before_options.append({'age': age, 'sex': sex, 'items': options})
            else:
                res[title2].append({'name': title3, 'type': option_type,
                                    'options': [{'age': age, 'sex': sex, 'items': options}]})
            before_title2, before_title3 = title2, title3
        res['common_signs'] = self.common_signs
        res['general_info'] = self.general_info
        res['examination'] = self.examination
        return res

    def update_symptom(self, symptom, file_name):
        data = self.load_symptom_data(file_name)
        ori_data = self.load_dict()
        ori_data[symptom] = data

    def update_all_symptom(self, dir_path):
        dict_info = {}
        for root, _, files in os.walk(dir_path, topdown=False):
            for file_name in files:
                name, ext = os.path.splitext(file_name)
                if not name.startswith('1'):
                    continue
                print('导入 {}'.format(name))
                dict_info[name[1:]] = self.load_symptom_data(os.path.join(root, file_name))
        self.save_dict(dict_info)


if __name__ == '__main__':
    te2d = TemplateExcel2Dict()
    te2d.update_all_symptom(base_path)
    # print(te2d.load_common_signs())
    # res = te2d.load_symptom_data(base_path + '1腹痛.xlsx')
    # print(te2d.load_examination())
    # print(te2d.load_general_info())
