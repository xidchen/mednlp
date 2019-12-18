#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class HospitalNearByProcessor(BasicProcessor):
    """
    处理附近医院的意图
    """

    def get_search_result(self):
        #调用医院搜索接口中默认的参数
        hospital_search_params = {'rows': '3',
                       'start': '0',
                       'do_spellcheck': '1',
                       'dynamic_filter':'1',
                       'opensource': '9',
                       'wait_time': 'all',
                       'haoyuan': '2',
                       'sort': 'distance'}

        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = {}, []
        if ai_search_common.check_location(self.input_params):
            search_params, fl_list = ai_search_common.get_hospital_search_params(
                ai_params, self.input_params, [], hospital_search_params)
        else:
            search_params, fl_list = ai_search_common.get_hospital_search_params(
                ai_params, self.input_params)
        response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
	hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)

        hospital_json_list = ai_search_common.hospital_to_json(hospital_obj_list)
        self.response_data = hospital_json_list

        # self.ai_result['area'] = area
        # hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
        # self.ai_result['hospital'] = hospital_obj_list
        # self.ai_result['valid_object'] = ['hospital']
        # self.ai_result['query_content'] = q_content


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

