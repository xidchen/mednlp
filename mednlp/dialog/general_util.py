#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import traceback
from ailib.utils.log import GLLog
import global_conf
import copy

logger = GLLog('get_service_data_input_output', level='info', log_dir=global_conf.log_dir).getLogger()


def get_attr(obj, field_name, **kwargs):
    # 根据key从对象里获取实例的值
    result = None
    if kwargs.get('default'):
        result = kwargs['default']
    if hasattr(obj, field_name):
        result = getattr(obj, field_name)
    return result


def set_attr(obj, field_name, holder):
    # 设置对象的某个key
    setattr(obj, field_name, holder)
    return getattr(obj, field_name)


def get_service_data(params, holder, service_name, **kwargs):
    """
    http获取相关数据
    kwargs:
        method: 采取的方式 post、get
        throw: 请求抛出异常，是否让上层知道
        return_response: True 全部返回, False 返回data_key
        result: 默认返回值
        logger: 打印日志logger, 用户若不传,则记在get_service_data_input_output.log里
    """
    result = []
    if 'result' in kwargs:
        result = kwargs['result']
    attr = {
        'code': '0',
        'method': 'post',
        'data_key': 'data',
        'throw': False,
        'return_response': False,
        'logger': logger
    }
    params_str = params
    if isinstance(params, dict):
        params_str = json.dumps(params, ensure_ascii=False)
    for key_temp in kwargs:
        if key_temp in attr:
            attr[key_temp] = kwargs[key_temp]
    try:
        res = holder.query(params, service_name, method=attr['method'])
        if not res or ('code' in res and (str(attr['code']) != str(res.get('code', '-1')))):
            raise Exception('%s接口请求异常' % service_name)
        if attr['return_response']:
            result = res
        elif res.get(attr['data_key']):
            result = res[attr['data_key']]
    except Exception as err:
        attr['logger'].error(traceback.format_exc())
        attr['logger'].error('调用%s服务异常,入参:%s' % (service_name, params_str))
        if attr['throw']:
            raise Exception(err)
    return result

def transform_answer_keyword(copyed_object, dest, value):
    """
    :param copyed_object: 被复制对象
    :param dest: 存放的地方
    :param value: 具体k_v值
    :return:
    """
    copy_value = copy.deepcopy(copyed_object)
    copy_value.update(value)
    dest.append(copy_value)
