#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
from mednlp.dialog.active_2 import Active
import json
from mednlp.dialog.general_util import get_service_data
from mednlp.dialog.dialogue_util import cgm, build_age_sex_symptom_result, set_placeholder, \
    reset_box_type, doctor_card_transform, parse_input, add_option_attribute, add_area_params, trans_entity_input,\
    trans_area, del_params
from mednlp.dialog.configuration import logger, ai_client, sc_client
from mednlp.dialog.builder.answer_builder import AnswerSkillRuleBuilder
from mednlp.dialog.builder.interactive_box_builder import InteractiveSkillRuleBuilder
from mednlp.dialog.builder.card_builder import CardSkillRuleBuilder
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.processer.skill.find_hospital_skill import FindHospitalSkill
from mednlp.dialog.processer.skill.question_answerSkill import QuestionAnswerSkill
from mednlp.dialog.processer.skill.auto_diagnose_skill import AutoDiagnoseSkill
from mednlp.dialog.configuration import Constant as constant, get_organization_dict


class SkillFactory(object):
    @classmethod
    def generate(cls, skill, environment):
        if skill == 'find_doctor':
            return FindDoctorSkill.generate(environment)
        elif skill == 'find_hospital':
            return FindHospitalSkill.generate(environment)
        elif skill == 'question_answer':
            return QuestionAnswerSkill.generate(environment)
        elif skill == 'auto_diagnose':
            return AutoDiagnoseSkill.generate(environment)


