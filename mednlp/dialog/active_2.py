#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.configuration import Constant as constant
from mednlp.dialog.builder.answer_builder import AnswerBuilderV2
from mednlp.dialog.builder.card_builder import CardBuilderV2
from mednlp.dialog.builder.interactive_box_builder import InteractiveBoxBuilderV2
from mednlp.dialog.builder.out_link_builder import OutLinkBuilderV2
from mednlp.dialog.dialogue_constant import cgm
from mednlp.dialog.dialogue_util import deal_q, greeting_interactive
from mednlp.utils.utils import transform_dict_data
import copy

class Active(object):

    def __init__(self, **kwargs):
        self.card_builder = None
        self.answer_builder = None
        self.out_link_builder = None
        self.interactive_box_builder = None
        self.processer = None
        self.is_strategy = False
        self.strategy_info = None

    def set_card_builder(self, card_builder):
        self.card_builder = card_builder

    def set_answer_builder(self, answer_builder):
        self.answer_builder = answer_builder

    def set_out_link_builder(self, out_link_builder):
        self.out_link_builder = out_link_builder

    def set_interactive_box_builder(self, interactive_box_builder):
        self.interactive_box_builder = interactive_box_builder

    def set_processer(self, processer):
        self.processer = processer

    def set(self, field_name, holder):
        setattr(self, field_name, holder)
        return getattr(self, field_name)

    def builder_skill(self, data, result):
        if self.card_builder:
            self.card_builder.build(environment=self, data=data, result=result)
        if self.interactive_box_builder:
            self.interactive_box_builder.build(environment=self, data=data, result=result)
        if self.answer_builder:
            self.answer_builder.build(environment=self, data=data, result=result)
        return result

    def build_auto_diagnose(self, data, **kwargs):
        # 处理自诊数据包含了基本的返回字段
        result_data = {}
        result_data['intention'] = 'auto_diagnose'
        result_data['intention_details'] = []
        result_data['intentionDetails'] = []
        result_data['is_end'] = data.get('is_end', 1)
        result_data['is_help'] = data.get('is_help', 0)
        result_data['isEnd'] = data.get('is_end', 1)
        result_data['isHelp'] = data.get('is_help', 0)
        result_data['dialogue'] = data.get('dialogue', {})
        result_data['search_params'] = data.get('search_params', {})
        if data.get('query_content'):
            result_data['query_content'] = data['query_content']
        if data.get('auto_diagnose_merge'):
            result_data['auto_diagnose_merge'] = data['auto_diagnose_merge']
        if data.get('service_list'):
            result_data['service_list'] = data['service_list']
        if data.get('progress'):
            result_data['progress'] = data['progress']
        card = self.card_builder.build(data)
        if card:
            result_data['card'] = card
        interactive_box = self.interactive_box_builder.build(data)
        if interactive_box:
            result_data['interactive_box'] = interactive_box
        answer = self.answer_builder.build(data)
        if answer:
            result_data['answer'] = answer
        return result_data

    def build_2(self, data, environment):
        result_data = {}
        intention_conf = environment.intention_conf
        result_data['is_end'] = data.get('is_end', 1)
        result_data['is_help'] = data.get('is_help', 0)
        result_data['isEnd'] = data.get('is_end', 1)
        result_data['isHelp'] = data.get('is_help', 0)
        result_data['intention'] = intention_conf.intention
        result_data['intentionDetails'] = intention_conf.intention_details
        result_data['intention_details'] = intention_conf.intention_details
        result_data['intention_set_id'] = intention_conf.intention_set_id
        result_data['dialogue'] = data.get('dialogue', {})
        result_data['search_params'] = data.get('search_params', {})
        result_data['query_content'] = data.get('query_content', '')
        transform_dict_data(result_data, data, {
            'registered': 'registered', 'area': 'area', 'accuracy': 'accuracy',
            'valid_auto_diagnose': 'valid_auto_diagnose', 'among': 'among',
            'confirm': 'confirm', 'standard_question_id': 'standard_question_id'
        })
        if intention_conf.intention in ('corpusGreeting', 'greeting', 'guide'):
            greeting_interactive(environment, data, result_data)
        card = self.card_builder.build_3(data, environment)
        if card:
            result_data['card'] = card
        interactive_result = self.interactive_box_builder.build_3(data, environment)
        if interactive_result.get('interactive_box'):
            result_data['interactive_box'] = interactive_result['interactive_box']
        elif interactive_result.get("interactive"):
            result_data['interactive'] = interactive_result['interactive']
        answer = self.answer_builder.build_3(data, environment)
        if answer:
            result_data['answer'] = answer
        out_link = self.out_link_builder.build(data, intention_conf)
        if out_link:
            result_data['out_link'] = out_link
        return result_data



    def build(self, data, inputs, **kwargs):
        """
                build可以重写,先仅1个，可以不做逻辑判断
                data属于result['data']
                data 是由process里得到的,会有is_end,is_help,dialogue,search_params返回参数
                由build包装下
                data:{
                    is_end: int,
                    is_help: int,
                    dialogue: {},
                    search_params: {},

                    ai_dept: {}
                    doctor_search: {}
                    hospital_search: {}
                    post_search: {}
                    greeting: {}
                    guide: {}
                }

                intention_conf:{
                    answer: {}
                    card: {}
                    out_link: {}
                    keyword: {}
                }
                :param data:
                :param inputs:
                :return:
                """
        intention_conf = kwargs['intention_conf']
        interactive_option = kwargs.get('interactive_option', 1)    # 1:interactive_box, 2:interactive_option
        result_data = {}  # 代表result里的data
        result_data['intention_details'] = intention_conf.intention_details
        result_data['is_end'] = data.get('is_end', 1)
        result_data['is_help'] = data.get('is_help', 0)

        result_data['intention'] = intention_conf.intention
        result_data['intentionDetails'] = intention_conf.intention_details
        result_data['intention_set_id'] = intention_conf.intention_set_id
        result_data['isEnd'] = data.get('is_end', 1)
        result_data['isHelp'] = data.get('is_help', 0)
        result_data['dialogue'] = data.get('dialogue', {})
        result_data['search_params'] = data.get('search_params', {})
        if data.get('area'):
            result_data['area'] = data['area']
        result_data['query_content'] = data.get('query_content', '')
        result_data['extends'] = data.get('extends', {})
        if data.get(constant.RESULT_FIELD_SHOW_GUIDING):
            result_data[constant.RESULT_FIELD_SHOW_GUIDING] = data[constant.RESULT_FIELD_SHOW_GUIDING]
        if constant.RESULT_FIELD_GREETING_NUM in data:
            result_data[constant.RESULT_FIELD_GREETING_NUM] = data[constant.RESULT_FIELD_GREETING_NUM]
        card = self.card_builder.build(data, intention_conf=intention_conf)
        if card:
            result_data['card'] = card
        out_link = self.out_link_builder.build(data, intention_conf)
        if out_link:
            result_data['out_link'] = out_link
        interactive_box = self.interactive_box_builder.build(data)
        answer_params = {}
        if interactive_box:
            if interactive_option == 1:
                result_data['interactive_box'] = interactive_box
                answer_params['interactive_box'] = interactive_box
            elif interactive_option == 2:
                result_data['interactive'] = interactive_box
                answer_params['interactive'] = interactive_box
        # answer需要针对所有的组件进行描述,因此需要放在最后
        answer = self.answer_builder.build(data, intention_conf, **answer_params)
        if answer:
            result_data['answer'] = answer
        # if intention_conf.configuration.mode in (constant.VALUE_MODE_XWYZ, constant.VALUE_MODE_XWYZ_DOCTOR):
        #     # 门户小微医助需要额外的字段,因此需要填充
        #     for temp_key in ('accuracy', 'departmentId', 'departmentName', 'department_updated',
        #                  'confirm', 'among', 'is_consult'):
        #         if temp_key in data:
        #             pass
                    # result_data[temp_key] = data[temp_key]
        return result_data

    def process(self, query, **kwargs):
        """
        :param query: dict
        :param kwargs:
        :return:
        """
        result = self.processer.process(query, **kwargs)
        return result

    def process_2(self, environment):
        if not self.is_strategy:
            result = self.processer.process_2(environment)  # 处理器
            return result
        input_params = copy.deepcopy(environment.input_dict)
        pop_fields = ('city', 'province', 'hospital', 'doctor', 'hospitalName', 'doctorName', 'symptomName')
        [input_params.pop(k) for k in pop_fields if k in input_params]   # 去除掉固定的几个数据
        for temp in self.strategy_info.get('changed _params', []):
            if temp == 'q':
                input_params[temp] = deal_q(environment, self.strategy_info.get('q_strategy_type', 1), return_q=True)
                continue
        input_params.update(self.strategy_info.get('fixed_params', {}))
        strategy_params = self.strategy_info.get('strategy_params', {})
        result = cgm.get_strategy(environment.organization, self.strategy_info['strategy_name'], input_params, **strategy_params)
        if result.get('slot'):
            result['is_end'] = 0
        return result
