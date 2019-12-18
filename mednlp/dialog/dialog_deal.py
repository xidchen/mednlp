#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dialog_deal.py -- the deal of dialog
处理琐碎的信息
Author: renyx <renyx@guahao.com>
Create on 2018-08-21 Tuesday.
"""
import sys
import global_conf
import mednlp.dialog.dialog_constant as constant
from mednlp.utils.utils import unicode2str

import re

age_pattern = re.compile('\D')


def deal_diagnose_service_age(age_str, **kwargs):
    """
    处理age字符串
    24 岁 = 24 * 365
    :param age_str:   24天
    :return: 天数
    """
    unit = 1
    if constant.OPTION_TIME_YEAR_OF_AGE in age_str:
        unit = 365
    elif constant.OPTION_TIME_MONTH in age_str:
        unit = 30
    try:
        days = int(age_pattern.sub("", age_str))
        days *= unit
    except:
        raise Exception("诊断服务年龄计算失败")
    return days


def deal_cause(symptom_name, values, **kwargs):
    """
    处理诱因
    :param symptom_name:
    :param values:
    :return:
    if not values，return ''
    if values & is_single = 1:
        if values[0] == 不明原因 : return 无明显诱因
        else: values length = 1
    else：deal values
    """
    if not values:
        return ''
    dialog_template, is_single = dialog_property.get('cause')
    dialog_padding = {'name': symptom_name}
    if len(values) == 1 and constant.OPTION_FUZZY_NO_CAUSE == unicode2str(values[0]):
        return '无明显诱因'
    else:
        dialog_padding['value'] = '、'.join(values)
    return dialog_template % dialog_padding


def deal_other_symptom_mutex(symptom_value, diagnose_symptom, **kwargs):
    """
    清理掉具有包含关系的其他症状
    :param symptom_value:
    :param diagnose_symptom:
    :return:
    """
    other_symptom_result = []
    for diagnose_symptom_temp in diagnose_symptom:
        other_symptom_temp = diagnose_symptom_temp
        for symptom_temp in symptom_value:
            if diagnose_symptom_temp in symptom_temp or symptom_temp in diagnose_symptom_temp:
                other_symptom_temp = None
                break
        if other_symptom_temp:
            other_symptom_result.append(other_symptom_temp)
    return other_symptom_result

# 1 表示单值 2表示多值
dialog_property = {
    'time_happen': ('%(value)s前', 1),
    'body_part': ('位于%(value)s部位，', 2),
    'alleviate': ('%(value)s缓解，', 2),
    'cause': ('因%(value)s', 2),
    'frequence': ('频次%(value)s，', 1),
    'degree': ('程度%(value)s，', 1),
    'exacerbation': ('%(value)s加重，', 2)
}
# 自诊
dialog_property_auto_diagnose = {
    'time_happen': ('%(value)s', 1),
    'body_part': ('位于%(value)s部位，', 2),
    'alleviate': ('%(value)s缓解，', 2),
    'cause': ('因%(value)s', 2),
    'frequence': ('频次%(value)s，', 1),
    'degree': ('程度%(value)s，', 1),
    'exacerbation': ('%(value)s加重，', 2)
}



dialog_property_order = [('time_happen', None),
                         ('cause', deal_cause),
                         ({'other': '出现%(name)s，'}, None),
                         ('body_part', None),
                         ('frequence', None),
                         ('degree', None),
                         ('alleviate', None),
                         ('exacerbation', None)]
if __name__ == '__main__':
    import global_conf
    import configparser

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(global_conf.cfg_path)
    organization = config.items('XwyzOrganization')[0][1]
    organization_doctor = config.items('XwyzDoctorOrganization')[0][1]
    print(organization)