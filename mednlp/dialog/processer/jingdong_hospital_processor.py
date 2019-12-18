#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor


class JingdongHospitalProcessor(BasicProcessor):
    """
    处理默认医院的意图
    """

    def get_search_result(self):
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_hospital_search_params(
            ai_params, self.input_params)
        response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
        hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
        hospital_json_list = ai_search_common.hospital_to_json(hospital_obj_list)
        #self.response_data = hospital_json_list
        answer = ai_search_common.process_jingong_hospital(hospital_json_list)
        res = {}
        res['code'] = response['code']
        res['answer'] = answer
        res['search_params'] = ai_params
        res['is_end'] = 1
        return res

        # self.ai_result['area'] = area
        # self.ai_result['hospital'] = hospital_obj_list
        # self.ai_result['valid_object'] = ['hospital']
        # self.ai_result['query_content'] = q_content


