#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dept_classify_processer.py -- the processer of dept classify

Author: maogy <maogy@guahao.com>
Create on 2018-10-02 Tuesday.
"""


import global_conf
from mednlp.dialog.processer.doctor import DoctorProcesser
import mednlp.utils.utils as utils
from ailib.utils.exception import AIServiceException
from ailib.client.ai_service_client import AIServiceClient


class DeptClassifyProcesser(object):
    """
    科室分诊处理器.
    """
    result_field_dict = {''
    }

    def __init__(self, **kwargs):
        self.ai_server = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.doctor_processer = DoctorProcesser()

    def process(self, inputs, dialog):
        params = {}
        input_field = {'q': 'q', 'sex': 'sex', 'age': 'age',
                      'symptom': 'symptom', 'rows': 'rows'}
        for input_item in inputs:
            for dialog_field, dept_field in input_field.items():
                if dialog_field in input_item:
                    params[dept_field] = input_item[dialog_field]
        res = self.ai_server.query(params, 'dept_classify_interactive')
        res = utils.unicode2str(res)
        dept = self._get_dept(res)
        if not dept:
            res['is_end'] = 0
            return res
        doctor_field = ['city', 'province', 'area', 'hospital', 'q']
        doctor_inputs = {'std_department_name': dept['dept_name']}
        for input_item in inputs:
            for field in doctor_field:
                if input_item.get(field):
                    doctor_inputs[field] = input_item[field]
        doctor_res = self.doctor_processer.process([doctor_inputs], dialog)
        res['doctor_search'] = doctor_res
        res['search_parmas'] = doctor_res.pop('search_params', {})
        res['is_end'] = 1
        return res
            
    def _get_dept(self, data):
        data = self._get_data(data)
        if not data:
            return data
        if data['isEnd'] != 1:
            return None
        depts = data['depts']
        if not depts:
            return depts
        if depts[0]['dept_name'] != 'unknow':
            return depts[0]
        return {}

    def _get_data(self, data):
        if data['code'] != 0:
            return None
        return data['data']
        
