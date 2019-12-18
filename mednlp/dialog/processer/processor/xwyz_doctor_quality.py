# !/usr/bin/env python
# encoding=utf-8

import json
import copy
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, logger, search_sc
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.dialogue_util import get_area_params, deal_q, request_doctor, get_doctor_json_obj,\
    get_consult_doctor, deal_xwyz_doctor_quality_answer


class xwyzDoctorQualityProcessor(BasicProcessor):

    def process_2(self, environment):
        result = {'is_end': 1}
        q_content = deal_q(environment, q_type=2, return_q=True)
        area_params = get_area_params(environment, 'id')
        area_params['q'] = q_content
        doctor_result = request_doctor(area_params)
        transform_dict_data(result, doctor_result, {'search_params': 'search_params', 'area': 'area'})
        result[constant.RESULT_FIELD_QUERY_CONTENT] = q_content
        res = doctor_result['res']
        if (not res) or res.get('code') != 0 or len(res.get('docs', [])) == 0:
            result['card'] = [{'type': constant.CARD_FLAG_DICT['doctor'], 'content': []}]
            # result['answer'] = [{'text': '找不到'}]
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
        answer = deal_xwyz_doctor_quality_answer(environment, result)
        result['answer'] = answer
        return result
