#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor

class ResultDepartmentProcessor(BasicProcessor):
    """
    默认处理返回医生的意图
    """

    def get_search_result(self):

        params_set = ['departmentName']

        params = {}
        if self.input_params.get('input').get('q'):
            params['q'] = self.input_params.get('input').get('q')
        for item in ('sex','age','symptomName'):
            if self.input_params.get('input') and self.input_params['input'].get(item):
                params[item] = self.input_params['input'].get(item)
        ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)
        depts = []
        if ai_dept_response.get('data') and ai_dept_response.get('data').get('depts'):
            depts = ai_dept_response['data']['depts']
        dept_name_list = []
        for dept in depts:
            if dept.get('dept_name') and dept['dept_name'] != 'unknow':
                dept_name_list.append(dept['dept_name'])

        self.ai_result['departmentName'] = dept_name_list
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, in_params_set=params_set)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)

        answer_pre = '小微的建议仅供参考，具体的用药及建议谨遵医嘱, 小微推荐就诊%s，推荐以下医生'
        answer = ai_search_common.process_jingong_doctor(doctor_json_list)
        if dept_name_list and '很抱歉' not in answer:
            answer_pre = answer_pre % dept_name_list[0]
            answer = answer_pre + answer
        res = {}
        res['code'] = response['code']
        res['answer'] = answer
        res['search_params'] = ai_params
        res['is_end'] = 1
        return res


