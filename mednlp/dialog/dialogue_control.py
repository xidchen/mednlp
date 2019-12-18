#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.configuration import Configuration2 as Configuration, deal_input, logger, get_organization_dict,\
    get_search_params
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.active_factory_2 as active_factory
from mednlp.service.ai_medical_service.ai_search_common import get_entity
from mednlp.dialog.environment import Environment, DialogueStatus
import json
import copy
import configparser
from mednlp.dialog.processer.skill.find_doctor_skill import SkillFactory
from mednlp.dialog.dialogue_util import postprocess, preprocess
from mednlp.dialog.component_config import organization_intention_config
from mednlp.dialog.dialogue_constant import db, ai_sc, cgm, Constant as constant2
from mednlp.dialog.general_util import get_service_data


class DialogueControl(object):
    """
    控制类,处理整个业务流程,仅存储常量,不存储变量
    """

    def control(self, query_dict):
        """
        构造1个Environment,将所有信息存入

        1.预处理:
            1.query_dict里对mode和organization进行处理

        2.初始化environment对象
        3.实体识别、意图识别,并把结果设置到environment里
        4.根据environment里的intention对象钟走不痛的逻辑
            1.skill
            2.自诊
            3.其他意图
        5.返回

        未处理的注意点：
        1.entity_params
        2.
        """
        preprocess(query_dict)
        environment = DialogueStatus.generate(query_dict)
        if 'guiding' in environment.input_dict:
            result = {'data': {'guiding': constant2.guiding_list}}
            return result
        environment.load_configuration()  # 加载机构配置
        result = self.init_control(environment)
        return result

    def init_raw_control(self, environment):
        """
        ai_qa、京东音箱的逻辑处理
        1.处理other意图
        2.无意图配置
        3.
        """
        result = {constant.RESULT_DATA: {}}
        is_bottom = False  # 是否兜底
        intention = environment.intention
        if constant.INTENTION_OTHER == intention:
            if constant.VALUE_MODE_JD_BOX == environment.mode:
                # 京东音箱为other的process处理放入这里
                result['data']['intention'] = environment.intention_combine
                result['data']['answer'] = '很抱歉，我还在学习中。您可以问我，胃不舒服挂什么科'
                return is_bottom, result
            # ai_qa模式下意图为other[识别不到意图] 走兜底
            is_bottom = True
            return is_bottom, result
        else:
            strategy = organization_intention_config.get(environment.get('organization'), {}).get(
                environment.intention_combine, {}).get('strategy', {})
            if strategy.get('execute'):
                strategy_params = copy.deepcopy(environment.input_dict)
                if strategy.get('params'):
                    strategy_params.update(strategy['params'])
                data = cgm.get_strategy(environment.get(constant.QUERY_FIELD_ORGANIZATION),
                                        environment.intention_combine, strategy_params)
                intention_conf = environment.conf.create_intention_conf()
                # keyword_symptom仅用了cardbuild
                active = active_factory.build_generator_active(intention_conf, environment.mode)
                result_data = active.build(data, strategy_params, intention_conf=intention_conf, interactive_option=2)
                result['data'] = result_data
                return is_bottom, result
        if environment.intention_conf.is_empty():
            # 若无意图配置, 显示异常文案【启用自定义配置还未配置】
            self.deal_intention_result(result, intention=intention, intentionDetails=environment.intention_detail)
            result['data']['answer'] = []
            result['data']['answer'].append({'text': environment.conf.get_exception_answer(
                constant.EXCEPTION_ANSWER_CODE_NO_CONFIG)})
            return is_bottom, result
        # step4:获取数据,构建active
        active = active_factory.build_active(environment)
        process_data = active.process(environment.original_input)  # 需明确process_data到底是什么结构
        if self.has_data(process_data, environment.mode):
            result_data = active.build(process_data, environment.input_dict, intention_conf=environment.intention_conf)
            result['data'] = result_data
        else:
            bottom_intention_set = environment.conf.get_intention_set(True)
            if not bottom_intention_set:
                self.deal_intention_result(result, intention=intention, intentionDetails=environment.intention_detail)
                result['data']['answer'] = []
                result['data']['answer'].append({'text': environment.conf.get_exception_answer(
                    constant.EXCEPTION_ANSWER_CODE_NO_RESULT)})
                return is_bottom, result
            # step7:进行兜底
            is_bottom = True
            environment.is_bottom = True
        return is_bottom, result

    def bottom_raw_control(self, environment):
        result = {}
        self.intention_recognition(environment)
        intention = environment.intention
        if constant.INTENTION_OTHER == intention:
            # 若兜底意图为other,显示异常文案【无法识别意图默认返回文案】
            result['data']['answer'] = []
            result['data']['answer'].append({'text': environment.conf.get_exception_answer(
                constant.EXCEPTION_ANSWER_CODE_NO_INTENTION)})
            # result['data']['intention'] = intention
            return result
        if environment.intention_conf.is_empty():
            # 若无意图配置,显示异常文案【启用自定义配置还未配置】
            result['data']['answer'] = []
            result['data']['answer'].append({'text': environment.conf.get_exception_answer(
                constant.EXCEPTION_ANSWER_CODE_NO_CONFIG)})
            return result
        # step4:获取数据,构建active
        active = active_factory.build_active(environment)
        process_data = active.process(environment.original_input)  # 需明确process_data到底是什么结构
        if self.has_data(process_data, environment.mode):
            result_data = active.build(process_data, environment.input_dict, intention_conf=environment.intention_conf)
            result['data'] = result_data
        else:
            result['data']['answer'] = []
            result['data']['answer'].append({'text': environment.conf.get_exception_answer(
                constant.EXCEPTION_ANSWER_CODE_NO_RESULT)})
        return result

    def init_control(self, environment):
        self.intention_recognition(environment)  # 意图识别
        if environment.skill:
            # skill 需要对输入做处理,再进行实体识别
            skill_manager = SkillFactory.generate(environment.skill, environment)
            result = skill_manager.process()
            environment.result = result
            return result
        elif environment.mode not in constant.VALUE_MODE_MENHU:
            # mode 在 ai_qa、loudspeaker_box 走老逻辑
            environment.parse_entity()  # 实体识别
            is_bottom, result = self.init_raw_control(environment)
            if is_bottom:
                result = self.bottom_raw_control(environment)
            self.deal_result(result)
            return result
        elif environment.intention_combine:
            # 已经有意图配置, 获取意图的处理器获取data, 小微医助处理
            environment.parse_entity()  # 实体识别
            active = active_factory.build_active_2(environment)
            data = active.process_2(environment)
            if environment.intention_combine in (
                    'keyword_treatment', 'content', 'other', 'keyword_examination', 'keyword_medical_word',
                    'Keyword_symptom', 'keyword_medicine', 'keyword_city', 'keyword_province', 'keyword_body_part'
            ):
                post_data = [temp for temp in data.get('card', []) if temp.get(
                    constant.GENERATOR_CARD_FLAG) == constant.GENERATOR_CARD_FLAG_POST]
                if not post_data and environment.mode == 'xwyz':
                    environment.reset_environment()
                    environment.dialogue.update({'intention': 'department', 'intentionDetails': []})
                    return self.init_control(environment)
                elif not post_data and environment.mode == 'xwyz_doctor':
                    environment.reset_environment()
                    environment.dialogue.update({'intention': 'departmentSubset', 'intentionDetails': []})
                    environment.input[-1].update({'is_end': 1, 'confirm_information': 1})
                    return self.init_control(environment)
            build_data = active.build_2(data, environment)
            result = {'data': build_data}
            postprocess(environment, result)
            return result

    def deal_result(self, result):
        data = result.setdefault('data', {})
        for temp in constant2.deal_result_dict:
            if temp not in data:
                data[temp] = constant2.deal_result_dict[temp]
        dialogue = data.setdefault('dialogue', {})
        if data.get('intention'):
            dialogue['intention'] = data['intention']
        if data.get('intentionDetails'):
            dialogue['intentionDetails'] = data['intentionDetails']

    def deal_intention_result(self, result, **kwargs):
        data = result.setdefault('data', {})
        if 'intention' in kwargs:
            data['intention'] = kwargs['intention']
        if 'intentionDetails' in kwargs:
            data['intention_details'] = kwargs['intentionDetails']
            data['intentionDetails'] = kwargs['intentionDetails']

    def has_data(self, process_data, mode):
        # 只要constant.HAS_PROCESS_DATA_KEY 有一个key存在且不为空,则有数据
        """
        有数据?
        1.交互框有 or 卡片有 or process_data有general_answer
        :param process_data:
        :param bottom:
        :return:
        """
        result = False
        if mode in (constant.VALUE_MODE_JD_BOX, constant.VALUE_MODE_XWYZ, constant.VALUE_MODE_XWYZ_DOCTOR):
            # 京东音箱默认有数据
            return True
        has_process_data_temp = constant.HAS_PROCESS_DATA_KEY
        for key_temp in has_process_data_temp:
            if process_data.get(key_temp):
                result = True
                break
        return result

    def intention_recognition(self, environment):
        """
        1.设置skill
        2.需要意图识别的,先从数据库加载配置,再意图识别

        skill: 固定意图，有find_doctor、find_hospital、question_answer、auto_diagnose
        intention: 根据
        """
        if environment.input_dict.get('skill'):
            environment.skill = environment.input_dict['skill']
            return
        elif environment.input_dict.get('auto_diagnosis'):
            environment.skill = 'auto_diagnose'
            return
        intention = environment.dialogue.get('intention')
        intention_details = environment.dialogue.get('intentionDetails', [])
        open_intention_set = environment.conf.get_intention_set(environment.is_bottom)
        intention_combine = intention
        if intention == 'keyword' and intention_details:
            intention_combine = '%s_%s' % (intention, intention_details[0])
        if intention_combine and (intention_combine in open_intention_set or intention_combine in (
                'auto_diagnose_skill',)):
            # dialogue里有意图并且该意图是有效意图
            environment.intention = intention
            environment.intention_detail = intention_details
            environment.intention_combine = intention_combine
            intention_conf = environment.conf.create_intention_conf()
            environment.intention_conf = intention_conf
            return
        else:
            intention, intention_details, intention_combine, accompany_intention = self.get_intention(
                environment, open_intention_set)
            environment.intention = intention
            environment.intention_detail = intention_details
            environment.intention_combine = intention_combine
            environment.accompany_intention = accompany_intention
            intention_conf = environment.conf.create_intention_conf()
            environment.intention_conf = intention_conf

    def get_intention(self, environment, open_intention_set):
        params = {
            'intention_set': open_intention_set,
            'mode': environment.mode,
            'q': environment.input_dict.get('q'),
            'accompany_intention_set': constant2.accompany_intention_set
        }
        res = get_service_data(json.dumps(params, ensure_ascii=False), ai_sc, 'intention_recognition',
                               method='post', logger=logger, return_response=True, throw=True)
        if not res or res['code'] != 0 or not res.get('data'):
            raise Exception('意图识别服务异常!!!')
        intention_object = res['data']
        intention = intention_object['intention']
        intention_details = []
        accompany_intention = []
        if intention_object.get('intentionDetails'):
            intention_details.append(intention_object['intentionDetails'])
        intention_combine = intention
        if intention == 'keyword' and intention_details:
            intention_combine = '%s_%s' % (intention, intention_details[0])
        if intention_object.get('accompany_intention'):
            accompany_intention = intention_object['accompany_intention']
        return intention, intention_details, intention_combine, accompany_intention


