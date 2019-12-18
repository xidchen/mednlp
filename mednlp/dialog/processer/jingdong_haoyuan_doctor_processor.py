#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor

class JingdongHaoyuanDoctorProcessor(BasicProcessor):
    """
    处理京东返回医生号源的意图
    """


    def get_search_result(self):

        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)

        answer = ai_search_common.process_jingong_haoyuan_doctor(doctor_json_list)
        res = {}
        res['code'] = response['code']
        res['answer'] = answer
        res['search_params'] = ai_params
        res['is_end'] = 1
        return res
        #self.response_data = doctor_json_list
        # self.ai_result['area'] = area
        # self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
        #                                                 response, self.ai_result)
        # self.ai_result['doctor'] = doctor_obj_list
        # self.ai_result['valid_object'] = ['doctor']
        # self.ai_result['query_content'] = q_content
