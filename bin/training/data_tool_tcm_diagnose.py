# ！/usr/bin/env python
# -*- coding：utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-23 Tuesday
@Desc: 中医诊断训练数据处理
"""

import os
import sys
import codecs
import global_conf
from mednlp.text.vector import Char2vector, Pinyin2vector, Word2vector
from data_tool import seg_traindata
from optparse import OptionParser

source_base_path = os.path.join(global_conf.train_data_path, 'tcm_diagnose')


def make_train_data(in_file, out_file, data_type, n_limit=sys.maxsize, vector_type='char'):
    """
    把原始数据转化为词向量
    :param in_file: => 原始训练文件
    :param out_file: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :param x_vector:请求转为为词向量的词典
    :return: 无返回值
    """
    disease_name_no = {}
    dict_name = global_conf.tcm_disease_path
    if data_type == '2':
        dict_name = global_conf.tcm_syndrome_path
    with codecs.open(dict_name, 'r', 'utf-8') as f:
        for i, line in enumerate(f.readlines()):
            disease_name_no[line.strip().split('=')[0]] = str(i)

    if vector_type == 'pinyin':
        x_vector = Pinyin2vector()
    elif vector_type == 'cnn':
        x_vector = Word2vector()
    else:
        x_vector = Char2vector(global_conf.dept_classify_char_dict_path)

    with codecs.open(out_file, 'w', 'utf-8') as fo:
        with codecs.open(in_file, 'r', 'utf-8') as fi:
            count = 0
            for line in fi.readlines():
                if count > n_limit:
                    break
                count += 1
                items = line.strip().split('\t')
                if len(items) != 4:
                    continue
                vectors = x_vector.get_vector(items[3])
                if not vectors:
                    continue
                fo.write('{} {}\n'.format(disease_name_no[items[0]], ",".join(vectors)))

def get_char_data(file_path, data_type=1, seg_length=600):
    input_file, train_vector_file, seg_file = generate_train_vector_file_path(file_path, train_type='char')
    make_train_data(input_file, train_vector_file, data_type)
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


def get_train_data(file_name, data_type):
    input_file = os.path.join(source_base_path, file_name)
    get_char_data(input_file, data_type, seg_length=600)


if __name__ == '__main__':
    # get_train_data('tcm_mr_train.txt')
    command = """\n python %s [-d -c config_file]""" % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-d', '--data', dest='data_file', default='tcm_mr_train.txt', help='data file', metavar='FILE')
    parser.add_option("-t", "--type", dest="data_type", default='1', help="类型 1-疾病  2-证型")
    (options, args) = parser.parse_args()
    get_train_data(options.data_file, options.data_type)
