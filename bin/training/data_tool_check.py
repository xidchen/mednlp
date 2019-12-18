# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/3/18 15:55
# @Auther:caoxg@<475586711@qq.com>
# @File:data_tool_check.py


import xlrd
import sys
import codecs
import global_conf
from mednlp.text.vector import Char2vector, Pinyin2vector, Word2vector
import os
from data_tool import seg_traindata


base_path = '/home/caoxg/work/mednlp/data/traindata/check'


def transform(num):
    """
    :param num: 输入数字或者字段
    :return: 返回整数
    """
    if not num:
        num = 0
    else:
        try:
            num = int(num)
            # print(num)
        except Exception:
            # print(num)
            num = None

    return num


def xls_to_txt(file_name):
    """
    把文件从xls 转化为txt
    :param file_name: 文件名
    :return:无
    """
    name, dex = os.path.splitext(file_name)
    input_name = os.path.join(base_path, file_name)
    output_name = os.path.join(base_path, name + '.txt')
    data = xlrd.open_workbook(input_name)
    table = data.sheet_by_index(0)
    out_format = '%s\t%s\t%s\t%s\t%s\t%s\n'
    output_file = codecs.open(output_name, 'w', encoding='utf-8')
    nrows = table.nrows
    count = 0
    for i in range(1, nrows):
        order_id = str(table.row_values(i)[0]).strip()
        order_len = len(str(order_id).strip().split('/'))
        if order_len > 1:
            count = count + 1
            continue
        activate = table.row_values(i)[4]
        disease_analysis = table.row_values(i)[5]
        clear_advice = table.row_values(i)[6]
        have_temperature = table.row_values(i)[7]
        further = table.row_values(i)[8]
        print('before', activate)
        activate = transform(activate)
        print('after', activate)

        disease_analysis = transform(disease_analysis)
        if disease_analysis is None:
            continue
        clear_advice = transform(clear_advice)
        if clear_advice is None:
            continue
        have_temperature = transform(have_temperature)
        if have_temperature is None:
            continue
        further = transform(further)
        if further is None:
            continue
        line = out_format % (order_id, activate, disease_analysis, clear_advice, have_temperature, further)
        output_file.write(line)
    print(count)


def get_order_id(input_names, output_name):
    """
    把多个文件写入到一个文件里
    :param input_names: 文件名list
    :param output_name: 输出文件名
    :return: 返回无
    """
    result = []
    file_names = []
    for file in input_names:
        file_names.append(os.path.join(base_path, file))
    output_name = os.path.join(base_path, output_name)
    output_file = codecs.open(output_name, 'w', encoding='utf-8')
    for file in file_names:
        f = codecs.open(file, 'r', encoding='utf-8')
        for line in f:
            # lines = line.strip().split('\t')
            # sentence = lines[0]
            # result.append(sentence)
            sentence = line
            output_file.write(sentence)


def split_file_name(input_name):
    """
    把一个文件按照列拆分为多个文件
    :param input_name: 文件名
    :return: 无
    """
    input = os.path.join(base_path, input_name)
    input_file = codecs.open(input, 'r', encoding='utf-8')
    outformat = '%s\t%s\n'
    output_1 = codecs.open(os.path.join(base_path, 'test_1.txt'), 'w', encoding='utf-8')
    output_2 = codecs.open(os.path.join(base_path, 'test_2.txt'), 'w', encoding='utf-8')
    output_3 = codecs.open(os.path.join(base_path, 'test_3.txt'), 'w', encoding='utf-8')
    output_4 = codecs.open(os.path.join(base_path, 'test_4.txt'), 'w', encoding='utf-8')
    output_5 = codecs.open(os.path.join(base_path, 'test_5.txt'), 'w', encoding='utf-8')

    for line in input_file:
        lines = line.strip().split('\t')
        if len(lines) != 6:
            print(line)
            continue
        outline_1 = outformat % (lines[0], lines[1])
        outline_2 = outformat % (lines[0], lines[2])
        outline_3 = outformat % (lines[0], lines[3])
        outline_4 = outformat % (lines[0], lines[4])
        outline_5 = outformat % (lines[0], lines[5])
        output_1.write(outline_1)
        output_2.write(outline_2)
        output_3.write(outline_3)
        output_4.write(outline_4)
        output_5.write(outline_5)


