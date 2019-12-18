#!/usr/bin/python
#encoding=utf-8

from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service.basic_intention import BasicIntention

class DefaultHospitalIntention(BasicIntention):
    """
    处理默认医院的意图
    """

    def get_search_result(self):
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_hospital_search_params(
            ai_params, self.input_params)
        response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
        self.ai_result['area'] = area
        hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
        hospital_json_list = ai_search_common.get_hospital_json_obj(response, self.ai_result, fl_list)
        self.ai_result['json_hospital'] = hospital_json_list
        self.ai_result['hospital'] = hospital_obj_list
        self.ai_result['valid_object'] = ['hospital']
        self.ai_result['query_content'] = q_content
        self.ai_result['search_params'] = ai_params


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