if __name__ == '__main__':
    dialog_control = DialogueControl()
    # corpusGreeting: 去你妈妈的
    # greeting: 您好
    # guide: 西湖怎么走
    # customer_service: 订单有问题
    # 浙二医院有男科吗 hospitalDepartment
    # 胃痛看哪个医生 doctor   慢性子宫内膜炎看哪个医生
    # 卢玉英看白癜风怎么样 doctorQuality
    # 儿科医院看哪个好 hospital
    # 头痛挂什么科 department
    # 糖尿病亟待解决 | 糖尿病治疗 content
    # 张星耀医生最近的号是哪天
    # 儿科医院看哪个好 hospital
    # 范青看白癜风怎么样
    # 高血压介入术  keyword_treatement
    
    # 20e69819207b4b359f5f67a990454027
    # c9ace68e78c345489bcf3007f9c04f6a sf
    # 993c190641e846d7bc3eaf57abfee3aa ryx
    # 0b8ed5e3c86949b09ed54534f56d7629 merge_search
    aa = {
        "input": [{
            "q": "友号",
            # "greeting_num": 2,
            # "q": "杭州",
            # "symptomName": "头晕"
            # 'skill': 'find_doctor'
            }
        ],
        "mode": "xwyz",
        "organization": "20e69819207b4b359f5f67a990454027",
        "source": "aa"
    }
    decoded_query = aa
    result = dialog_control.control(decoded_query)
    print(json.dumps(result, indent=True, ensure_ascii=False))
