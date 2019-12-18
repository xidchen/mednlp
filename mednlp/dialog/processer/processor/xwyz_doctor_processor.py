# !/usr/bin/env python
# encoding=utf-8

import json
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
import mednlp.dialog.processer.ai_search_common as ai_search_common
import mednlp.dialog.processer.ai_constant as ai_constant
from mednlp.dialog.dialogue_util import deal_q, get_area_params, request_doctor, get_doctor_json_obj,\
    get_consult_doctor, deal_xwyz_doctor_answer
from mednlp.dialog.dialogue_constant import Constant as constant, search_sc


class XwyzDoctorProcessor(BasicProcessor):
    fl_return = ['doctor_uuid', 'doctor_photo_absolute',
                 'doctor_name', 'doctor_technical_title',
                 'hospital_department_detail',
                 'specialty_disease', 'doctor_recent_haoyuan_detail',
                 'doctor_haoyuan_time', 'doctor_haoyuan_detail',
                 'is_service_package', 'is_health', 'sns_user_id',
                 'comment_score', 'total_order_count', 'is_patient_praise',
                 'base_rank', 'contract_register',
                 'is_consult_serviceable', 'doctor_introduction', 'feature',
                 'is_image_text', 'is_diagnosis', 'is_consult_phone',
                 'imagetext_fee', 'phone_consult_fee', 'diagnosis_fee',
                 'serve_type', 'accurate_package_price']

    def initialize(self):
        self.search_params = {
            'rows': '18',
            # 'rows': '2',
            'start': '0',
            'do_spellcheck': '1',
            'travel': '0',
            'sort': 'general',
            'secondsort': '0',
            'aggr_field': 'contract_register',
            'opensource': '9',
            'fl': ','.join(ai_constant.return_list_dict['doctor'])
        }

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
        answer = deal_xwyz_doctor_answer(environment, result)
        result['answer'] = answer
        return result

    def process(self, query, **kwargs):
        """
                result返回值:
                area
                is_consult
                query_content
                search_params
                is_end
        """
        result = {}
        ceil_process_info = query.pop(constant.PROCESS_FIELD_CEIL_PROCESS_INFO, {})
        _set_param = {}
        if ceil_process_info.get('ai_result'):
            _set_param['ai_result'] = ceil_process_info['ai_result']
        self.set_params(query, **_set_param)
        # 上层指定了参数集合, 获取相对应的数据
        params_set = None
        if ceil_process_info.get('params_set'):
            params_set = ceil_process_info['params_set']
        _params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, in_params_set=params_set)
        if not q_content:
            _params['q'] = self.input_params['input'].get('q')
        self.search_params.update(_params)
        response, area = ai_search_common.get_extend_response(self.search_params, self.input_params, 'doctor')
        result['area'] = area
        # doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.get_doctor_json_obj(response, self.ai_result)
        # result['json_doctor'] = doctor_json_list
        # 咨询信息
        result['is_consult'] = ai_search_common.get_consult_doctor(response, self.ai_result)

        result[constant.QUERY_KEY_DOCTOR_SEARCH] = doctor_json_list
        result[constant.RESULT_FIELD_QUERY_CONTENT] = self.search_params.get('q')
        result[constant.RESULT_FIELD_SEARCH_PARAMS] = _params
        result['is_end'] = 1
        ai_search_common.extends_progress_result(result, self.ai_result)
        return result
