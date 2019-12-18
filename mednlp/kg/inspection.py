#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
inspection.py -- the class of entity inspection

Author: maogy <maogy@guahao.com>
Create on 2018-04-18 Wednesday.
"""


class Inspection(object):

    def __init__(self):
        pass

    def build_entity(self, detail):
        """
        组装网站的检查检验实体.
        参数:
        detail->实体的一些详情.
        返回值->完整实体.
        """
        if detail.get('option_value'):
            detail['entity_name'] += detail['option_value']
        else:
            min_str = detail.get('min_value', '')
            max_str = detail.get('max_value', '')
            if min_str and detail.get('unit'):
                min_str += detail['unit']
            if max_str and detail.get('unit'):
                max_str += detail['unit']
            value_str = ''
            if min_str and not max_str:
                value_str = '>' + min_str
            elif not min_str and max_str:
                value_str = '<' + max_str
            elif min_str and max_str:
                value_str = '%s~%s' % (min_str, max_str)
            detail['entity_name'] += value_str
        if detail.get('parent_name'):
            detail['entity_name'] = detail['parent_name'] + detail['entity_name']
        return detail
    
