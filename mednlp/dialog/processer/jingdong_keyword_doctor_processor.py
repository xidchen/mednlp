#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor

class JingdongKeywordDoctorProcessor(BasicProcessor):
    """
    处理返回关键字医生的意图
    """


    def get_search_result(self):

        default_params = {'rows': '18',
                          'start': '0',
                          'do_spellcheck': '1',
                          'travel': '0',
                          'sort': 'general',
                          'opensource': '9',
                          'aggr_field': 'contract_register',
                          'secondsort': '0'}
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor', [], default_params)
        response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'doctor')
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)
        answer = ai_search_common.process_jingong_doctor(doctor_json_list)
        res = {}
        res['code'] = response['code']
        res['answer'] = answer
        res['search_params'] = ai_params
        res['is_end'] = 1
        return res


