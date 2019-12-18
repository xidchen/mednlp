#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class JingdongDefaultDoctorProcessor(BasicProcessor):
    """
    默认处理返回医生的意图
    """


    def get_search_result(self):

        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
	doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)

        answer = ai_search_common.process_jingong_doctor(doctor_json_list)
	self.response_data = [{'_text_': answer}]
        #self.response_data = doctor_json_list
        # self.ai_result['area'] = area
        # self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
        #                                                 response, self.ai_result)
        # self.ai_result['doctor'] = doctor_obj_list
        # self.ai_result['valid_object'] = ['doctor']
        # self.ai_result['query_content'] = q_content


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

