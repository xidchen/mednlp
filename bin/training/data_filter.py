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


max_number = sys.maxint
output1_file = 'result1.txt'
output2_file = 'result2.txt'
save_accuracy = 'save_accuracy.txt'
tc_b = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
base_path = os.path.dirname(__file__)
data_source_path = os.path.join(base_path, '../../data/traindata/traindata_dept_classify.txt')
data_valid_path = os.path.join(base_path, '../../data/traindata/traindata_dept_classify_valid.txt')
data_error_path = os.path.join(base_path, '../../data/traindata/traindata_dept_classify_error.txt')
data_true_path = os.path.join(base_path, '../../data/traindata/traindata_dept_classify_true.txt')
data_false_path = os.path.join(base_path, '../../data/traindata/traindata_dept_classify_false.txt')
input_file = data_source_path
data_union_path = os.path.join(base_path, '../../data/traindata/traindata_dept_classify_union.txt')


def get_valid_data(data_source_path, data_valid_path):
    """
    对原有的训练数据进行过滤，拆分为有效数据和无效数据
    :param data_source_path: 原始训练数据文件所在地
    :param data_valid_path: 所有可以用来训练的文件
    :param data_error_path: 所有不可以用来训练的数据
    :return:无
    """
    source_file = codecs.open(data_source_path, 'r', encoding='utf-8')
    valid_file = codecs.open(data_valid_path, 'w', encoding='utf-8')
    error_file = codecs.open(data_error_path, 'w', encoding='utf-8')
    for count, line in enumerate(source_file):
        line_list = line.strip().split('\t')
        if len(line_list) < 4:
            error_file.write(line)
            continue
        valid_file.write(line)
    print 'count:', (count+1)


def get_true_data(data_valid_path, data_true_path):
    """
    对于有效训练数据利用现有的模型进行预测，对于预测概率大于0.7且标注数据和预测结果不一样的数据，去掉
    :param data_valid_path: 有效训练数据路径
    :param data_true_path: 去除预测概率大于0.7且标注数据和预测结果不一样的数据后的，数据保存陆行
    :return:无返回值
    """
    valid_file = codecs.open(data_valid_path, 'r', encoding='utf-8')
    true_file = codecs.open(data_true_path, 'w', encoding='utf-8')
    false_file = codecs.open(data_false_path, 'w', encoding='utf-8')
    true_count = 0
    false_count = 0
    for count, line in enumerate(valid_file):
        line_list = line.strip().split('\t')
        content = line_list[0]
        dept_name = line_list[3]
        classify_result_b = tc_b.query({'q': content.encode('utf-8')}, service='dept_classify')
        try:
            data = classify_result_b.get('data')
            pre_dept_name = data[0].get('dept_name')

            if pre_dept_name != 'unknow' and pre_dept_name != dept_name:
                    pre_dept_name_pro = data[0].get('score')
                    if pre_dept_name_pro >= 0.7:
                        false_file.write(line.strip()+'\t'+pre_dept_name+'\n')
                        false_count = false_count + 1
                    else:
                        true_file.write(line)
                        true_count = true_count + 1
            else:
                true_file.write(line)
                true_count = true_count + 1
        except:
            true_file.write(line)
            true_count = true_count + 1
    print 'total_count:', (count+1)
    print 'true_count:', true_count
    print 'false_count', false_count


if __name__ == "__main__":
    """
    confidenc>=0 and confidence <1 
    """
    get_true_data(data_valid_path, data_true_path)
