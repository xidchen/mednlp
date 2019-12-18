#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
named_entity_recognition.py -- medical entities recognition from content via deep learning model
Author : raogj(raogj@guahao.com)
Create on 2019.07.23
"""

from ailib.model.base_model import BaseModel
from keras.models import model_from_json
from mednlp.text.vector import Char2vector
from mednlp.dao.data_loader import Key2Value
from keras.preprocessing.sequence import pad_sequences
import global_conf
import numpy as np
import time
import re
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


class WordSegmentation(BaseModel):

    def initialize(self, model_version=1, segment_len=25, **kwargs):
        self.model_version = model_version
        self.segment_max_len = segment_len
        self.segmentation_model = self.load_model()
        self.char2vector = Char2vector(global_conf.named_entity_recognition_char_dict_path)
        self.type_dict = Key2Value(path=global_conf.named_entity_recognition_type_dict_path, swap=True).load_dict()

    def segment(self, text, split_char):
        """
        分词预测
        :param text: 输入的文本列表
        :param split_char: 分隔符
        :return: 分词结果和待分类的词
        """
        results = []
        phrases_list, punctuations_list = self.cut_sentences(text, split_char)
        for i in range(len(phrases_list)):
            label_vec = self.predict(phrases_list[i])
            word_list = self.get_words(phrases_list[i], label_vec)
            word_loc = self.get_word_location(text[i], punctuations_list[i], word_list, split_char)
            results.append(word_loc)
        return results

    def get_word_location(self, sentence, punctuation, predict_words, spilt_char):
        """
        计算每个每个词，标点和空格的位置信息
        :param sentence: 原始句子
        :param punctuation: 标点下标
        :param predict_words: 预测词
        :param spilt_char: 分隔符
        :return: 返回每个词，标点和空格的位置对应标列表
        """
        word_loc = []
        for word in predict_words:
            loc_begin = sentence.find(word)
            loc_end = loc_begin + len(word) - 1
            word_loc.append({'entity_name': word, 'loc': (loc_begin, loc_end), 'type': '', 'type_all': [''],
                             'entity_id': '', 'entity_id_all': ['']})
            sentence = re.sub(word, spilt_char*len(word), sentence, count=1)
        for p_char in punctuation:
            loc_begin = sentence.find(p_char)
            word_loc.append({'entity_name': p_char, 'loc': (loc_begin, loc_begin),
                             'type': 'punctuation', 'type_all': ['punctuation']})
            sentence = re.sub(p_char, spilt_char, sentence, count=1)
        return word_loc

    # def get_word_location(self, sentence, punctuation, predict_words):
    #     """
    #     计算每个每个词，标点和空格的位置信息
    #     :param sentence: 原始句子
    #     :param punctuation: 标点下标
    #     :param predict_words: 预测词
    #     :return: 返回每个词，标点和空格的位置对应标列表
    #     """
    #     p_index = 0
    #     word_loc = []
    #     if not predict_words:
    #         return [{'entity_name': punctuation[i], 'loc': (i, i), 'type': 'punctuation', 'type_all': ['']} for i in punctuation]
    #     for word in predict_words:
    #         loc_begin = sentence.find(word)
    #         loc_end = loc_begin + len(word) - 1
    #         sentence = re.sub(word, '。'*len(word), sentence, count=1)
    #         if punctuation and p_index < len(punctuation):
    #             while loc_end > punctuation[p_index]:
    #                 word_loc.append({'entity_name': sentence[punctuation[p_index]],
    #                                  'loc': (punctuation[p_index], punctuation[p_index]),
    #                                  'type': 'punctuation', 'type_all': ['']})
    #                 p_index += 1
    #             word_loc.append({'entity_name': word, 'loc': (loc_begin, loc_end), 'type': '', 'type_all': [''],
    #                              'entity_id': '', 'entity_id_all': ['']})
    #             if loc_end < punctuation[p_index]:
    #                 continue
    #             elif loc_end == punctuation[p_index]:
    #                 p_idx = p_index+1
    #                 p_num = 1
    #                 if p_idx < len(punctuation):
    #                     while punctuation[p_idx]-1 == punctuation[p_idx-1]:
    #                         p_num += 1
    #                         p_idx += 1
    #                         if p_idx >= len(punctuation):
    #                             break
    #             for idx in range(p_num):
    #                 p_name = sentence[punctuation[p_index+idx]]
    #                 word_loc.append({'entity_name': p_name, 'loc': (punctuation[p_index+idx], punctuation[p_index+idx]),
    #                                  'type': 'punctuation', 'type_all': ['']})
    #             p_index += p_num
    #         else:
    #             word_loc.append({'entity_name': word, 'loc': (loc_begin, loc_end), 'type': '', 'type_all': [''],
    #                              'entity_id': '', 'entity_id_all': ['']})
    #     while p_index < len(punctuation):
    #         word_loc.append({'entity_name': sentence[punctuation[p_index]],
    #                          'loc': (punctuation[p_index], punctuation[p_index]),
    #                          'type': 'punctuation', 'type_all': ['']})
    #         p_index += 1
    #     return word_loc

    def cut_sentences(self, text, split_char):
        """
        将长句根据标点切分成短句，默认短句最大长度不超过 self.segment_max_len
        :param text: 输入的长句文本
        :param split_char: 分隔符
        :return: 短句列表
        """
        if not split_char:  # 当分隔符为空时，从自定义的列表中选择分隔符
            for char in ['#', '$', '@', '*', '/', '|', '-', '+', '%', '^']:
                if char not in text:
                    split_char = char
                    break
        punctuation_patt = r'(?:，|。|？|！|；|：|、|,|:|\?|!| )'
        p_patt = re.compile(punctuation_patt)
        phrases, punctuations = [], []
        for sentences in text:
            punctuations.append(p_patt.findall(sentences))
            phrase = []
            sentences = re.sub(split_char, '', sentences)
            sentences = p_patt.sub(split_char, sentences)
            for s in sentences.split(split_char):
                if len(s) == 0:
                    continue
                while len(s) > self.segment_max_len:   # 处理长度超过self.segment_max_len的短句，待优化
                    phrase.append(s[:self.segment_max_len])
                    s = s[self.segment_max_len:]
                phrase.append(s)
            phrases.append(phrase)
        return phrases, punctuations

    # def cut_sentences(self, text, split_char):
    #     """
    #     将长句根据标点切分成短句，默认短句最大长度不超过 self.segment_max_len
    #     :param text: 输入的长句文本
    #     :param split_char: 分隔符
    #     :return: 短句列表
    #     """
    #     if not split_char:  # 当分隔符为空时，从自定义的列表中选择分隔符
    #         for char in ['#', '$', '@', '*', '/', '|', '-', '+', '%', '^']:
    #             if char not in text:
    #                 split_char = char
    #                 break
    #     punctuation_patt = r'(?:，|。|？|！|；|：|、|,|:|\?|!| )'
    #     p_patt = re.compile(punctuation_patt)
    #     phrases, punctuations_index = [], []
    #     for sentences in text:
    #         p_index, phrase = [], []
    #         punctuation_list = p_patt.findall(sentences)
    #         s_str = sentences
    #         for punctuation in punctuation_list:
    #             p_index.append(s_str.index(punctuation))
    #             s_str = p_patt.sub(split_char, s_str, count=1)
    #         punctuations_index.append(p_index)
    #         sentences = re.sub(split_char, '', sentences)
    #         sentences = p_patt.sub(split_char, sentences)
    #         for s in sentences.split(split_char):
    #             if len(s) == 0:
    #                 continue
    #             while len(s) > self.segment_max_len:   # 处理长度超过self.segment_max_len的短句，待优化
    #                 phrase.append(s[:self.segment_max_len])
    #                 s = s[self.segment_max_len:]
    #             phrase.append(s)
    #         phrases.append(phrase)
    #     return phrases, punctuations_index

    def predict(self, phrases):
        """
        获取短句的标签向量
        :param phrases: 输入的短句列表
        :return: 文本的标签向量列表
        """
        phrases_vec = np.array([np.array(self.char2vector.get_char_vector(line, isIgnore=False)) for line in phrases])
        text_vec = pad_sequences(phrases_vec, maxlen=self.segment_max_len, padding='post', truncating='post', value=0)
        segment_prob = self.segmentation_model.predict(text_vec)
        label_vec = [list(map(lambda prob: np.argmax(prob), p))for p in segment_prob]
        return label_vec

    def get_words(self, phrases, label_vec):
        """
        根据短句标签获取分词结果
        :param phrases: 输入短句列表
        :param label_vec: 短句对应的标签列表
        :return: 返回分词结果列表
        """
        word_list = []
        for i in range(len(phrases)):
            phrase = phrases[i]
            word_str = ''
            for j in range(len(phrases[i])):
                word_str += phrase[j]
                if label_vec[i][j] == 3 or label_vec[i][j] == 4:
                    word_list.append(word_str)
                    word_str = ''
        return word_list

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        return model


def main():
    # context = [',.你好，，，，我是王刚，最近有点头疼，，,，。发烧感冒',
    #            '请问杭州第一人民医院，杭州市中医医院，湘雅医院和浙江大学附属医院。',
    #            '我的头部有点疼，腰酸，小腿胀痛，全身都不舒服，应该怎么办？',
    #            '杭州市萧山区哪个医院的皮肤科，五官科，肿瘤科最好',
    #            '胆囊造口术是做什么的，主动脉冠状动脉分流又是什么，动脉瓣狭窄扩张术，输精管结扎术',
    #            '开腹探查术， 肝管切开术， 乳房切除术 ， ']
    # context = ['请问杭州第一人民医院']
    context = ['##，##，##岁, T37.5℃，####:10.20Pmol/L,T3 42.5,###：37mol/l，###48.5,']

    word_segmrnt = WordSegmentation(cfg_path=global_conf.cfg_path,
                                    model_section='NAMED_ENTITY_RECOGNITION_MODEL_TO_SEGMENT')
    t0 = time.time()
    for i in range(1):
        results = word_segmrnt.segment(context)
    t1 = time.time()
    print(results)
    print(t1-t0)


if __name__ == '__main__':
    main()
