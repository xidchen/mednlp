#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
neg_filter.py -- negative meaning filter

Author: chenxd <chenxd@guahao.com>
Create on 2018-09-24 Monday
"""

import re


def filter_negative(sentence):
    new_sequences = []
    pattern = '(?:无|否认|未|正常|可|良好|原籍|不详|健康|体健|暂缺)'
    for seq_split in re.split('([，。；？！;]|\.\.)', sentence):
        if re.search(pattern, seq_split):
            if re.search('无(明显)?[诱原]因|无法|无力|可见', seq_split):
                new_sequences.append(seq_split)
        else:
            new_sequences.append(seq_split)
    new_sentence = remove_redundant_punctuation(''.join(new_sequences))
    return new_sentence


def remove_redundant_punctuation(sentence):
    redundant_punctuation = re.findall('[，。；：？！;:]{2,}', sentence)
    if redundant_punctuation:
        for pun in redundant_punctuation:
            sentence = re.sub(pun, '。', sentence)
    if re.match('[。，]', sentence):
        sentence = sentence[1:]
    return sentence


def filter_physical_examination_negative(sentence):
    new_sequences = []
    for seq_split in re.split(r'([，。；？！;]|\.\.)', sentence):
        if re.search(r'未闻及(明显)?干湿(性)?[罗啰]音', seq_split):
            continue
        if re.search(r'未闻及(明显)?痰鸣音', seq_split):
            continue
        new_sequences.append(seq_split)
    new_sentence = remove_redundant_punctuation(''.join(new_sequences))
    return new_sentence


if __name__ == '__main__':
    original_sentence = input('original sentence: ')
    print('modified sentence:', filter_negative(original_sentence))
