#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: menghz <jolleh@sina.cn>

import codecs
import sys, os
import time
import jieba
import jieba.posseg as pseg
import global_conf
from mednlp.utils.utils import unicode_python_2_3
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding('utf8')

jieba.enable_parallel(2)
base_path = global_conf.dict_path
dictionary = {}


def reload_dictionary(dictfile=base_path + 'segword.dic'):
    global dictionary
    dictionary = {}
    print('start set')
    jieba.set_dictionary(dictfile)
    print('end set')
    jieba.load_userdict(dictfile)
    print('load userdict')
    for line in codecs.open(dictfile, 'r', 'utf-8'):
        w, freq, pos = line.strip().split(' ')
        dictionary[w] = pos


def initital_smartseg(dictfile=base_path + '/../../data/dict/segword.dic'):
    reload_dictionary(dictfile)


def cut(s):
    """绿线智能分词接口.

    Args:
        s: 分词内容.

    Returns:
        分词数组，[word|ictclas词性|挂号网词性|挂号网ID,word|ictclas词性|挂号网词性|挂号网ID],unicode编码
    """
    words = pseg.cut(s)
    res = []
    for w in words:
        flag = dictionary[w.word] if w.word in dictionary else w.flag
        if flag.count('|') == 0:
            flag = "%s|%s|%s" % (flag, flag, 'nil')
        res.append((w.word + "|" + flag))
    return res

if __name__ == "__main__":
    print('start')
    reload_dictionary()
    print('end reload')
    test_default = "X光片肺上有结节、无任何其他症状、请问会不会只是炎症,肺动脉,糖尿病补肾胶囊后大便出血眼袋天生就有小孩刚满月 " \
                   " 乳汁很清每月月经都会提前打鼾  嗜睡  夜间憋气   发困很多痘子脸上长痘，脸上冒油怎么办"
    if len(sys.argv) > 1:
        test_default = sys.argv[1]
    words = cut(unicode_python_2_3(test_default))
    print('end cut')
    for w in words:
        print(w)


