#!/usr/bin/python
#encoding=utf-8
from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service.basic_intention import BasicIntention
import json
import pdb
from mednlp.service.ai_medical_service.ai_constant import logger


class AutoDiagnoseIntention(BasicIntention):
    """
    处理自诊的意图
    """

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            result['dialogue'] = data.get('dialogue', {})
            result['search_params'] = data.get('search_params', {})
            result['intention'] = data.get('intention')
            result['intentionDetails'] = data.get('intention_details')
            result['isHelp'] = data.get('is_help', 0)
            result['isEnd'] = data.get('is_end', 1)
            if 'service_list' in data:
                result['service_list'] = data['service_list']
            if 'auto_diagnose_merge' in data:
                result['auto_diagnose_merge'] = data['auto_diagnose_merge']
            if 'query_content' in data:
                result['query_content'] = data['query_content']
            ai_search_common.get_fields_from_extends(result, data)
            interactive_box = data.get('interactive_box', [])
            if self.input_params.get('input').get('auto_diagnosis'):
                card = data.get('card', {})
                answer = data.get('answer', {})
                if interactive_box:
                    result['interactive_box'] = interactive_box
                if answer:
                    result['answer'] = answer.get('text')
                if card and str(card.get('type')) == 'diagnose':
                    result['diagnosis'] = card['content']
                    result['valid_object'] = ['diagnosis']
                if 'progress' in data:
                    result['progress'] = data.get('progress')
                return result
            answer = data.get('answer', [])
            answer_dict = {temp['code']: temp['text'] for temp in answer if 'code' in temp and 'text' in temp}
            if interactive_box:
                # 有交互框返回交互框
                for temp in interactive_box:
                    if temp.get('field') in ('age', 'sex', 'symptomName'):
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
            # 返回卡片文案之类的.
            result['valid_object'] = ['doctor']
            result['json_doctor'] = []
            for temp in answer:
                if temp.get('id') == '%s_no_id' % data.get('intention'):
                    keywords = temp.get('keyword', [])
                    for keyword_temp in keywords:
                        if keyword_temp.get('id') == 'departmentName':
                            result['departmentName'] = [keyword_temp.get('text')]
                        if keyword_temp.get('id') == 'accuracy':
                            result['accuracy'] = keyword_temp.get('text')
                        if keyword_temp.get('id') == 'query_content':
                            result['query_content'] = keyword_temp.get('text')
                        if keyword_temp.get('id') == 'area':
                            result['area'] = keyword_temp.get('text')
            card = data.get('card', [])
            for card_temp in card:
                if str(card_temp.get('type')) == '1' and 'content' in card_temp:
                    result['json_doctor'] = ai_search_common.transform_card_content2dict(card_temp['content'])
        return result

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return

        logger.info("未走dialogue_service, 参数:%s" % json.dumps(self.input_params['input']))
        self.debug = False
        if self.input_params.get('auto_diagnosis') or self.input_params.get('input').get('auto_diagnosis'):
            self.input_params['mode'] = 'ai_qa'
            input_list = []
            input_list.append(self.input_params['input'])
            self.input_params['input'] = input_list
            post_json = (json.dumps(self.input_params, ensure_ascii=False))
            params = {}
            params['data'] = post_json
            result = self.aiserver.query(params, self.debug, method='post', service='dialogue_service')
            if result.get('data'):
                if result.get('data').get('interactive_box'):
                    self.ai_result['interactive_box'] = result.get('data').get('interactive_box')
                if result.get('data').get('answer') and result.get('data').get('answer').get('text'):
                    self.ai_result['answer'] = result.get('data').get('answer').get('text')
                if result.get('data').get('card') and result.get('data').get('card').get('type') == 'diagnose':
                    self.ai_result['diagnosis'] = result.get('data').get('card').get('content')
                    self.ai_result['valid_object'] = ['diagnosis']
                if result.get('data').get('dialogue'):
                    self.ai_result['dialogue'] = result.get('data').get('dialogue')
                if 'isEnd' in result.get('data'):
                    self.ai_result['isEnd'] = result.get('data').get('isEnd')
            return
        q_content = self.input_params['input'].get('q')
        params = {'q': q_content}
        for item in ('sex','age','symptomName'):
            if self.input_params.get('input') and self.input_params['input'].get(item):
                params[item] = self.input_params['input'].get(item)
        ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)
        depts = []
        if ai_dept_response.get('data') and ai_dept_response.get('data').get('depts'):
            depts = ai_dept_response['data']['depts']
        dept_name_list = []
        for dept in depts[0:1]:
            if dept.get('dept_name') and dept['dept_name'] != 'unknow':
                dept_name_list.append(dept['dept_name'])
                if dept.get('accuracy'):
                    self.ai_result['accuracy'] = dept.get('accuracy')
        if dept_name_list:
            self.ai_result['departmentName'] = dept_name_list
            params_set = ['departmentName']
            ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, params_set)
            search_params, fl_list = ai_search_common.get_search_params(
                ai_params, self.input_params, 'doctor')
            response, area = ai_search_common.get_extend_response(search_params,
                                                                    self.input_params, 'doctor')
            doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
            doctor_json_list = ai_search_common.get_doctor_json_obj(response, self.ai_result)
            self.ai_result['json_doctor'] = doctor_json_list
            self.ai_result['area'] = area
            self.ai_result['query_content'] = q_content
            self.ai_result['doctor'] = doctor_obj_list
            self.ai_result['valid_object'] = ['doctor']
            self.ai_result['isEnd'] = 1
            if ai_params:
                self.ai_result['search_params'] = ai_params
            #search_params, fl_list = ai_search_common.get_hospital_search_params(
            #    ai_params, self.input_params)
            #response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
            #hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
            #self.ai_result['hospital'] = hospital_obj_list



