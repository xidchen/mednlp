#!/usr/bin/python
# -*- coding: utf8 -*-
import os
import re
import sys
import json
import time
import jieba
import codecs
import global_conf
import numpy as np
import pandas as pd
import jieba.posseg as psg
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding("utf-8")
from ailib.model.base_model import BaseModel

from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences

### 设置初始化路径
cfg_path = global_conf.cfg_path
training_path = os.path.dirname(__file__) + '/' + 'bin/training/'
train_data_path = os.path.dirname(__file__) + '/' + 'data/traindata/'
entity_dict = os.path.dirname(__file__) + '/' + 'data/dict/entity_dict.txt'
# 读入字典
jieba.load_userdict(entity_dict)
# 开启并行分词模式，参数为并发执行的进程数
jieba.enable_parallel(10)


def label_list_alter(list_data, label):
    '''
    tran_list:规则模型中特有，将两个目标标签中间隔的一个非目标标签页替换为目标标签
    '''
    index_list = []
    for index, m in enumerate(list_data):
        if m == label:
            index_list.append(index)
        else:
            pass
    for l in range(1, len(index_list)):
        if index_list[l] - index_list[l-1] == 2:
            list_data[index_list[l]-1] = label
        else:
            pass
    return list_data


def sen_pseg_list(sen):
    '''
    计算 各个词性词的个数
    '''
    symptom_ls = []
    disease_ls = []
    check_ls = []
    k = 0
    for words in psg.cut(sen):
        k += 1
        flag = words.flag
        word = words.word
        if flag == 'as':
            symptom_ls.append(word)
        elif flag == 'nd':
            disease_ls.append(word)
        elif flag == 'ne':
            check_ls.append(word)
    slen = len(set(symptom_ls))
    dlen = len(set(disease_ls))
    clen = len(set(check_ls))
    sen_len = k
    return sen_len, slen, dlen, clen


def label_rule_pos(sen, parameter):
    '''
    rule_pos:规则模型
    parameter：特征词和标签的组合列表
        eg： [u'临床表现|具体表现|临床症状', 'clinical_manifestation']
    '''
    pattern ,label = parameter
    sen_len, slen, dlen, clen = sen_pseg_list(sen)
    if float(slen)/sen_len > 0.5:
        labels = label

    elif clen > 1:  ## 首先不包括检查类的症状
        labels = 'other'

    elif re.findall(pattern, sen) and dlen < slen:
        labels = label

    elif slen > 3 and dlen < slen:
        labels = label

    else:
        labels = 'other'

    return labels


def sen_to_sequence(sen, word_dict):
    sen_split = jieba.lcut(sen)
    sequence = []
    for word in  sen_split:
        if word in word_dict.keys():
            sequence.append(word_dict[word])
        else:
            sequence.append(0)
    return sequence


class Clinical_Predict(BaseModel):
    '''
    input_file: 输入文本可以是 文本列表，也可以是文本字符串
    parameter：形如：[u'临床表现|具体表现|临床症状', 'clinical_manifestation']，
        是一个列表前面是关键词，后面是标签名称
    maxlen ：单个文本最大词个数
    '''
    def __init__(self, input_file, parameter, maxlen = 100):
        self.input_file = input_file
        self.parameter = parameter
        self.maxlen = maxlen

    def rule_model_pred(self):
        '''
        规则模型预测
        '''
        pattern, label = self.parameter
        if isinstance(self.input_file, list):
            label_list = []
            for sen in self.input_file:
                label_list.append(label_rule_pos(sen, self.parameter))
            new_label = label_list_alter(label_list, label)
        elif isinstance(self.input_file, (unicode,str)):
            new_label = label_rule_pos(self.input_file, self.parameter)
        else:
            new_label = 'other'
        return new_label

    def deep_model_pred(self):
        ####全部 段落类别
        label_kinds = ['other', 'clinical_manifestation']
        #读取model  和 词典
        model_path = os.path.join(training_path, 'clinical_classify_model_1.h5')
        wordindex_path = os.path.join(train_data_path, 'word_order_dictionary.json')

        model = load_model(model_path)
        with open(wordindex_path,'r') as load_f:
            word_dict = json.load(load_f)

        text_split = []
        if isinstance(self.input_file, list):
            for sen in self.input_file:
                sen_split_index = sen_to_sequence(sen, word_dict)
                text_split.append(sen_split_index)
        else:
            sen_split_index = sen_to_sequence(self.input_file, word_dict)
            text_split.append(sen_split_index)

        sequences = np.array(text_split)
        data = pad_sequences(sequences, maxlen=self.maxlen)
        pred_pro = model.predict(data, batch_size=256)
        pred_pro = np.argmax(pred_pro, axis=1)###获取预测值概率最大的坐标

        label_list = [label_kinds[x] for x in pred_pro]
        return label_list

    def combine_result(self):
        '''
        融合模型预测结果
        '''
        label = self.parameter[-1]
        result_model = self.deep_model_pred()
        result_rule = self.rule_model_pred()
        if isinstance(result_rule ,list):
            result = []
            for index, lab in enumerate(result_rule):
                if lab == label and result_model[index] == label:
                    result.append(label)
                else:
                    result.append('other')
        else:
            if result_model == [label] and result_rule == label:
                result = label
            else:
                result = 'other'
        return result


if __name__ == '__main__':
    data_df = pd.read_excel('/home/yinwd/work/mynlp/test/new_predict_test_01.xlsx', encoding='utf8')
    sen_ls = data_df['content'].tolist()
    clinical_manifestation = [u'临床表现|具体表现|临床症状', 'clinical_manifestation']
    diagnosis = [u'诊断依据|诊断标准|诊断', 'diagnosis']
    datasen = sen_ls[10:30]  ##字符串列表
    # datasen = sen_ls[16] ##字符串
    Model = Clinical_Predict(datasen, clinical_manifestation)

    result_model = Model.deep_model_pred()
    print('=======the result of cnn model=========')
    print(result_model)
    result_rule = Model.rule_model_pred()
    print('=======the result of rule model=========')
    print(result_rule)
    result_combine = Model.combine_result()
    print('=======the result of combine model=========')
    print(result_combine)