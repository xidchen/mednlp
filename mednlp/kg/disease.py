#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease.py -- the module of disease entity processor

Author: maogy <maogy@guahao.com>
Create on 2018-04-05 Thursday.
"""


class DiseaseEntity(object):

    _disease_history = 'disease_history'
    
    field_handler = {
        _disease_history: '_disease_history_format'
    }
    
    def __init__(self, **kwargs):
        pass

    def format(self, content, fields=None):
        """
        实体格式化.
        参数:
        content->需要格式化的实体内容(dict).
        fields->执行需要格式化的类,默认全部.
        """
        fields_set = set()
        if fields:
            if isinstance(fields, (list, set)):
                fields_set.update(fields)
            else:
                fields_set.add(fields)
        if not fields_set:
            fields_set.update(self.field_handler.keys())
        # 过滤可格式化字段外的字段
        fields_set = fields_set & set(self.field_handler.keys())
        # 格式化每个字段
        for field in fields_set:
            handler_name = self.field_handler[field]
            handler = getattr(self, handler_name)
            handler(content, field)
        return

    def disease_history_weight(self, content, diseases):
        """
        计算既往史权重.
        参数:
        content->需要计算既往史权重的实体内容(dict).
        diseases->相关的疾病
        """
        if self._disease_history not in content:
            return []
        disease_history = content[self._disease_history]
        weight_list = []
        for disease in diseases:
            if disease_history.get(disease):
                weight_list.append(disease_history[disease])
        return weight_list

    def _disease_history_format(self,  content, field):
        """
        相关既往病史格式化.
        参数:
        content->实体内容(dict)
        field->字段名称(string).
        格式化格式->字典,{disease_id, weight(100)}
        """
        if not content.get(field):
            return
        disease_history = content[field]
        content[field] = {}
        for disease_weight_str in disease_history:
            item_list = disease_weight_str.split('|')
            if len(item_list) != 2:
                print('error for format disease history:', disease_weight_str)
                continue
            disease_id, weight = item_list[0], item_list[1]
            content[field][disease_id] = weight
        return

