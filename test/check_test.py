#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-03-08 星期四.
"""

import sys
import os
from optparse import OptionParser
import codecs
import global_conf
from ailib.client.ai_service_client import AIServiceClient


cfg_path = global_conf.cfg_path
tc_b = AIServiceClient(cfg_path=cfg_path, service='AIService', port=3638)
base_path = '/ssddata/testdata/mednlp/check_consult'
data_source_path = os.path.join(base_path, 'check_doctor_test_union_unique.txt')
data_true_path = os.path.join('check_doctor_test_union_unique_out.txt')


format = '%s=%s=%s\n'

check_code_dict = {
    u'违反规则17': '17',
    u'违反规则15': '15',
    u'违反规则22': '22',
    u'未违反规则': '0'
}


def get_pred_data(data_valid_path):
    """
    对于有效训练数据利用现有的模型进行预测，对于预测概率大于0.7且标注数据和预测结果不一样的数据，去掉
    :param data_valid_path: 有效训练数据路径
    :param data_true_path: 去除预测概率大于0.7且标注数据和预测结果不一样的数据后的，数据保存陆行
    :return: 无返回值
    """
    valid_file = codecs.open(data_valid_path, 'r', encoding='utf-8')
    output_data = codecs.open(data_true_path, 'w', encoding='utf-8')
    true_count = 0
    valid_count = 0
    count = 0
    count_two = 0
    for line in valid_file:
        count = count + 1
        line_list = line.strip().split('\t')
        content = line_list[0]
        dept_name = line_list[3]
        dept_name_code = check_code_dict.get(dept_name)
        if not sys.version > '3':
            content = content.encode('utf-8')
        classify_result_b = tc_b.query({'q': content}, service='check_consult')
        try:
            data = classify_result_b.get('data')
            pre_dept_name = data.get('check_code')
            valid_count = valid_count + 1
            if pre_dept_name != 'unknow' and dept_name_code in pre_dept_name:
                true_count = true_count + 1
        except:
            print('error')
    print('count:', count)
    print('valid_count', valid_count)
    print('true_count', true_count)
    print('count_two', count_two)


def get_single_pred_data(data_valid_path):
    """
    对于有效训练数据利用现有的模型进行预测，对于预测概率大于0.7且标注数据和预测结果不一样的数据，去掉
    :param data_valid_path: 有效训练数据路径
    :param data_true_path: 去除预测概率大于0.7且标注数据和预测结果不一样的数据后的，数据保存陆行
    :return: 无返回值
    """
    valid_file = codecs.open(data_valid_path, 'r', encoding='utf-8')
    output_data = codecs.open(data_true_path, 'w', encoding='utf-8')
    true_count = 0
    valid_count = 0
    count = 0
    count_two = 0
    for line in valid_file:
        count = count + 1
        line_list = line.strip().split('\t')
        content = line_list[0]
        dept_name = line_list[3]
        dept_name_code = check_code_dict.get(dept_name)
        if not sys.version > '3':
            content = content.encode('utf-8')
        classify_result_b = tc_b.query({'q': content}, service='check_consult')
        try:
            data = classify_result_b.get('data')
            pre_dept_name = data.get('check_code')
            valid_count = valid_count + 1
            out_line = format % (content, dept_name_code, "#".join(pre_dept_name))
            output_data.write(out_line)
            if pre_dept_name != 'unknow' and len(pre_dept_name) == 1 and dept_name_code == pre_dept_name[0]:
                print(dept_name_code, pre_dept_name[0])
                true_count = true_count + 1
        except:
            print('error')
    print('count:', count)
    print('valid_count', valid_count)
    print('true_count', true_count)
    print('count_two', count_two)


def get_concat_data(data_source_path):
    """
    主要是把单一的测试数据标签，相同的数据整成统一的格式，原理有两个标签的记录，重新写成两个标签，一个记录
    :param data_source_path: 
    :return: 
    """
    input_data = codecs.open(data_source_path, 'r', encoding='utf-8')
    input_data_dict = {}
    count = 0
    for line in input_data:
        count = count + 1
        lines = line.strip().split('\t')
        content = lines[0]
        check_label = lines[3]
        check_label_code = check_code_dict.get(check_label)
        if content not in input_data_dict:
            input_data_dict[content] = [check_label_code]
        else:
            input_data_dict[content].append(check_label_code)
    return input_data_dict


def get_equal_list(a, b):
    if len(a) != len(b):
        return False
    else:
        a_list = set(a)
        b_list = set(b)
        set_list = list(set(a) & set(b))
        if len(set_list) == len(a_list):
            return True
        else:
            return False


def get_mul_label_pre_data(data_source_path):
    result = get_concat_data(data_source_path)
    output_data = codecs.open(data_true_path, 'w', encoding='utf-8')
    true_count = 0
    valid_count = 0
    count = 0
    for key, values in result.items():
        count = count + 1
        classify_result_b = tc_b.query({'q': key.encode('utf-8')}, service='check_consult')
        try:
            valid_count = valid_count + 1
            data = classify_result_b.get('data')
            pre_dept_name = data.get('check_code')
            print(pre_dept_name, values)
            out_line = format % (key, "#".join(values), "#".join(pre_dept_name))
            output_data.write(out_line)
            if pre_dept_name != 'unknow' and get_equal_list(pre_dept_name, values):
                true_count = true_count + 1
        except:
            print('error')

    print('count:', count)
    print('valid_count', valid_count)
    print('true_count', true_count)


if __name__ == "__main__":
    """
    confidenc>=0 and confidence <1 
    """
    get_pred_data(data_source_path)
    # get_mul_label_pre_data(data_source_path)