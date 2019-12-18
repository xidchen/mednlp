#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class HospitalDepartmentProcessor(BasicProcessor):
    """
    处理医院科室意图
    """

    #hospital_params_dict = {
    #    'hospitalId': 'hospital_uuid',
    #    'cityId': 'city_id',
    #    'provinceId': 'province_id',
    #    'diseaseName': 'hospital_diseases',
    #}


    def get_search_result(self):
        ai_search_params = ai_search_common.ai_to_search_params(
                                self.ai_result, 'doctor')
        q_content = ai_search_common.get_keyword_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
            ai_search_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                    self.input_params, 'doctor')
	doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)

        self.response_data = doctor_json_list

        # doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)


        #ai_solr_params = ai_common.ai_to_solr(self.ai_result, 'doctor')
        #solr_params = ai_common.get_solr_params(ai_solr_params, 'doctor')
        #response, area = ai_common.get_extend_solr_response(solr_params, False, 'doctor', self.solr)
        #doctor_obj_list = ai_common.get_doctor_obj(response, self.ai_result)
        #is_consult = ai_common.get_consult_doctor(response, self.ai_result)
        # if (self.ai_result.get('hospitalId')
        #     and len(self.ai_result.get('hospitalId')) == 1
        #     and len(doctor_obj_list) > 0):
        #     self.ai_result['valid_object'] = ['doctor']
        #     self.ai_result['query_content'] = q_content
        #     self.ai_result['area'] = area
        #     self.ai_result['doctor'] = doctor_obj_list
        #     self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
        #                                             response, self.ai_result)
        #
        # ai_search_params = ai_search_common.ai_to_search_params(
        #                          self.ai_result, 'hospital')
        # q_content = ai_search_common.get_keyword_q_params(self.ai_result)
        # search_params, fl_list = ai_search_common.get_hospital_search_params(
        #     ai_search_params, self.input_params)
        # response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
        # hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
        # if not ('valid_object' in self.ai_result
        #         and 'doctor' in self.ai_result['valid_object']):
        #     self.ai_result['area'] = area
        #     self.ai_result['hospital'] = hospital_obj_list
        #     self.ai_result['valid_object'] = ['hospital']
        #     self.ai_result['query_content'] = q_content


        #ai_solr_params = ai_common.ai_to_solr(self.ai_result, 'hospital', self.hospital_params_dict)
        #solr_params, fl_list = ai_common.get_hospital_solr_params(ai_solr_params, self.input_params)
        #response, area = ai_common.get_extend_solr_response(solr_params, False, 'hospital', self.solr)
        #hospital_obj_list = ai_common.get_hospital_obj(response, self.ai_result, fl_list)
        #q_content = ai_search_common.get_keyword_q_params(self.ai_result)
        #self.ai_result['hospital'] = hospital_obj_list
        #if not ('valid_object' in self.ai_result
        #    and 'doctor' in self.ai_result['valid_object']):
        #    self.ai_result['valid_object'] = ['hospital']
        #    self.ai_result['area'] = area
        #    self.ai_result['query_content'] = q_content
        #    self.ai_result['hospital'] = hospital_obj_list


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

