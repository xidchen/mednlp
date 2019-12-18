#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
padding.py -- the model of padding

Author: chenxd <chenxd@guahao.com>
Create on 2018-05-28 Monday
"""


def pad_sentences(sentences, length, value='<PAD>',
                  padding='pre', truncating='post'):
    """
    把sentences pad成固定的length长度，缺少的部分用<PAD>填充
    :param sentences: 类型list
    :param length: pad成固定的长度
    :param value: 填充的字符
    :param padding: 填充的方式，'pre'填充前段，‘post'填充后段
    :param truncating: 截断的方式, 'pre'舍弃前段，‘post'舍弃后段
    :return: 返回length长度的list
    """
    if length:
        sequence_length = length
    else:
        sequence_length = max(len(x) for x in sentences)
    padded_sentences = []
    for i in range(len(sentences)):
        sentence = sentences[i]
        if truncating == 'pre':
            sentence = sentence[-sequence_length:]
        if truncating == 'post':
            sentence = sentence[:sequence_length]
        num_padding = sequence_length - len(sentence)
        new_sentence = []
        if padding == 'pre':
            new_sentence = [value] * num_padding + sentence
        if padding == 'post':
            new_sentence = sentence + [value] * num_padding
        padded_sentences.append(new_sentence)
    return padded_sentences
