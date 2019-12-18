# !/usr/bin/env python
# encoding=utf-8

import json
import copy
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, logger, search_sc
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.dialogue_util import get_area_params, deal_q, request_hospital, get_hospital_json_obj,\
    request_doctor, get_doctor_json_obj, get_consult_doctor


class xwyzKeywordHospitalProcessor(BasicProcessor):

    def process_2(self, environment):
        """
        1.xwyz获取医院列表
        2.xwyz_doctor获取医生列表
        :param environment:
        :return:
        """
        result = {'is_end': 1}
        area_params = get_area_params(environment, 'id')
        q_content = deal_q(environment, q_type=2, return_q=True)
        area_params['q'] = q_content
        if environment.mode == 'xwyz':
            hospital_result = request_hospital(area_params)
            transform_dict_data(result, hospital_result, {'search_params': 'search_params', 'area': 'area'})
            result[constant.RESULT_FIELD_QUERY_CONTENT] = q_content
            res = hospital_result['res']
            if (not res) or res.get('code') != 0 or len(res.get('hospital', [])) == 0:
                result['card'] = [{'type': constant.CARD_FLAG_DICT['hospital'], 'content': []}]
                return result
            docs = res['hospital']
            department_name = environment.get_entity(source=['entity_dict'], key=['department'], attr='name')
            ai_result = {'departmentName': department_name}
            content = get_hospital_json_obj(docs, ai_result, constant.hospital_return_list)
            result['card'] = [{'type': constant.CARD_FLAG_DICT['hospital'], 'content': content}]
            return result
        else:
            # 找医生
            doctor_result = request_doctor(area_params)
            transform_dict_data(result, doctor_result, {'search_params': 'search_params', 'area': 'area'})
            result[constant.RESULT_FIELD_QUERY_CONTENT] = q_content
            res = doctor_result['res']
            if (not res) or res.get('code') != 0 or len(res.get('docs', [])) == 0:
                result['card'] = [{'type': constant.CARD_FLAG_DICT['doctor'], 'content': []}]
                return result
            content = res['docs']
            ai_result = {}
            for (_v1, _v2) in (('department_classify', 'departmentName'), ('hospital', 'hospitalName')):
                ai_entity_temp = environment.get_entity('entity_dict', _v1, 'name')
                if ai_entity_temp:
                    ai_result[_v2] = ai_entity_temp
            content = get_doctor_json_obj(content, ai_result, search_sc, constant.doctor_return_list,
                                          haoyuan_range=environment.input_dict.get('contract_price_range'))
            result['is_consult'] = get_consult_doctor(res)
            result['card'] = [{'type': constant.CARD_FLAG_DICT['doctor'], 'content': content}]
            return result
