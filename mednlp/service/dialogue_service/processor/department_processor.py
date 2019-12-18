#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class DepartmentProcessor(BasicProcessor):
    """
    默认处理返回医生的意图
    """


    def get_search_result(self):


	params = {}
	if self.input_params.get('input').get('q'):
	    params['q'] = self.input_params.get('input').get('q')    
	for item in ('sex','age','symptomName'):
            if self.input_params.get('input') and self.input_params['input'].get(item):
		if item == 'symptomName':
		    params['symptom'] = self.input_params['input'].get(item)
             	params[item] = self.input_params['input'].get(item)
        ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)
	if not ai_dept_response['data'].get('isEnd'):
	    self.response_data = []
	    self.response_data.append(ai_dept_response['data'])
	    return

        depts = ai_dept_response['data']['depts']
        dept_name_list = []
        for dept in depts:
            if dept.get('dept_name') and dept['dept_name'] != 'unknow':
            	dept_name_list.append(dept['dept_name'])
	
	input_param_set = ['departmentName']
	self.ai_result['departmentName'] = dept_name_list
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, input_param_set)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
       	doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
	doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)
	
        self.response_data = doctor_json_list
        # self.ai_result['area'] = area
        # doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        # self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
        #                                                 response, self.ai_result)
        # self.ai_result['doctor'] = doctor_obj_list
        # self.ai_result['valid_object'] = ['doctor']
        # self.ai_result['query_content'] = q_content


