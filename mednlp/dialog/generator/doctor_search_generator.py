#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
the generator of doctor_search

Author: renyx <renyx@guahao.com>
Create on 2019-03-28 ThursDay.
"""
from ailib.client.http_client import HttpClient
from ailib.utils.exception import AIServiceException
from mednlp.dialog.generator.search_generator import SearchGenerator
from mednlp.dialog.configuration import Constant as constant
from mednlp.dialog.dialogue_util import extend_area_search, get_doctor_json_obj, get_consult_doctor
from mednlp.utils.utils import transform_dict_data
from ailib.client.ai_service_client import AIServiceClient
import configparser
import json
import global_conf


class DoctorSearchGenerator(SearchGenerator):
    name = 'doctor_search'
    input_field = ['q', 'start', 'rows', 'sort',
                   'serve_type', 'is_public', 'hospital_level', 'doctor_title',
                   'std_dept_3d_haoyuan', 'is_doctor_on_rank', 'order_count_range',
                   'total_praise_rate_range', 'city_id', 'province_id', 'contract_price_range',
                   'consult_price_range', 'hospital_name', 'department_name', 'consult_service_type',
                   'extend_area', 'disease_name', 'doctor_id']

    output_field = ['service_package_id', 'recent_haoyuan_date', 'recent_haoyuan_time',
                    'haoyuan_fee', 'haoyuan_remain_num', 'recent_haoyuan_refresh',
                    'doctor_haoyuan_detail', 'hospital_name', 'department_name',
                    'hospital_level', 'department_id', 'hospital_id',
                    'hospital_province', 'doctor_name',

                    'doctor_id', 'doctor_photo', 'doctor_technical_title',
                    'specialty_disease', 'comment_score', 'is_health',
                    'sns_user_id', 'total_order_count', 'is_patient_praise',
                    'base_rank', 'contract_register', 'is_consult_serviceable',
                    'doctor_introduction', 'feature', 'is_image_text',
                    'is_diagnosis', 'is_consult_phone', 'lowest_consult_fee',
                    'highest_consult_fee', 'accurate_package', 'accurate_package_price',
                    'accurate_package_code',
                    constant.GENERATOR_CARD_FLAG,
                    constant.GENERATOR_EXTEND_SEARCH_PARAMS, constant.GENERATOR_AREA,
                    constant.GENERATOR_EXTEND_IS_CONSULT]

    # 搜索请求的fl
    fl_return = ['is_service_package', 'doctor_recent_haoyuan_detail', 'doctor_haoyuan_time',
                 'doctor_haoyuan_detail', 'hospital_department_detail', 'doctor_name',

                 'doctor_uuid', 'doctor_photo_absolute', 'doctor_technical_title',
                 'specialty_disease', 'comment_score', 'is_health',
                 'sns_user_id', 'total_order_count', 'is_patient_praise',
                 'base_rank', 'contract_register', 'is_consult_serviceable',
                 'doctor_introduction', 'feature', 'doctor_haoyuan_detail',
                 'doctor_consult_detail', 'is_consult_phone', 'phone_consult_fee',
                 'serve_type', 'accurate_package_code', 'accurate_package_price']

    def __init__(self, cfg_path, **kwargs):
        super(DoctorSearchGenerator, self).__init__(cfg_path, **kwargs)
        self.plat_sc = AIServiceClient(cfg_path, 'SEARCH_PLATFORM_SOLR')
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(cfg_path)
        self.primaryKey = config.items('SEARCH_PLATFORM_SOLR')[5][1]

    def ai_doctor_search(self, input_obj, **kwargs):
        result = {}
        doctors = []
        params = {
            'cat': 'ai_doctor_search',
            'primaryKey': self.primaryKey,
            'start': 0,
            'rows': 10,
            'fl': 'id,name',
            'filter': ['status:1'],
            'sort': {'score': 'desc', 'created_time': 'desc'},
            'query': '*'
        }
        """
        query: "name:(傅雯雯 王学廉) AND (1=1 OR disease_name:()^3 OR department_name:()^2 OR id:()^4)"
        """
        q = input_obj.get('q')
        if not q:
            return doctors, result
        sort = input_obj.get('sort')
        if sort == 'social_recommended':
            query_format = 'name:(%s) AND (%s)'
            query_list = ['*:*']
            department_name = [temp for temp in input_obj.get('department_name', '').split(',') if temp]
            # 疾病名字或许有逗号,因此改为数组
            disease_name = input_obj.get('disease_name', [])
            doctor_id = [temp for temp in input_obj.get('doctor_id', '').split(',') if temp]
            if department_name:
                query_list.append('department_name:(%s)^5' % ' OR '.join(department_name))
            if disease_name:
                query_list.append('disease_name:(%s)^10' % ' OR '.join(disease_name))
            if doctor_id:
                query_list.append('id:(%s)^20' % ' OR '.join(doctor_id))
            query = query_format % (q, ' OR '.join(query_list))
            params['query'] = query
        for field in ('start', 'rows'):
            value = input_obj.get(field)
            if not value:
                continue
            params[field] = value

        fq_params = {
            'city_id': ('city_id', 1),
            'province_id': ('province_id', 1)
        }
        for param, (field, params_type) in fq_params.items():
            para_value = input_obj.get(param)
            if not para_value:
                continue
            if params_type == 1:
                params['filter'].append('%s:%s' % (field, para_value))
        res = self.plat_sc.query(json.dumps(params), 'search/1.0', method='post', timeout=0.3)
        if not res or res['code'] != 200:
            message = 'ai_doctor_search error'
            if not res:
                message += ' with no res'
            else:
                message += res.get('msg', '')
            raise AIServiceException(message)
        doctors = res.get('data', [])
        return doctors, result

    def doctor_search(self, input_obj, **kwargs):
        result = {}
        param = {
            'q': '*',
            'start': 0,
            'rows': 10,
            'fl': ','.join(self.fl_return),
            'do_spellcheck': '1',
            'travel': '0',
            'secondsort': '0',
            'aggr_field': 'contract_register',
            'opensource': '9',
            'sort': 'general'
        }
        input_trans_dict = {
            'city_id': 'city',
            'province_id': 'province'
        }
        for field in self.input_field:
            value = input_obj.get(field)
            if field not in input_obj or value is None:
                # 输入中无该数据 or value is None
                continue
            elif field in ['hospital_name', 'department_name', 'extend_area']:
                continue
            elif field in input_trans_dict.keys():
                transform_dict_data(param, input_obj, {input_trans_dict[field]: field})
                continue
            param[field] = value
        res, area_range = extend_area_search(params=param, holder=self.sc, target='doctor_search',
                                             data_key='docs', method='get')
        if not res or res['code'] != 0:
            message = 'doctor_search error'
            if not res:
                message += ' with no res'
            else:
                message += res.get('message')
            raise AIServiceException(message)
        doctor_temp = res.get('docs')
        # 扩展地区, 1=扩展地区, 2=精确地区
        extend_area = input_obj.get('extend_area', 1)
        if extend_area == 2 and area_range == 'all' and ('city_id' in input_obj or 'province_id' in input_obj):
            # 若精确地区 & 搜索范围是全国 & 有地区入参, 置为空list
            doctor_temp = []
        ai_result = {}
        ai_result_trans_dict = {
            'hospitalName': 'hospital_name',
            'departmentName': 'department_name'
        }
        for key, value in ai_result_trans_dict.items():
            if input_obj.get(value):
                ai_result[key] = input_obj[value].split(',')
        doctors = get_doctor_json_obj(doctors=doctor_temp, ai_result=ai_result, holder=self.sc, fl_list=self.fl_return,
                                      haoyuan_range=input_obj.get('contract_price_range'))
        fl = input_obj.get('fl', self.output_field)
        if constant.GENERATOR_EXTEND_IS_CONSULT in fl:
            is_consult = get_consult_doctor(res)
            result[constant.GENERATOR_EXTEND_IS_CONSULT] = is_consult
        if constant.GENERATOR_EXTEND_SEARCH_PARAMS in fl:
            result[constant.GENERATOR_EXTEND_SEARCH_PARAMS] = param
        if constant.GENERATOR_AREA in fl:
            result[constant.GENERATOR_AREA] = area_range
        return doctors, result

    def generate(self, input_obj, **kwargs):
        # 1.search   2.变更字段   3.挑选fl里的字段
        sort = input_obj.get('sort')
        result = {}
        doctors = []
        info = {}
        if sort in ('social_recommended',):
            doctors, info = self.ai_doctor_search(input_obj, **kwargs)
        else:
            doctors, info = self.doctor_search(input_obj, **kwargs)
        fl = input_obj.get('fl', self.output_field)
        content = result.setdefault('content', [])
        field_trans = {
            'hospital_uuid': 'hospital_id',
            'doctor_photo_absolute': 'doctor_photo',
            'doctor_uuid': 'doctor_id',
            'department_uuid': 'department_id',
            'id': 'doctor_id',
            'name': 'doctor_name'
        }
        for temp in doctors:
            content_item = {}
            for field, value in temp.items():
                if field not in fl and field_trans.get(field) not in fl:
                    continue
                if field in field_trans:
                    content_item[field_trans[field]] = value
                else:
                    content_item[field] = value
            if constant.GENERATOR_CARD_FLAG in fl:
                content_item[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_DOCTOR
            content.append(content_item)
        if constant.GENERATOR_EXTEND_IS_CONSULT in fl and constant.GENERATOR_EXTEND_IS_CONSULT in info:
            result[constant.GENERATOR_EXTEND_IS_CONSULT] = info[constant.GENERATOR_EXTEND_IS_CONSULT]
        if constant.GENERATOR_EXTEND_SEARCH_PARAMS in fl and constant.GENERATOR_EXTEND_SEARCH_PARAMS in info:
            result[constant.GENERATOR_EXTEND_SEARCH_PARAMS] = info[constant.GENERATOR_EXTEND_SEARCH_PARAMS]
        if constant.GENERATOR_AREA in fl and constant.GENERATOR_AREA in info:
            result[constant.GENERATOR_AREA] = info[constant.GENERATOR_AREA]
        return result





if __name__ == '__main__':
    # ['q', 'start', 'rows', 'sort',
    #  'serve_type', 'is_public', 'hospital_level', 'doctor_title',
    #  'std_dept_3d_haoyuan', 'is_doctor_on_rank', 'order_count_range',
    #  'total_praise_rate_range', 'city_id', 'province_id', 'contract_price_range',
    #  'haoyuan_date', 'hospital_name', 'department_name']
    # city_id、province_id、department_name逗号分隔
    generator = DoctorSearchGenerator(global_conf.cfg_path)
    input_obj = {
        "q": "name_21",
        'start': 0,
        'rows': 4,
        # 'sort': 'general',
        # 'serve_type': '1',
        # 'is_public': 1,
        # 'hospital_level': 33,
        # 'doctor_title': '1,3',
        # 'std_dept_3d_haoyuan': '123',
        # 'is_doctor_on_rank': '1',
        # 'order_count_range': '10|*',
        # 'total_praise_rate_range': '95|*',
        'city_id': 552,
        'province_id': 2,
        # 'contract_price_range': '0|300',
        # 'department_name': '神经内科',
        # 'extend_area': 2,
        'sort': 'social_recommended',
        'department_id': '1,2,3',
        'disease_id': '1,2,3',
        'doctor_id': '1,2,3',
        'fl': ['doctor_id', 'doctor_name']
        # "fl": ['doctor_uuid', 'hospital_id', constant.GENERATOR_EXTEND_SEARCH_PARAMS]
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))
