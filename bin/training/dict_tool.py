#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dict_tool.py -- some tool for dict

Author: maogy <maogy@guahao.com>
Create on 2017-05-27 Saturday.
"""

import codecs
import global_conf
import itertools
import jieba
import sys
import re
import mednlp.text.pinyin as pinyin
import mednlp.text.dept_vector as dept_vector
from collections import Counter
from optparse import OptionParser
from ailib.storage.db import DBWrapper


jieba_dict = '/home/caoxg/.virtualenvs/realdoctor/lib/python2.7/site-packages/jieba/dict.txt'


def build_disease_part():
    """
    所有疾病相关的词
    :return: => 以字典返回所有疾病的词语 
    """
    sql = """
    SELECT
        t.name
    FROM medical_knowledge.tag t
    WHERE t.source in  (1)
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')
    rows = db.get_rows(sql)
    disease_dict = {}
    count = 1
    for row in rows:
        name = row['name']
        name = name.strip()
        name = name.replace(' ', '')
        name = name.replace('\n', '')
        name = ''.join(name.split())
        if name and ' ' not in name and name not in disease_dict:
            disease_dict[name] = count
            count += 1
    return disease_dict


def build_medical_part():
    """ 
    所有医学相关的词
    :return: => 以字典返回所有医学的词语
    """
    sql = """
    SELECT
        t.name
    FROM medical_knowledge.tag t
    WHERE t.source in  (2,4,7,8,9,10,11)
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')
    rows = db.get_rows(sql)
    medical_dict = {}
    count = 1
    for row in rows:
        name = row['name']
        name = name.strip()
        name = name.replace(' ', '')
        name = name.replace('\n', '')
        name = ''.join(name.split())
        if name and ' ' not in name and name not in medical_dict:
            medical_dict[name] = count
            count += 1
    return medical_dict


def build_body_part():
    """ 
    所有身体部位相关的词
    :return: 以字典返回所有身体部门的词语
    """
    sql = """
    SELECT
        t.body_part_name  name
    FROM medical_kg.body_part t
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    rows = db.get_rows(sql)
    body_part_dict = {}
    count = 1
    for row in rows:
        name = row['name']
        name = name.strip()
        name = name.replace(' ', '')
        name = name.replace('\n', '')
        name = ''.join(name.split())
        if name and ' ' not in name and name not in body_part_dict:
            body_part_dict[name] = count
            count += 1
    return body_part_dict


def build_symptom_part():
    """ 
    所有疾病症状相关的词
    :return: => 以字典返回所有疾病症状的词语
    """
    sql = """
    SELECT
        t.symptom_name  name
    FROM medical_kg.symptom t
    where t.source=1
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    rows = db.get_rows(sql)
    symptom_part_dict = {}
    count = 1
    for row in rows:
        name = row['name']
        name = name.strip()
        name = name.replace(' ', '')
        name = name.replace('\n', '')
        name = ''.join(name.split())
        if name and ' ' not in name and name not in symptom_part_dict:
            symptom_part_dict[name] = count
            count += 1

    old_sql = """
         SELECT
             t.name
         FROM medical_knowledge.tag t
         WHERE t.source in  (3)
         """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')
    rows = db.get_rows(old_sql)
    for row in rows:
        name = row['name']
        name = name.strip()
        name = name.replace(' ', '')
        name = name.replace('\n', '')
        name = ''.join(name.split())
        if name and ' ' not in name and name not in symptom_part_dict:
            symptom_part_dict[name] = count
            count += 1
    return symptom_part_dict


def build_extend_part():
    """
    一些需要特殊添加的词
    :return: 以字典返回一些新加的词语
    """
    sql = """
    SELECT
        name  name
    FROM ai_medical_knowledge.medical_word t
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    rows = db.get_rows(sql)
    extend_part_dict = {}
    count = 1
    for row in rows:
        name = row['name']
        name = name.strip()
        name = name.replace(' ', '')
        name = name.replace('\n', '')
        name = ''.join(name.split())
        if name and ' ' not in name and name not in extend_part_dict:
            extend_part_dict[name] = count
            count += 1
    return extend_part_dict


