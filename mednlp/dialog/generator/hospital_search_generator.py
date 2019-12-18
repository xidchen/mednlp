#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
hospital_search_generator.py -- the generator of hospital search

Author: maogy <maogy@guahao.com>
Create on 2019-01-13 Sunday.
"""

import json
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.generator.search_generator import SearchGenerator
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.exception import AIServiceException
from mednlp.service.ai_medical_service import ai_search_common
from mednlp.dialog.configuration import Constant as constant
from mednlp.dialog.dialogue_util import extend_area_search, get_hospital_json_obj


class HospitalSearchGenerator(SearchGenerator):
    name = 'hospital_search'
    """
    """
    input_field = ['q', 'sort', 'start', 'rows', 'department_name',
                   'hospital_level', 'hospital_type', 'std_dept_3d_haoyuan',
                   'authority', 'order_count_range', 'praise_rate_range',
                   'city_id', 'province_id', 'longitude', 'latitude', 'extend_area']
    output_field = [
        'hospital_id', 'hospital_name', 'hospital_photo_absolute', 'hospital_level',
        'order_count', 'hospital_hot_department', 'distance_desc', 'hospital_rule',
        'conclude_department', 'authority', 'dept_standard_name',
        'dept_province_top_rank', 'dept_city_top_rank', 'dept_country_top_rank',
        'dept_city_name', 'dept_province_name', constant.GENERATOR_EXTEND_SEARCH_PARAMS,
        constant.GENERATOR_CARD_FLAG, 'area'
    ]

    hospital_search_fl = [
        'hospital_uuid', 'hospital_name', 'hospital_level',
        'hospital_photo_absolute', 'order_count',
        'hospital_hot_department', 'distance_desc',
        'hospital_rule', 'hospital_standard_department',
        'hospital_department']

    def __init__(self, cfg_path, **kwargs):
        super(HospitalSearchGenerator, self).__init__(cfg_path, **kwargs)
        self.cgc = AIServiceClient(global_conf.cfg_path, 'AIService')

    def generate(self, input_obj, **kwargs):
        result = {}
        # city_id、province_id、department_name逗号分隔
        department_search_params = {
            # 'standard_name': input_obj['department_name'].split(',')[0],
            'department_country_rank_range': '0|100',
            'rows': 1,
            'sort': 'fudan_country'
        }
        param = {
            'q': '*',
            'start': 0,
            'rows': 3,
            'do_spellcheck': '1',
            'dynamic_filter': '1',
            'opensource': '9',
            'fl': ','.join(self.hospital_search_fl),
            'sort': 'default'
        }
        transform_dict_data(department_search_params, input_obj, {'city': 'city_id', 'province': 'province_id'})
        transform_dict_data(param, input_obj, {'city': 'city_id', 'province': 'province_id'})
        # step1:存在科室名,获取top_hospital_id
        department_name = []
        department_first = ''
        top_hospital_id = ''
        if input_obj.get('department_name'):
            # 获取 top_hospital_id
            department_name = input_obj['department_name'].split(',')
            department_first = department_name[0]
            department_search_params['standard_name'] = department_first
            department_response = self.sc.query(department_search_params, 'department_search', method='get')
            if department_response.get('department'):
                top_hospital_id = department_response.get('department')[0].get('hospital_uuid')

        # 获取医院列表
        for field in self.input_field:
            value = input_obj.get(field)
            if field in ('department_name', 'city_id', 'province_id', 'extend_area'):
                continue
            elif not value:
                continue
            elif field == 'authority':
                param['fudan_specialty_rank'] = 1
                continue
            param[field] = value

        res, area_range = extend_area_search(params=param, holder=self.sc, target='hospital_search',
                                             data_key='hospital', method='get')
        if not res or res['code'] != 0:
            message = 'hospital_search error'
            if not res:
                message += ' with no res'
            else:
                message += res.get('message')
            raise AIServiceException(message)
        hospital_temp = res.get('hospital')
        # 扩展地区, 1=扩展地区, 2=精确地区
        extend_area = input_obj.get('extend_area', 1)
        if extend_area == 2 and area_range == 'all' and ('city_id' in input_obj or 'province_id'in input_obj):
            # 若精确地区 & 搜索范围是全国, 置为空list
            hospital_temp = []
            top_hospital_id = None
        ai_result = {'departmentName': department_name}
        hospitals = get_hospital_json_obj(datas=hospital_temp, ai_result=ai_result, fl_list=self.hospital_search_fl)
        hospital_uuid_list = [temp.get('hospital_uuid') for temp in hospitals]

        # 根据top_hospital_id获取权威医院,对权威医院排前, 非精确模式
        if top_hospital_id:
            # top_hospital_id 在医院列表里
            if top_hospital_id in hospital_uuid_list:
                top_hospital_index = hospital_uuid_list.index(top_hospital_id)
                top_hospital_json = hospitals.pop(top_hospital_index)
                hospitals.insert(0, top_hospital_json)
                hospitals[0]['authority'] = 1
            elif extend_area != 2:
                # top_hospital_id不在医院列表里 & 地区非精确模式 extend_area != 2
                top_search_params = {
                    'start': '0',
                    'rows': '1',
                    'do_spellcheck': '1',
                    'dynamic_filter': '1',
                    'opensource': '9',
                    'wait_time': 'all',
                    'haoyuan': '-1',
                    'hospital': top_hospital_id
                }
                top_res, top_area = extend_area_search(params=top_search_params, holder=self.sc,
                                                       target='hospital_search', data_key='hospital', method='get')
                top_hospitals = get_hospital_json_obj(
                    datas=top_res.get('hospital'), ai_result=ai_result, fl_list=self.hospital_search_fl)
                top_hospitals.extend(hospitals)
                hospitals = top_hospitals
                hospitals[0]['authority'] = 1
        if hospitals:
            self.set_department_rank(hospitals, department_first)
        field_trans = {
            'hospital_uuid': 'hospital_id',
            'hospital_photo_absolute': 'hospital_photo',
            'hospital_hot_department': 'hot_department',
            }

        fl = input_obj.get('fl', self.output_field)
        content = result.setdefault('content', [])
        for temp in hospitals:
            content_item = {}
            for field, value in temp.items():
                if field not in fl and field_trans.get(field) not in fl:
                    continue
                if field in field_trans:
                    content_item[field_trans[field]] = value
                else:
                    content_item[field] = value
            if constant.GENERATOR_CARD_FLAG in fl:
                content_item[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_HOSPITAL
            if 'distance_desc' in fl and (not content_item.get('distance_desc')):
                content_item['distance_desc'] = '>99km'
            content.append(content_item)
        if constant.GENERATOR_EXTEND_SEARCH_PARAMS in fl:
            result[constant.GENERATOR_EXTEND_SEARCH_PARAMS] = param
        if 'area' in fl:
            result['area'] = area_range
        return result

    def set_department_rank(self, hospitals, department_name=''):
        hospital_uuid_list = [temp.get('hospital_uuid') for temp in hospitals]
        hospital_uuid_str = ','.join(hospital_uuid_list)
        dept_fl = ['standard_name', 'country_top_rank', 'province_top_rank',
                   'city_top_rank', 'city_name', 'province_name']
        department_search_params = {
            'standard_name': department_name,
            'sort': 'fudan_country',
            'hospital_uuid': hospital_uuid_str,
            'fl': '''standard_name, country_top_rank, province_top_rank,
            city_top_rank, hospital_uuid, city_name, province_name'''}
        department_response = self.sc.query(department_search_params, 'department_search', method='get')
        if department_response.get('department'):
            for dept_obj in department_response.get('department'):
                if dept_obj.get('hospital_uuid') in hospital_uuid_list and 'hospital_uuid' in dept_obj:
                    index = hospital_uuid_list.index(dept_obj['hospital_uuid'])
                    new_obj = {}
                    for item in dept_fl:
                        if item in dept_obj:
                            key = 'dept_' + item
                            new_obj[key] = dept_obj[item]
                    hospitals[index].update(new_obj)

    def _sort_department_country_rank_range(self, input_obj):
        input_param = {'fl': 'hospital_id',
                       'q': input_obj.get('department_name')}
        params = {'source': '789', 'generator': 'department_search',
                  'method': 'generate', 'parameter': input_param}
        params_str = json.dumps(params, ensure_ascii=False)
        # print('params_str:'+str(params_str))
        res = self.cgc.query(params_str, 'content_generation')
        hospital_ids = []
        if res and res.get('data') and res['data'].get('content'):
            hospital_ids.append(res['data']['content'][0].get('hospital_id'))
        for field in ('longitude', 'latitude'):
            if input_obj.get(field):
                input_param[field] = input_obj[field]
        input_param['exclude_hospital'] = ','.join(hospital_ids)
        res, area = ai_search_common.get_extend_response(
            input_param, input_param, 'hospital')
        if not res or not res.get('hospital'):
            return [], area
        hospital_ids = []
        for hospital in res['hospital']:
            if hospital.get('hospital_uuid'):
                hospital_ids.append(hospital['hospital_uuid'])
        return hospital_ids, area
        # print(str(res)+area)


if __name__ == '__main__':
    import global_conf
    import json

    generator = HospitalSearchGenerator(global_conf.cfg_path)
    input_obj = {
        "q": "消化内科",
        "department_name": "消化内科",
        # 'city_id': '552',
        'extend_area': 2,
        'rows': 4,
        'latitude': '',
        'longitude': '',
        'authority': 1
        # 'hospital_level': '33',
        # 'province_id': '2',
        # 'hospital_level': 33,
        # 'authority': 1,
        # 'order_count_range': '10000|*',
        # 'longitude': '123',
        # 'latitude': '23'
        # ['q', 'sort', 'start', 'rows', 'department_name',
        #  'hospital_level', 'hospital_type', 'std_dept_3d_haoyuan',
        #  'authority', 'order_count_range', 'praise_rate_range',
        #  'city_id', 'province_id']
        # "sex": 1,
        # "age": 19,
        # "confirm_patient_info": 1,
        # 'symptom': '发烧,头痛'
        # "fl": ['doctor_uuid', 'hospital_id'
        #     , constant.GENERATOR_EXTEND_SEARCH_PARAMS
        #        ]
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))
