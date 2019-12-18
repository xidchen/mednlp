#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2017-11-22 星期三.
"""

import os
import sys
import pypinyin
from mednlp.utils.utils import unicode_python_2_3
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding('utf8')
base_dir = os.path.dirname(__file__)
default_gl_pinyin_dic = os.path.join(base_dir, '../../data/dict/gl_pinyin_custom.dic')
mode_dict = {'full': pypinyin.NORMAL, 'first': pypinyin.FIRST_LETTER}


def get_pinyin(content, mode='full', errors='ignore', separator=u''):
    """
    生成拼音.
    参数:
    content->unicode类型的字符串.
    mode->可选值:full-全拼,first-拼音首字母
    返回值:
    unicode类型的字符串.
    """
    unicode_content = unicode_python_2_3(content)
    return pypinyin.slug(unicode_content, separator=separator, style=mode_dict[mode],
                         errors=errors)


def load_pinyin_dic(dicfiles=[default_gl_pinyin_dic]):
    """
    加载自定义词典.
    参数:
    dicfiles->字典文件列表.
    """
    pinyin_dict = {}
    for dicfile in dicfiles:
        for line in open(dicfile):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = unicode_python_2_3(line)
            (word, pinyin) = line.split(u'|')
            pinyin = pinyin.split(u',')
            pinyin_dict[word] = [[py] for py in pinyin]
    pypinyin.load_phrases_dict(pinyin_dict, style=pypinyin.NORMAL)


if __name__ == '__main__':
    load_pinyin_dic()
    print(get_pinyin(u'我☆-'))
    print(get_pinyin(u'枸橼酸铋钾胶囊'))
    print(get_pinyin(u'我☆-', mode='first'))
    print(get_pinyin(u'枸橼酸铋钾胶囊', mode='first'))
