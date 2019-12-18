#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2017-11-22 星期三.
"""
import re
import sys
import global_conf


def load_dept_dict():
    """主要是生成部门列表"""
    dept_dict = {}
    dept_id = {}
    dept_name_to_id = {}
    for i, line in enumerate(open(global_conf.dept_classify_dept_path, 'r')):
        dept_name, dept_name_id = line.strip().split('=')
        dept_dict[i] = dept_name
        dept_id[dept_name] = dept_name_id
        dept_name_to_id[dept_name] = i
    return dept_dict, dept_id, dept_name_to_id


def clean_str(string):
    """
    去掉string中的所有非中文字符
    :param string: 每句话的文本字符串
    :return: 返回字符串中的中文字符
        """
    if not sys.version > '3':
        string = re.sub(u'[^\u4e00-\u9fff]', '', string)
    else:
        string = re.sub(r'[^\u4e00-\u9fff]', '', string)
    string = re.sub(r'\s{2,}', '', string)
    return string.strip()
