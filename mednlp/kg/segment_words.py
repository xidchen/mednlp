#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
segment_words.py -- segment sentence by jieba which load some entity dict
Author : chenxd
Create on 2018.06.27
"""

import re
import jieba
import global_conf
import jieba.posseg as psg


## 字典路径
entity_dict = global_conf.structuration_entity_dict
char_dict = global_conf.symptom_char_dict

## 读入字典
jieba.load_userdict(entity_dict)
jieba.load_userdict(char_dict)
## 开启并行分词模式，参数为并发执行的进程数
jieba.enable_parallel(10)


# 里面是提炼出的时间正则模式
def time_re_pattern():
    # p1: 绝对时间点
    p1_1 = u'\d+年\d+月\d+日'
    p1_2 = u'[1|2]\d{3}[\-\.\/]\d{1,2}[\-\.\/]\d{1,2}'
    p1_3 = u'\d+月\d+日'
    p1_4 = u'\d+年\d+月'
    p1_5 = u'[1|2]\d{3}[\-|\.|\/]1{0,1}[012]'
    p1_6 = u'[1|2]\d{3}[\-|\.|\/]0{0,1}[1-9]'

    # p2: 相对时间
    p2_1 = u'昨天|今天|明天|昨日|今日|明日|上周|本周|这周|下周|上月|本月|下月|去年|今年|明年'
    p2_2 = u'现在|目前'

    # p3: 时间段
    p3_1 = u'\d+[\-|\~\/]\d+[小时|时|日|天|周|月|年]{1,2}'
    p3_2 = u'近?第?前?[半|一|二|三|四|五|六|七|八|九|十|百|千|万|两]{1,2}余?[小时|时|日|天|周|月|年]{1,2}前?(余前)?余?后?(左右)?'
    p3_3 = u'近?第?前?\d+个?余?多?[小时|日|天|周|月|年]{1,2}前?(余前)?余?后?(左右)?期?'
    plist = [p1_1, p1_2, p1_3, p1_4, p1_6, p1_5, p3_1, p3_2, p3_3, p2_1, p2_2]

    return  plist


# 这个函数是利用时间正则模式time_re_pattern提取文本中时间实体
def time_find(sentence):
    time_dict = {}
    plist = time_re_pattern()

    for p in plist:
        splitter = re.compile(p)
        for t in splitter.finditer(sentence):
            if t.span() in time_dict:
                time_dict[(t.span()[0] + 1, t.span()[1] + 1)] = t.group()
            else:
                time_dict[t.span()] = t.group()
            sentence = splitter.sub(u'Ю', sentence)
    time_dict = sorted(time_dict.items(), key=lambda x: x[0], reverse=False)
    return time_dict, sentence


def words_segment(sentence):
    time_dict, sentence = time_find(sentence)
    seg_result = []
    for words in psg.cut(sentence):
        word = words.word
        flag = words.flag
        seg_result.append([word, flag])

    index_time = []
    for index, word_flag in enumerate(seg_result):
        if word_flag[0] == u'Ю':
            index_time.append(index)
    for ind, t_index in enumerate(index_time):
        seg_result[t_index] = [time_dict[ind][1], 'nt']

    return seg_result


if __name__ == '__main__':
    sentence0 = """
    2018.03.05患者于因胸闷、前1周，前两天，2天前，近3周，第三天，治疗半年，.今日复诊。
    """
    print(words_segment(sentence0))
