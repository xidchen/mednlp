#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from ailib.utils.exception import AIServiceException
from mednlp.kg.item_value_range import item_normal_range, item_physiological_range, \
    child_item_range, status_2_code, status_2_cue


class OverrunPromptedException(AIServiceException):
    code = 1
    base_message = '超出提示:%s只能输入%s之间的数值'

    def __init__(self, name='', range=''):
        """
        构造函数.
        参数:
        name->参数名称,可空,默认为空字符串.
        value->参数值,可空,默认为空字符串.
        """
        self.message = self.base_message % (name, range)


class ArgumentErrorException(AIServiceException):
    code = 1
    base_message = '参数:%s错误'

    def __init__(self, name=''):
        """
        构造函数.
        参数:
        name->参数名称,可空,默认为空字符串.
        """
        self.message = self.base_message % (name)


def get_status(examination, age, sex):
    gender = sex_2_string(sex)
    years = age_2_range(age)
    examination_status_list = []
    items_list = []
    for item_exam in examination:
        exam_dict = dict()
        if not isinstance(item_exam, dict):
            raise ArgumentErrorException('item_exam')
        value = item_exam.get('value')
        ori_value = value
        try:
            value = float(value)
        except Exception:
            raise ArgumentErrorException('value')
        items = item_exam.get('name')
        new_items = items
        if items == '腰围':
            new_items = items + gender
        value_legal_range = item_physiological_range.get(items)
        is_illegality = '1'
        if value_legal_range:
            if value < float(value_legal_range[0]) or value > float(value_legal_range[1]):
                raise OverrunPromptedException(items, "-".join([str(x) for x in value_legal_range]))
            else:
                is_illegality = '0'
        reference_range = item_exam.get('reference_range')
        # print(reference_range)
        if reference_range:
            if not isinstance(reference_range, dict):
                raise ArgumentErrorException('reference_range')
            status = reference_rage_status(new_items, value, reference_range)
        else:
            if years != 'adult' and items in ['呼吸频率', '脉率']:
                status = child_range_age(items, value, years)
            elif years != 'adult' and items in ['收缩压', '舒张压']:
                status = child_range_pressure(items, value, age)
            else:
                status = match_range(value, item_normal_range.get(new_items))

        exam_dict['examination_name'] = items
        exam_dict['examination_value'] = ori_value
        exam_dict['physiological_range'] = value_legal_range
        exam_dict['is_illegality'] = is_illegality
        exam_dict['examination_status'] = status
        exam_dict['status_code'] = get_status_code(items, status, years)
        examination_status_list.append(exam_dict)
        # print(years, exam_dict)
        items_list.append(items)
    if '收缩压' in items_list and '舒张压' in items_list:
        examination_status_list = updata_dict(examination_status_list)
    examination_dict = get_status_cue(examination_status_list)
    return examination_dict


def sex_2_string(sex):
    if str(sex) == '2':
        gender = '女'
    else:
        gender = '男'
    return gender


def age_2_range(age):
    years = ''
    try:
        day = int(age)
    except Exception:
        raise ArgumentErrorException('age')
    if day <= 28:
        years = 'years0'
    elif day < 365:
        years = 'years1'
    elif day < 365 * 4:
        years = 'years2'
    elif day < 365 * 8:
        years = 'years3'
    elif day <= 365 * 14:
        years = 'years4'
    else:
        years = 'adult'
    return years


def reference_rage_status(items, value, reference_range):
    """
    传入参考范围，返回状态、状态码，具体逻辑
    只传入正常范围，如果实际范围不大于3个, 大于该范围，返回该指标异常高的最坏的状态，小于该范围返回该指标异常低的最坏的状态
    （假如有两个异常高：正常高值和过高，状态选取最后一个过高）,如果大于3个提示范围错误
    传入完整闭环范围，如果给定的范围段和标准范围段相同，则按照对应位置取标准分为段的位置，否则按照只传入正常范围来走，如果值落入高于正常段，
    返回该指标异常高的最坏的状态，落入低于正常段该指标异常低的最坏的状态
    如果范围小于指标实际范围段，提示范围错误
    :param items: 指标名称
    :param value: 指标值
    :param reference_range: 传入范围
    :return: 状态
    """
    status = '正常'
    status_ls = []

    item_status = item_normal_range.get(items)
    if item_status:
        status_ls = list(item_status.keys())
    keys_ls = list(reference_range.keys())
    if reference_range:
        for dkey, dvalue in reference_range.items():
            if value >= dvalue[0] and value <= dvalue[1]:
                status = dkey

    if len(keys_ls) == 1 and keys_ls[0] == '正常':
        value_range = reference_range.get('正常')
        if isinstance(value_range, list):
            value_up = value_range[1]
            value_down = value_range[0]
            if status_ls:
                if value > value_up:
                    status = status_ls[-1]
                elif value < value_down:
                    status = status_ls[0]
    # 状态强制修改为我们默认的了
    elif len(keys_ls) > 1 and status:
        # reference_range_ls = list(reference_range.keys())
        value_key = {value[0]: key for key, value in reference_range.items()}
        reference_range_ls = [value_key[x] for x in sorted(value_key.keys())]
        # print(reference_range_ls, len(status_ls))
        if len(reference_range_ls) == len(status_ls):
            if reference_range_ls.index('正常') == status_ls.index('正常'):
                # print(items, reference_range_ls.index('正常'), status_ls.index('正常'))
                index_status = reference_range_ls.index(status)
                status = status_ls[index_status]
            else:
                raise ArgumentErrorException(str(items) + '的reference_range不完整')
            # print(reference_range_ls, status)
        else:
            if len(status_ls) <= 3:
                # print(items)
                normal_range = reference_range.get('正常')
                if not normal_range:
                    raise ArgumentErrorException(str(items) + '的reference_range不完整')
                if status_ls:
                    if normal_range[1] < value:
                        status = status_ls[-1]
                    elif normal_range[0] > value:
                        status = status_ls[0]
            else:
                raise ArgumentErrorException(str(items) + '的reference_range不完整')
    # print('status', status)
    else:
        raise ArgumentErrorException(str(items) + '的reference_range不完整')
    if not status:
        raise ArgumentErrorException(str(items) + '的reference_range不完整')
    return status


