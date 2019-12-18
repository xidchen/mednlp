# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/3/12 9:42
# @Auther:caoxg@<caoxg@guahao.com>
# @File:data_tool_intelligence.py


import os
import sys
import codecs
import global_conf
from mednlp.text.vector import Char2vector, Pinyin2vector, Word2vector
from collections import Counter
from data_tool import data2vector_dept, seg_traindata
from data_tool import data2vector_faq

source_base_path = os.path.join(global_conf.train_data_path, 'order_check_standard')

def load_order_info(file_name):
    """ 加载订单内容
    :file_name: 订单内容存放文件
    :returns: 一个字典，订单id -> 内容
    """
    order_info = {}
    with codecs.open(file_name, 'r', 'utf-8') as f:
        for line in f.readlines():
            items = line.strip().split('\t')
            if len(items) == 2:
                order_info[items[0]] = items[1]

    return order_info

def make_train_data(in_file, out_file, n_limit=sys.maxsize):
    """ 构造训练数据

    :in_file: 输入数据
    :out_file: 保存的文件
    :n_limit: 允许的最大文件长度
    :returns:
    """
    data2vector_faq(in_file, out_file, n_limit, Char2vector(global_conf.dept_classify_char_dict_path))


def get_char_data(file_path, seg_length=37):
    input_file, train_vector_file, seg_file = generate_train_vector_file_path(file_path, train_type='char')
    make_train_data(input_file, train_vector_file)
    seg_traindata(train_vector_file, seg_file, cut_type='cut', seg_length=seg_length)
    return seg_file


def generate_train_vector_file_path(input_file_path, train_type='cnn'):
    if os.path.split(input_file_path)[0]:
        file_path = input_file_path
    else:
        file_path = os.path.join(source_base_path, input_file_path)

    base_path, file_name_path = os.path.split(file_path)
    file_name, extension = os.path.splitext(file_name_path)
    if train_type == 'cnn':
        vector_file_path = os.path.join(base_path, file_name + '_cnn_vector' + extension)
        seg_file_path = os.path.join(base_path, file_name + '_cnn_seg' + extension)
    elif train_type == 'pinyin':
        vector_file_path = os.path.join(base_path, file_name + '_pinyin_vector' + extension)
        seg_file_path = os.path.join(base_path, file_name + '_pinyin_seg' + extension)
    else:
        vector_file_path = os.path.join(base_path, file_name + '_char_vector' + extension)
        seg_file_path = os.path.join(base_path, file_name + '_char_seg' + extension)
    return file_path, vector_file_path, seg_file_path


def get_train_data(file_name):
    input_file = os.path.join(source_base_path, file_name)
    get_char_data(input_file, seg_length=600)


if __name__ == '__main__':
    get_train_data('standard_5_0729_shuf.txt')
