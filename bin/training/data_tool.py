#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
data_tool.py -- some tool for data

Author: maogy <maogy@guahao.com>
Create on 2017-05-27 Saturday.
"""

import csv
import sys
import math
import numpy
import codecs
import random
import global_conf
from optparse import OptionParser
from ailib.storage.db import DBWrapper
from mednlp.dao.kg_dao import KGDao
from mednlp.dataset.padding import pad_sentences
from mednlp.text.mmseg import MMSeg
from mednlp.text.neg_filter import filter_negative
from mednlp.text.vector import Char2vector, Pinyin2vector, Word2vector
from mednlp.text.vector import Dept2Vector, Label2Vector
from mednlp.text.vector import get_sex_to_vector, get_age_to_vector_for_lstm
import os


def file_operation():
    file1 = 'dept_classification.csv'
    file2 = 'disease_id_name.csv'
    file3 = 'disease_id_dept.csv'

    with open(file1, 'r') as f1, open(file2, 'r') as f2, open(file3, 'w') as f3:
        reader1 = csv.reader(f1)
        dict1 = {row[0]: row[1:] for row in reader1}
        reader2 = csv.reader(f2)
        dict2 = {row[1]: row[0] for row in reader2}
        for key1 in dict1:
            for key2 in dict2:
                if key1 == key2:
                    output = key1 + ',,' + dict2[key2] + ',,' + \
                             '|'.join(filter(None, dict1[key1]))
                    print(f3, output)


def disease_classify_vector(infile, outfile, n_limit=sys.maxsize):
    disease_dict = global_conf.disease_classify_dict_path
    data2vector(infile, outfile, n_limit,
                Char2vector(global_conf.char_vocab_dict_path),
                Label2Vector(disease_dict))


def disease_classify_vector_sexandage(infile, outfile, n_limit=sys.maxsize):
    disease_dict = global_conf.disease_classify_dict_path
    data2vector_sexandage(infile, outfile, n_limit,
                          Char2vector(global_conf.char_vocab_dict_path),
                          Label2Vector(disease_dict))


def disease_classify_vector_history(infile, outfile, n_limit=sys.maxsize):
    disease_dict = global_conf.disease_classify_dict_path
    data2vector_history(infile, outfile, n_limit,
                        Char2vector(global_conf.char_vocab_dict_path),
                        Label2Vector(disease_dict))


def disease_classify_vector_examination(infile, outfile, n_limit=sys.maxsize):
    disease_dict = global_conf.disease_classify_dict_path
    data2vector_examination(infile, outfile, n_limit,
                            Char2vector(global_conf.char_vocab_dict_path),
                            Label2Vector(disease_dict))


def train_data_char(infile, outfile, n_limit=sys.maxsize):
    """
    :param infile: => 原始训练文件
    :param outfile: => 根据字符字典转化为词向量的文件
    :param n_limit: 允许的最大文件长度
    :return: 无返回值
    """
    dept_dict = global_conf.dept_classify_dept_path
    data2vector_dept(infile, outfile, n_limit,
                     Char2vector(global_conf.dept_classify_char_dict_path),
                     Dept2Vector(dept_dict))


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
        line_items = line.split('\t')
        if len(line_items) != 4:
            continue
        department = line_items[3].strip()
        department = str(department.encode('utf-8'))
        if not y_vector.check_value(department):
            print('not available label:', department)
            continue
        content = line_items[0]
        words = x_vector.get_vector(content)
        if not words:
            continue
        line = line_format % (
            str(y_vector.get_vector(department)), ','.join(words))
        outfile.write(line)
    print(count)
    fin.close()
    outfile.close()


def data2vector_faq(infile, outfile, n_limit=sys.maxsize, x_vector=None):
    """
    把原始数据转化为词向量
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :param x_vector:请求转为为词向量的词典
    :return: 无返回值
    """
    with codecs.open(outfile, 'w', 'utf-8') as fo:
        with codecs.open(infile, 'r', 'utf-8') as fi:
            count = 0
            for line in fi.readlines():
                if count > n_limit:
                    break
                count += 1
                items = line.strip().split('==')
                if len(items) != 2:
                    continue
                vectors = x_vector.get_vector(items[1])
                if not vectors:
                    continue
                fo.write('{} {}\n'.format(items[0], ",".join(vectors)))


def data2vector(infile, outfile, n_limit=sys.maxsize,
                x_vector=None, y_vector=None):
    """
    把原始数据转化为词向量
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :param x_vector:
    :param y_vector:
    :return: 无返回值
    """
    kgd = KGDao()
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    label_alias = kgd.load_disease_alias(db)
    outfile = codecs.open(outfile, 'w')
    line_format = '%s %s\n'
    fin = codecs.open(infile)
    for count, line in enumerate(fin):
        if count > n_limit:
            break
        line_items = str(line).strip().split('\t')
        if len(line_items) < 4:
            continue
        label = line_items[3]
        if label in label_alias:
            label = label_alias[label]
        if not y_vector.check_value(label):
            continue
        words = x_vector.get_vector(line_items[0])
        if not words:
            continue
        line = line_format % (y_vector.get_vector(label), ','.join(words))
        outfile.write(line)
    outfile.close()


def data2vector_sexandage(infile, outfile, n_limit=sys.maxsize,
                          x_vector=None, y_vector=None):
    """
    把原始数据转化为词向量，考虑性别年龄
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :param x_vector:
    :param y_vector:
    :return: 无返回值
    """
    seq_len = 600
    max_len = seq_len - 6
    kgd = KGDao()
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    label_alias = kgd.load_disease_alias(db)
    outfile = codecs.open(outfile, 'w')
    line_format = '%s %s\n'
    fin = codecs.open(infile)
    for count, line in enumerate(fin):
        if count > n_limit:
            break
        line_items = str(line).strip().split('\t')
        if len(line_items) < 4:
            continue
        label = line_items[3]
        if label in label_alias:
            label = label_alias[label]
        if not y_vector.check_value(label):
            continue
        words = x_vector.get_vector(line_items[0])
        if not words:
            continue
        sex = get_sex_to_vector(line_items[1])
        age = get_age_to_vector_for_lstm(line_items[2])
        words = words[:max_len]
        sep = ['0'] * 2
        words.extend(sep + [sex] + sep + [age])
        line = line_format % (y_vector.get_vector(label), ','.join(words))
        outfile.write(line)
    outfile.close()


def data2vector_history(infile, outfile, n_limit=sys.maxsize,
                        x_vector=None, y_vector=None):
    """
    把原始数据转化为词向量，在考虑性别年龄的基础上，还考虑既往史
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :param x_vector:
    :param y_vector:
    :return: 无返回值
    """
    seq_len = 550
    max_len = seq_len - 6
    history_len = 50
    kgd = KGDao()
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    label_alias = kgd.load_disease_alias(db)
    outfile = codecs.open(outfile, 'w')
    line_format = '%s %s\n'
    fin = codecs.open(infile)
    for count, line in enumerate(fin):
        if count > n_limit:
            break
        line_items = str(line).strip().split('\t')
        if len(line_items) < 4:
            continue
        label = line_items[3]
        if label in label_alias:
            label = label_alias[label]
        if not y_vector.check_value(label):
            continue
        words = x_vector.get_vector(line_items[0])
        if not words:
            continue
        words = words[:max_len]
        sex = get_sex_to_vector(line_items[1])
        age = get_age_to_vector_for_lstm(line_items[2])
        sep = ['0'] * 2
        words.extend(sep + [sex] + sep + [age])
        words.extend(['0'] * history_len)
        line = line_format % (y_vector.get_vector(label), ','.join(words))
        outfile.write(line)
    rows = kgd.load_medical_record_with_history(db)
    for row in rows:
        label = row['disease_name']
        if label in label_alias:
            label = label_alias[label]
        if not y_vector.check_value(label):
            continue
        query = row['query']
        sex, age = row['sex'], row['age']
        past_history = row['past_medical_history']
        words = x_vector.get_vector(query)
        words = words[:seq_len]
        sex = get_sex_to_vector(sex)
        age = get_age_to_vector_for_lstm(age)
        past_history = x_vector.get_vector(past_history)
        past_history = pad_sentences([past_history], history_len, value='0',
                                     padding='post', truncating='post')[0]
        sep = ['0'] * 2
        words.extend(sep + [sex] + sep + [age] + sep + past_history)
        line = line_format % (y_vector.get_vector(label), ','.join(words))
        outfile.write(line)
    outfile.close()


def data2vector_examination(infile, outfile, n_limit=sys.maxsize,
                            x_vector=None, y_vector=None):
    """
    将原始数据转化为词向量，除了考虑性别年龄，既往史，还考虑检查检验和体格检查
    主诉现病史，检查检验，体格检查，既往史的序列长度为500，150，100，50
    :param infile: => 原始输入文件
    :param outfile: =>  词向量输出文件
    :param n_limit: 允许的最大输入文件长度
    :param x_vector:
    :param y_vector:
    :return: 无返回值
    """
    seq_len = 500
    sep_len = 2
    ins_len = 150 - sep_len
    pe_len = 100 - sep_len
    sex_and_age_len = 8
    history_len = 50 - sex_and_age_len
    kgd = KGDao()
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    label_alias = kgd.load_disease_alias(db)
    outfile = codecs.open(outfile, 'w')
    line_format = '%s %s\n'
    fin = codecs.open(infile)
    for count, line in enumerate(fin):
        if count > n_limit:
            break
        line_items = str(line).strip().split('\t')
        if len(line_items) < 4:
            continue
        label = line_items[3]
        if label in label_alias:
            label = label_alias[label]
        if not y_vector.check_value(label):
            continue
        words = x_vector.get_vector(line_items[0])
        if not words:
            continue
        words = words[:seq_len + sep_len + ins_len + sep_len + pe_len]
        sex = get_sex_to_vector(line_items[1])
        age = get_age_to_vector_for_lstm(line_items[2])
        sep = ['0'] * 2
        pmh = ['0'] * history_len
        words.extend(sep + [sex] + sep + [age] + sep + pmh)
        line = line_format % (y_vector.get_vector(label), ','.join(words))
        outfile.write(line)
    rows = kgd.load_medical_record_with_examination(db)
    for row in rows:
        label = row['disease_name']
        if label in label_alias:
            label = label_alias[label]
        if not y_vector.check_value(label):
            continue
        query = row['query']
        ins = row['inspection']
        pe = row['physical_exam']
        sex, age = row['sex'], row['age']
        pmh = row['past_medical_history']
        query = filter_negative(query) if query else ''
        words = x_vector.get_vector(query)[:seq_len] if query else []
        ins = x_vector.get_vector(ins)[:ins_len] if ins else []
        pe = x_vector.get_vector(pe)[:pe_len] if pe else []
        sex = get_sex_to_vector(sex) if sex else '0'
        age = get_age_to_vector_for_lstm(age) if age else '0'
        pmh = filter_negative(pmh) if pmh else ''
        pmh = x_vector.get_vector(pmh) if pmh else []
        pmh = pad_sentences([pmh], history_len, value='0',
                            padding='post', truncating='post')[0]
        sep = ['0'] * 2
        words.extend(sep + ins + sep + pe)
        words.extend(sep + [sex] + sep + [age] + sep + pmh)
        line = line_format % (y_vector.get_vector(label), ','.join(words))
        outfile.write(line)
    outfile.close()


def train_data_pinyin(infile, outfile, n_limit=sys.maxsize):
    """
    把原始数据转化为词向量
    :param infile: => 原始训练文件
    :param outfile: =>  分隔以后转化为词向量
    :param n_limit: 允许的最大文件长度
    :return: 无返回值
    """
    dept_dict = global_conf.dept_classify_dept_path
    data2vector_dept(infile, outfile, n_limit,
                     Pinyin2vector(),
                     Dept2Vector(dept_dict))


def train_data_cnn(infile, outfile, n_limit=sys.maxsize):
    """
       把原始数据转化为词向量
       :param infile: => 原始训练文件
       :param outfile: =>  按照分词词典转化为词向量的文件
       :param n_limit: 允许的最大文件长度
       :return: 无返回值
       """
    dept_dict = global_conf.dept_classify_dept_path
    data2vector_dept(infile, outfile, n_limit,
                     Word2vector(global_conf.dept_classify_cnn_dict_path),
                     Dept2Vector(dept_dict))


def seg_traindata_backup(infile, outfile, seg_length=10):
    """
    把词向量按照固定的长度拆分成多条
    :param infile: =>  转化为词向量的文件
    :param outfile: =>  按照固定长度截断每句话生成的文件
    :param seg_length: => 每句话截断的固定长度
    :return: 无返回值
    """
    line_format = '%s %s\n'
    infile = codecs.open(infile, 'r', encoding='utf-8')
    outfile = codecs.open(outfile, 'w', encoding='utf-8')
    for line in infile:
        line_items = line.split(' ')
        if len(line_items) < 2:
            continue
        department = line_items[0].strip()
        words_str = line_items[1].strip()
        words = words_str.split(',')
        p = 0
        words_list = []
        while len(words[p: p + seg_length]) == seg_length:
            words_list.append(words[p: p + seg_length])
            p += seg_length
        if p != len(words):
            words_list.append(words[p:len(words)])
        for w in words_list:
            out = line_format % (department, ','.join(w))
            outfile.write(out)
    infile.close()
    outfile.close()


def seg_traindata(infile, outfile, cut_type='full', seg_length=10):
    """
    把词向量按照固定的长度拆分成多条
    :param infile: => 转化为词向量的文件
    :param outfile: => 按照固定长度截断每句话生成的文件
    :param cut_type: => 取值为'cut'和'full'，其中'cut'即是直接截断，'full'采用拆分为多条
    :param seg_length: => 每句话截断的固定长度
    :return: 无返回值
    """
    line_format = '%s %s\n'
    infile = codecs.open(infile)
    outfile = codecs.open(outfile, 'w')
    for line in infile:
        line_items = line.split(' ')
        if len(line_items) < 2:
            continue
        department = line_items[0].strip()
        words_str = line_items[1].strip()
        words = words_str.split(',')
        p = 0
        words_list = []
        if cut_type == 'cut':
            words_list.append(words[0:seg_length])
        else:
            while len(words[p: p + seg_length]) == seg_length:
                words_list.append(words[p: p + seg_length])
                p += seg_length
            if p != len(words):
                words_list.append(words[p:len(words)])
        for w in words_list:
            out = line_format % (department, ','.join(w))
            outfile.write(out)
    infile.close()
    outfile.close()


def seg_traindata_sex_age(infile, outfile, cut_type='full', seg_length=10):
    """
    把包含性别和年龄的词向量按照固定的长度拆分成多条
    :param infile: => 转化为词向量的文件
    :param outfile: => 按照固定长度截断每句话生成的文件
    :param cut_type: => 取值为'cut'和'full'，其中'cut'即是直接截断，'full'采用拆分为多条
    :param seg_length: => 每句话截断的固定长度
    :return: 无返回值
    """
    line_format = '%s %s\n'
    infile = codecs.open(infile, 'r', encoding='utf-8')
    outfile = codecs.open(outfile, 'w', encoding='utf-8')
    for line in infile:
        line_items = line.strip().split(' ')
        if len(line_items) < 2:
            continue
        department = line_items[0].strip()
        words_str = line_items[1].strip()
        words = words_str.split(',')
        sex_age = words[-2:]
        query = words[:-2]
        p = 0
        words_list = []
        if cut_type == 'cut':
            words_list.append(query[0:seg_length] + sex_age)
        else:
            while len(query[p:p + seg_length]) == seg_length:
                words_list.append(query[p:p + seg_length] + sex_age)
                p += seg_length
            if p != len(words):
                words_list.append(query[p:len(words)] + sex_age)
        for w in words_list:
            out = line_format % (department, ','.join(w))
            outfile.write(out)
    infile.close()
    outfile.close()


def get_char_data(file_path='medical_record_dept_train_union.txt', seg_length=100):
    input_file, train_vector_file, seg_file = generate_train_vector_file_path(file_path, train_type='char')
    train_data_char(input_file, train_vector_file)
    seg_traindata(train_vector_file, seg_file,
                  cut_type='cut', seg_length=seg_length)
    return seg_file


# def get_char_data(seg_length=100):
#     train_vector_file = train_data_path + 'medical_char_vector_record_dept_union.txt'
#     input_file = train_data_path + 'medical_record_dept_train_union.txt'
#     seg_file = train_data_path + 'medical_char_seg_record_dept_union.txt'
#     train_data_char(input_file, train_vector_file)
#     seg_traindata(train_vector_file, seg_file,
#                   cut_type='cut', seg_length=seg_length)


# def get_pinyin_data(seg_length=100):
#     """
#     把原始文件转化为词向量，分为转词向量和拆分成固定长度的向量两部分
#     :param seg_length: 每句话拆分的词向量长度
#     :return: 无返回值
#     """
#     train_vector_file = train_data_path + 'dept_classify_all_cnn_20180621_pinyin_vector.txt'
#     input_file = train_data_path + 'dept_classify_all_cnn_20180621.txt'
#     seg_file = train_data_path + 'dept_classify_all_cnn_20180621_pinyin_seg.txt'
#     train_data_pinyin(input_file, outfile=train_vector_file)
#     seg_traindata(train_vector_file, outfile=seg_file,
#                   cut_type='cut', seg_length=seg_length)


