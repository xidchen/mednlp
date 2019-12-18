#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class DefaultDoctorPostProcessor(BasicProcessor):
    """
    处理返回医院带文章字段意图
    """


    def process(self):
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
        # self.ai_result['area'] = area
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
	doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)
        self.response_data = doctor_json_list

        # self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
        #                                                 response, self.ai_result)
        # self.ai_result['doctor'] = doctor_obj_list
        # self.ai_result['valid_object'] = ['doctor']
        # self.ai_result['query_content'] = q_content
        # self.ai_result['is_post'] = self.get_post_data()

    # def get_post_data(self):
    #     ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
    #     search_params, fl_list = ai_search_common.get_search_params(
    #                         ai_params, self.input_params, 'post')
    #     response = ai_search_common.query(search_params, self.input_params, 'post')
    #     is_post = ai_search_common.get_doctor_post(response)
    #     return is_post
    #
    # def data_output(self, return_type=3):
    #     """
    #     返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
    #     """
    #     if return_type == 3:
    #         return self.ai_result

