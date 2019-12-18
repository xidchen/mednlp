#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
out_link_builder.py -- some builder of out_link

Author: maogy <maogy@guahao.com>
Create on 2018-10-04 Thursday.
"""
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.configuration import get_ai_field_value
from mednlp.dialog.configuration import Constant as constant
import copy
from mednlp.dialog.component_config import consult_out_link, satisfy_out_link, valid_auto_diagnose_out_link

class OutLinkBuilderDB(object):
    """
    按钮的数据库配置构建器.
    """

    def __init__(self, conf, **kwargs):
        self.conf = conf
        self.out_links = conf['conf']


class OutLinkBuilderDBDeptClassify(OutLinkBuilderDB):
    """
    科室分诊的按钮的数据库配置构建器.
    """

    open_fields = ['city', 'province', 'department_name']
    
    def build(self, data, inputs):
        # data = data['data']
        out_links = []
        for out_link_conf in self.out_links:
            fields = []
            if out_link_conf.get('biz_conf'):
                fields = out_link_conf['biz_conf']
            parameter = []
            out_link = {'conf_id': out_link_conf['conf_id']}
            if 'city' in fields:
                if 'city' in data['search_params']:
                    parameter.append({'key': 'city',
                                      'value': data['search_params']['city']})
            if 'province' in fields:
                if 'province' in data['search_params']:
                    parameter.append({
                        'key': 'province',
                        'value': data['search_params']['province']})
            if 'department_name' in fields:
                dept = data['data']['depts'][0]
                if dept['dept_name'] != 'unknow':
                    parameter.append({
                        'key': 'department_name',
                        'value': dept['dept_name']})
            out_link['parameter'] = parameter
            out_links.append(out_link)
        return out_links

class DefaultOutLinkBuilder():

    def __init__(self, conf, **kwargs):
        self.out_link_obj_list = []
        self.fl = set()
        self.set_out_link_conf(conf.get('conf', []))

    def get_fl(self):
        return self.fl

    def set_out_link_conf(self, conf):
        for link in conf:
            if link:
                link_obj = OutLinkObj()
                link_obj.set_out_link_conf(link)
                self.out_link_obj_list.append(link_obj)

    def build(self, response_data=[], input=None):
        return_obj = []
        res_data = []
        if response_data.get('doctor_search'):
            res_data = response_data['doctor_search']
        elif response_data.get('hospital_search'):
            res_data = response_data['hospital_search']
        elif response_data.get('post_search'):
            res_data = response_data['post_search']
        for out_link_obj in self.out_link_obj_list:
            json_obj = out_link_obj.build_obj_result(res_data)
            if json_obj:
                return_obj.append(json_obj)
        return return_obj

class OutLinkObj():
    
    field_list = ['conf_id', 'parameter']

    def __init__(self):
        self.id = ''
        self.parameter = []
        self.fl = set()

    def set_out_link_conf(self, out_link):
        self.id = out_link.get('conf_id', '')
        if not self.id:
            self.id = ''
        self.fl = out_link.get('biz_conf', set())
        if not self.fl:
            self.fl = set()

    def get_id(self):
        return self.id

    def get_parameter(self):
        return self.parameter

    def get_fl(self):
        return self.fl

    def build_obj_result(self, response_data=[]):
        out_link_obj = {}
        out_link_obj['conf_id'] = self.id
        out_link_obj['parameter'] = []
        for data_item in response_data:
            out_link_dict = {}
            for key,value in data_item.items():
                if key in self.fl and value:
                    out_link_dict[key] = value
            if out_link_dict:
                out_link_obj['parameter'].append(out_link_dict)
        return_obj = {}
        for field in self.field_list:
            if out_link_obj.get(field):
                return_obj[field] = out_link_obj.get(field)
        return return_obj


class OutLinkBuilderV2(object):
    # out_link 组装器,由active调用
    def __init__(self):
        pass

    def build(self, data, intention_conf):
        result = []
        if intention_conf.configuration.mode in constant.VALUE_MODE_MENHU:
            self.deal_xwyz_outlink(result, data, intention_conf)
        out_links = intention_conf.out_link_dict.get('intention', {}).get(intention_conf.intention_set_id, [])
        for temp in out_links:
            part = OutLinkPart(temp)
            result.append(part.build(data, intention_conf, source='out_link_build'))
        return result

    def deal_xwyz_outlink(self, result, data, intention_conf):
        intention_temp = intention_conf.intention
        if intention_temp == 'keyword':
            intention_temp = '%s_%s' % (intention_conf.intention, intention_conf.intention_details[0])
        if intention_conf.intention in ('departmentConfirm', 'departmentAmong', 'departmentSubset', 'doctor'):
            # 意图在该3个里
            if data.get('is_consult'):
                # 加入去问诊的按钮
                consult_out_link_copy = copy.deepcopy(consult_out_link)
                if data.get('query_content'):
                    consult_out_link_copy['text'] = consult_out_link['text'] % data['query_content']
                result.append(consult_out_link_copy)
        if intention_temp in ('auto_diagnose',):
            satisfy_out_link_copy = copy.deepcopy(satisfy_out_link)
            result.append(satisfy_out_link_copy)
        if intention_conf.intention in ('department', 'auto_diagnose'):
            if data.get('valid_auto_diagnose'):
                valid_auto_diagnose_out_link_copy = copy.deepcopy(valid_auto_diagnose_out_link)
                result.append(valid_auto_diagnose_out_link_copy)


class OutLinkPart(object):
    # out_link 组件
    def __init__(self, out_link):
        self.out_link = out_link

    def build(self, data, intention_conf, **kwargs):
        """
        :param data:
        :param intention_conf:
        :return:
        {
            content: str,   外链内容，URL或文本
            action: int,     外链动作：1-链接跳转，2-返回文本
            outlink_start_location: int     外联位置
        }
        """
        result = {}
        out_link_id = self.out_link['out_link_id']
        result['id'] = out_link_id
        if self.out_link.get('type') in [2, 3, 4]:
            result['type'] = self.out_link['type']
        transform_dict_data(result, self.out_link, {'id': 'id', 'name': 'name', 'text': 'text',
                                                    'action': 'action'})
        # keyword 组装
        keywords = intention_conf.keyword_dict.get('out_link', {}).get(out_link_id, [])
        if keywords and result.get('text'):
            text = list(result['text'])
            last_keyword_len = 0
            for temp in keywords:
                if temp.get('location') and temp.get('ai_field'):
                    ai_field_value = get_ai_field_value(data, 0, temp['ai_field'])
                    # 大家帮和帖子需要搜索的q,在search_params里返回
                    if 'user_q_content' == temp['ai_field']:
                        ai_field_value = data.get('search_params', {}).get('q')
                    if ai_field_value:
                        start_temp = temp['location'] + last_keyword_len
                        text = text[:start_temp] + list(ai_field_value) + text[start_temp:]
                        last_keyword_len += len(ai_field_value)
            result['text'] = ''.join(text)
        return result
