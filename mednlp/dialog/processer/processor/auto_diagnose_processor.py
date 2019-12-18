# !/usr/bin/env python
# encoding=utf-8

from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
import json
import re
from mednlp.dialog.configuration import Constant as constant
import copy


class AutoDiagnoseProcessor(BasicProcessor):
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

    def process(self, query, **kwargs):
        self.set_params(query, **kwargs)
        inputs = self.input_params.get('input', {})
        source = self.input_params.get('source', 'bb')
        dialogue = self.input_params.get('dialogue', {})
        symptom_error_count = dialogue.get('symptom_error_count', 0)
        post_json = self.process_params(self.input_params)
        self.check_age_sex_params(post_json['input'])
        if inputs.get('terminate_diagnose'):
            post_json['terminate'] = 1
        post_body = json.dumps(post_json)
        response = constant.ai_server.query((post_body), self.service, method='post')
        res = {'dialogue': {}}
        res['code'] = response['code']
        if response.get('data'):
            card_type = response['data'].get('card_type')
            res['auto_diagnose'] = response['data']
            extends = response.get('data').get('extends', {})
            flag = extends.get('flag', '')
            if 'symptom' == card_type:
                response.get('data')['answer'] = '''请输入您的症状，如“头痛”、“小腿痉挛”'''
                if str(flag) == '1':
                    # 需要提示
                    symptom_error_count += 1
                    res.setdefault('dialogue', {}).setdefault('symptom_error_count', symptom_error_count)
                    if symptom_error_count == 1:
                        response.get('data')['answer'] = '''小微当前是疾病自测状态哦，不能识别您的输入，请重新简单描述您的症状～'''
                    else:
                        auto_diagnose_data = copy.deepcopy(response['data'])
                        if auto_diagnose_data:
                            auto_diagnose_data.pop('card_type')
                            auto_diagnose_data['answer'] = '对不起，小微不能识别您的症状，已退出疾病自测技能～'
                            res['answer'] = auto_diagnose_data['answer']
                        query_content = None
                        for temp in post_json.get('input', []):
                            key_temp = temp.get('key')
                            if key_temp == 'symptom':
                                query_content = temp['value']
                        if query_content:
                            res['query_content'] = query_content[0]
                        res['auto_diagnose'] = auto_diagnose_data
                        res['is_end'] = 1
                        res['service_list'] = [1, 2]
                        res['auto_diagnose_merge'] = 1
                        res['progress'] = 1
                        res['card_return'] = 1
                        res['dialogue']['input'] = post_json
                        res['dialogue']['answer'] = response['data']
                        res['search_params'] = {'post_body': post_body}
                        return res
            if 'auto_diagnose_progress' in extends:
                res['progress'] = extends['auto_diagnose_progress']
            if response.get('data').get('diagnose'):
                res['diagnose'] = response.get('data').get('diagnose')
                if res['diagnose']:
                    for diagnose_item in res['diagnose']:
                        if diagnose_item.get('disease_name') == '急性上呼吸道感染' and diagnose_item.get('disease_id'):
                            diagnose_item.pop('disease_id')
            if response.get('data').get('answer'):
                res['answer'] = response.get('data').get('answer')
        res['dialogue']['input'] = post_json
        res['dialogue']['answer'] = response['data']
        res['search_params'] = {'post_body': post_body}
        if response.get('data') and response['data'].get('card_type') == 'medical_record':
            res['is_end'] = 1
            res['service_list'] = [1, 2]
        else:
            res['is_end'] = 0
        return res

    def check_age_sex_params(self, auto_diagnose_list):
        has_sex = False
        has_age = False
        has_symptom = False
        for temp in auto_diagnose_list:
            if temp.get('key') == 'sex':
                has_sex = True
            elif temp.get('key') == 'age':
                has_age = True
            elif temp.get('key') == 'symptom':
                has_symptom = True
            if has_sex and has_age and has_symptom:
                break
        inputs = self.input_params.get('input')
        if (not has_sex) and inputs.get('sex'):
            sex = str(inputs.get('sex'))
            sex_param = {}
            post_sex = ''
            if sex == '2':
                post_sex = '男'
            elif sex == '1':
                post_sex = '女'
            sex_param["key"] = 'sex'
            sex_param["value"] = [post_sex]
            auto_diagnose_list.append(sex_param)
        if (not has_age) and inputs.get('age'):
            age = inputs.get('age')
            age_param = {}
            post_age = '%s天' % str(age)
            age_param["key"] = 'age'
            age_param["value"] = [post_age]
            auto_diagnose_list.append(age_param)
        if (not has_symptom) and inputs.get('symptomName'):
            auto_diagnose_list.append({'key': 'symptom', 'value': [inputs['symptomName']]})
        return


    def process_params(self, input_params={}):
        inputs = input_params.get('input')
        # dialogue
        last_input = input_params.get('dialogue', {}).get('input')
        last_answer = input_params.get('dialogue', {}).get('answer', {})
        card_type = last_answer.get('card_type')
        progress = last_answer.get('extends', {}).get('auto_diagnose_progress')

        params = {}
        if last_input:
            if progress:
                last_input.setdefault('dialogue', {})['auto_diagnose_progress'] = progress
            if card_type == 'age' and inputs.get('age'):
                age = inputs.get('age')
                post_age = '%s天' % str(age)
                params["key"] = 'age'
                params["value"] = [post_age]
            if card_type == 'sex' and inputs.get('sex'):
                sex = str(inputs.get('sex'))
                post_sex = ''
                if sex == '2':
                    post_sex = '男'
                elif sex == '1':
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
        if not last_input:
            last_input = {
                'input': [],
                'source': 'aa'
            }
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
            sex = str(inputs.get('sex'))
            post_sex = ''
            if sex == '2':
                post_sex = '男'
            elif sex == '1':
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
        a = AutoDiagnoseProcessor()
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
        result = a.process(input, None)
        print(result)