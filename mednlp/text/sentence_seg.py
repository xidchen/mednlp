#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sentence_seg.py -- 主要是实现语义相似性的各种分词

Author: caoxg <caoxg@guahao.com>
Create on 2018-08-16 星期三.
"""

import codecs
import jieba
import re
import global_conf


def line_symb_split(line):
    """
    :param lines: 需要处理的数据行数据格式[[line]]每一行为一个list
    :return:
    """
    symp_str = '’!"#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}~'

    sub_lines = []
    sub_line = ''
    for ch in line:
        if ch in symp_str:
            if sub_line:
                sub_lines.append(sub_line)
                sub_line = ''
            continue
        sub_line += ch
    if sub_line:
        sub_lines.append(sub_line)
    return sub_lines

def line_max_num_word(line):
    """
    :param lines: 需要处理的数据行 数据格式[[line]]
    :return: 已经处理好的数据行 数据格式[[line]]  其中 line为按照最大单词数据进行分词的数据
    """
    sentence_phrases = line_symb_split(line)
    phrase_split = []
    for phrase in sentence_phrases:
        words = split_by_max_lenth(phrase)
        phrase_split.append(' '.join(words))
    return phrase_split


def split_by_max_lenth(phrase):
    """
    :param phrase: 一句话
    :return: 返回这句话按照最大单词进行分词的结果
    """
    phrase = phrase.strip()
    words = list(jieba.cut_for_search(phrase))
    point = 0
    max_lenth_words = []
    while point < len(phrase):
        min_point = len(phrase) + 1
        min_word = phrase[point:]
        for word in words:
            try_point = phrase[point:].find(word)
            try_point += point
            if try_point < 0 or try_point < point:
                continue
            if try_point < min_point or (try_point < min_point and len(word) <= len(min_word)):
                min_point = try_point
                min_word = word
        if min_point > point:
            max_lenth_words.append(phrase[point: min_point])
        if min_point + len(min_word) > len(phrase):
            break
        max_lenth_words.append(min_word)
        point = min_point + len(min_word)
    return max_lenth_words



class SentenceSeg(object):
    """
    实现分词，主要是风险分词
    """

    def __init__(self,**kwargs):
        self.seg_type = kwargs.get('seg_type' , '')
        self.dict_file_names = kwargs.get('dict_file_name',[])
        if self.dict_file_names:
            self.get_dict_file(self.dict_file_names)

    def get_dict_file(self, dict_file_names=[]):
            """
            :param dict_file_names: 词典名列表
            :return: 无
            """
            dict_base_path = global_conf.dict_path
            for dict_file_name in dict_file_names:
                dict_file = dict_base_path + dict_file_name
                jieba.load_userdict(dict_file)
                print('load_dict')

    def cut_line(self,line):
        """
        :param line:对于一行单词进行分词
        :return: 返回分词后的结果以list返回
        """
        if self.seg_type == 'max_num_word':
            line_seg = line_max_num_word(line)
        elif self.seg_type == 'cut_all':
            line_seg = jieba.lcut(line, cut_all=True)
        elif self.seg_type == 'cut_for_search':
            line_seg = jieba.lcut_for_search(line)
        else:
            line_seg = jieba.lcut(line)
        return line_seg

    def cut_lines(self,lines):
        pass


if __name__ == '__main__':
    a = "中华人民共和国，中华人民，中国，头有点疼"
    # words =line_symb_split(a)
    # print(words)
    # for word in words:
    #     print(word)
    sentence_seg = SentenceSeg(seg_type='cut_all')
    print(" ".join(sentence_seg.cut_line(a)))
    sentence_seg = SentenceSeg(seg_type='cut_for_search')
    print(" ".join(sentence_seg.cut_line(a)))
    sentence_seg = SentenceSeg(seg_type='max_num_word')
    print(" ".join(sentence_seg.cut_line(a)))
    sentence_seg = SentenceSeg()
    print(" ".join(sentence_seg.cut_line(a)))

    # jieba_cut = jieba.lcut(a,cut_all=True)
    # print('cut','ok'.join(jieba_cut))
    # jieba_cut = jieba.lcut_for_search(a)
    # print ('cut_for_serach',"ok".join(jieba_cut))


