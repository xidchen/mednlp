#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.model.similarity import TfidfSimilarity
import global_conf


class HospitalProcessor(BasicProcessor):
    """
    医院处理的意图
    """
    default_rows = 2

    fl = ['hospital_uuid', 'hospital_name', 'hospital_level',
          'hospital_photo_absolute', 'order_count',
          'hospital_hot_department']        # 实际只需要该行之前的【包含hospital_hot_department】
          # 'distance_desc', 'hospital_rule', 'hospital_standard_department',
          # 'hospital_department']

    fl_return_dict = {
        'hospital_uuid': 'hospital_uuid',
        'hospital_name': 'hospital_name',
        'hospital_level': 'hospital_level',
        'hospital_photo_absolute': 'hospital_picture',
        'order_count': 'order_num',
        'hospital_hot_department': 'special_department_name'
    }

    def initialize(self):
        self.search_params = {
            'rows': self.default_rows,
            'start': '0',
            'do_spellcheck': '1',
            'opensource': '27'
        }

    def process(self, query, **kwargs):
        """
        http://192.168.1.46:2000/hospital_search?rows=12&start=0&do_spellcheck=1&hospital=125336070937502000,
        5cee04f9-4cc8-4499-a35b-6f37f2dd8a74000,de14f61e-4577-4b72-b06d-0ca3db1943d8000,
        de14f61e-4577-4b72-b06d-0ca3db1943d8000,253aa3fe-45ea-45e0-976b-c49ee58b92fb000,
        BF314EAD23323ED3E040007F01004B66000,125358368239002000,8f113a19-eee7-47b8-9517-2ad069a2f57a000&
        q=儿科&city=552&province=24&fl=hospital_uuid,hospital_name,hospital_level,hospital_photo_absolute,
        order_count,hospital_hot_department,distance_desc,hospital_rule,
        hospital_standard_department,hospital_department
        :param query:
        :param kwargs:
        :return:
        """
        result = {}
        self.set_params(query, **kwargs)  # set ai_result + input_params
        self.set_rows()  # 设置rows

        if constant.CONFIG_HOSPITAL_SOURCE_ALL != self.intention_conf.configuration.hospital_source:
            # hospital_source配置成 非 全平台医院
            # 获取hospital_relation
            hospital_relation = self.intention_conf.configuration.hospital_relation
            hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if temp.get('hospital_uuid')]
            if not hospital_ids:
                result['code'] = 0
                result['is_end'] = 1
                return result
            self.search_params['hospital'] = ','.join(hospital_ids)
        _params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        if not q_content:
            _params['q'] = self.input_params.get('input', {}).get('q')
        # 添加省份,城市参数
        self.search_params.update(_params)
        self.search_params['fl'] = ','.join(self.fl)
        # 添加 医院筛选功能
        response, area = ai_search_common.get_extend_response(self.search_params, self.input_params, 'hospital')
        hospital_data = self.get_hospital_data(response)
        if hospital_data:
            result[constant.QUERY_KEY_HOSPITAL_SEARCH] = hospital_data
        result['code'] = response['code']
        result['search_params'] = self.search_params
        result['is_end'] = 1
        return result

    def set_rows(self):
        self.search_params['rows'] = super(
            HospitalProcessor, self).basic_set_rows(3, default_rows=self.default_rows)

    def get_hospital_data(self, response):
        result = []
        if response and response.get('count', 0) > 0:
            for temp in response.get('hospital', []):
                hospital_temp = {}
                for fl_key, return_key in self.fl_return_dict.items():
                    if fl_key in temp:
                        if 'hospital_hot_department' == fl_key:
                            hospital_temp[return_key] = [hot_dept_temp.split(
                                '|')[1] for hot_dept_temp in temp[fl_key] if hot_dept_temp]
                        else:
                            hospital_temp[return_key] = temp[fl_key]
                result.append(hospital_temp)
        return result
