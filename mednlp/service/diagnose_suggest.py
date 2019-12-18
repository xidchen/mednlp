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

diagnoses = []
diagnose_position = {}
diagnose_time = []
diagnose_reason = {}
diagnose_symptom = {}

file_content = codecs.open(global_conf.suggest_consult_prompt_path, 'r', encoding='utf-8')
for line in file_content:
    values = line.strip().split('=')
    if len(values) != 2:
        continue
    prompt_key = values[0]
    prompt_value = json.loads(values[1])
    if '症状原因' == prompt_key:
        diagnoses = prompt_value
    elif '症状部位' == prompt_key:
        diagnose_position = prompt_value
    elif '症状持续时间' == prompt_key:
        diagnose_time = prompt_value
    elif '发病诱因' == prompt_key:
        diagnose_reason = prompt_value
    elif '伴随症状' == prompt_key:
        diagnose_symptom = prompt_value

config_parser = configparser.ConfigParser()
config_parser.optionxform = str
config_parser.read(global_conf.cfg_path)
config_organizecode = config_parser.get('DeepDiagnosis', 'organizecode')
config_rulegroupname = '问诊提示规则组'

str_dialogue='dialogue';str_suggest_input='suggest_input';str_skip_step='skip_step'
str_answer='answer';str_question_id='question_id';str_question_answer='question_answer'
str_question_answer_unit='question_answer_unit';str_session_id='session_id'
str_interactive_box='interactive_box';str_is_end='is_end'
str_text='text';str_code='code';str_answer_code='answer_code';str_options='options'
str_field='field';str_pre_desc='pre_desc';str_type='type';str_content='content'
str_default_content='default_content';str_desc='desc';str_default_desc='default_desc'
str_conflict='conflict';str_validator='validator';str_is_special_option='is_special_option'
str_id='id';str_single='single';str_diagnose_suggestion='diagnose_suggestion'

