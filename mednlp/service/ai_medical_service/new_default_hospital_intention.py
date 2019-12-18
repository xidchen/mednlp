#!/usr/bin/python
#encoding=utf-8

import mednlp.service.ai_medical_service.ai_search_common as ai_search_common
from mednlp.service.ai_medical_service.basic_intention import BasicIntention

class NewDefaultHospitalIntention(BasicIntention):
    """
    处理默认医院的意图
    """

    department_classify_dict = {'age': 'age',
                                'sex': 'sex',
                                'symptomName': 'symptom'}
    def get_search_result(self):


        #医院的返回列表
        hospital_fl_list = ['hospital_uuid', 'hospital_name', 'hospital_level',
                        'hospital_photo_absolute', 'order_count',
                        'hospital_hot_department', 'distance_desc',
                        'hospital_rule', 'hospital_standard_department',
                        'hospital_department', 'hospital_praise_rate']
        #文章的返回列表
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        params = {'q': q_content}
        if self.input_params.get('input', {}).get('q'):
            params['q'] = self.input_params['input']['q']
        # 若有科室名, 则不进行分科;若没有科室名,则进行分科
        if not self.ai_result.get('departmentName'):
            if not self.input_params.get('input', {}).get('confirm_information'):
                # 质疑模式, interactive=2表示 科室分类认为传过去的age，sex都是错的，需要重新输入
                params['interactive'] = 2

            for item in self.department_classify_dict.keys():
                if self.input_params.get('input') and self.input_params['input'].get(item):
                    params[self.department_classify_dict[item]] = self.input_params['input'].get(item)
            if params.get('symptom') in ('都没有', ):
                params['symptom'] = '-1'
            ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)

            # deal 交互框
            if ai_dept_response and ai_dept_response.get('code') == 0 and ai_dept_response.get(
                    'data', {}).get('isEnd') == 0:
                dept_data = ai_dept_response['data']
                if dept_data.get('isSex') or dept_data.get('isAge'):
                    self.ai_result['isEnd'] = 0
                    self.ai_result['needSexAge'] = 1
                    return
                if dept_data.get('symptoms'):
                    self.ai_result['isEnd'] = 0
                    symptom_box = {}
                    content = dept_data['symptoms']
                    content.insert(0, '都没有')
                    content_length = len(content)
                    symptom_box['field'] = 'symptomName'
                    symptom_box['conflict'] = [[0, index_temp] for index_temp in range(1, content_length)]
                    symptom_box['content'] = content
                    symptom_box['type'] = 'multiple'
                    symptom_box['conf_id'] = 9996
                    self.ai_result['answer'] = '请问您还有以下症状吗？请挑选出来哦~'
                    self.ai_result['interactive_box'] = [symptom_box]
                    return

            depts = ai_dept_response.get('data', {}).get('depts', [])
            dept_name_list = []
            dept_ids = []
            for dept in depts:
                if dept.get('dept_name') and dept['dept_name'] != 'unknow':
                    dept_name_list.append(dept['dept_name'])
                    if dept.get('dept_id'):
                        dept_ids.append(dept['dept_id'])
            if dept_name_list:
                self.ai_result['departmentName'] = dept_name_list
                self.ai_result['departmentId'] = dept_ids

        if self.ai_result.get('departmentName'):
            params_set = ['departmentName']
            ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, params_set)

            #获取权威医院信息
            department_search_params = {'standard_name': self.ai_result['departmentName'][0],
                                        'department_country_rank_range': '0|100',
                                        'rows': 1,
                                        'sort': 'fudan_country'}
            if self.ai_result.get('cityId'):
                department_search_params['city_id'] = ','.join(self.ai_result.get('cityId'))
            if self.ai_result.get('provinceId'):
                department_search_params['province_id'] = ','.join(self.ai_result.get('provinceId'))
            department_response = ai_search_common.get_department(department_search_params)

            top_hospital_id = ''
            if department_response.get('department'):
                top_hospital_id = department_response.get('department')[0].get('hospital_uuid')

            #默认的医院信息
            search_params, fl_list = ai_search_common.get_hospital_search_params(
                ai_params, self.input_params)
            response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
            self.ai_result['area'] = area
            hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
            hospital_json_list = ai_search_common.get_hospital_json_obj(response, self.ai_result, hospital_fl_list)

            hospital_uuid_list = self.get_hospital_uuid(hospital_json_list)

            if top_hospital_id:
                top_hospital_index = 0
                if top_hospital_id in hospital_uuid_list:
                    top_hospital_index = hospital_uuid_list.index(top_hospital_id)
                    top_hospital_json = hospital_json_list.pop(top_hospital_index)
                    hospital_json_list.insert(0,top_hospital_json)
                else:
                    top_search_params = {'rows': '1',
                           'start': '0',
                           'do_spellcheck': '1',
                           'dynamic_filter':'1',
                           'opensource':'9',
                           'wait_time':'all',
                           'haoyuan': '-1',
                            'hospital': top_hospital_id
                            }
                    top_response, top_area = ai_search_common.get_extend_response(top_search_params, self.input_params, 'hospital')
                    top_hospital_json_list = ai_search_common.get_hospital_json_obj(top_response, self.ai_result, fl_list)
                    top_hospital_json_list.extend(hospital_json_list)
                    hospital_json_list = top_hospital_json_list
                hospital_json_list[0]['authority'] = 1
            if hospital_json_list:
                self.set_department_rank(hospital_json_list, self.ai_result['departmentName'][0])

            self.ai_result['json_hospital'] = hospital_json_list
            self.ai_result['hospital'] = hospital_obj_list
            self.ai_result['valid_object'] = ['hospital']
            self.ai_result['query_content'] = q_content
            self.ai_result['search_params'] = ai_params
        else:
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


    def get_hospital_uuid(self,hospital_json_list=None):
        if not hospital_json_list:
           return []
        hospital_uuid = []
        if hospital_json_list:
            for hospital in hospital_json_list:
                hospital_uuid.append(hospital.get('hospital_uuid'))
        return hospital_uuid

    def set_department_rank(self,hospital_json_list=None, department_name=''):
        if not hospital_json_list:
            hospital_json_list = []
        hospital_uuid = self.get_hospital_uuid(hospital_json_list)
        hospital_uuid_str = ','.join(hospital_uuid)
        dept_fl = ['standard_name', 'country_top_rank', 'province_top_rank',
                   'city_top_rank', 'hospital_uuid', 'city_name', 'province_name']
        department_search_params = {'standard_name': department_name,
                                        'sort': 'fudan_country',
                                    'hospital_uuid': hospital_uuid_str,
                                    'fl': 'standard_name, country_top_rank, province_top_rank, city_top_rank, hospital_uuid, city_name, province_name'}
        department_response, area = ai_search_common.get_extend_response(department_search_params,
                self.input_params, 'search_dept', 'city_id', 'province_id')
        if department_response.get('department'):
            for dept_obj in department_response.get('department'):
                if dept_obj.get('hospital_uuid') in hospital_uuid:
                    index = hospital_uuid.index(dept_obj.get('hospital_uuid'))
                    new_obj = {}
                    for item in dept_fl:
                        if item in dept_obj:
                            key = 'dept_' + item
                            new_obj[key] = dept_obj[item]
                    hospital_json_list[index].update(new_obj)


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