def bulid_new_dict(dept_classify_segword_path):
    """
    生成医学相关的词典
    :param dept_classify_segword_path: 自定义医学词典保存路径 
    :return: 返回自定义医学词典
    """
    import codecs
    dict_path = dept_classify_segword_path
    file = codecs.open(dict_path, 'w', encoding='utf-8')
    body_part = build_body_part()
    disease_part = build_disease_part()
    medical_part = build_medical_part()
    symptom_part = build_symptom_part()
    extend_part = build_extend_part()
    new_dic = extend_part.copy()
    new_dic.update(medical_part)
    new_dic.update(disease_part)
    new_dic.update(symptom_part)
    new_dic.update(body_part)
    medical_dict = {}
    count = 1
    for row in new_dic:
        if row and row not in medical_dict:
            medical_dict[row] = count
            count += 1
    format = '%s %s n|%s|nil\n'
    valid_dic = {}
    count1 = 1
    for name in disease_part:
        if name not in valid_dic:
            line = format % (name, 100000, 'disease')
            valid_dic[name] = count1
            count1 += 1
            file.write(line)

    for name in symptom_part:
        if name not in valid_dic:
            line = format % (name, 100000, 'symptom')
            valid_dic[name] = count1
            count1 += 1
            file.write(line)
    for name in body_part:
        if name not in valid_dic:
            line = format % (name, 50000, 'body_part')
            valid_dic[name] = count1
            count1 += 1
            file.write(line)

    for name in medical_part:
        if name not in valid_dic:
            line = format % (name, 100000, 'medical')
            valid_dic[name] = count1
            count1 += 1
            file.write(line)
    for name in extend_part:
        if name not in valid_dic:
            line = format % (name, 100000, 'medical')
            valid_dic[name] = count1
            count1 += 1
            file.write(line)
    file.close()
    return medical_dict


