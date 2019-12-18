#!/usr/bin/python
#encoding=utf-8

from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service import basic_intention
from mednlp.service.ai_medical_service.auto_diagnose_intention import AutoDiagnoseIntention
from mednlp.service.ai_medical_service.department_intention import DepartmentIntention
from mednlp.service.ai_medical_service.ai_constant import logger
import json


class DepartmentClassifyIntention(basic_intention.BasicIntention):
    """
    默认处理返回科室的意图
    """

    department_classify_dict = {'age': 'age',
                                'sex': 'sex',
                                'symptomName': 'symptom'}

    def get_dialogue_service_result(self):
        result = {'data': {}}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            ai_search_common.department_classify_build_dialogue_service(data, result['data'])
        return result

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return

        logger.info("未走dialogue_service, 参数:%s" % json.dumps(self.input_params['input']))
        if self.input_params['input'].get('auto_diagnosis'):
            intention_object = AutoDiagnoseIntention()
            intention_object.set_params(self.ai_result, self.input_params, self.solr)
            self.ai_result = intention_object.get_intention_result()
        elif self.input_params['input'].get('doctor_result'):
            intention_object = DepartmentIntention()
            intention_object.set_params(self.ai_result, self.input_params, self.solr)
            self.ai_result = intention_object.get_intention_result()
        else:
            q_content = self.input_params.get('input').get('q')
            params = {'q': q_content}
            for item in self.department_classify_dict.keys():
                params['level'] = 4
                if self.input_params.get('input') and self.input_params['input'].get(item):
                    params[self.department_classify_dict[item]] = self.input_params['input'].get(item)
            ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)
            depts = ai_dept_response['data']['depts']
            dept_json_list = []
            for dept in depts[0:2]:
                dept_json = {}
                if dept.get('dept_name') and dept['dept_name'] != 'unknow':
                    if 'departmentName' in self.ai_result and dept.get('dept_name') not in self.ai_result['departmentName']:
                         self.ai_result['departmentName'].append(dept.get('dept_name'))
                    elif 'departmentName' not in self.ai_result:
                         self.ai_result['departmentName'] = []
                         self.ai_result['departmentName'].append(dept.get('dept_name'))
                    dept_json['accuracy'] = dept.get('accuracy')
                    dept_json['department_name'] = dept.get('dept_name')
                    dept_id = dept.get('dept_id')
                    department_search_params = {'std_dept': dept_id,
                                        'rows': 1,
                                        'fl': 'common_disease, introduction, std_dept_id'}
                    std_dept_response = ai_search_common.get_std_dept(department_search_params, self.input_params)
                    if std_dept_response.get('docs'):
                        std_dept_item = std_dept_response.get('docs')[0]
                        dept_json['common_disease'] = std_dept_item.get('common_disease', [])
                        dept_json['introduction'] = std_dept_item.get('introduction', '')
                        dept_json['department_uuid'] = std_dept_item.get('std_dept_id', '')
                if dept_json:
                    dept_json_list.append(dept_json)
            self.ai_result['department'] = dept_json_list
            self.ai_result['valid_object'] = ['department']


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