def get_pinyin_data(file_path='dept_classify_all_cnn_20180621.txt', seg_length=100):
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


def get_cnn_data(file_path='dept_classify_all_cnn_20180621.txt', seg_length=200):
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


# def get_cnn_data(seg_length=200):
#     """
#     把原始文件转化为词向量，分为转词向量和拆分成固定长度的向量两部分
#     :param seg_length: 每句话拆分的词向量长度
#     :return: 无返回值
#     """
#     train_vector_file = train_data_path + 'dept_classify_all_cnn_20180621_cnn_vector.txt'
#     input_file = train_data_path + 'dept_classify_all_cnn_20180621.txt'
#     seg_file = train_data_path + 'dept_classify_all_cnn_20180621_cnn_seg.txt'
#     train_data_cnn(input_file, outfile=train_vector_file)
#     seg_traindata(train_vector_file, outfile=seg_file,
#                   cut_type='cut', seg_length=seg_length)


def symptom_diagnose(n_limit=0):
    """
    症状诊断数据.
    """
    from mednlp.dao.diagnose_service_dao import DiagnoseServiceDao
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kgd = KGDao()
    symptoms = kgd.load_top_symptom(db, n_limit)
    dsd = DiagnoseServiceDao()
    for symptom in symptoms:
        medical_record = {'chief_complaint': symptom}
        diseases = dsd.diagnose(medical_record)
        if not diseases:
            diseases = []
        disease_names = []
        for disease in diseases:
            name = disease.get('disease_name')
            if not name:
                continue
            disease_names.append(name)
        print('%s,%s' % (symptom, '|'.join(disease_names)))


