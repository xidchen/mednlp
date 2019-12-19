#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
pinyin.py -- the pinyin file

Author: caoxg
Create on 2017-11-22.
"""

import os
import pypinyin
import global_conf


base_dir = os.path.dirname(__file__)
mode_dict = {'full': pypinyin.NORMAL, 'first': pypinyin.FIRST_LETTER}


def get_pinyin(content, mode='full', errors='ignore', separator=''):
    """
    生成拼音.
    参数:
    content->unicode类型的字符串.
    mode->可选值:full-全拼,first-拼音首字母
    返回值:
    unicode类型的字符串.
    """
    return pypinyin.slug(content, separator=separator,
                         style=mode_dict[mode],
                         errors=errors)


def load_pinyin_dic(dic_file_list=None):
    """
    加载自定义词典.
    参数:
    dic_file_list->字典文件列表.
    """
    if not dic_file_list:
        dic_file = os.path.join(global_conf.dict_path, 'gl_pinyin_custom.dic')
        dic_file_list = [dic_file]
    pinyin_dict = {}
    for dic_file in dic_file_list:
        for line in open(dic_file):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            (word, pinyin) = line.split('|')
            pinyin = pinyin.split(',')
            pinyin_dict[word] = [[py] for py in pinyin]
    pypinyin.load_phrases_dict(pinyin_dict, style=pypinyin.NORMAL)


if __name__ == '__main__':
    load_pinyin_dic()
    print(get_pinyin('我☆-'))
    print(get_pinyin('枸橼酸铋钾胶囊'))
    print(get_pinyin('我☆-', mode='first'))
    print(get_pinyin('枸橼酸铋钾胶囊', mode='first'))
