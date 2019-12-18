#!/usr/bin/python
#encoding=utf-8

from mednlp.dialog.processer.basic_processor import BasicProcessor
#from ai_service_client import AIServiceClient
import json
import re

class AutoDialogueProcessor(BasicProcessor):
    """
    处理自诊意图
    """
    auto_dia_init_field = ['age', 'sex', 'symptomName']
    service = 'auto_diagnose'
    symptom_dict = {'time_happen': 'timeHappen',
                    'body_part': 'bodyPart',
                    'alleviate': 'alleviate',
                    'cause': 'cause',
                    'frequence': 'frequence',
                    'degree': 'degree',
                    'exacerbation': 'exacerbation',
                    'symptom': 'symptomName',
                    'other_symptom': 'otherSymptom',
                    'treatment': 'treatment',
                    'past_medical_history': 'pastMedicalHistory'}

    def get_search_result(self):
        inputs = self.input_params.get('input',{})
        source = self.input_params.get('source', '')
        post_json = {
            "input":[],
            "source":source
        }
        if inputs and self.input_params.get('dialogue'):
            post_json = self.process_params(self.input_params)
        else:
            params_list = self.init_params(inputs)
            post_json['input'].extend(params_list)
        if inputs.get('terminate_diagnose'):
            post_json['terminate'] = 1
        post_body = json.dumps(post_json)
        response = self.ai_server.query((post_body), self.service, method='post')
        print (post_body)
        res = {}
        res['code'] = response['code']
        if response.get('data'):
            res['auto_diagnose'] = response['data']
            if response.get('data').get('diagnose'):
                res['diagnose'] = response.get('data').get('diagnose')
                if res['diagnose']:
                    for diagnose_item in res['diagnose']:
                        if diagnose_item.get('disease_name') == '急性上呼吸道感染' and diagnose_item.get('disease_id'):
                            diagnose_item.pop('disease_id')
            if response.get('data').get('answer'):
                res['answer'] = response.get('data').get('answer')
        res['dialogue'] = {}
        res['dialogue']['input'] = post_json
        res['dialogue']['answer'] = response['data']
        res['search_parmas'] = {'post_body': post_body}
        if response.get('data') and response['data'].get('card_type') == 'medical_record':
            res['is_end'] = 1
        else:
            res['is_end'] = 0
        return res

    def process_params(self, input_params={}):
        inputs = input_params.get('input')
        last_input = input_params.get('dialogue').get('input')
        last_answer = input_params.get('dialogue').get('answer')
        card_type = last_answer.get('card_type')
        params = {}
        if last_input:
            if card_type == 'age' and inputs.get('age'):
                age = inputs.get('age')
                post_age = '%s天' % str(age)
                params["key"] = 'age'
                params["value"] = [post_age]
            if card_type == 'sex' and inputs.get('sex'):
                sex = inputs.get('sex')
                post_sex = ''
                if sex == 2:
                    post_sex = '男'
                elif sex == 1:
                    post_sex = '女'
                params["key"] = 'sex'
                params["value"] = [post_sex]
            if card_type in self.symptom_dict and inputs.get(self.symptom_dict.get(card_type)):
                params["key"] = card_type
                params["value"] = [inputs.get(self.symptom_dict.get(card_type))]
            card_re = re.match( r'symptom\|(\w+)\|(\w+)', card_type, re.M|re.I)
            session_id = ''
            symptom_name = card_type
            if card_re:
                session_id = card_re.group(1)
                symptom_name = card_re.group(2)
            if session_id and symptom_name in self.symptom_dict and inputs.get(self.symptom_dict.get(symptom_name)):
                params["key"] = card_type
                params["value"] = [inputs.get(self.symptom_dict.get(symptom_name))]
        if params:
            last_input['input'].append(params)
        return last_input



    def init_params(self, inputs={}):
        params_list = []
        if inputs.get('age'):
            age = inputs.get('age')
            post_age = '%s天' % str(age)
            params = {}
            params["key"] = 'age'
            params["value"] = [post_age]
            params_list.append(params)
        if inputs.get('sex'):
            sex = inputs.get('sex')
            post_sex = ''
            if sex == 2:
                post_sex = '男'
            elif sex == 1:
                post_sex = '女'
            params = {}
            params["key"] = 'sex'
            params["value"] = [post_sex]
            params_list.append(params)
        if inputs.get('symptomName'):
            params = {}
            params["key"] = 'symptom'
            params["value"] = [inputs.get('symptomName')]
            params_list.append(params)
        return params_list


if __name__ == '__main__':
        a = AutoDialogueProcessor()
        input = """
                {
                    "source":12,
                    "input": [
                        {
                            "sex":1,
                            "age":10000,
                            "symptomName": "头晕",
                            "timeHappen": "15天"
                        }
                    ],
                    "dialogue": {
                        "input": {
                            "input": [
                                {
                                    "value": [
                                        "男"
                                    ], 
                                    "key": "sex"
                                }, 
                                {
                                    "value": [
                                        "15天"
                                    ], 
                                    "key": "age"
                                }, 
                                {
                                    "value": [
                                        "头晕"
                                    ], 
                                    "key": "symptom"
                                }   
                            ], 
                            "source": "bb"                           
                        },
                        "answer": {
                                "answer": "请问{头晕}出现多长时间了?",
                                "card_type": "symptom|08f10d04e659b499ee2fa3335ab24876|time_happen",
                                "card_content": [
                                    {
                                        "attribute": {
                                            "default": "1"
                                        },
                                        "value": [
                                            "小时",
                                            "天",
                                            "月",
                                            "年"
                                        ]
                                    }
                                ]
                        }
                    }
                }
                """
        result = a.process(input,None)
        print(result)






