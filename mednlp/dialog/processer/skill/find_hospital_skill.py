#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mednlp.dialog.configuration import logger, ai_client, sc_client
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.active_2 import Active
import traceback
import json
from mednlp.dialog.general_util import get_service_data
from mednlp.dialog.dialogue_util import cgm, build_age_sex_symptom_result, reset_box_type, \
    set_placeholder, add_option_attribute, parse_input, add_area_params, trans_entity_input, trans_area, del_params
from mednlp.dialog.builder.answer_builder import AnswerSkillRuleBuilder
from mednlp.dialog.builder.interactive_box_builder import InteractiveSkillRuleBuilder
from mednlp.dialog.builder.card_builder import CardSkillRuleBuilder
from mednlp.dialog.configuration import Constant as constant, get_organization_dict


class FindHospitalSkill(object):
    default_process_code = 'default_v1'
    no_data_process_code = 'no_data'

    def pre_default_to_rule(self):
        result = {}
        result['continue'] = 1
        self.current_process_code = FindHospitalSkill.default_process_code
        self.rule_params = {
            'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['continue']}]
        }
        return result

    def post_default(self, rule_result, **kwargs):
        self.active.set('interactive_box_builder', InteractiveSkillRuleBuilder())
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        result = {
            'data': rule_result,
        }
        return result

    def post_find_hospital_require(self, rule_result, **kwargs):
        department = self.entity.get('department_classify')
        if department and department[0].get('name'):
            rule_result['answer'][0]['text'] = '小微推荐你去看%(department)s哦，请问您对医院有什么要求？' % {
                'department': department[0].get('name')}
        # 2=无数据回退  3=输入alter_require
        if self.skip_type == 2:
            rule_result['answer'] = [{
                "code": self.current_process_code,
                "keyword": [],
                "text": "很抱歉，没有找到符合您筛选条件的医院，请放宽筛选条件试试～"
            }]
        find_hospital_require = self.environment.get('input_dict').get('find_hospital_require')
        interactive = rule_result.get('interactiveBox')
        if find_hospital_require and interactive and interactive[0].get('options'):
            for option in interactive[0].get('options'):
                if option.get('content') in find_hospital_require:
                    option['defaultContent'] = '1'
        add_option_attribute(rule_result, {'skip': 1})
        result = self.post_default(rule_result, **kwargs)
        return result

    def pre_find_hospital_is_has(self):
        result = {}
        q = self.environment.get('input_dict').get('q')
        if not q:
            # 未输入q,提示用户输入
            result['continue'] = 1
            self.current_process_code = FindHospitalSkill.default_process_code
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['没有']}]
            }
            return result
        entity = self.environment.get('entity_dict')
        if entity.get('hospital'):
            # 有医院词 , 返回对应医院卡片
            hospital_params = {
                'q': entity['hospital'][0].get('name'),
                'rows': 4
            }
            add_area_params(hospital_params, entity)
            hospital_data = cgm.get_strategy(self.environment.get('organization'),
                                             'find_hospital_hospital', hospital_params, raise_exception=False)
            if hospital_data.get('card', []):
                answer = {
                    "code": self.current_process_code,
                    "keyword": [],
                    "text": "小微为您找到相关的医院："
                }
                hospital_data['answer'] = [answer]
                self.active.set('answer_builder', AnswerSkillRuleBuilder())
                self.active.set('card_builder', CardSkillRuleBuilder())
                result['data'] = hospital_data
                self.is_end = 1
                return result
            logger.info('find_hospital entity[%s]无结果' % entity['hospital'][0].get('name'))
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
                # 可能分科无结果
                department_name = dept_classify_data.get('card')[0].get('department_name')
                department_id = dept_classify_data.get('card')[0].get('department_id')
                if department_name and department_id and department_name != 'unknow':
                    self.entity['department_classify'] = [{'id': department_id, 'name': department_name}]
                    self.current_process_code = self.default_process_code
                    result['continue'] = 1
                    self.rule_params = {
                        'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['识别']}]
                    }
                    return result
                logger.info('find_hospital 分科[%s]无结果' % input_dict['q'])
        if entity.get('department'):
            # 继续
            result['continue'] = 1
            self.current_process_code = FindHospitalSkill.default_process_code
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['识别']}]
            }
            return result
        result['continue'] = 1
        self.current_process_code = FindHospitalSkill.default_process_code
        self.rule_params = {
            'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['有']}]
        }
        return result

    def pre_find_hospital_hospital_error(self):
        # 医院识别错误
        result = {}
        entity = self.environment.get('entity_dict')
        if entity.get('hospital'):
            # 有医院词 , 返回对应医院卡片
            hospital_params = {
                'q': entity['hospital'][0].get('name'),
                'rows': 4
            }
            add_area_params(hospital_params, entity)
            hospital_data = cgm.get_strategy(self.environment.get('organization'),
                                             'find_hospital_hospital', hospital_params, raise_exception=False)
            if hospital_data.get('card', []):
                answer = {
                    "code": self.current_process_code,
                    "keyword": [],
                    "text": "小微为您找到相关的医院："
                }
                hospital_data['answer'] = [answer]
                self.active.set('answer_builder', AnswerSkillRuleBuilder())
                self.active.set('card_builder', CardSkillRuleBuilder())
                result['data'] = hospital_data
                self.is_end = 1
                return result
            logger.info('find_hospital entity[%s]无结果' % entity['hospital'][0].get('name'))
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
                # 可能分科无结果
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
                logger.info('find_hospital 分科[%s]无结果' % input_dict['q'])
        if entity.get('department'):
            # 继续
            result['continue'] = 1
            self.current_process_code = FindHospitalSkill.default_process_code
            self.rule_params = {
                'userAnswers': [{'questionId': self.question_id, 'questionAnswer': ['department']}]
            }
            return result
        answer = {
            "code": self.current_process_code,
            "keyword": [],
            "text": "很抱歉，小微没有理解您的意思，您可以这样问小微“头痛去哪家医院”。"
        }
        data = {'answer': [answer]}
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        result['data'] = data
        self.is_end = 1
        return result

    def pre_back(self):
        result = {}
        input_dict = self.environment.get('input_dict')
        if input_dict.get('alter_require') == 1:
            self.rule_params['skipStep'] = -1
            self.current_process_code = '_v1'
            result['continue'] = 1
            # 设置回退
            self.skip_type = 3
            return result

    def pre_hospital_search(self):
        result = {}
        self.active.set('card_builder', CardSkillRuleBuilder())
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        self.current_process_code = 'find_hospital_end'
        self.is_end = 1
        entity = self.environment.get('entity_dict')
        input_dict = self.environment.get('input_dict')
        hospital_params = {
            'rows': 4,
            'extend_area': 2
        }
        disease_name = [temp['name'] for temp in entity.get('disease', []) if temp.get('name')]
        department_id = []
        department_name = []
        department_id.extend([temp['id'] for temp in self.entity.get(
            'department_classify', []) if temp.get('id')])
        if not department_id:
            department_id.extend([temp['id'] for temp in entity.get('department', []) if temp.get('id')])

        department_name.extend([temp['name'] for temp in self.entity.get(
            'department_classify', []) if temp.get('name')])
        if not department_name:
            department_name.extend([temp['name'] for temp in entity.get('department', []) if temp.get('name')])
        if department_name:
            hospital_params['department_name'] = ','.join(department_name)

        q_list = []
        q_list.extend(department_name)
        q_list.extend(disease_name)
        if q_list:
            hospital_params['q'] = ' '.join(q_list)
        else:
            # 若q都没有,说明查询不存在
            answer = {
                "code": self.current_process_code,
                "keyword": [],
                "text": "很抱歉，没有找到符合您筛选条件的医院，请放宽筛选条件试试～"
            }
            hospital_data = {
                'answer': [answer],
                'alter_require': 1
            }
            result['data'] = hospital_data
            logger.info('找医院无q,不进行搜索')
            return result
        transform_dict_data(hospital_params, input_dict, {'longitude': 'longitude', 'latitude': 'latitude'})
        find_hospital_require = input_dict.get('find_hospital_require', [])
        for temp in find_hospital_require:
            if temp == '三甲医院':
                hospital_params['hospital_level'] = 33
            elif temp == '综合医院':
                hospital_params['hospital_type'] = 1
            elif temp == '3日内有号':
                if department_id:
                    hospital_params['std_dept_3d_haoyuan'] = ','.join(department_id)
            elif temp == '权威推荐':
                hospital_params['authority'] = 1
            elif temp == '就诊患者多':
                hospital_params['order_count_range'] = '10000|*'
            elif temp == '患者评价好':
                hospital_params['praise_rate_range'] = '98|*'
        # 地区
        add_area_params(hospital_params, entity)
        hospital_data = cgm.get_strategy(self.environment.get('organization'),
                                         'find_hospital_hospital', hospital_params, raise_exception=False)
        if hospital_data.get('card', []):
            answer = {
                "code": self.current_process_code,
                "keyword": [],
                "text": "小微为您找到最匹配的相关医院，按照推荐程度排序："
            }
        else:
            answer = {
                "code": self.current_process_code,
                "keyword": [],
                "text": "很抱歉，没有找到符合您筛选条件的医院，请放宽筛选条件试试～"
            }
            logger.info('找医生无结果,查询参数：%s, 返回结果：%s' % (
                json.dumps(hospital_params), json.dumps(hospital_data)))
        hospital_data['answer'] = [answer]
        hospital_data['alter_require'] = 1
        result['data'] = hospital_data
        return result

    def post_find_hospital_is_has(self, rule_result, **kwargs):
        self.active.set('interactive_box_builder', InteractiveSkillRuleBuilder())
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        # 有/没有添加placeholder
        options = rule_result.get('interactiveBox', [{}])[0].get('options', [])
        shibie_index = -1
        for temp in options:
            if temp.get('content') == '有':
                temp['placeholder'] = '填写医院名称，必填'
                temp['isSpecialOption'] = 1
            if temp.get('content') == '识别':
                shibie_index = options.index(temp)
        if shibie_index != -1 and options:
            options.pop(shibie_index)
        result = {
            'data': rule_result,
        }
        return result

    def post_find_hospital_hint(self, rule_result, **kwargs):
        # 有/没有添加placeholder
        options = rule_result.get('interactiveBox', [{}])[0].get('options', [])
        for temp in options:
            temp['placeholder'] = '请输入科室/疾病/症状'
        result = self.post_default(rule_result)
        return result

    def post_find_hospital_hospital_error(self, rule_result, **kwargs):
        answer_text = rule_result.get('answer', [{}])[0].get('text')
        if answer_text:
            rule_result['answer'][0]['text'] = answer_text % {'hospital': self.environment.get(
                'input_dict').get('q', '')}
        # reset_box_type(rule_result, box_type='text_q')
        result = self.post_default(rule_result)
        return result

    # def post_find_hospital_without_entity(self, rule_result, **kwargs):
    #     set_placeholder(rule_result, '请输入科室/疾病/症状')
        # reset_box_type(rule_result, box_type='text_q')
        # result = self.post_default(rule_result)
        # return result

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

    """
    1.start, 走规则,返回没有/有  find_hospital_is_has
    3.有,输入医院,返回卡片  或者 走规则 提示：很抱歉, find_hospital_hospital_error
        小微没有找到浙江省中医院，告诉小微哪里不舒服，小微给您推荐适合您的医院～
    4.没有 跳到好的，请问您哪里不输服   find_hospital_hint
    5.错误，好的，请问您哪里不舒服？(若您已知科室或入科室或疾病名)～返回find_hospital_without_entity
    6.还是错误, 返回find_hospital_without_entity_2,正确跳到find_hospital_require
    7.到find_hospital_require、返回alter_area
    8.alter_area 返回医生、 若没有，则返回find_hospital_without_data
    (很抱歉，没有找到符合您筛选条件的医院，请放宽筛选条件试试～)
    """
    # 预处理
    pre_process_dict = {
        'find_hospital_is_has': pre_find_hospital_is_has,
        'find_hospital_hospital_error': pre_find_hospital_hospital_error,
        # 'find_hospital_without_entity': pre_find_hospital_hospital_error,
        # 'find_hospital_without_entity_2': pre_find_hospital_hospital_error,
        'find_hospital_hint': pre_find_hospital_hospital_error,
        'find_hospital_require': pre_default_to_rule,
        'alter_area': pre_hospital_search,
        'find_hospital_end': pre_back
        # 'find_doctor_guahao_fee': pre_search_doctor
    }
    # 规则系统
    post_process_dict = {
        'find_hospital_is_has': post_find_hospital_is_has,
        'find_hospital_hint': post_find_hospital_hint,
        'find_hospital_hospital_error': post_find_hospital_hospital_error,
        # 'find_hospital_without_entity': post_find_hospital_without_entity,
        # 'find_hospital_without_entity_2': post_find_hospital_without_entity,
        'find_hospital_require': post_find_hospital_require,
        'alter_area': post_area,
        # 'find_hospital_without_data': post_default
    }

    def __init__(self):
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

    def _parse_input(self):
        q = None
        input_list = self.environment.get('input', default=[])
        q = parse_input(input_list, ['find_hospital_is_has', 'find_hospital_hospital_error',
                                     'find_hospital_hint'])
        input_dict = self.environment.get('input_dict')
        if q:
            input_dict['q'] = q[0]
        trans_entity_input(input_dict)
        trans_area(input_dict)
        del_params(input_dict, key=['find_hospital_require'])
        self.environment.parse_entity()
        # self.environment.reset_entity()
        # self.environment.parse_input_dict_entity()

    def process(self):
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
        self.post_build(self.return_result, result.get('data', {}))
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
            'trigger': '浙一医院'
            # 'trigger': 'find_hospital'
        }
        if self.session_id:
            params['sessionId'] = self.session_id
        if self.rule_params:
            params.update(self.rule_params)
            # self.pre_process_params(params, key)
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

    @classmethod
    def generate(cls, environment):
        result = cls()
        result.environment = environment
        result.dialogue = result.environment.get('dialogue', default={})
        return result


if __name__ == '__main__':
    pass
