#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor

class JingdongKeywordHospitalProcessor(BasicProcessor):
    """
    处理返回关键字医院的意图
    """

    def get_search_result(self):
        default_params = {'rows': '3',
                          'start': '0',
                          'do_spellcheck': '1',
                          'dynamic_filter':'1',
                          'opensource':'9',
                          'wait_time':'all',
                          'haoyuan': '-1'}
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_hospital_search_params(
                            ai_params, self.input_params, [], default_params)

        response = ai_search_common.query(search_params, self.input_params, 'hospital')
        hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)

        hospital_json_list = ai_search_common.hospital_to_json(hospital_obj_list)
        answer = ai_search_common.process_jingong_hospital(hospital_json_list)

        res = {}
        if response.get('code'):
            res['code'] = response['code']
        res['answer'] = answer
        res['search_parmas'] = ai_params
        res['is_end'] = 1
        return res
        # response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
        # self.ai_result['area'] = area
        # hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
        # self.ai_result['hospital'] = hospital_obj_list
        # self.ai_result['valid_object'] = ['hospital']
        # self.ai_result['query_content'] = q_content


    # def get_default_result(self):
    #     default_params = {'rows': '18',
    #                       'start': '0',
    #                       'do_spellcheck': '1',
    #                       'travel': '0',
    #                       'sort': 'general',
    #                       'opensource': '9',
    #                       'aggr_field': 'contract_register',
    #                       'secondsort': '0'}
    #
    #     ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
    #     search_params, fl_list = ai_search_common.get_search_params(
    #                         ai_params, self.input_params, 'doctor', [], default_params)
    #     response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'doctor')
    #
    #     self.ai_result['area'] = area
    #     doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
    #     self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(response, self.ai_result)
    #     self.ai_result['doctor'] = doctor_obj_list
    #     self.ai_result['valid_object'] = ['doctor']
    #     self.ai_result['query_content'] = q_content
    #     self.ai_result['intentionDetails'] = ['doctor']
    #
    # def data_output(self, return_type=3):
    #     """
    #     返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
    #     """
    #     if return_type == 3:
    #         return self.ai_result