def dept_symptom(infile, n_limit=sys.maxsize):
    dept_dict = {}
    seg = MMSeg(dict_type=['symptom_wy'])
    for count, line in enumerate(codecs.open(infile, 'r', 'utf-8')):
        if count > n_limit:
            break
        if count % 1000 == 0:
            print(count)
        if not line:
            continue
        line = line.strip()
        item_list = line.split('\t')
        if len(item_list) < 4:
            continue
        content = item_list[0]
        dept = item_list[3]
        symptoms = seg.cut(content)
        if not symptoms:
            continue
        for s_name, s_id in symptoms.items():
            count_dict = dept_dict.setdefault(dept, {})
            if s_name not in count_dict:
                count_dict[s_name] = 1
            else:
                count_dict[s_name] += 1
    dept_symptom_count_sort(dept_dict)


def dept_symptom_kg():
    """
    科室相关症状,根据图谱数据.
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kgd = KGDao()
    disease_std_dept = kgd.load_disease_std_dept(db)
    symptom_disease = kgd.load_symptom_disease(db)
    symptom_info = kgd.load_symptom_info(db)
    symptom_dict = {s['entity_id']: s['entity_name'] for s in symptom_info}
    disease_symptom = {}
    for symptom_id, disease_info in symptom_disease.items():
        for disease_id, item in disease_info.items():
            rate = int(math.pow(4.0, float(item['rate']) / 10.0))
            weight = float(item['weight']) / 10000.0
            symptom_count = disease_symptom.setdefault(disease_id, {})
            symptom_count[symptom_id] = float(rate) * weight
    dept_symptom_dict = {}
    for disease_id, dept_info in disease_std_dept.items():
        dept_name = dept_info['std_dept_name']
        if not disease_symptom.get(disease_id):
            continue
        symptom_info = dept_symptom_dict.setdefault(dept_name, {})
        for symptom_id, weight in disease_symptom[disease_id].items():
            symptom_name = symptom_dict[symptom_id]
            if symptom_name not in symptom_info:
                symptom_info[symptom_name] = weight
            else:
                symptom_info[symptom_name] += weight
    dept_symptom_count_sort(dept_symptom_dict)


def dept_symptom_count_sort(dept_dict):
    for dept, count_dict in dept_dict.items():
        count_list = []
        for symptom, count in count_dict.items():
            if count < 20:
                continue
            count_list.append((symptom, count))
        count_list = sorted(count_list, key=lambda s: s[1], reverse=True)
        print('###', dept, '###')
        for symptom, count in count_list:
            if len(symptom) > 13:
                continue
            print('%s|%s|%s' % (dept, symptom, count))


def kg_generate_medical_record(total_size, medical_record_generated_file):
    symptom_min_length = 6
    symptom_name_min_length = 3
    symptom_name_max_length = 10

    kgd = KGDao()
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    medical_record_generated = codecs.open(medical_record_generated_file, 'w')
    disease_symptom_dict = kgd.load_disease_symptom(db, symptom_min_length)
    disease_prevalence_dict, prevalence_sum = kgd.load_disease_prevalence(db)
    for disease, symptom in disease_symptom_dict.items():
        disease_occurrence = 0
        if disease_prevalence_dict.get(disease):
            disease_occurrence = int(
                total_size * disease_prevalence_dict[disease] / prevalence_sum)
        symptom_list = list(symptom.keys())
        prevalence_list = list(symptom.values())
        symptom_prob_list = [
            float(p) / sum(prevalence_list) for p in prevalence_list]
        disease_occurrence_dict = {}
        for i in range(disease_occurrence):
            disease_occurrence_dict[i] = []
            min_length = symptom_name_min_length
            max_length = min(symptom_name_max_length, len(symptom_list))
            symptom_length = random.randint(min_length, max_length)
            while True:
                generated_symptom = numpy.random.choice(
                    symptom_list, p=symptom_prob_list)
                if generated_symptom not in disease_occurrence_dict[i]:
                    disease_occurrence_dict[i].append(generated_symptom)
                if len(disease_occurrence_dict[i]) >= symptom_length:
                    break
            disease_occurrence_dict[i].insert(
                random.randint(0, symptom_length), disease)
            symptoms = '，'.join(disease_occurrence_dict[i])
            medical_record = '\t'.join([symptoms, '1', '1', disease])
            medical_record_generated.write(medical_record + '\n')


def generate_train_file_path(input_file_path):
    """
    根据input_file_path按照在文件名后面加入train和test生成训练文件目录和测试文件目录
    :param input_file_path: 输入文件名
    :return: 返回原始文件目录，训练文件目录，测试文件目录
    """
    if os.path.split(input_file_path)[0]:
        file_path = input_file_path
    else:
        file_path = global_conf.train_data_path + input_file_path

    base_path, file_name_path = os.path.split(file_path)
    file_name, extension = os.path.splitext(file_name_path)

    train_file_path = os.path.join(base_path, file_name + '_train' + extension)
    test_file_path = os.path.join(base_path, file_name + '_test' + extension)
    return file_path, train_file_path, test_file_path


def generate_train_vector_file_path(input_file_path, train_type='cnn'):
    if os.path.split(input_file_path)[0]:
        file_path = input_file_path
    else:
        file_path = global_conf.train_data_path + input_file_path

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


def split_train_test_data(input_file_path, train_file_path, test_file_path, num=100000):
    """
    :param input_file: 原本的训练数据集
    :param train_file: 训练数据集
    :param test_file: 测试数据集
    :param sep: x和y分隔符
    :param num: 测试数据集的数目
    :return: 无
    """
    input_file = codecs.open(input_file_path, 'r', encoding='utf-8')
    train_file = codecs.open(train_file_path, 'w', encoding='utf-8')
    test_file = codecs.open(test_file_path, 'w', encoding='utf-8')
    contents = [line for line in input_file]

    random.shuffle(contents)
    test_list = contents[:num]
    train_list = contents[num:]
    # train_list = transform_train_data(train_list)
    for test_line in test_list:
        test_file.write(test_line)
    for train_line in train_list:
        train_file.write(train_line)

    input_file.close()
    train_file.close()
    test_file.close()


if __name__ == '__main__':
    command = '\n python %s [-t type -n number -c config_file]' % sys.argv[0]
    train_data_path = global_conf.train_data_path
    train_vector_file = train_data_path + 'train_vector_char_true.txt'
    input_file = train_data_path + 'traindata_dept_classify_true.txt'
    seg_file = train_data_path + 'train_seg_data_char_true.txt'
    parser = OptionParser(usage=command)
    parser.add_option('-t', '--type', dest='type', help='the type of operate')
    parser.add_option('-i', '--input', dest='input', help='the file input')
    parser.add_option('-v', '--vector', dest='vector_file', help='vector file')
    parser.add_option('-s', '--seg', dest='seg_file', help='seg words to file')
    parser.add_option('-n', '--num', dest='seg_num', help='seg length of words')
    parser.add_option('--kg', dest='kg_size', help='size to generate from kg')
    parser.add_option('--sa', dest='sa_mode', help='mode of sex and age')
    parser.add_option('--history', dest='history_mode', help='mode of history')
    parser.add_option('--exam', dest='exam_mode', help='mode of examination')
    parser.add_option('--tfinput', dest='tfinput', help='transform input file')
    parser.add_option('--tftype', dest='tftype', help='科室分诊采用何种方式处理')
    operate_type = 'all'
    num = 100
    sa_mode = 0
    history_mode = 0
    exam_mode = 0
    tftype = 'train'
    (options, args) = parser.parse_args()

    if options.type:
        operate_type = options.type
    if options.input:
        input_file = options.input
    if options.vector_file:
        train_vector_file = options.vector_file
    if options.seg_file:
        seg_file = options.seg_file
    if options.seg_num:
        num = int(options.seg_num)
    if options.kg_size:
        size = int(options.kg_size)
        f = train_data_path + 'mr_generated.txt'
        kg_generate_medical_record(size, f)
    if options.sa_mode:
        sa_mode = int(options.sa_mode)
        sa_mode = 1 if sa_mode > 0 else 0
    if options.history_mode:
        history_mode = int(options.history_mode)
        history_mode = 1 if history_mode > 0 else 0
    if options.exam_mode:
        exam_mode = int(options.exam_mode)
        exam_mode = 1 if exam_mode > 0 else 0
    if options.tftype:
        tftype = options.tftype

    if options.tfinput:
        origin_input_file = options.tfinput
        if tftype == 'char':
            seg_file = get_char_data(origin_input_file, seg_length=100)
            input_file_path, train_file_path, test_file_path = generate_train_file_path(seg_file)
            split_train_test_data(input_file_path, train_file_path, test_file_path)
        elif tftype == 'cnn':
            seg_file = get_cnn_data(origin_input_file, seg_length=200)
            input_file_path, train_file_path, test_file_path = generate_train_file_path(seg_file)
            split_train_test_data(input_file_path, train_file_path, test_file_path)

        elif tftype == 'pinyin':
            seg_file = get_pinyin_data(origin_input_file, seg_length=100)
            input_file_path, train_file_path, test_file_path = generate_train_file_path(seg_file)
            split_train_test_data(input_file_path, train_file_path, test_file_path)
        elif tftype == 'vector':
            get_char_data(origin_input_file, seg_length=100)
            get_cnn_data(origin_input_file, seg_length=200)
            get_pinyin_data(origin_input_file, seg_length=100)
        else:
            seg_file = get_char_data(origin_input_file, seg_length=100)
            input_file_path, train_file_path, test_file_path = generate_train_file_path(seg_file)
            split_train_test_data(input_file_path, train_file_path, test_file_path)
            seg_file = get_cnn_data(origin_input_file, seg_length=200)
            input_file_path, train_file_path, test_file_path = generate_train_file_path(seg_file)
            split_train_test_data(input_file_path, train_file_path, test_file_path)
            seg_file = get_pinyin_data(origin_input_file, seg_length=100)
            input_file_path, train_file_path, test_file_path = generate_train_file_path(seg_file)
            split_train_test_data(input_file_path, train_file_path, test_file_path)
    if options.input and options.vector_file:
        if sa_mode:
            disease_classify_vector_sexandage(input_file, train_vector_file)
        if history_mode:
            disease_classify_vector_history(input_file, train_vector_file)
        if exam_mode:
            disease_classify_vector_examination(input_file, train_vector_file)
        else:
            disease_classify_vector(input_file, train_vector_file)

    if options.input and options.seg_file:
        if options.type == 'train':
            disease_classify_vector(input_file, train_vector_file)
        elif options.type == 'seg':
            seg_traindata(train_vector_file, seg_file,
                          cut_type='cut', seg_length=num)
        else:
            disease_classify_vector(input_file, train_vector_file)
            seg_traindata(train_vector_file, seg_file,
                          cut_type='cut', seg_length=num)
