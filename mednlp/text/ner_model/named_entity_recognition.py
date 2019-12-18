#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
named_entity_recognition.py -- medical entities recognition from content via deep learning model
Author : raogj(raogj@guahao.com)
Create on 2019.07.23
"""

from mednlp.text.ner_model.word_segment import WordSegmentation
from mednlp.text.ner_model.word_bi_classify import WordBiClassify
from mednlp.text.ner_model.word_multi_classify import WordMultiClassify
from mednlp.text.vector import Char2vector
from mednlp.dao.data_loader import Key2Value
import global_conf
import time
import os
import re
from collections import OrderedDict

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


class NamedEntityRecognitionModel():

    def __init__(self, model_version=1, **kwargs):
        self.model_version = model_version
        self.char2vector = Char2vector(global_conf.named_entity_recognition_char_dict_path)
        self.type_dict = Key2Value(path=global_conf.named_entity_recognition_type_dict_path, swap=True).load_dict()
        self.word_segment = WordSegmentation(cfg_path=global_conf.cfg_path,
                                             model_section='NAMED_ENTITY_RECOGNITION_MODEL_TO_SEGMENT')
        self.word_bi_classify = WordBiClassify(cfg_path=global_conf.cfg_path,
                                               model_section='NAMED_ENTITY_RECOGNITION_MODEL_TO_BI_CLASSIFY')
        self.word_multi_classify = WordMultiClassify(cfg_path=global_conf.cfg_path,
                                                     model_section='NAMED_ENTITY_RECOGNITION_MODEL_TO_MULTI_CLASSIFY')

    def ner(self, context, known_entity=[], is_normal=0):
        """
        实体识别
        :param context: 输入文本
        :param known_entity: 一直实体列表
        :param is_normal: 获取模式，0——获取医学实体词和普通词，1——仅获取医学实体词，默认值 0
        :return: 返回实体识别结果列表
        """
        predict_result = []
        text, split_char = self.refactoring_text(context, known_entity=known_entity)
        cut_result = self.word_segment.segment([text], split_char)
        words = self.filter_words(cut_result)
        bi_label_vec = self.word_bi_classify.predict(words)
        med_words = self.get_med_words(words, bi_label_vec)
        multi_label_vec = self.word_multi_classify.predict(med_words)
        index = 0
        label_vec = bi_label_vec
        for i in range(len(label_vec)):
            if label_vec[i] == 1:
                label_vec[i] = multi_label_vec[index] + 1
                index += 1
        count = 0
        if is_normal == 0:
            for i in range(len(cut_result)):
                word_list = []
                for word in cut_result[i]:
                    if count < len(words):
                        if word['entity_name'] == words[count]:
                            word['type'] = self.type_dict[label_vec[count]]
                            word['type_all'] = [word['type']]
                            count += 1
                    word_list.append(word)
                predict_result.append(word_list)
        elif is_normal == 1:
            for i in range(len(cut_result)):
                word_list = []
                for word in cut_result[i]:
                    if count < len(words):
                        if word['entity_name'] == words[count]:
                            word['type'] = self.type_dict[label_vec[count]]
                            word['type_all'].append(word['type'])
                            if label_vec[count] >= 1:
                                word['type_all'] = [word['type']]
                            count += 1
                predict_result.append(word_list)
        else:
            raise ValueError('实体识别模式选择错误，请根据序号选择模式：'
                             '1--仅获取医学实体词'
                             '2--获取医学实体词和普通词', is_normal)
        ner_result = self.regroup_result(predict_result, known_entity=known_entity)
        return ner_result

    def filter_words(self, word_list):
        """
        过滤type=punctuation的词
        :param word_list:待过滤的词列表
        :return:过滤后的词列表
        """
        words = []
        for word_list in word_list:
            count = 0
            for word in word_list:
                if word['type'] != 'punctuation':
                    words.append(word['entity_name'])
                    count += 1
        return words

    def get_med_words(self, words, label_vec):
        """
        获取二分类下的医学实体词
        :param words: 输入词列表
        :param label_vec: 输入词标签向量
        :return: 医学实体词列表
        """
        med_words = []
        for i in range(len(label_vec)):
            if label_vec[i] == 1:
                med_words.append(words[i])
        return med_words

    def refactoring_text(self, context, known_entity=[]):
        """
        根据已知实体重构待句子文本
        :param context: 句子文本
        :param known_entity: 已知实体列表
        :return: 重构的句子文本和分隔符
        """
        if not known_entity:
            return context, ''
        split_char = ['#', '$', '@', '*', '/', '|', '-', '+', '%', '^']
        s_char = ''
        for char in split_char:
            if char not in context:
                s_char = char
                break
        for key in known_entity:
            if 'entity_text' in known_entity[key]:
                entity_name = known_entity[key]['entity_text']
            else:
                entity_name = known_entity[key]['entity_name']
            context = re.sub(entity_name, s_char * len(entity_name), context, count=1)
        return context, s_char

    def regroup_result(self, predict_entity, known_entity=[]):
        """
        根据已知实体与预测实体重构实体识别结果
        :param predict_entity: 模型预测实体列表
        :param known_entity: 已知实体列表
        :return: 重构的实体识别结果列表
        """
        result = {}
        for k_key in known_entity:
            k_loc = known_entity[k_key]['loc']
            key = known_entity[k_key]['entity_name'] + '\t' + str(k_loc[0]) + '\t' + str(k_loc[1])
            result[key] = known_entity[k_key]
        for entity_list in predict_entity:
            for entity in entity_list:
                p_loc = entity['loc']
                key = entity['entity_name'] + '\t' + str(p_loc[0]) + '\t' + str(p_loc[1])
                result[key] = entity
        result = OrderedDict(sorted(result.items(), key=lambda x: (x[1]["loc"][0], -x[1]["loc"][1])))
        return result


def main():
    context = '请问杭州第一人民医院'
    # context = '贫血，男性，27岁, T37.5℃，游离T3:10.20Pmol/L,T3 42.5,白细胞：37mol/l，红细胞48.5,'
    ner = NamedEntityRecognitionModel()
    t0 = time.time()
    ner_result = ner.ner(context, is_normal=0)
    t1 = time.time()
    print(t1 - t0)
    print(ner_result)


if __name__ == '__main__':
    main()
