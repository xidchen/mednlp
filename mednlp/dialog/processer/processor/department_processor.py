#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.model.similarity import TfidfSimilarity
import global_conf
from mednlp.dialog.processer.processor.doctor_processor import DoctorProcessor
import mednlp.dialog.processer.common as common
from mednlp.dialog.processer.ai_search_common import query
from mednlp.dialog.interactive_box_info import InteractiveBoxConstant
import copy
from ailib.client.ai_service_client import AIServiceClient
import configparser
from mednlp.dialog.configuration import logger


class DepartmentProcessor(BasicProcessor):
    # 科室处理

    default_rows = 2
    dept_classify_params_mapping = {
        'sex': 'sex',
        'age': 'age',
        'symptomName': 'symptom'
    }

    def __init__(self):
        super(DepartmentProcessor, self).__init__()
        self.doctor_process = DoctorProcessor()  # 必须保证一定有intention_conf

    def initialize(self):
        self.search_params = {
            'fl': 'hospital_department_name,hospital_name,hospital_uuid,department_uuid',
            'rows': self.default_rows
        }
        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'SEARCH_PLATFORM_SOLR')
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(global_conf.cfg_path)
        self.primaryKey = config.items('SEARCH_PLATFORM_SOLR')[6][1]

    def set_intention_conf(self, intention_conf):
        self.intention_conf = intention_conf
        self.doctor_process.set_intention_conf(intention_conf)

    def go_dept_classify_box(self):
        result = False
        intention = self.intention_conf.intention
        intention_details = self.intention_conf.intention_details
        if intention in ('departmentConfirm', 'departmentAmong', 'departmentSubset', 'department'):
            result = True
        if intention == 'keyword' and 'symptom' in intention_details:
            result = True
        return result

    def process(self, query, **kwargs):
        """
        1.科室分类:http://192.168.4.30:3000/dept_classify_interactive?level=4&q=头痛挂什么科&sex=2&age=9125
        2.医院科室搜索：http://192.168.1.46:2000/department_search?fl=hospital_department_name,hospital_name&rows=3
        &hospital_uuid=08991199-fee5-48cc-b827-95eb0fdbd980000,125336131920301000,125369370584301000,
        125336754304601000,a7fb2715-5e71-4d75-9f16-bcfc1c81f739000,127529327571445000,
        c102e248-751a-4d0b-941d-94a2c33a4e0b000,22fbe56c-13e2-4e34-9cee-24ab874b6b9c000,
        ED25EA3F3F5BA102E040A8C00F01221B000&standard_department_uuid=7f67994c-cff3-11e1-831f-5cf9dd2e7135
        3.医生搜索
        :param query:
        :param kwargs:
        :return:
        """
        result = {}
        self.set_rows()
        self.set_params(query)
        dept_classify_result = self.init_dept_classify2()
        if 'data' not in dept_classify_result or (not isinstance(dept_classify_result.get('data'), dict)):
            # 没有data字段 或者 data非dict,则抛异常
            raise Exception('dept_classify异常')
        # 科室分类表明未结束 & 意图在()中,才返回交互框
        if isinstance(dept_classify_result['data'], dict) and dept_classify_result['data'].get('isEnd') == 0 \
                and self.go_dept_classify_box():
            # 分类分类需要补充数据
            result[constant.QUERY_KEY_AI_DEPT] = dept_classify_result['data']
            result['is_end'] = 0
            result['code'] = dept_classify_result['code']
            self.set_dialogue_info(result)  # 设置previous_q
            return result

        # 获取hospital_relation
        hospital_relation = self.intention_conf.configuration.hospital_relation
        hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if temp.get('hospital_uuid')]

        not_mapping_hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if
                                    temp.get('hospital_uuid') and temp.get('is_map_department') == 0]
        mapping_hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if
                                temp.get('hospital_uuid') and temp.get('is_map_department') == 1]

        ai_dept = dept_classify_result['data']['depts']
        std_dept_ids = [temp['dept_id'] for temp in ai_dept if temp.get('dept_id')]
        std_dept_name_list = [temp['dept_name'] for temp in ai_dept if temp.get(
            'dept_name') and temp['dept_name'] != 'unknow']

        # 查医院科室(未开启映射)
        hospital_dept_info = self.dept_search(not_mapping_hospital_ids, std_dept_ids)
        # 开启映射的医院科室信息
        mapping_hospital_dept_info = self.dept_mapping_search(mapping_hospital_ids, std_dept_ids,
                                                              std_dept_name=std_dept_name_list)
        # mapping_hospital_dept_info = [{'department_uuid': '123', 'hospital_department_name': '任宇翔', 'mapping_url': 'http://guahao.com'}]
        if mapping_hospital_ids and (not hospital_dept_info) and (not mapping_hospital_dept_info):
            # 有映射医院id & 2种方式都没有数据，返回无数据的信息
            result['is_end'] = 1
            return result
        elif hospital_dept_info or mapping_hospital_dept_info:
            hospital_dept_info.extend(mapping_hospital_dept_info)
            result[constant.QUERY_KEY_DEPT_SEARCH] = hospital_dept_info
        else:
            # 查不到数据,返回标准科室id和名字
            for ai_dept_temp in ai_dept:
                hosp_dept_dict_temp = {}
                if ai_dept_temp.get('dept_id'):
                    hosp_dept_dict_temp['department_uuid'] = ai_dept_temp['dept_id']
                if ai_dept_temp.get('dept_name') and ai_dept_temp['dept_name'] != 'unknow':
                    hosp_dept_dict_temp['hospital_department_name'] = ai_dept_temp['dept_name']
                if hosp_dept_dict_temp:
                    result.setdefault(constant.QUERY_KEY_DEPT_SEARCH, []).append(hosp_dept_dict_temp)

        # 设置previous_q
        self.set_dialogue_info(result)
        if constant.CONFIG_HOSPITAL_SOURCE_ALL != self.intention_conf.configuration.hospital_source and (
                not hospital_ids):
            # 配置为非全平台 & 无医院相关信息,不进行医生查询
            result['is_end'] = 1
            result['code'] = 0
            return result
        # 查doctor
        need_doctor_card = False
        # 需要医生卡片,才去搜索
        for id_temp, config_temp in self.intention_conf.get('card_dict', default={}).items():
            if config_temp.get('type') == constant.CARD_FLAG_DICT.get(constant.GENERATOR_CARD_FLAG_DOCTOR, -1):
                need_doctor_card = True
        if need_doctor_card:
            if std_dept_name_list:
                kwargs['ceil_q'] = ' '.join(std_dept_name_list)
            doctor_result = self.doctor_process.process(query, **kwargs)
            if doctor_result.get(constant.QUERY_KEY_DOCTOR_SEARCH):
                result[constant.QUERY_KEY_DOCTOR_SEARCH] = doctor_result[constant.QUERY_KEY_DOCTOR_SEARCH]
        return result

    def dept_search(self, hospital_ids, std_dept_ids):
        # 科室查询
        """
        hospital_ids: []
        std_dept_ids: []
        http://192.168.1.46:2000/department_search?fl=hospital_department_name,hospital_name&rows=3
        &hospital_uuid=08991199-fee5-48cc-b827-95eb0fdbd980000%2C125336131920301000%2C125369370584301000
        &standard_department_uuid=7f67994c-cff3-11e1-831f-5cf9dd2e7135%2C7f67bf44-cff3-11e1-831f-5cf9dd2e7135
        :return:
        """
        if not std_dept_ids:
            # 标准科室必须要有
            return []
        self.search_params['rows'] = self.rows
        self.search_params['standard_department_uuid'] = ','.join(std_dept_ids)
        if constant.CONFIG_HOSPITAL_SOURCE_ALL != self.intention_conf.configuration.hospital_source:
            # 非全医院平台
            if not hospital_ids:
                return []
            self.search_params['hospital_uuid'] = ','.join(hospital_ids)
        result = {}
        url = common.get_outer_service_url()
        result = query(self.search_params, self.input_params, 'department', url)
        return result.get('department', [])

    def dept_mapping_search(self, hospital_ids, std_dept_ids, **kwargs):
        if not std_dept_ids:
            # 标准科室必须要有
            return []
        params = {
            'cat': 'ai_hosp_dept_mapping',
            'primaryKey': self.primaryKey,
            'start': 0,
            'rows': self.rows,
            'fl': 'hospital_department_name,department_url,hospital_name',
            'filter': ['status:1', 'organize_code:%s' % self.intention_conf.configuration.organization],
            'sort': {'sort_code': 'asc', 'score': 'desc', 'created_time': 'desc'},
            'query': '*:*'
        }
        if kwargs.get('std_dept_name'):
            params['query'] = '*:* OR hospital_department_name_cn:(%s)' % ' OR '.join(
                kwargs['std_dept_name'])
        params['filter'].append('std_department_id:(%s)' % ' OR '.join(std_dept_ids))
        if constant.CONFIG_HOSPITAL_SOURCE_ALL != self.intention_conf.configuration.hospital_source:
            # 非全医院平台
            if not hospital_ids:
                return []
            params['filter'].append('hospital_id:(%s)' % ' OR '.join(hospital_ids))
        data = []
        try:
            result = self.plat_sc.query(json.dumps(params), 'search/1.0', method='post', timeout=0.3)
            if result.get('code') != 200:
                logger.error('hosp_dept_mapping error, result:%s' % json.dumps(result))
            else:
                data = result.get('data', [])
                for temp in data:
                    mapping_url = temp.pop('department_url', None)
                    if mapping_url:
                        temp['mapping_url'] = mapping_url
        except:
            logger.error('hosp_dept_mapping error, params:%s' % json.dumps(params))
        return data

    def set_rows(self):
        self.rows = super(
            DepartmentProcessor, self).basic_set_rows(2, default_rows=self.default_rows)

    def init_dept_classify2(self):
        params = {'level': '4', 'q': self.input_params['input']['q']}
        if not self.input_params['input'].get('confirm_information'):
            params['interactive'] = 2
        for item in self.dept_classify_params_mapping.keys():
            value = self.input_params['input'].get(item)
            if value is not None:
                if item == 'symptomName' and value in ('都没有',):
                    value = '-1'
                params[self.dept_classify_params_mapping[item]] = value
        url = common.get_ai_service_url()
        response = ai_search_common.query(params, self.input_params, 'ai_dept', url)
        if 'data' not in response or (not isinstance(response.get('data'), dict)):
            #  没有data字段 或者 data非dict,则抛异常
            raise Exception('dept_classify_1异常')
        return response


    def init_dept_classify(self):
        # 初始返回待填槽
        result = {constant.CONTROL_FIELD_RESTART_INTENTION: False}
        params = {'level': '4'}
        # 默认没有槽位
        params['q'] = self.input_params['input']['q']
        for key_temp in ['sex', 'age', 'symptomName']:
            if self.input_params['input'].get(key_temp):
                validator_temp = InteractiveBoxConstant.validator['department'][key_temp]
                is_pass, pass_value = validator_temp().validate(self.input_params['input'][key_temp])
                if is_pass and pass_value:
                    params[self.dept_classify_params_mapping[key_temp]] = pass_value
        if params.get('symptom') in ('都没有', ):
            params['symptom'] = '-1'
        url = common.get_ai_service_url()
        response = ai_search_common.query(params, self.input_params, 'ai_dept', url)
        if 'data' not in response or (not isinstance(response.get('data'), dict)):
            #  没有data字段 或者 data非dict,则抛异常
            raise Exception('dept_classify_1异常')
        if isinstance(response['data'], dict) and response['data'].get('isEnd') == 0 and \
                self.go_dept_classify_box():
            # 需要交互框, 构建槽位,主要是校验槽位的正确性
            slot_dict = self.create_slots(response['data'])
            params_2 = {'level': '4'}
            params_2['q'] = self.input_params['input']['q']
            for key_temp in ['sex', 'age', 'symptomName']:
                if self.input_params['input'].get(key_temp):
                    validator_temp = InteractiveBoxConstant.validator['department'][key_temp]
                    is_pass, pass_value = validator_temp().validate(
                        self.input_params['input'][key_temp], slot_dict.get(key_temp))
                    if not is_pass:
                        """
                        如果不通过, 说明答非所问,  重置意图和数据,需要返回一个新的query_dict，
                        1.只保留dialogue, input, del_key, origin这4个key
                        2.dialogue重置为{'previous_q': ''}
                        3.input 用 origin_input的值,修改新的input里的q为 key_temp的值
                        4.原来的del_key加入key_temp
                        5.origin再次copy  input的值
                        返回
                        {
                            'restart_query': True
                            ''
                        }
                        """
                        result[constant.CONTROL_FIELD_RESTART_INTENTION] = True
                        new_query_dict = {}
                        # 2.dialogue重置为{'previous_q': ''}
                        new_query_dict['dialogue'] = {
                            constant.QUERY_FIELD_DIALOGUE_PREVIOUS_Q: self.input_params['input'][key_temp]}
                        # origin_input -> input,修改新的input里的q为 key_temp的值
                        new_query_dict[constant.QUERY_FIELD_INPUT] = copy.deepcopy(
                            self.input_params[constant.QUERY_FIELD_ORIGIN_INPUT])

                        last_dialog = new_query_dict[constant.QUERY_FIELD_INPUT][-1]
                        last_dialog['q'] = self.input_params[constant.QUERY_FIELD_INPUT].get(key_temp)
                        # 4.添加del_key
                        del_keys = self.input_params.get(constant.QUERY_FIELD_DEL_KEYS)
                        if del_keys:
                            new_query_dict[constant.QUERY_FIELD_DEL_KEYS] = copy.deepcopy(del_keys)
                        new_query_dict.setdefault(constant.QUERY_FIELD_DEL_KEYS, []).append(key_temp)
                        # 5.origin再次copy  input的值
                        new_query_dict[constant.QUERY_FIELD_ORIGIN_INPUT] = copy.deepcopy(
                            new_query_dict[constant.QUERY_FIELD_INPUT])
                        result[constant.CONTROL_FIELD_RESTART_QUERY] = new_query_dict
                        return result
                    if is_pass and pass_value:
                        params_2[self.dept_classify_params_mapping[key_temp]] = pass_value
            url_2 = common.get_ai_service_url()
            response_2 = ai_search_common.query(params_2, self.input_params, 'ai_dept', url_2)
            result['dept_classify_result'] = response_2
        else:
            # 不需要交互框
            result['dept_classify_result'] = response
            return result
        return result

    def create_slots(self, data):
        box_dict = {}
        is_sex = data.get('isSex')
        is_age = data.get('isAge')
        symptoms = data.get('symptoms')
        if is_sex:
            sex_box = {}
            sex_box['field'] = 'sex'
            sex_box['type'] = 'single'
            sex_box['content'] = [0, 1, 2]
            sex_box['conf_id'] = 9998
            box_dict['sex'] = sex_box
        if is_age:
            age_box = {}
            age_box['field'] = 'age'
            age_box['type'] = 'single'
            age_box['conf_id'] = 9997
            box_dict['age'] = age_box
        if symptoms:
            symptom_box = {}
            symptom_box['field'] = 'symptomName'
            symptom_box['content'] = symptoms
            symptom_box['type'] = 'multiple'
            symptom_box['conf_id'] = 9996
            box_dict['symptomName'] = symptom_box
        return box_dict
