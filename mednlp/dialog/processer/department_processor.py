#!/usr/bin/env python
# encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor
from mednlp.dialog.configuration import Constant as constant


class DepartmentProcessor(BasicProcessor):
    """
    默认处理返回医生的意图
    """

    def get_search_result(self):
        """
        科室分类
        1.需要补充科室分类数据,格式：
        {
            is_end:0
            code:int
            ai_dept:{}
            doctor_search:{}
        }
        :return:
        """
        result = {}
        dept_classify_result = ai_search_common.get_dept_classify(self.input_params)
        if 'data' not in dept_classify_result:
            raise Exception('dept_classify异常')
        if not dept_classify_result['data'].get('isEnd'):
            # 分类分类需要补充数据
            result[constant.QUERY_KEY_AI_DEPT] = dept_classify_result['data']
            result['is_end'] = 0
            result['code'] = dept_classify_result['code']
            return result
        # set result[constant.QUERY_KEY_AI_DEPT]
        result[constant.QUERY_KEY_AI_DEPT] = dept_classify_result['data']
        # 获取hospital_relation
        hospital_relation = self.intention_conf.configuration.hospital_relation
        # 无医院相关信息,不进行科室查询和医生查询
        if not hospital_relation:
            return result
        ai_dept = dept_classify_result['data']['depts']
        dept_name_list = [temp['dept_name'] for temp in ai_dept if temp.get(
            'dept_name') and temp['dept_name'] != 'unknow']
        # 查医院科室
        hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if temp.get('hospital_uuid')]
        std_dept_ids = [temp['dept_id'] for temp in ai_dept if temp.get('dept_id')]
        hospital_dept_info = ai_search_common.dept_search(hospital_ids, std_dept_ids)
        if hospital_dept_info:
            result[constant.QUERY_KEY_DEPT_SEARCH] = hospital_dept_info
        # 科室分类结果锁定,进行搜索
        input_param_set = ['departmentName']
        self.ai_result['departmentName'] = dept_name_list
        # 查doctor
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, input_param_set)
        search_params, fl_list = ai_search_common.get_search_params(ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'doctor')
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)
        # 有数据返回
        result['code'] = response['code']
        result[constant.QUERY_KEY_DOCTOR_SEARCH] = doctor_json_list
        result['search_params'] = ai_params
        result['is_end'] = 1
        return result


    def get_search_result_2(self):
        # 根据 q, sex, age, symptom获取科室分类 # http://192.168.4.30:3000/dept_classify_interactive?q=头痛是挂内科吗&sex=2&age=9125
        """
        1.科室分类return：{'ai_dept'; {}, 'code': 0, 'is_end': 0}

        :return:
        """
        params = {}
        if self.input_params.get('input').get('q'):
            params['q'] = self.input_params.get('input').get('q')
        for item in ('sex', 'age', 'symptomName'):
            if self.input_params.get('input') and self.input_params['input'].get(item):
                if item == 'symptomName':
                    params['symptom'] = self.input_params['input'].get(item)
                params[item] = self.input_params['input'].get(item)
        ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)  # 科室分类结果
        # print('说明一下+++++++++++', ai_dept_response)
        if not ai_dept_response['data'].get('isEnd'):   # 交互没有结束
            self.response_data = []
            self.response_data.append(ai_dept_response['data'])
            res = {}    # {'ai_dept'; {}, 'code': 0, 'is_end': 0}
            res['code'] = ai_dept_response['code']
            res['ai_dept'] = ai_dept_response['data']
            res['is_end'] = 0
            return res

        depts = ai_dept_response['data']['depts']
        dept_name_list = []
        for dept in depts:
            if dept.get('dept_name') and dept['dept_name'] != 'unknow':
                dept_name_list.append(dept['dept_name'])
        # 科室分类结果锁定,进行搜索
        input_param_set = ['departmentName']
        self.ai_result['departmentName'] = dept_name_list
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, input_param_set)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'doctor')
        response, area = ai_search_common.get_extend_response(search_params,
                                                self.input_params, 'doctor')
        doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        doctor_json_list = ai_search_common.doctor_to_json(doctor_obj_list)

        res = {}
        res['code'] = response['code']
        res['doctor_search'] = doctor_json_list
        res['search_params'] = ai_params
        res['is_end'] = 1
        return res
        ##self.response_data = doctor_json_list
        # self.ai_result['area'] = area
        # doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
        # self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
        #                                                 response, self.ai_result)
        # self.ai_result['doctor'] = doctor_obj_list
        # self.ai_result['valid_object'] = ['doctor']
        # self.ai_result['query_content'] = q_content