def data2vector_dept(infile, outfile, n_limit=sys.maxsize,
                     x_vector=None, y_vector=None):
    """
    把原始数据转化为词向量
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :param x_vector:请求转为为词向量的词典
    :param y_vector:预测科室转化为词向量的词典
    :return: 无返回值
    """
    outfile = codecs.open(outfile, 'w', encoding='utf-8')
    line_format = '%s %s\n'
    fin = codecs.open(infile, 'r', encoding='utf-8')
    count = 0
    for line in fin:
        if count > n_limit:
            break
        count += 1
        line_items = line.split('==')
        if len(line_items) != 2:
            continue
        department = line_items[0].strip()
        department = str(department)
        content = line_items[1]
        words = x_vector.get_vector(content)
        if not words:
            continue
        line = line_format % (department, ','.join(words))
        outfile.write(line)
    fin.close()
    outfile.close()


def train_data_char(infile, outfile, n_limit=sys.maxsize):
    """
    :param infile: => 原始训练文件
    :param outfile: => 根据字符字典转化为词向量的文件
    :param n_limit: 允许的最大文件长度
    :return: 无返回值
    """
    dept_dict = global_conf.dept_classify_dept_path
    data2vector_dept(infile, outfile, n_limit,
                     Char2vector(global_conf.dept_classify_char_dict_path))


def get_add_name(file_name, add='seg'):
    """
    :param file_name: 文件名
    :param add: 需要加入到文件名中的内容
    :return: 返回原文件名和拼装以后的文件名
    """
    name, edx = os.path.splitext(file_name)
    target_name = name + '_' + add + edx
    return file_name, target_name


def get_source_name(file_name, base_path=''):
    if not base_path:
         base_path = '/home/caoxg/work/mednlp/data/traindata/check'
    file_path = os.path.join(base_path, file_name)
    return file_path


def get_file_hander(file_name, type='r'):
    input = codecs.open(file_name, type, encoding='utf-8')
    return input


def get_data_vector(file_name):
    file = get_source_name(file_name)
    _, vector_file = get_add_name(file_name, add='vector')
    _, seg_file = get_add_name(vector_file, add='seg')
    seg = get_source_name(seg_file)
    vector = get_source_name(vector_file)
    train_data_char(file, vector)
    seg_traindata(vector, seg, cut_type='cut', seg_length=600)


if __name__ == '__main__':
    # xls_to_txt('test_24.xlsx')
    # xls_to_txt('test_32.xlsx')
    # xls_to_txt('test_39.xlsx')
    # get_order_id(['test_24.txt', 'test_32.txt', 'test_39.txt'], 'test_all.txt')
    # split_file_name('test_all.txt')
    # input = os.path.join(base_path, 'test_5_save.txt')
    # output = os.path.join(base_path, 'test_5_train_vector.txt')
    # train_data_char(input, output)
    # vector, seg = get_add_name('test_5_train_vector.txt')
    # vector_path = get_source_name(vector)
    # seg_path = get_source_name(seg)
    # seg_traindata(infile=vector_path, outfile=seg_path, cut_type='cut', seg_length=600)
    # result = get_split_data('test_3_train_vector_seg.txt')
    # for key, value in result.items():
    #     print(key, len(value))
    # a, b = get_split_train_test_num(result)
    # for key, value in a.items():
    #     print(key, len(value))
    # for key, value in b.items():
    #     print(key, len(value))
    # get_split_train_test('test_5_train_vector_seg.txt')
    get_data_vector('test_1_save_train.txt')
    get_data_vector('test_1_save_test.txt')
    get_data_vector('test_2_save_train.txt')
    get_data_vector('test_2_save_test.txt')
    get_data_vector('test_3_save_train.txt')
    get_data_vector('test_3_save_test.txt')
    get_data_vector('test_4_save_train.txt')
    get_data_vector('test_4_save_test.txt')
    get_data_vector('test_5_save_train.txt')
    get_data_vector('test_5_save_test.txt')
