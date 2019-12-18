# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/3/12 9:42
# @Auther:caoxg@<caoxg@guahao.com>
# @File:data_tool_intelligence.py


import sys
import codecs
import random
import global_conf
from mednlp.text.vector import Char2vector, Pinyin2vector, Word2vector
import os
from collections import Counter
from data_tool import data2vector_dept, seg_traindata
from data_tool import data2vector_faq

source_base_path = os.path.join(global_conf.train_data_path, 'similarity_faq')
train_path = os.path.join(source_base_path, 'similarity_ask_190617_shuf.txt')


def select_best_length():
    """
    选取合适的序列长度进行训练
    :return:
    """
    len_list = []
    max_length = 0
    cover_rate = 0.0
    for line in codecs.open(train_path, 'r', encoding='utf-8'):
        line = line.strip().split('==')
        if not line:
            continue
        sent = line[1]
        sent_len = len(sent)
        len_list.append(sent_len)
    all_sent = len(len_list)
    sum_length = 0
    len_dict = Counter(len_list).most_common()
    for i in len_dict:
        sum_length += i[1] * i[0]
    average_length = sum_length / all_sent
    for i in len_dict:
        rate = i[1] / all_sent
        cover_rate += rate
        if cover_rate >= 0.9:
            max_length = i[0]
            break
    print('average_length:', average_length)
    print('max_length:', max_length)
    return max_length


def train_data_char(infile, outfile, n_limit=sys.maxsize):
    """
    :param infile: => 原始训练文件
    :param outfile: => 根据字符字典转化为词向量的文件
    :param n_limit: 允许的最大文件长度
    :return: 无返回值
    """
    data2vector_faq(infile, outfile, n_limit, Char2vector(global_conf.dept_classify_char_dict_path))


def train_data_pinyin(infile, outfile, n_limit=sys.maxsize):
    """
    把原始数据转化为词向量
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :return: 无返回值
    """
    data2vector_faq(infile, outfile, n_limit, Pinyin2vector())


def train_data_cnn(infile, outfile, n_limit=sys.maxsize):
    """
       把原始数据转化为词向量
       :param infile: => 原始训练文件
       :param outfile: =>  按照分词词典转化为词向量的文件
       :param n_limit: 允许的最大文件长度
       :return: 无返回值
       """
    data2vector_faq(infile, outfile, n_limit, Word2vector(global_conf.dept_classify_cnn_dict_path))


def get_char_data(file_path='medical_record_dept_train_union.txt', seg_length=37):
    input_file, train_vector_file, seg_file = generate_train_vector_file_path(file_path, train_type='char')
    train_data_char(input_file, train_vector_file)
    seg_traindata(train_vector_file, seg_file,
                  cut_type='cut', seg_length=seg_length)
    return seg_file


def get_pinyin_data(file_path='dept_classify_all_cnn_20180621.txt', seg_length=37):
    """
    把原始文件转化为词向量，分为转词向量和拆分成固定长度的向量两部分
    :param seg_length: 每句话拆分的词向量长度
    :return: 无返回值
    """
    input_file, train_vector_file, seg_file = generate_train_vector_file_path(file_path, train_type='pinyin')
    train_data_pinyin(input_file, outfile=train_vector_file)
    seg_traindata(train_vector_file, outfile=seg_file,
                  cut_type='cut', seg_length=seg_length)
    return seg_file


def get_cnn_data(file_path='dept_classify_all_cnn_20180621.txt', seg_length=37):
    """
    把原始文件转化为词向量，分为转词向量和拆分成固定长度的向量两部分
    :param seg_length: 每句话拆分的词向量长度
    :return: 无返回值
    """
    input_file, train_vector_file, seg_file = generate_train_vector_file_path(file_path, train_type='cnn')
    train_data_cnn(input_file, outfile=train_vector_file)
    seg_traindata(train_vector_file, outfile=seg_file,
                  cut_type='cut', seg_length=seg_length)
    return seg_file


def generate_train_file_path(input_file_path):
    """
    根据input_file_path按照在文件名后面加入train和test生成训练文件目录和测试文件目录
    :param input_file_path: 输入文件名
    :return: 返回原始文件目录，训练文件目录，测试文件目录
    """
    # base_path = '/home/caoxg/work/mednlp/data/traindata/intelligent_service'
    if os.path.split(input_file_path)[0]:
        file_path = input_file_path
    else:
        file_path = os.path.join(source_base_path, input_file_path)

    base_path, file_name_path = os.path.split(file_path)
    file_name, extension = os.path.splitext(file_name_path)

    train_file_path = os.path.join(base_path, file_name + '_train'+extension)
    test_file_path = os.path.join(base_path, file_name + '_test' + extension)
    return file_path, train_file_path, test_file_path


def generate_train_vector_file_path(input_file_path, train_type='cnn'):
    if os.path.split(input_file_path)[0]:
        file_path = input_file_path
    else:
        file_path = os.path.join(source_base_path, input_file_path)

    base_path, file_name_path = os.path.split(file_path)
    file_name, extension = os.path.splitext(file_name_path)
    if train_type == 'cnn':
        vector_file_path = os.path.join(base_path, file_name + '_cnn_vector'+extension)
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
    get_char_data(input_file, seg_length=37)
    get_cnn_data(input_file, seg_length=37)
    get_pinyin_data(input_file, seg_length=37)


if __name__ == '__main__':
    get_train_data('similarity_ask_190711_shuf.txt')
