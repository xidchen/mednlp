#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cg_util.py -- 内容生成器的工具类
Author: renyx <renyx@guahao.com>
Create on 2019-06-25 Tuesday.
"""
import json
import math
import traceback
import global_conf
from mednlp.dialog.cg_constant import array_field, logger, REQUEST_IS_OK


# 转义的特殊字符
escape_char_list = ['\\', '+', '&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '?', ':', '®']

def parse_prefix_suffix_params(params):
    """
    解析前缀后缀语法
    若前缀为:#in#测量时间不详$$$为#not_in#测量时间不详
    表示有2条规则,第一条表示当前key对应的值在[测量时间不详],显示空字符串,
    第二条规则表示当前对应的值不在 [测量时间不详],显示 为 这个字。
    :param params:
    :return:
    """
    result = []
    prefix = params.split('$$$')
    if len(prefix) == 1:
        prefix_options = prefix[0].split('#')
        if len(prefix_options) == 1:
            result.append({'fill_value': prefix[0], 'op': 'assign'})
        else:
            result.append({'fill_value': prefix_options[0], 'op': prefix_options[1], 'params': prefix_options[2:]})
    else:
        for prefix_temp in prefix:
            prefix_options = prefix_temp.split('#')
            result.append({'fill_value': prefix_options[0], 'op': prefix_options[1], 'params': prefix_options[2:]})
    return result


def parse_key_params(params, info):
    """
    属性值的规则比前缀和后缀简单一致,但是有额外的规则:若不符合条件,显示当前值
    :param params:
    :param info:
    :return:
    """
    result = []
    value = params.split('$$$')
    info['key'] = value[0]
    for temp in value[1:]:
        options = temp.split('#')
        result.append({'fill_value': options[0], 'op': options[1], 'params': options[2:]})
    info['center'] = result
    return


def parse_symptom_data(data):
    result = {}
    symptom_split = data.split('@')
    symptom = symptom_split[0].split('#')
    link = []
    for temp in symptom_split[1:]:
        info = {}
        question_list = temp.split('|')
        info['prefix'] = parse_prefix_suffix_params(question_list[0])
        parse_key_params(question_list[1], info=info)
        info['suffix'] = parse_prefix_suffix_params(question_list[2])
        link.append(info)
    for symptom_temp in symptom:
        result[symptom_temp] = link

    return result


def get_symptom_dict(file_name):
    symptom_dict = {}
    result = []
    with open(file_name) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            result.append(line)
    for temp in result:
        symptom_dict.update(parse_symptom_data(temp))
    return symptom_dict


# 预问诊字典
previous_diagnose_dict = get_symptom_dict(global_conf.dict_path + 'previous_diagnose.dic')


def op_in(fill_value, key, params, data):
    """
    data[key]对应的值 在 params里,则赋值fill_value
    :param fill_value:  被填充的值
    :param key: 当前key
    :param params: 规则里key对应的参数
    :param data: 原始数据
    :return:
    """
    result = None
    if key in array_field:
        # 数组类型
        if set(data[key]).intersection(set(params)):
            result = fill_value
    else:
        if data[key] in params:
            result = fill_value
    return result


def op_not_in(fill_value, key, params, data):
    # data[key]对应的值 不在 params里,则赋值fill_value
    result = None
    if key in array_field:
        # 数组类型
        if not set(data[key]).intersection(set(params)):
            result = fill_value
    else:
        if data[key] not in params:
            result = fill_value
    return result


def op_assign(fill_value, key, params, data):
    return fill_value


def op_exist_key(fill_value, key, params, data):
    # data有params对应的key， 则返回fill_value
    result = None
    for temp in params:
        if data.get(temp):
            result = fill_value
            break
    return result


def op_not_exist_key(fill_value, key, params, data):
    # data没有params对应的key， 则返回fill_value
    result = None
    has_key = False
    for temp in params:
        if data.get(temp):
            has_key = True
            break
    if not has_key:
        result = fill_value
    return result


def op_blank(fill_value, key, params, data):
    return ''

op_dict = {
    'in': op_in,
    'not_in': op_not_in,
    'assign': op_assign,
    'exist_key': op_exist_key,
    'not_exist_key': op_not_exist_key,
    'blank': op_blank
}


def query_search_plat(params, holder, **kwargs):
    """
    调用search_plat
    :param holder:
    :param params:
    :return:
    """
    result = {}
    res = None
    try:
        logger.info('search/1.0参数:%s' % params)
        res = holder.query(params, 'search/1.0', method='post', timeout=0.3)
    except Exception as err:
        logger.exception(traceback.format_exc())
    if res and res.get('code') == REQUEST_IS_OK:
        result['content'] = res.get('data', [])
    elif res:
        logger.exception('search_plat 异常, 结果:%s' % json.dumps(res, ensure_ascii=False))
    return result


def batch_query_search_plat(params, holder, max_rows, **kwargs):
    """
    批量调用搜索
    :param params:
    :param holder:
    :param rows:
    :return:
    """
    result = {}
    batch = math.ceil(max_rows / 99)
    start = int(params.get('start', 0))
    rows = int(params.get('rows', 99))
    for i in range(batch):
        params['start'] = start
        params['rows'] = rows
        query_result = query_search_plat(json.dumps(params, ensure_ascii=False), holder)
        if query_result.get('content'):
            result.setdefault('content', []).extend(query_result['content'])
        start += 99
    return result


def filter_q(q):
    result = []
    for char in q:
        if char in escape_char_list:
            result.append('\\'+char)
        else:
            result.append(char)
    return ''.join(result)




if __name__ == '__main__':
    # result = get_symptom_dict(global_conf.dict_path + 'previous_diagnose.dic')
    from ailib.client.ai_service_client import AIServiceClient
    plat_sc = AIServiceClient(global_conf.cfg_path, 'SEARCH_PLATFORM_SOLR')
    batch_query_search_plat({}, plat_sc, 100)
    print('ok')