def match_range(value, range_dict):
    status = ''
    if range_dict:
        for dkey, dvalue in range_dict.items():
            if value >= dvalue[0] and value <= dvalue[1]:
                status = dkey
    else:
        status = '正常'
    return status


def child_range_pressure(items, value, age):
    years = int(int(age) / 365)
    status = ''
    systolic = 80 + years * 2
    diastolic = systolic * 2 / 3
    # print('%d天的舒张压：'%age, round(diastolic * 0.8, 4), round(diastolic * 1.2, 4))
    # print("%d天的收缩压："%age,round(systolic * 0.8, 4), round(systolic * 1.2, 4))
    if items == '舒张压':
        if value < round(diastolic * 0.8, 4):
            status = '低血压'
        elif value > round(diastolic * 1.2, 4):
            status = '高血压'
        else:
            status = '正常'
    elif items == '收缩压':
        if value < round(systolic * 0.8, 4):
            status = '低血压'
        elif value > round(systolic * 1.2, 4):
            status = '高血压'
        else:
            status = '正常'
    # print(items, status)
    return status


def child_range_age(items, value, years):
    range_dict = child_item_range.get(years).get(items)
    # print(years, range_dict)
    status = match_range(value, range_dict)
    return status


def updata_dict(examination_status_list):
    examination = []
    new_status = []
    for dict in examination_status_list:
        examination_name = dict['examination_name']
        status = dict['examination_status']
        if examination_name not in ['收缩压', '舒张压']:
            examination.append(dict)
        else:
            new_status.append(status)
    dict_not_status = {'examination_name': '血压', 'physiological_range': [1, 300],
                       'is_illegality': '0'}
    if '高血压' in new_status:
        dict_not_status['examination_status'] = '高血压'
        dict_not_status['status_code'] = '2'
    elif '高值' in new_status:
        dict_not_status['examination_status'] = '高值'
        dict_not_status['status_code'] = '1'
    elif '低血压' in new_status:
        dict_not_status['examination_status'] = '低血压'
        dict_not_status['status_code'] = '-2'
    else:
        dict_not_status['examination_status'] = '正常'
        dict_not_status['status_code'] = '0'
    examination.append(dict_not_status)

    return examination


def get_status_code(entity_name, entity_status, years):
    status_code = ''
    # if entity_name in ['呼吸频率', '脉率'] and years != 'adult':
    #     if entity_status == '过高':
    #         status_code = '1'
    #     elif entity_status == '低值':
    #         status_code = '-1'
    #     else:
    #         status_code = '0'
    if entity_name in ['血氧饱和度']:
        if entity_status == '过低':
            status_code = '2'
        elif entity_status == '低值':
            status_code = '-1'
        else:
            status_code = '0'
    else:
        status_code = status_2_code.get(entity_status, '0')

    return status_code


def get_status_cue(examination_dict):
    if examination_dict:
        for exam_dict in examination_dict:
            name = exam_dict.get('examination_name')
            status_code = exam_dict.get('status_code')
            cue_txt = ''
            try:
                cue_txt = status_2_cue.get(name).get(status_code, '')
            except:
                pass
            exam_dict['cue_words'] = cue_txt
    return examination_dict


if __name__ == '__main__':
    items = [
        {"name": "舒张压",
         "reference_range": {
             "正常": [37.6, 41]
         },
         "value": "34"}
        , {
            "name": "身高",
            "value": "159",
            "reference_range": {
                "正常": [37.6, 41]
            },
        }
    ]
    age = 365 * 2
    sex = 2
    result = get_status(items, age, sex)
    print(result)