def build_medical_dict():
    """
    增加一些医学相关的词，
    :return: 返回医学相关的词
    """
    sql = """
    SELECT
        t.name
    FROM medical_knowledge.tag t
    WHERE t.source NOT IN (5,6)
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')
    rows = db.get_rows(sql)
    medical_dict = {}
    count = 1
    for row in rows:
        name = row['name']
        if name and ' ' not in name and name not in medical_dict:
            medical_dict[name] = count
            count += 1
    return medical_dict


def add_jieba_dict(dict_dict, jieba_dict, medical_jieba_new_file):
    """
    在自定义的医学词库的基础上，增加jieba的名词词库
    :param dict_dict: =>  以字典返回的所有医学相关词语
    :param jieba_dict: =>  结巴分词的原始词典路径
    :param medical_jieba_new_file: => 词库的保存路径
    :return: 增加结巴名词之后的词典
    """
    import codecs
    count = len(dict_dict)
    for line in open(jieba_dict, 'r'):
        word, other, word_type = line.split(' ')
        if word and ' ' not in word and word_type[0] == 'n' and word not in dict_dict:
            dict_dict[word] = count
            count += 1

    format = '%s\t%s\n'
    output_file = codecs.open(medical_jieba_new_file, 'w', encoding='utf-8')
    for x, y in dict_dict.items():
        line = format % (x, y)
        output_file.write(line)
    output_file.close()
    return dict_dict


def build_char_file(filename):
    """
    :param filename: 用来读取字符串词典文件
    :return: 内容和标签列表
    """
    contents, labels = [], []
    with codecs.open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line_items = line.split('\t')
            if len(line_items) < 4:
                continue
            department = line_items[3].strip()
            content = line_items[0].strip()
            contents.append(content)
            labels.append(department)
    return contents, labels


def build_char_vocab(train_dir, vocab_dir, vocab_size=8000):
    """
    给出训练数据构建当个字的词典
    :param train_dir: 训练数据路径
    :param vocab_dir: 单个字的词典路径
    :param vocab_size: 单个字的词典大小
    :return: 无
    """
    f = codecs.open(vocab_dir, 'w', encoding='utf-8')
    data_train, _ = build_char_file(train_dir)
    all_data = []
    count = 1
    count_dict = {}
    format = '%s\t%s\n'
    for content in data_train:
        content = dept_vector.clean_str(content)
        for char in content:
            if char not in count_dict:
                count_dict[char] = count
                line = format % (char, count)
                f.write(line)
                count += 1
    f.close()


def build_pinyin_char_vocab(train_dir, pinyin_vocab_dir, vocab_size=8000):
    """
    根据训练数据构建基于拼音的词典
    :param train_dir: 训练数据路径
    :param pinyin_vocab_dir: 单个拼音的词典路径
    :param vocab_size: 单个拼音的词典大小
    :return: 无
    """
    pinyin.load_pinyin_dic()
    f = codecs.open(pinyin_vocab_dir, 'w', encoding='utf-8')
    data_train, _ = build_char_file(train_dir)
    all_data = []
    count = 1
    count_dict = {}
    format = '%s\t%s\n'
    for content in data_train:
        content = dept_vector.clean_str(content)
        for char in content:
            p_char = pinyin.get_pinyin(char)
            if p_char not in count_dict:
                count_dict[p_char] = count
                line = format % (p_char, count)
                f.write(line)
                count += 1
    f.close()


def build_cnn_word_vocab_backup(train_dir, word_vocab_dir):
    """
    生成分词用的词典
    :return: 把词典保存到一个文件里面
    """
    p = re.compile('\s+')
    format = '%s\t%s\n'
    count = 0
    fin = codecs.open(train_dir, 'r', encoding='utf-8')
    cnn_dict = codecs.open(word_vocab_dir, 'w', encoding='utf-8')
    lines = []
    for line in fin:
        line = re.sub(p, '', line)
        lines.append(jieba.lcut(line))
    word_counts = Counter(itertools.chain(*lines))
    most_common_list = word_counts.most_common()
    vocabulary_ind2w_list = [x[0] for x in most_common_list]
    for x, i in enumerate(vocabulary_ind2w_list):
        line = format % (i, x)
        cnn_dict.write(line)
    cnn_dict.close()
    fin.close()


def build_cnn_word_vocab(train_dir, word_vocab_dir, num=200):
    """
    :param train_dir: 生成cnn词典的文件
    :param word_vocab_dir: 保存cnn词典的文件
    :param num: 
    :return: 无返回值
    """
    f = codecs.open(word_vocab_dir, 'w', encoding='utf-8')
    data_train, _ = build_char_file(train_dir)
    count = 1
    count_dict = {}
    format = '%s\t%s\n'
    for content in data_train:
        words = jieba.lcut(content)
        for word in words:
            if word not in count_dict:
                count_dict[word] = count
                line = format % (word, count)
                f.write(line)
                count += 1
    f.close()


if __name__ == '__main__':
    command = """\npython %s [-i input -o output_jieba -s output_seg_dict -c config_file]""" % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-c', '--config', dest='config', help='the config file', metavar='FILE')
    parser.add_option('-i', '--input', dest='input', help='the input')
    parser.add_option('-o', '--output', dest='output_jieba', help='out_jieba')
    parser.add_option('-s', '--outpt_seg_dict', dest='output_segword', help='out_jieba')
    parser.add_option('-t', '--seg_type', dest='seg_type', help='seg word or seg char')
    (options, args) = parser.parse_args()
    char_train_data_dir = '/home/caoxg/work/mednlp/data/traindata/traindata_dept_classify_consult_result_union.txt'
    cnn_word_dict = '/home/caoxg/work/mednlp/data/dict/dept_classify_cnn_word_consult_result_union_20180522.dic'
    pinyin_char_dict = '/home/caoxg/work/mednlp/data/dict/pinyin_char_vocab_union.dic'
    medical_jieba_new_file = global_conf.dept_classify_char_dict_path
    jieba_dict = jieba_dict
    dept_classify_segword_path = global_conf.dept_classify_segword_path
    seg_type = 'seg_word'
    if options.config is None:
        options.config = global_conf.cfg_path
    if options.input:
        jieba_dict = options.input
    if options.output_jieba:
        medical_jieba_new_file = options.output_jieba
    if options.output_segword:
        dept_classify_segword_path = options.output_segword
    if options.seg_type:
        seg_type = options.seg_type
    build_pinyin_char_vocab(char_train_data_dir, pinyin_char_dict, vocab_size=8000)
    build_cnn_word_vocab(char_train_data_dir, cnn_word_dict)

