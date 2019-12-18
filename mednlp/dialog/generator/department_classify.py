#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
department_classify.py -- the generator of department classify

Author: maogy <maogy@guahao.com>
Create on 2019-01-13 Sunday.
"""


import global_conf
from mednlp.dialog.generator.ai_generator import AIGenerator
from ailib.utils.exception import AIServiceException
from mednlp.dialog.general_util import get_service_data
from mednlp.dialog.cg_constant import logger


class DepartmentClassify(AIGenerator):
    name = 'department_classify'
    input_field = ['q', 'sex', 'age', 'level', 'rows']
    output_field = ['department_id', 'department_name', 'accuracy']

    def __init__(self, cfg_path, **kwargs):
        super(DepartmentClassify, self).__init__(
            cfg_path, **kwargs)

    def generate(self, input_obj, **kwargs):
        result = {}
        param = {'source': global_conf.source, 'rows': 1}
        for field in self.input_field:
            value = input_obj.get(field)
            if not value:
                continue
            param[field] = value
        res = self.ac.query(param, 'dept_classify')
        if not res or res['code'] != 0:
            message = 'dept_classify error'
            if not res:
                message += ' with no res'
            else:
                message += res.get('message')
            raise AIServiceException(message)
        depts = res['data']
        content = result.setdefault('content', [])
        field_trans = {
            'dept_name': 'department_name', 'dept_id': 'department_id'}
        fl = input_obj.get('fl', self.output_field)
        for dept in depts:
            content_item = {}
            for field, value in dept.items():
                if field not in fl and field_trans.get(field) not in fl:
                    continue
                if field in field_trans:
                    content_item[field_trans[field]] = value
                else:
                    content_item[field] = value
            content.append(content_item)
        return result


class DepartmentClassifyInteractiveGenerator(AIGenerator):

    name = 'department_classify_interactive'
    input_field = ['q', 'sex', 'age', 'level', 'confirm_patient_info', 'symptom', 'return_type']
    output_field = [
        'department_id', 'department_name', 'score', 'accuracy']
    slot = ['sex', 'age', 'symptom']

    def __init__(self, cfg_path, **kwargs):
        super(DepartmentClassifyInteractiveGenerator, self).__init__(
            cfg_path, **kwargs)

    def generate(self, input_obj, **kwargs):
        # 默认高可信,质疑模式
        return_type = 1    # 1: 有slot直接返回 2: 返回全部信息
        param = {'source': global_conf.source, 'interactive': 2}
        for field in self.input_field:
            value = input_obj.get(field)
            if value is None:
                continue
            if field == 'confirm_patient_info':
                param.pop('interactive')
            elif field == 'return_type':
                return_type = value
            else:
                param[field] = value
        data = get_service_data(param, self.ac, 'dept_classify_interactive', logger=logger, throw=True, result={})
        result = {}
        if data['isSex'] == 1:
            result.setdefault('slot', []).append({'name': 'sex'})
        if data['isAge'] == 1:
            result.setdefault('slot', []).append({'name': 'age'})
        if data.get('symptoms'):
            result.setdefault('slot', []).append(
                {'name': 'symptom', 'content': data['symptoms']})
        if result.get('slot') and return_type == 1:
            return result
        depts = data['depts']
        content = result.setdefault('content', [])
        field_trans = {
            'dept_name': 'department_name', 'dept_id': 'department_id'}
        fl = input_obj.get('fl', self.output_field)
        for dept in depts:
            if dept.get('dept_name') == 'unknow':
                continue
            content_item = {}
            for field, value in dept.items():
                if field not in fl and field_trans.get(field) not in fl:
                    continue
                if field in field_trans:
                    content_item[field_trans[field]] = value
                else:
                    content_item[field] = value
            content.append(content_item)
        return result


if __name__ == '__main__':
    import global_conf
    import json

    generator = DepartmentClassifyInteractiveGenerator(global_conf.cfg_path)
    # generator = DepartmentClassify(global_conf.cfg_path)
    input_obj = {
        "q": "头痛是挂内科还是外科",
        "level": 4,
        'return_type': 1,
        # "sex": 1,
        # "age": 19,
        # "confirm_patient_info": 1,
        # 'symptom': '发烧,头痛'
        # "q": "头痛",
        # "sex": 1,
        # "age": 3285,
        # "confirm_patient_info": 1,
        'symptom': '-1'
        # "fl": ['doctor_uuid', 'hospital_id'
        #     , constant.GENERATOR_EXTEND_SEARCH_PARAMS
        #        ]
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))

    
