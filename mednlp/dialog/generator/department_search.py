#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
department_search.py -- the generator of department search

Author: maogy <maogy@guahao.com>
Create on 2019-01-14 Monday.
"""


from .search_generator import SearchGenerator
from ailib.utils.exception import AIServiceException


class DepartmentSearchGenerator(SearchGenerator):

    name = 'department_search'
    input_field = ['department_name', 'city_id', 'province_id']
    output_field = ['hospital_id']

    def __init__(self, cfg_path, **kwargs):
        super(DepartmentSearchGenerator, self).__init__(cfg_path, **kwargs)

    def generate(self, input_obj, **kwargs):
        param = {'department_country_rank_range': '0|100',
                 'rows': 1, 'sort': 'fudan_country'}
        for field in self.input_field:
            value = input_obj.get(field)
            if not value:
                continue
            if field == 'department_name':
                param['standard_name'] = value
            else:
                param[field] = value
        res = self.sc.query(param, 'department_search', method='get')
        if not res or res['code'] != 0:
            message = 'dept_search error'
            if not res:
                message += ' with no res'
            else:
                message += res.get('message')
            raise AIServiceException(message)
        depts = res.get('department')
        result = {}
        content = result.setdefault('content', [])
        field_trans = {'hospital_uuid': 'hospital_id'}
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
