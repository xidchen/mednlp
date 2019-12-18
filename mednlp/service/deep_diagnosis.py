#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_suggest.py -- the service of diagnose suggest

Author: maogy <maogy@guahao.com>
Create on 2019-01-30 Wednesday.
"""

import codecs
import json
import configparser
import tornado.web
from tornado.options import define
import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.client.ai_service_client import AIServiceClient
import traceback

life_advice_list = {}
file_content = codecs.open(global_conf.diagnosis_life_advice_path, 'r', encoding='utf-8')
for line in file_content:
    values = line.strip().split('%_(=)_%')
    if len(values) != 2:
        continue
    advice_key = values[0]
    advice_value = json.loads(values[1])
    if '生活建议' == advice_key:
        life_advice_list = advice_value

config_parser = configparser.ConfigParser()
config_parser.optionxform = str
config_parser.read(global_conf.cfg_path)
config_organizecode = config_parser.get('DeepDiagnosis', 'organizecode')
config_rulegroupname = config_parser.get('DeepDiagnosis', 'rulegroupname')

str_dialogue='dialogue';str_suggest_input='suggest_input';str_skip_step='skip_step'
str_answer='answer';str_question_id='question_id';str_question_answer='question_answer'
str_question_answer_unit='question_answer_unit';str_session_id='session_id'
str_interactive_box='interactive_box';str_is_end='is_end'
str_text='text';str_code='code';str_answer_code='answer_code';str_options='options'
str_field='field';str_pre_desc='pre_desc';str_type='type';str_content='content'
str_default_content='default_content';str_desc='desc';str_default_desc='default_desc'
str_conflict='conflict';str_validator='validator';str_is_special_option='is_special_option'
str_id='id';str_single='single';str_diagnose_suggestion='diagnose_suggestion'

class DeepDiagnosis(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(DeepDiagnosis, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self):

        input_obj = json.loads(self.request.body)
        disease_name=input_obj.get('disease_name')
        print('deep 参数')
        print(json.dumps(input_obj,ensure_ascii=False))
        print()

        result={};
        resp_data = {}

        env = []
        if 'systolic_pressure' in input_obj:
            systolic_pressure = input_obj.get('systolic_pressure', '0')
            systolic_pressure = int(systolic_pressure)
            env.append({'questionCode': "SBP", "questionAnswer": [systolic_pressure], "questionAnswerUnit": "mmHg"})
        if 'diastolic_pressure' in input_obj:
            diastolic_pressure = input_obj.get('diastolic_pressure', '0')
            diastolic_pressure = int(diastolic_pressure)
            env.append({'questionCode': "DBP", "questionAnswer": [diastolic_pressure], "questionAnswerUnit": "mmHg"})

        req_dialogue = input_obj.get('dialogue',{})

        #判定dialogue中是否具有session_id参数，有：则直接请求规则系统，没有则需要触发规则系统
        req_session_id=''
        if str_session_id in req_dialogue:
            req_session_id=req_dialogue.get(str_session_id)

        rule_param={}
        skip_step=1
        suggest_input=input_obj.get('rule_info')
        history=req_dialogue.get('history',[])
        if suggest_input:
            skip_step=suggest_input.get(str_skip_step)
            if suggest_input.get(str_skip_step)==-1:
                if not history:
                    result['data']= {'message':'skip_step参数超出范围'}
                    return result
                if len(history)==1:
                    history = history[:-1]
            else:
                history.append(suggest_input.get(str_answer))
                answer=suggest_input.get(str_answer)
                if len(answer)>0 and answer[0].get('question_code')=='drugStoreId':
                    env.append({'questionCode': "drugStoreId", "questionAnswer": answer[0].get('question_answer'), "questionAnswerUnit": ""})

        req_dialogue['history']=history

        if req_session_id:
            #使用session_id请求规则系统
            user_answers=suggest_input.get(str_answer)
            #针对血压值和血糖值做特殊处理

            rule_param['sessionId']=req_session_id
            rule_param['userAnswers']=self.get_user_answers(user_answers)
            rule_param['skipStep']=skip_step
        else:
            #触发规则系统
            rule_param['organizeCode']=config_organizecode
            rule_param['ruleGroupName']=config_rulegroupname
            rule_param['skipStep'] = skip_step
            rule_param['trigger']=disease_name
            rule_param['initQuestionAnswer'] = env

        resp_diagnose_suggestion={}
        current={}

        interactive_box={}
        try:
            self.ask_rule_engine(rule_param,req_dialogue,history,resp_diagnose_suggestion,current,interactive_box)
        except:
            traceback.format_exc()
            resp_data['is_end']=1
            resp_data['has_treatment_path']=0
            result['data']=resp_data
            return result

        if skip_step == -1:
            history=history[:-1]
        req_dialogue['history'] = history
        # 特殊处理  血压值 血糖值需要排序
        if resp_diagnose_suggestion and resp_diagnose_suggestion.get(
                str_interactive_box) and resp_diagnose_suggestion.get(str_interactive_box).get(str_options):
            options = resp_diagnose_suggestion.get(str_interactive_box).get(str_options)
            if len(options) == 2 and options[0].get(str_field) in ['SBP', 'DBP', 'fasting_plasma_glucose',
                                                                   'fasting_plasma_glucose_2hour']:
                # 排序  保证收缩压(SBP)在第0个  舒张压在第1个
                # 排序  保证空腹血糖在第0个  餐后2h血糖在第1个
                if options[0].get(str_field) == 'DBP' or options[0].get(str_field) == 'fasting_plasma_glucose_2hour':
                    ite = options[0]
                    options[0] = options[1]
                    options[1] = ite
            resp_diagnose_suggestion[str_interactive_box][str_options]=options
        resp_data=resp_diagnose_suggestion

        resp_data['dialogue'] = req_dialogue
        resp_data['life_advice']=life_advice_list.get(disease_name, '')
        if resp_data['is_end']==1:
            value=resp_diagnose_suggestion['action']['value']
            print(value[0])
            print('{' in value)
            if value[0]=='{':
                result_value=json.loads(value)
                if 'completeText' in result_value:
                    resp_data['treatment_advice'] = result_value['completeText']
                    if 'resultData' in result_value:
                        resp_data['prescription']= result_value['resultData']['prescription']
            else:
                resp_data['treatment_advice'] = resp_diagnose_suggestion['action']['value']
                resp_data['prescription']=[]
        else :
            resp_data['treatment_advice']=''
        resp_data['title']='确诊：' + disease_name
        resp_data['has_treatment_path'] = 1

        result['data']=resp_data
        print('suggest 返回数据')
        print(result)

        return result

    def get_history_answer(self,history,answer_key):
        for item in history:
            for ite in item:
                if ite.get('question_code')==answer_key:
                    return ite

    def ask_rule_engine(self,rule_param,req_dialogue,history,resp_diagnose_suggestion,current,interactive_box):
        print('ask rule param : {}')
        print(json.dumps(rule_param, ensure_ascii=False))
        aisc = AIServiceClient(global_conf.cfg_path, 'AIService')
        rule_result = aisc.query(json.dumps(rule_param, ensure_ascii=False), 'rule_engine')
        print('rule result :  {}')
        print(json.dumps(rule_result, ensure_ascii=False))

        if rule_result.get('code') in ['0',0]:
            rule_result=rule_result.get('data')
        if rule_result:
            resp_diagnose_suggestion['is_end'] = rule_result['isEnd']
            if rule_result['isEnd'] == 0:
                req_dialogue[str_session_id] = rule_result['sessionId']
                resp_diagnose_suggestion[str_answer] = rule_result[str_answer][0]
                rule_inter_box = rule_result['interactiveBox'][0]
                interactive_box = self.get_interactivebox_from_java(rule_inter_box, current,interactive_box,rule_param['skipStep'])
                resp_diagnose_suggestion[str_interactive_box] = interactive_box
                req_dialogue['current'] = current

                if interactive_box.get(str_options):
                    current_field = interactive_box.get(str_options)[0].get(str_field)
                    if current_field == 'SBP' or current_field == 'DBP' or current_field == 'fasting_plasma_glucose' or current_field == 'fasting_plasma_glucose_2hour':
                        # 判定是否已经回答 没有回答则追加关联问题  有回答则构造问答数据请求规则系统
                        relation_answer = self.get_relation_answer(history, current_field)
                        if relation_answer:
                            # 已回答
                            user_answers=rule_param['userAnswers']
                            user_answers[0]['questionId']=interactive_box.get(str_options)[0].get(str_question_id)
                            user_answers[0]['questionAnswer']=relation_answer
                            rule_param['userAnswers']=user_answers
                            if len(interactive_box.get(str_options))<2:
                                self.ask_rule_engine(rule_param,req_dialogue,history,resp_diagnose_suggestion,current,interactive_box)
                            if rule_param['skipStep'] > 0 and len(interactive_box.get(str_options))>=2:
                                del interactive_box.get(str_options)[0]
                        else:
                            # 未回答
                            interactive_box = self.add_box_option(interactive_box, current_field)
                            resp_diagnose_suggestion[str_interactive_box] = interactive_box
            else:
                req_dialogue['message'] = rule_result['message']
                resp_diagnose_suggestion['action']=rule_result['action']

    def get_user_answers(self,user_answer):
        res=[]
        if isinstance(user_answer,list):
            for item in user_answer:
                resp_ans={
                    'questionId':item.get('question_id'),
                    'questionAnswer':item.get('question_answer'),
                    'questionAnswerUnit':item.get('question_answer_unit')
                }
                res.append(resp_ans)
        return res

    def get_main_symptom_question(self,init_code,skip_step,history):
        resp_answer = {str_text: '请询问患者就诊的主要症状/原因：',
                       str_code: init_code, str_id: int(init_code)}

        resp_interactive_box = {
            str_answer_code: init_code,
            str_options: [
            ]
        }
        main_symptom_options_content = ['血压升高', '血糖升高','头晕','发热','腹痛','头痛','咳嗽','腹泻','失眠','消化不良']
        for item in main_symptom_options_content:
            default_content='0'
            if skip_step==-1 and history:
                main_symptom_answer=history[0][0].get(str_question_answer)
                if item==main_symptom_answer[0]:
                    default_content='1'

            item_value = {str_question_id: int(init_code), str_field: 'main_symptom',
                          str_pre_desc: '', str_type: str_single,
                          str_content: item, str_default_content: default_content,
                          str_desc: [], str_default_desc: 0, str_conflict: [],
                          str_is_special_option: 0, str_validator: 1}
            resp_interactive_box[str_options].append(item_value)
        suggest = {str_answer: resp_answer, str_interactive_box: resp_interactive_box,'is_end':0}
        return suggest

    def get_interactivebox_from_java(self,rule_inter_box,current,interactive_box,skip_step):
        inter_options = []
        if str_options in interactive_box:
            inter_options=interactive_box[str_options]
        for item in rule_inter_box['options']:
            op = {
                str_conflict: item.get(str_conflict),
                str_content: item.get(str_content),
                str_default_content: item.get('defaultContent'),
                str_default_desc: item.get('defaultDesc'),
                str_desc: item.get(str_desc),
                str_field: item.get(str_field),
                str_is_special_option: item.get('isSpecialOption', ),
                str_pre_desc: item.get('preDesc'),
                str_question_id: item.get('questionId'),
                str_type: item.get(str_type),
                str_validator: item.get(str_validator)
            }
            inter_options.append(op)
            current[op.get(str_question_id)] = op.get(str_field)

        if skip_step<0:
            for item in inter_options:
                if item.get(str_field)=='SBP':
                    item[str_pre_desc]='收缩压'
                if item.get(str_field)=='DBP':
                    item[str_pre_desc]='舒张压'
                if item.get(str_field)=='fasting_plasma_glucose':
                    item[str_pre_desc]='空腹血糖'
                if item.get(str_field)=='fasting_plasma_glucose_2hour':
                    item[str_pre_desc]='餐后2h血糖'

        interactive_box[str_answer_code] = rule_inter_box.get('answerCode')
        interactive_box[str_options] = inter_options
        return interactive_box

    def add_box_option(self,interactive_box,current_field):
        if current_field=='SBP':
            add_field='DBP'
            add_pre_desc='舒张压'
            current_pre_desc='收缩压'
        if current_field=='DBP':
            add_field='SBP'
            add_pre_desc='收缩压'
            current_pre_desc='舒张压'
        if current_field=='fasting_plasma_glucose':
            add_field='fasting_plasma_glucose_2hour'
            add_pre_desc='餐后2h血糖'
            current_pre_desc='空腹血糖'
        if current_field=='fasting_plasma_glucose_2hour':
            add_field='fasting_plasma_glucose'
            add_pre_desc='空腹血糖'
            current_pre_desc='餐后2h血糖'

        op = {
            str_conflict: [],
            str_content: '',
            str_default_content: '',
            str_default_desc:0 ,
            str_desc: interactive_box.get(str_options)[0].get(str_desc),
            str_field: add_field,
            str_is_special_option: 0,
            str_pre_desc: add_pre_desc,
            str_question_id: 0,
            str_type: 'unitText',
            str_validator: interactive_box.get(str_options)[0].get(str_validator)
        }
        if interactive_box.get(str_options) :
            interactive_box.get(str_options)[0][str_pre_desc]=current_pre_desc
        interactive_box.get(str_options).append(op)
        return interactive_box

    def get_relation_answer(self,history,current_field):
        for item in history:
            for ite in item:
                if ite.get('question_code')==current_field:
                    return ite.get('question_answer')
        return ''

if __name__ == '__main__':
    define('lstm_port', default=None, help='run on the given port', type=int)
    define('cnn_port', default=None, help='run on the given port', type=int)
    tornado.options.parse_command_line()
    handlers = [(r'/deep_diagnosis', DeepDiagnosis)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