class FindDoctorSkill(object):
    default_process_code = 'default_v1'

    def pre_default_to_rule(self):
        result = {}
        result['continue'] = 1
        self.current_process_code = FindDoctorSkill.default_process_code
        self.rule_params = {
            'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['continue']}]
        }
        return result

    def pre_doctor_require(self):
        input_dict = self.environment.get('input_dict')
        find_doctor_service = input_dict.get('find_doctor_service', [''])
        if find_doctor_service[0] == '其他':
            return self.pre_search_doctor()
        return self.pre_default_to_rule()

    def pre_doctor_service(self):
        result = {}
        input_dict = self.environment.get('input_dict')
        find_doctor_service = input_dict.get('find_doctor_service', [''])
        result['continue'] = 1
        self.current_process_code = FindDoctorSkill.default_process_code
        if find_doctor_service[0] == '其他':
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['其他']}]
            }
        elif find_doctor_service[0] == '挂号':
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['挂号']}]
            }
        elif find_doctor_service[0] == '问诊':
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['问诊']}]
            }
        return result

    def pre_entity_extract(self):
        """
        1.医生没数据
        2.分科分不出来
        """
        result = {}
        entity = self.environment.get('entity_dict')
        if entity.get('doctor'):
            doctor_params = {
                'q': entity['doctor'][0].get('name'),
                'rows': 4,
            }
            add_area_params(doctor_params, entity)
            doctor_data = cgm.get_strategy(self.environment.get('organization'),
                                           'find_doctor_doctor', doctor_params, raise_exception=False)
            if doctor_data.get('card', []):
                answer = {
                    "code": self.current_process_code,
                    "keyword": [],
                    "text": "小微为您找到相关的医生："
                }
                doctor_data['answer'] = [answer]
                self.active.set('answer_builder', AnswerSkillRuleBuilder())
                self.active.set('card_builder', CardSkillRuleBuilder())
                result['data'] = doctor_data
                self.is_end = 1
                return result
            logger.info('find_doctor entity[%s]无结果' % entity['doctor'][0].get('name'))
        if entity.get('disease') or entity.get('symptom'):
            # 返回交互框
            input_dict = self.environment.get('input_dict')
            dept_classify_params = {
                'q': input_dict['q']
            }
            transform_dict_data(dept_classify_params, input_dict,
                                {'confirm_patient_info': 'confirm_information',
                                 'age': 'age',
                                 'sex': 'sex',
                                 'symptom': 'symptomName'})
            dept_classify_data = cgm.get_strategy(
                self.environment.get('organization'), 'department_classify_interactive',
                dept_classify_params, raise_exception=False)
            if dept_classify_data.get('slot'):
                result['data'] = build_age_sex_symptom_result(dept_classify_data)
                self.active.set('interactive_box_builder', InteractiveSkillRuleBuilder())
                self.active.set('answer_builder', AnswerSkillRuleBuilder())
                return result
            elif dept_classify_data.get('card'):
                # 分科有结果
                department_name = dept_classify_data.get('card')[0].get('department_name')
                department_id = dept_classify_data.get('card')[0].get('department_id')
                if department_name and department_id and department_name != 'unknow':
                    self.entity['department_classify'] = [{'id': department_id, 'name': department_name}]
                    self.current_process_code = self.default_process_code
                    result['continue'] = 1
                    self.rule_params = {
                        'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['department']}]
                    }
                    return result
                logger.info('find_doctor 分科[%s]无结果' % input_dict['q'])
        if entity.get('department'):
            self.current_process_code = '_v1'
            result['continue'] = 1
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['department']}]
            }
            return result
        # 调用规则系统,返回文案
        answer = {
            "code": self.current_process_code,
            "keyword": [],
            "text": "很抱歉，小微没有理解您的意思，您可以这样问小微“看白癜风哪个医生好”～"
        }
        data = {'answer': [answer]}
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        result['data'] = data
        self.is_end = 1
        return result

    def pre_back(self):
        result = {}
        input_dict = self.environment.get('input_dict')
        find_doctor_service = input_dict.get('find_doctor_service', [''])
        if input_dict.get('alter_require') == 1:
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id}]
            }
            if find_doctor_service[0] == '其他':
                self.rule_params = {}
            elif find_doctor_service[0] == '挂号':
                self.rule_params['skipStep'] = -2
            elif find_doctor_service[0] == '问诊':
                self.rule_params['skipStep'] = -1
            self.current_process_code = self.default_process_code
            result['continue'] = 1
            return result

    def pre_search_doctor(self):
        result = {}
        self.active.set('card_builder', CardSkillRuleBuilder())
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        self.current_process_code = 'find_doctor_end'
        self.is_end = 1
        entity = self.environment.get('entity_dict')
        input_dict = self.environment.get('input_dict')
        doctor_params = {
            'q': '*',
            'rows': 4,
            'extend_area': 2
        }
        disease_name = [temp['name'] for temp in entity.get('disease', []) if temp.get('name')]
        department_id = []
        department_name = []
        hospital_name = []
        department_id.extend([temp['id'] for temp in self.entity.get(
            'department_classify', []) if temp.get('id')])
        if not department_id:
            department_id.extend([temp['id'] for temp in entity.get('department', []) if temp.get('id')])

        department_name.extend([temp['name'] for temp in self.entity.get(
            'department_classify', []) if temp.get('name')])
        if not department_name:
            department_name.extend([temp['name'] for temp in entity.get('department', []) if temp.get('name')])
        hospital_name.extend([temp['name'] for temp in entity.get('hospital', []) if temp.get('name')])
        if department_name:
            doctor_params['department_name'] = ','.join(department_name)
        if hospital_name:
            doctor_params['hospital_name'] = ','.join(hospital_name)
        # 设置q
        q_list = []
        q_list.extend(department_name)
        q_list.extend(disease_name)
        if q_list:
            doctor_params['q'] = ' '.join(q_list)
        else:
            answer = {
                "code": self.current_process_code,
                "keyword": [],
                "text": "很抱歉，没有找到符合您筛选条件的医生，是否放宽筛选条件试试～"
            }
            doctor_data = {
                'answer': [answer],
                'alter_require': 1
            }
            result['data'] = doctor_data
            logger.info('找医生无q,不进行搜索')
            return result
        find_doctor_service = input_dict.get('find_doctor_service', [''])
        # 找医生的时候设置用户历史信息
        if find_doctor_service[0] == '其他':
            doctor_params['serve_type'] = '1,2,11'
        else:
            if find_doctor_service[0] == '挂号':
                doctor_params['serve_type'] = '1'
                doctor_params['contract_price_range'] = input_dict.get('find_doctor_guahao_fee', ['0|200'])[0]
                # 地区
                add_area_params(doctor_params, entity)
            elif find_doctor_service[0] == '问诊':
                doctor_params['serve_type'] = '2'
                consult_price_range = input_dict.get('find_doctor_guahao_fee', ['0|800'])[0].split('|')
                if consult_price_range and len(consult_price_range) == 2:
                    consult_price_range = '|'.join([str(int(temp) * 100) for temp in consult_price_range])
                    doctor_params['consult_price_range'] = consult_price_range
        find_doctor_require = input_dict.get('find_doctor_require', [])
        for temp in find_doctor_require:
            if temp == '公立三甲坐诊':
                doctor_params['is_public'] = 1
                doctor_params['hospital_level'] = '33'
            elif temp == '副主任以上':
                doctor_params['doctor_title'] = '1,3'
            elif temp == '3日内有号':
                if department_id:
                    doctor_params['std_dept_3d_haoyuan'] = ','.join(department_id)
            elif temp == '微医榜医生':
                doctor_params['is_doctor_on_rank'] = 1
            elif temp == '接诊患者多':
                doctor_params['order_count_range'] = '10|*'
            elif temp == '患者评价好':
                doctor_params['total_praise_rate_range'] = '95|*'
            elif temp == '问诊可约':
                doctor_params['consult_service_type'] = '1,2,3'
        doctor_data = cgm.get_strategy(self.environment.get('organization'),
                                       'find_doctor_doctor', doctor_params, raise_exception=False)
        if doctor_data.get('card', []):
            answer = {
                "code": self.current_process_code,
                "keyword": [],
                "text": "小微为您找到最匹配的相关医生，按照推荐程度排序："
            }
        else:
            answer = {
                "code": self.current_process_code,
                "keyword": [],
                "text": "很抱歉，没有找到符合您筛选条件的医生，是否放宽筛选条件试试～"
            }
            logger.info('找医生无结果,查询参数：%s, 返回结果：%s' % (
                json.dumps(doctor_params), json.dumps(doctor_data)))
        doctor_data['answer'] = [answer]
        doctor_data['alter_require'] = 1
        result['data'] = doctor_data
        return result

    def post_find_doctor_start(self, rule_result, **kwargs):
        self.active.set('interactive_box_builder', InteractiveSkillRuleBuilder())
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        set_placeholder(rule_result, self.placeholder_dict['find_doctor_start'])
        result = {
            'data': rule_result,
        }
        return result

    def post_doctor_service(self, rule_result, **kwargs):
        # 返回医生问诊/挂号/其他
        answer_text = rule_result.get('answer', [{}])[0].get('text')
        if answer_text:
            department = self.entity.get('department_classify')
            if department and department[0].get('name'):
                rule_result['answer'][0]['text'] = answer_text % {'department': department[0].get('name')}
            else:
                rule_result['answer'][0]['text'] = '好的，请问您是想挂号还是线上问诊呢？'
        result = self.post_default(rule_result, **kwargs)
        return result

    def post_doctor_require(self, rule_result, **kwargs):
        if self.skip_type == 2:
            rule_result['answer'] = [{
                "code": self.current_process_code,
                "keyword": [],
                "text": "很抱歉，没有找到符合您筛选条件的医生，请放宽筛选条件试试"
            }]
        # 若已经填过，用默认的
        find_doctor_require = self.environment.get('input_dict').get('find_doctor_require')
        add_option_attribute(rule_result, {'skip': 1})
        interactive = rule_result.get('interactiveBox')
        if find_doctor_require and interactive and interactive[0].get('options'):
            for option in interactive[0].get('options'):
                if option.get('content') in find_doctor_require:
                    option['defaultContent'] = '1'
        result = self.post_default(rule_result, **kwargs)
        return result

    def post_area(self, rule_result, **kwargs):
        # 返回地区
        answer_text = rule_result.get('answer', [{}])[0].get('text')
        if answer_text:
            area_name = None
            city = self.environment.get('entity_dict').get('city_default')
            province = self.environment.get('entity_dict').get('province_default')
            if city and city[0].get('name'):
                area_name = city[0].get('name')
            if not area_name and province and province[0].get('name'):
                area_name = province[0].get('name')
            if area_name:
                rule_result['answer'][0]['text'] = answer_text % {'city': area_name}
            else:
                rule_result['answer'][0]['text'] = '请选择您的就诊地：'
        reset_box_type(rule_result, box_type=constant.INTERACTIVE_TYPE_AREA)
        add_option_attribute(rule_result, {'skip': 1})
        result = self.post_default(rule_result, **kwargs)
        return result

    def post_default(self, rule_result, **kwargs):
        self.active.set('interactive_box_builder', InteractiveSkillRuleBuilder())
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        result = {
            'data': rule_result,
        }
        return result

    def post_guahao_fee(self, rule_result, **kwargs):
        # 挂号费进度条
        input_dict = self.environment.get('input_dict')
        find_doctor_guahao_fee = input_dict.get('find_doctor_guahao_fee')
        find_doctor_service = input_dict.get('find_doctor_service', [''])
        answer_text = rule_result.get('answer', [{}])[0].get('text')
        fee_text = '0-200'
        default_context = '0|200'
        if find_doctor_service[0] == '问诊':
            fee_text = '0-800'
            default_context = '0|800'
            answer_text = '好的，默认在线问诊价格区间为%(guahao_fee)s元，请问需要修改吗？'
        if answer_text:
            if find_doctor_guahao_fee:
                fee_text = '-'.join(find_doctor_guahao_fee[0].split('|')[:2])
            rule_result['answer'][0]['text'] = answer_text % {'guahao_fee': fee_text}
        for temp in rule_result.get('interactiveBox', [{}])[0].get('options', []):
            temp['type'] = constant.INTERACTIVE_TYPE_PROGRESS
            if find_doctor_guahao_fee:
                temp['defaultContent'] = find_doctor_guahao_fee[0]
            else:
                temp['defaultContent'] = default_context
        add_option_attribute(rule_result, {'skip': 1})
        result = self.post_default(rule_result, **kwargs)
        return result

    # 预处理
    pre_process_dict = {
        'find_doctor_start': pre_entity_extract,
        'find_doctor_service': pre_doctor_service,
        'find_doctor_require': pre_doctor_require,
        'alter_area': pre_default_to_rule,
        'find_doctor_guahao_fee': pre_search_doctor,
        'find_doctor_end': pre_back
    }
    # 规则系统
    post_process_dict = {
        'find_doctor_start': post_find_doctor_start,
        'find_doctor_service': post_doctor_service,
        'find_doctor_require': post_doctor_require,
        'alter_area': post_area,
        'find_doctor_guahao_fee': post_guahao_fee
    }
    placeholder_dict = {
        'find_doctor_start': '请输入医生名/症状/科室/疾病',
        'find_doctor_without_entity': '请输入医生名/症状/科室/疾病',
        'find_doctor_without_entity_2': '请输入医生名/症状/科室/疾病',
    }

    def __init__(self):
        """
        dialogue:{
            process_code: '',   # 下一轮处理code
            dialogue_result: {},    # 规则结果
        }
        """
        self.environment = None
        self.active = Active()
        self.dialogue = {}
        self.session_id = None
        self.question_id = None
        self.entity = {}
        self.is_end = 0
        self.rule_params = {}

        self.current_process_code = None  # 当前步处理code
        self.return_result = {}  # 返回结果
        self.skip_type = 1  # 2=无数据回退  3=输入alter_require
        organization_dict = get_organization_dict()
        self.organization = organization_dict[constant.VALUE_MODE_XWYZ]

        pass

    @classmethod
    def generate(cls, environment):
        result = cls()
        result.environment = environment
        result.dialogue = result.environment.get('dialogue', default={})
        return result

    def _parse_input(self):
        q = None
        input_list = self.environment.get('input', default=[])
        q = parse_input(input_list, ['find_doctor_start', ])
        input_dict = self.environment.get('input_dict')
        if q:
            input_dict['q'] = q[0]
        trans_entity_input(input_dict)
        trans_area(input_dict)
        del_params(input_dict, key=['find_doctor_require', 'find_doctor_guahao_fee'])
        self.environment.parse_entity()
        # self.environment.reset_entity()
        # self.environment.parse_input_dict_entity()

    def process(self):
        """
        a: 当前code需要去处理
        1.dialogue里获取current_process_code
        2.若business_process_dict里有current_process_code,获取其方法执行，返回处理data,设置其控制信息以及下一次处理的code
        3.若business_process_dict里无current_process_code,调用规则系统,获取规则系统的当前code, 通过rule_process_dict获取
            对应的执行方法,执行,  返回处理data,设置其控制信息以及下一次处理的code
        4.若控制信息说要继续调用,则跳到2.
        """
        # 重置环境
        self._parse_input()
        self.current_process_code = self.dialogue.get('process_code', 'start')
        self.session_id = self.dialogue.get('session_id')
        self.question_id = self.dialogue.get('question_id')
        self.entity = self.dialogue.get('entity', {})
        result = self.process_step()
        # 包装result:   1:result = data['data'],其他:通过包装器进行
        if result.get('data_type') == 1:
            self.return_result = result.get('data', {})
        else:
            self.active.builder_skill(result.get('data'), self.return_result)
        self.post_build(self.return_result, result.get('data'))
        return {'data': self.return_result}

    def process_step(self):
        if self.pre_process_dict.get(self.current_process_code):
            result = self.pre_process_dict[self.current_process_code](self)
        else:
            result = self.process_rule_engine()
        if result.get('continue') == 1:
            result = self.process_step()
        return result

    def post_build(self, result, data):
        # 返回时对dialogue进行处理
        dialogue = result.setdefault('dialogue', {})
        if self.current_process_code:
            dialogue['process_code'] = self.current_process_code
        result['isEnd'] = self.is_end
        result['is_end'] = self.is_end
        # result['is_end'] = self.is_end
        if self.question_id:
            dialogue['question_id'] = self.question_id
        if self.session_id:
            dialogue['session_id'] = self.session_id
        if self.entity:
            dialogue['entity'] = self.entity
        if 'alter_require' in data:
            # 变更医生要求
            result['alter_require'] = 1
        if 'search_params' in data:
            result['search_params'] = data['search_params']

    def process_rule_engine(self, key=None):
        params = {
            'organizeCode': self.organization,
            'ruleGroupName': 'xwyz',
            # 'trigger': 'find_doctor',
            'trigger': '华山医院'
        }
        if self.session_id:
            params['sessionId'] = self.session_id
        if self.rule_params:
            params.update(self.rule_params)
        code, rule_result = self.get_rule_engine_result(params=params)
        self.current_process_code = code
        self.deal_rule_result(rule_result)
        result = self.post_process_dict.get(code)(self, rule_result)
        return result

    def get_rule_engine_result(self, params):
        # 封装规则引擎
        rule_result = get_service_data(json.dumps(params), ai_client, 'rule_engine', return_response=True,
                                       result={}, throw=True)
        answer_code = None
        if rule_result.get('code') == 1:
            # 规则系统异常
            logger.exception(rule_result.get('message'))
            raise Exception(rule_result.get('message'))
        data = rule_result.get('data')
        if data:
            answer_code = data.get('answer', [])[0]['code']
        return answer_code, data

    def deal_rule_result(self, rule_result):
        # 处理规则结果
        if not self.session_id:
            self.session_id = rule_result.get('sessionId')
        if rule_result.get('interactiveBox') and rule_result['interactiveBox'][0].get('options'):
            options = rule_result['interactiveBox'][0]['options']
            if options and options[0].get('questionId'):
                self.question_id = options[0]['questionId']
        return


if __name__ == '__main__':
    pass
