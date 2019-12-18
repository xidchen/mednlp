#!/usr/bin/python
#encoding=utf-8

from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service import basic_intention
import json
import copy
import pdb
from mednlp.service.ai_medical_service.ai_constant import logger

class DepartmentIntention(basic_intention.BasicIntention):
    """
    默认处理返回科室的意图
    """

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        # 1.分科交互框(age,sex,symptom)  2.科室分类结果 + 医生结果
        if dialogue_response and dialogue_response.get('data'):
            #
            data = dialogue_response['data']
            result['dialogue'] = data.get('dialogue', {})
            result['search_params'] = data.get('search_params', {})
            result['intention'] = data.get('intention')
            result['intentionDetails'] = data.get('intention_details')
            result['isHelp'] = data.get('is_help', 0)
            result['isEnd'] = data.get('is_end', 1)
            interactive_box = data.get('interactive_box', [])
            answer = data.get('answer', [])
            answer_dict = {temp['code']: temp['text'] for temp in answer if 'code' in temp and 'text' in temp}
            ai_search_common.get_fields_from_extends(result, data)
            if interactive_box:
                # 有交互框返回交互框
                for temp in interactive_box:
                    if temp.get('field') in ('age', 'sex', 'symptomName'):
                        answer_code = temp.get('answer_code')
                        result_answer = answer_dict.get(temp.get('answer_code'))
                        if result_answer:
                            result['answer'] = result_answer
                        if temp.get('field') in ('age', 'sex'):
                            result['needSexAge'] = 1
                        if temp.get('field') == 'symptomName':
                            if temp.get('content') and len(temp['content']) > 0:
                                temp['content'].insert(0, '都没有')
                                content_length = len(temp['content'])
                                temp['conflict'] = [[0, index_temp] for index_temp in range(1, content_length)]
                            result['interactive_box'] = [temp]
                        break
                return result
            result['valid_object'] = ['doctor']
            result['json_doctor'] = []
            # result['doctor'] = []
            # 返回卡片文案之类的.
            out_link = data.get('out_link', [])
            for temp in out_link:
                if temp.get('id') == 'no_consult_id':
                    # 有去问诊按钮 is_consult=1
                    result['is_consult'] = 1
            for temp in answer:
                if temp.get('id') == '%s_no_id' % data.get('intention'):
                    keywords = temp.get('keyword', [])
                    for keyword_temp in keywords:
                        # if keyword_temp.get('id') == 'departmentName':
                        #     result['departmentName'] = [keyword_temp.get('text')]
                        if keyword_temp.get('id') == 'accuracy':
                            result['accuracy'] = keyword_temp.get('text')
                        if keyword_temp.get('id') == 'query_content':
                            result['query_content'] = keyword_temp.get('text')
                        if keyword_temp.get('id') == 'confirm':
                            result['confirm'] = 1
                        if keyword_temp.get('id') == 'among':
                            result['among'] = 1
                        if keyword_temp.get('id') == 'area':
                            result['area'] = keyword_temp.get('text')
            card = data.get('card', [])
            for card_temp in card:
                if str(card_temp.get('type')) == '1' and card_temp.get('content'):
                    doctor_result = ai_search_common.transform_card_content2dict(card_temp['content'])
                    result['json_doctor'] = doctor_result
                    # result['doctor'] = doctor_result
            # self.ai_result = result
        return result

    def compare_keywords_data(self, origin, dest, field_tuples):
        for (origin_key, origin_value, dest_key) in field_tuples:
            if origin.get(origin_key) == dest_key:
                dest[dest_key] = origin.get(origin_value)

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return

        logger.info("未走dialogue_service, 参数:%s" % json.dumps(self.input_params['input']))
        # 先走交互框, 若isEnd=1则查doctor
        params_set = ['departmentName']
        dept_fl = ai_search_common.department_interact(self.input_params, self.ai_result)
        self.ai_result.update(dept_fl)
        if self.ai_result.get('isEnd') == 1:
            ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, params_set)
            search_params, fl_list = ai_search_common.get_search_params(
                                ai_params, self.input_params, 'doctor')
            response, area = ai_search_common.get_extend_response(search_params,
                                                    self.input_params, 'doctor')
            self.ai_result['area'] = area
            doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
            doctor_json_list = ai_search_common.get_doctor_json_obj(response, self.ai_result)
            self.ai_result['json_doctor'] = doctor_json_list
            self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
                                                            response, self.ai_result)
            self.ai_result['doctor'] = doctor_obj_list
            self.ai_result['valid_object'] = ['doctor']
            self.ai_result['query_content'] = q_content
            self.ai_result['search_params'] = ai_params


    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

