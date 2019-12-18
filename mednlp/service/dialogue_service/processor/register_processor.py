#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class RegisterProcessor(BasicProcessor):
    """
    处理返回医院带文章字段意图
    """

    default_params = {'rows': '18',
                      'start': '0',
                      'do_spellcheck': '1',
                      'travel': '0',
                      'sort': 'general',
                      'opensource': '9',
                      'aggr_field': 'contract_register',
                      'secondsort': '0'}

    def get_search_result(self):
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        if self.input_params.get('input') and self.input_params['input'].get('doctor'):
            ai_params['doctor'] = self.input_params['input']['doctor']
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
	doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)

        self.response_data = doctor_json_list

    #     self.ai_result['area'] = area
    #     doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
    #     self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
    #                                                     response, self.ai_result)
    #     self.ai_result['doctor'] = doctor_obj_list
    #     self.ai_result['valid_object'] = ['doctor']
    #     self.ai_result['query_content'] = q_content
    #     self.ai_result['is_post'] = self.get_post_data()
    #     if len(doctor_obj_list) == 0:
    #         search_params, fl_list = ai_search_common.get_search_params(
    #             ai_params, self.input_params, 'doctor', [], self.default_params)
    #         response, area = ai_search_common.get_extend_response(search_params,
    #                                             self.input_params, 'doctor')
    #         doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
    #         if len(doctor_obj_list) == 0:
    #             self.ai_result['registered'] = 1
    #         else:
    #             self.ai_result['registered'] = 2
    #
    # def get_post_data(self):
    #     ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
    #     search_params, fl_list = ai_search_common.get_search_params(
    #                         ai_params, self.input_params, 'post')
    #     response = ai_search_common.query(search_params, self.input_params, 'post')
    #     is_post = ai_search_common.get_doctor_post(response)
    #     return is_post
    #
    # def change_ai_result(self):
    #     if self.ai_result.get('doctor'):
    #         if len(self.ai_result['doctor']) == 1:
    #             if 'needCondition' in self.ai_result:
    #                 self.ai_result.pop('needCondition')
    #             self.ai_result['isEnd'] = 1
    #         else:
    #             self.ai_result['isEnd'] = 0
    #     else:
    #         self.ai_result['isEnd'] = 1
    #
    #
    # def data_output(self, return_type=3):
    #     """
    #     返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
    #     """
    #     if return_type == 3:
    #         return self.ai_result
    #
