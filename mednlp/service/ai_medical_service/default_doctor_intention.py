#!/usr/bin/python
#encoding=utf-8

from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service.basic_intention import BasicIntention

class DefaultDoctorIntention(BasicIntention):
    """
    默认处理返回医生的意图
    """

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        # 1.分科交互框(age,sex,symptom)  2.科室分类结果 + 医生结果
        if dialogue_response and dialogue_response.get('data'):
            #
            data = dialogue_response['data']
            result['dialogue'] = data.get('dialogue', {})
            result['intention'] = data.get('intention')
            result['intentionDetails'] = data.get('intention_details')
            result['isHelp'] = data.get('is_help', 0)
            result['isEnd'] = data.get('is_end', 1)
            result['search_params'] = data.get('search_params', {})
            result['area'] = data.get('area', '')
            result['query_content'] = data.get('query_content', '')
            result['valid_object'] = ['doctor']
            result.update(self.entity_dict)
            for item in ('age','sex'):
                if result.get(item):
                    result.pop(item)
            card = data.get('card', [])
            for card_temp in card:
                if str(card_temp.get('type')) == '1' and card_temp.get('content'):
                    doctor_result = ai_search_common.transform_card_content2dict(card_temp['content'])
                    result['json_doctor'] = doctor_result
                    # result['doctor'] = doctor_result
            # self.ai_result = result
            out_link = data.get('out_link', [])
            for temp in out_link:
                if temp.get('id') == 'no_consult_id':
                    # 有去问诊按钮 is_consult=1
                    result['is_consult'] = 1
            return result

    def get_search_result(self):

        result = self.get_dialogue_service_result()
        if result and result.get('intention') and result.get('intention') == 'doctor':
            self.ai_result = result
            return

        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
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