class DiagnoseSuggest(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(DiagnoseSuggest, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self):

        input_obj = json.loads(self.request.body)
        print('suggest 参数')
        print(json.dumps(input_obj,ensure_ascii=False))
        print()

        result={};init_code='111'
        req_dialogue = {}
        history=[]
        resp_data={}
        if str_dialogue in input_obj:
            req_dialogue = input_obj.get(str_dialogue)
        #input_obj没有内容，问题初始化  返回主要症状问题
        init_history = []
        if not req_dialogue:
            # if input_obj.get('fasting_plasma_glucose') and input_obj.get('fasting_plasma_glucose_2hour'):
                # init_history.append([{'questionCode': 'fasting_plasma_glucose',
                                      # 'questionAnswer': [input_obj.get('fasting_plasma_glucose')],
                                      # 'questionAnswerUnit': 'mmol/L'},
                                     # {'questionCode': 'fasting_plasma_glucose_2hour',
                                      # 'questionAnswer': [input_obj.get('fasting_plasma_glucose_2hour')],
                                      # 'questionAnswerUnit': 'mmol/L'}])

            resp_data[str_diagnose_suggestion]=[self.get_main_symptom_question(init_code,1,[])]
            resp_data[str_dialogue]={'current':{int(init_code):'main_symptom'},'history': init_history}
        else:
            #判定dialogue中是否具有session_id参数，有：则直接请求规则系统，没有则需要触发规则系统
            req_session_id=''
            if str_session_id in req_dialogue:
                req_session_id=req_dialogue.get(str_session_id)

            rule_param={}
            suggest_input=input_obj.get(str_suggest_input)
            history=req_dialogue.get('history',[])
            if suggest_input.get(str_skip_step)==-1:
                if not history:
                    result['data']= {'message':'skip_step参数超出范围'}
                    return result
                if len(history)==1:
                    resp_data[str_diagnose_suggestion] = [self.get_main_symptom_question(init_code, -1,history)]
                    resp_data[str_dialogue] = {'current': {int(init_code): 'main_symptom'}, 'history': []}
                    history = history[:-1]
            else:
                history.append(suggest_input.get(str_answer))
            req_dialogue['history']=history

            if req_session_id:
                #使用session_id请求规则系统
                user_answers=suggest_input.get(str_answer)
                #针对血压值和血糖值做特殊处理

                rule_param['sessionId']=req_session_id
                rule_param['userAnswers']=self.get_user_answers(user_answers)
                rule_param['skipStep']=suggest_input.get(str_skip_step)
            else:
                #触发规则系统
                answer=suggest_input.get(str_answer)
                rule_param['organizeCode']=config_organizecode
                rule_param['ruleGroupName']=config_rulegroupname
                rule_param['skipStep'] = suggest_input.get(str_skip_step)
                if answer :
                    rule_param['trigger']=answer[0][str_question_answer][0]
                #初始化问题答案数据
                rule_param['initQuestionAnswer']=[]
                if input_obj.get('age'):
                    age=input_obj.get('age')
                    age_sui_val=float(age*1.0/365)
                    rule_param['initQuestionAnswer'].append({'questionCode':'age','questionAnswer':[str(age_sui_val)],'questionAnswerUnit':'岁'})
                sex_val='未知'
                if input_obj.get('sex'):
                    sex=input_obj.get('sex')
                    if sex==1:
                        sex_val='女'
                    elif sex==2:
                        sex_val='男'
                rule_param['initQuestionAnswer'].append({'questionCode': 'sex', 'questionAnswer': [sex_val], 'questionAnswerUnit': ''})
                if input_obj.get('height'):
                    rule_param['initQuestionAnswer'].append({'questionCode': 'height', 'questionAnswer': [input_obj.get('height')], 'questionAnswerUnit': 'cm'})
                if input_obj.get('body_weight'):
                    rule_param['initQuestionAnswer'].append({'questionCode': 'body_weight', 'questionAnswer': [input_obj.get('body_weight')],'questionAnswerUnit': 'cm'})
                if input_obj.get('fasting_plasma_glucose'):
                    rule_param['initQuestionAnswer'].append({'questionCode': 'fasting_plasma_glucose',
                                                             'questionAnswer': [input_obj.get('fasting_plasma_glucose')],
                                                             'questionAnswerUnit': 'mmol/L'})
                if input_obj.get('fasting_plasma_glucose_2hour'):
                    rule_param['initQuestionAnswer'].append({'questionCode': 'fasting_plasma_glucose_2hour',
                                                             'questionAnswer': [input_obj.get('fasting_plasma_glucose_2hour')],
                                                             'questionAnswerUnit': 'mmol/L'})
                if input_obj.get('systolic_blood_pressure'):
                    rule_param['initQuestionAnswer'].append({'questionCode': 'systolic_blood_pressure',
                                                             'questionAnswer': [input_obj.get('systolic_blood_pressure')],
                                                             'questionAnswerUnit': 'mmHg'})
                if input_obj.get('diastolic_blood_pressure'):
                    rule_param['initQuestionAnswer'].append({'questionCode': 'diastolic_blood_pressure',
                                                             'questionAnswer': [input_obj.get('diastolic_blood_pressure')],
                                                             'questionAnswerUnit': 'mmHg'})

            resp_diagnose_suggestion={}
            current={}

            interactive_box={}
            if suggest_input.get(str_skip_step) == 1 or len(history)>1:
                try:
                    self.ask_rule_engine(rule_param,req_dialogue,history,resp_diagnose_suggestion,current,interactive_box)
                except :
                    traceback.format_exc()
                    raise Exception('未匹配到规则或规则无法继续进行')

                if suggest_input.get(str_skip_step) == -1 and len(history) > 1:
                    history=history[:-1]
                req_dialogue['history'] = history
                resp_data[str_diagnose_suggestion]=[resp_diagnose_suggestion]
                resp_data['dialogue'] = req_dialogue

        # 特殊处理  无伴随症状需要添加冲突选项 血压值 血糖值需要排序
        resp_diagnose_suggestion=resp_data[str_diagnose_suggestion][0]
        if resp_diagnose_suggestion and resp_diagnose_suggestion.get(
                str_interactive_box) and resp_diagnose_suggestion.get(str_interactive_box).get(str_options):
            options = resp_diagnose_suggestion.get(str_interactive_box).get(str_options)
            if options[0].get(str_field) == 'symptom':

                accompany_index = 0
                for conflict_index, item in enumerate(options):
                    if item.get(str_content) == '无伴随症状':
                        accompany_index = conflict_index
                        break
                if accompany_index:
                    # 设置无伴随症状与其他选项冲突
                    options[accompany_index][str_conflict] = list(range(len(options)-1))
                    # 无伴随症状移到列表最后
                    _accompany = options[accompany_index]
                    del options[accompany_index]
                    options.append(_accompany)

                resp_diagnose_suggestion[str_interactive_box][str_options] = options

            if options[0].get(str_field) == 'reason':
                accompany_index = 0
                for conflict_index, item in enumerate(options):
                    if item.get(str_content) == '无明显诱因':
                        accompany_index = conflict_index
                        break
                if accompany_index:
                    # 设置无明显诱因与其他选项冲突
                    options[accompany_index][str_conflict] = list(range(len(options)-1))
                    # 无明显诱因移到列表最后
                    _accompany = options[accompany_index]
                    del options[accompany_index]
                    options.append(_accompany)
                resp_diagnose_suggestion[str_interactive_box][str_options] = options

            if len(options) == 2 and options[0].get(str_field) in ['SBP', 'DBP', 'fasting_plasma_glucose',
                                                                   'fasting_plasma_glucose_2hour']:
                # 排序  保证收缩压(SBP)在第0个  舒张压在第1个
                # 排序  保证空腹血糖在第0个  餐后2h血糖在第1个
                if options[0].get(str_field) == 'DBP' or options[0].get(
                        str_field) == 'fasting_plasma_glucose_2hour':
                    ite = options[0]
                    options[0] = options[1]
                    options[1] = ite
                resp_diagnose_suggestion[str_interactive_box][str_options] = options
        resp_data[str_diagnose_suggestion][0]=resp_diagnose_suggestion

        #回填规则
        resp_chief_complaint=''
        if len(history)>0:
            resp_medical_history='患者'
        else :
            resp_medical_history=''
        time_answer=self.get_history_answer(history,'time')
        if time_answer:
            resp_medical_history+=time_answer.get('question_answer')[0]+time_answer.get('question_answer_unit')+'前'
            resp_chief_complaint+=time_answer.get('question_answer')[0]+time_answer.get('question_answer_unit')

        other_reason = []
        reason_answer=self.get_history_answer(history,'reason')
        if reason_answer:
            _reason_answer = reason_answer.get('question_answer')[0]
            if str(_reason_answer).startswith('其他'):
                str_reason = str(_reason_answer[2:]).strip()
                for _reason in str_reason.split(' '):
                    if _reason not in other_reason:
                        other_reason.append(_reason)
            else:
                resp_medical_history += _reason_answer

        main_symptom_answer=self.get_history_answer(history,'main_symptom')
        if main_symptom_answer:
            resp_medical_history+='出现'+main_symptom_answer.get('question_answer')[0]
            resp_chief_complaint=main_symptom_answer.get('question_answer')[0]+resp_chief_complaint

        if other_reason:
            resp_medical_history +=  "，诱因是" + "、".join(other_reason)

        body_part_answer=self.get_history_answer(history,'body_part')
        if body_part_answer:
            _body_part_answer = body_part_answer.get('question_answer')[0]
            if str(_body_part_answer).startswith('其他'):
                str_body_part = _body_part_answer[2:]
                str_body_part = str(str_body_part).strip()
                if str_body_part:
                    resp_medical_history += '，部位是' + "、".join(set(str_body_part.split(' ')))
            else:
                resp_medical_history += '，部位是' + _body_part_answer

        symptom_answer=self.get_history_answer(history,'symptom')
        if symptom_answer:
            if symptom_answer.get('question_answer')[0]=='无伴随症状':
                resp_medical_history+='，无伴随症状'
            else :
                resp_medical_history += '，伴随'
                symptom_list=[]
                for sy in symptom_answer.get('question_answer'):
                    if str(sy).startswith('其他'):
                        str_other=sy[2:len(sy)]
                        str_other =str(str_other).strip()
                        if str_other:
                            symptom_list.extend(str_other.split(' '))
                    else :
                        symptom_list.append(sy)
                symptom_list=list(set(symptom_list))
                resp_medical_history+='、'.join(symptom_list)
            resp_medical_history+='。'

        body_temperature=''

        # physical_examination=''
        body_temperature_answer=self.get_history_answer(history,'body_temperature')
        if body_temperature_answer:
            body_temperature=body_temperature_answer.get('question_answer')[0]
            # physical_examination+='体温'+body_temperature_answer[0]+'℃'
        sbp=None
        if input_obj.get('systolic_blood_pressure'):
            sbp = input_obj.get('systolic_blood_pressure')
        else:
            sbp_answer=self.get_history_answer(history,'SBP')
            if sbp_answer:
                sbp=float(sbp_answer.get('question_answer')[0])
        dbp=None
        if input_obj.get('diastolic_blood_pressure'):
            dbp = input_obj.get('diastolic_blood_pressure')
        else:
            dbp_answer=self.get_history_answer(history,'DBP')
            if dbp_answer:
                dbp=float(dbp_answer.get('question_answer')[0])
        general_info=''
        fasting_plasma_glucose=None
        if input_obj.get('fasting_plasma_glucose'):
            general_info += '空腹血糖：' + str(input_obj.get('fasting_plasma_glucose')) + 'mmol/L'
            fasting_plasma_glucose = float(input_obj.get('fasting_plasma_glucose'))
        else:
            fasting_plasma_glucose_answer=self.get_history_answer(history,'fasting_plasma_glucose')
            if fasting_plasma_glucose_answer and fasting_plasma_glucose_answer.get('question_answer')[0]:
                general_info+='空腹血糖：'+fasting_plasma_glucose_answer.get('question_answer')[0]+'mmol/L'
                fasting_plasma_glucose=float(fasting_plasma_glucose_answer.get('question_answer')[0])
        if input_obj.get('fasting_plasma_glucose_2hour'):
            general_info += '，餐后2h血糖：' + str(input_obj.get('fasting_plasma_glucose_2hour')) + 'mmol/L'
            fasting_plasma_glucose_2hour = float(input_obj.get('fasting_plasma_glucose_2hour'))
        else:
            fasting_plasma_glucose_2hour_answer=self.get_history_answer(history,'fasting_plasma_glucose_2hour')
            fasting_plasma_glucose_2hour=None
            if fasting_plasma_glucose_2hour_answer and fasting_plasma_glucose_2hour_answer.get('question_answer')[0]:
                general_info+='，餐后2h血糖：'+fasting_plasma_glucose_2hour_answer.get('question_answer')[0]+'mmol/L'
                temp_plasma_glucose_2hour=fasting_plasma_glucose_2hour_answer.get('question_answer')[0]
                if temp_plasma_glucose_2hour:
                    fasting_plasma_glucose_2hour=float(temp_plasma_glucose_2hour)

        resp_data['chief_complaint']=resp_chief_complaint
        resp_data['medical_history'] = resp_medical_history
        resp_data['past_medical_history'] = input_obj.get('past_medical_history')
        resp_data['personal_history'] = input_obj.get('personal_history')
        resp_data['allergic_history'] = input_obj.get('allergic_history')
        resp_data['family_history'] = input_obj.get('family_history')
        resp_data['body_temperature'] = body_temperature
        resp_data['body_weight'] = input_obj.get('body_weight')
        resp_data['height'] = input_obj.get('height')
        resp_data['heart_rate'] = input_obj.get('heart_rate')
        resp_data['systolic_blood_pressure'] = sbp
        resp_data['diastolic_blood_pressure'] = dbp
        resp_data['physical_examination'] = input_obj.get('physical_examination')
        resp_data['general_info'] = general_info
        resp_data['department'] = input_obj.get('department')
        resp_data['fasting_plasma_glucose'] = fasting_plasma_glucose
        resp_data['fasting_plasma_glucose_2hour'] = fasting_plasma_glucose_2hour

        result['data']=resp_data
        print('suggest 返回数据')
        print(result)

        return result

    def get_history_answer(self,history,answer_key):
        for item in history:
            for ite in item:
                if ite.get('question_code')==answer_key:
                    return ite
        return None

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
                interactive_box = self.get_interactivebox_from_java(rule_inter_box, current,interactive_box)
                resp_diagnose_suggestion[str_interactive_box] = interactive_box
                req_dialogue['current'] = current

                if interactive_box.get(str_options):
                    current_field = interactive_box.get(str_options)[0].get(str_field)
                    # if current_field=='body_temperature':
                    #     interactive_box[str_options][0][str_pre_desc]='体温：'

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

    def get_user_answers(self,user_answer):
        res=[]
        if isinstance(user_answer,list):
            for item in user_answer:
                resp_ans={
                    'questionId':item.get('question_id'),
                    'questionCode':item.get('question_code'),
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

    def get_interactivebox_from_java(self,rule_inter_box,current,interactive_box):
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

        # if skip_step<0:
        for item in inter_options:
            if item.get(str_field)=='SBP':
                item[str_pre_desc]='收缩压：'
            if item.get(str_field)=='DBP':
                item[str_pre_desc]='舒张压：'
            if item.get(str_field)=='fasting_plasma_glucose':
                item[str_pre_desc]='空腹血糖：'
            if item.get(str_field)=='fasting_plasma_glucose_2hour':
                item[str_pre_desc]='餐后2h血糖：'
            if item.get(str_field)=='body_temperature':
                item[str_pre_desc]='体温：'
            if item.get(str_field)=='age':
                item[str_pre_desc]='年龄：'
            if item.get(str_field)=='sex':
                item[str_pre_desc]='性别：'
            if item.get(str_field)=='height':
                item[str_pre_desc]='身高：'
            if item.get(str_field)=='body_weight':
                item[str_pre_desc]='体重：'

        interactive_box[str_answer_code] = rule_inter_box.get('answerCode')
        interactive_box[str_options] = inter_options
        return interactive_box

    def add_box_option(self,interactive_box,current_field):
        if current_field=='SBP':
            add_field='DBP'
            add_pre_desc='舒张压：'
            current_pre_desc='收缩压：'
        if current_field=='DBP':
            add_field='SBP'
            add_pre_desc='收缩压：'
            current_pre_desc='舒张压：'
        if current_field=='fasting_plasma_glucose':
            add_field='fasting_plasma_glucose_2hour'
            add_pre_desc='餐后2h血糖：'
            current_pre_desc='空腹血糖：'
        if current_field=='fasting_plasma_glucose_2hour':
            add_field='fasting_plasma_glucose'
            add_pre_desc='空腹血糖：'
            current_pre_desc='餐后2h血糖：'

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
    handlers = [(r'/diagnose_suggest', DiagnoseSuggest)]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
