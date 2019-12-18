#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
interactive_box_builder.py -- some builder of  interactive box

Author: maogy <maogy@guahao.com>
Create on 2018-10-04 Thursday.
"""

import re
from mednlp.dialog.configuration import Constant as constant
from mednlp.dialog.dialogue_util import build_age_sex_symptom_result


class InteractiveBoxBuilder(object):
    """
    交互框构建器.
    """

    def __init__(self, conf, **kwargs):
        """
        交互框构建器初始化函数.
        参数:
        conf->配置,格式:{'conf':[{'field':回传字段,'type':类型,1-单选框,2-复选框,3-文本框,'content':[]可选内容数组,无则需生成},]}
        """
        self.conf = conf
        self._parse_conf(conf)

    def _parse_conf(self, conf):
        if conf and conf.get('conf'):
            self.box_conf = conf['conf']


class InteractiveBoxBuilderDeptClassify(InteractiveBoxBuilder):
    """
    科室分诊交互框构建器.
    """

    field_dict = {
        'sex': 'isSex',
        'age': 'isAge'
    }

    def build(self, data):
        if data['is_end'] == 1:
            return None
        data = data['data']
        boxs = []
        cp_field = ['field', 'content', 'type']
        for conf in self.box_conf:
            # print('data:' + str(data))
            # print('conf:' + str(conf))
            if conf['field'] == 'symptom':
                if data['symptoms']:
                    box = {'field': 'symptom',
                           'content': data['symptoms'], 'type': 2}
                    boxs.append(box)
                    continue
            if data[self.field_dict[conf['field']]] == 1:
                if conf.get('content'):
                    box = {field: conf[field] for field in cp_field}
                    boxs.append(box)
        return boxs


class InteractiveBoxAIDeptClassify(InteractiveBoxBuilder):

    def __init__(self, conf, **kwargs):
        super(InteractiveBoxAIDeptClassify, self).__init__(conf)

    def build(self, data):
        box = []
        res_data = {}
        if data.get('ai_dept'):
            res_data = data['ai_dept']
        if res_data and res_data.get('isEnd') == 0:
            is_sex = res_data.get('isSex')
            is_age = res_data.get('isAge')
            symptoms = res_data.get('symptoms')
            if is_sex:
                sex_box = {}
                sex_box['field'] = 'sex'
                sex_box['type'] = 'single'
                sex_box['content'] = [0, 1, 2]
                sex_box['conf_id'] = 9998
                # 给answer构建器使用
                sex_box[constant.BOX_ANSWER] = {constant.ANSWER_FIELD_TEXT: '请输入您的性别'}
                box.append(sex_box)
            elif is_age:
                age_box = {}
                age_box['field'] = 'age'
                age_box['type'] = 'single'
                age_box['conf_id'] = 9997
                age_box[constant.BOX_ANSWER] = {constant.ANSWER_FIELD_TEXT: '请输入您的年龄'}
                box.append(age_box)
            elif symptoms:
                symptom_box = {}
                symptom_box['field'] = 'symptomName'
                symptom_box['content'] = symptoms
                symptom_box['type'] = 'multiple'
                symptom_box['conf_id'] = 9996
                symptom_box[constant.BOX_ANSWER] = {constant.ANSWER_FIELD_TEXT:
                                                        '请问您还有以下症状吗？请挑选出来哦~'}
                box.append(symptom_box)
        return box


class InteractiveBoxBuilderDB(object):
    """
    数据库配置的交互框构建器.
    """

    def __init__(self, conf, **kwargs):
        self.conf = conf
        self.conf_id = conf.get('conf_id', None)


class InteractiveBoxBuilderDBDeptClassify(InteractiveBoxBuilderDB):
    """
    科室分诊交互框构建器.
    """

    def build(self, data):
        if data['is_end'] == 1:
            return None
        data = data['data']
        boxs = []
        if data['isSex'] == 1:
            box = {'field': 'sex', 'content': ['男', '女'], 'type': 1,
                   'conf_id': self.conf_id}
            boxs.append(box)
        if data['isAge'] == 1:
            box = {'field': 'age', 'content': ['天'], 'type': 1,
                   'conf_id': self.conf_id}
            boxs.append(box)
        if data['symstoms']:
            box = {'field': 'symptom', 'content': data['symptoms'],
                   'type': 2, 'conf_id': self.conf_id}
            boxs.append(box)
        return boxs


class InteractiveBoxBuilderAutoDialogue(InteractiveBoxBuilder):
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
                    'past_medical_history': 'pastMedicalHistory',
                    'age': 'age',
                    'sex': 'sex'}

    def __init__(self, conf, **kwargs):
        super(InteractiveBoxBuilderAutoDialogue, self).__init__(conf)

    def build(self, data):
        boxs = []
        res_data = {}
        if data.get('auto_diagnose'):
            res_data = data.get('auto_diagnose')
        if not res_data.get("card_content") and res_data.get('card_type', '') in ('symptom'):
            symptomName = res_data.get('card_type', '')
            box_main = {}
            if symptomName == 'symptom':
                box_main['type'] = 'text'
                box_main['field'] = self.symptom_dict.get(symptomName)
            if box_main:
                boxs.append(box_main)
        if res_data.get("card_content"):
            card_content_list = res_data.get("card_content", [])
            for card_content in card_content_list:
                box_main = {}
                card_type = res_data.get('card_type', '')
                symptomName = card_type
                if card_type:
                    card_re = re.match(r'symptom\|(\w+)\|(\w+)', card_type, re.M | re.I)
                    if card_re:
                        symptomName = card_re.group(2)
                    box_main['field'] = self.symptom_dict.get(symptomName)
                if card_content.get("value"):
                    box_main['content'] = card_content.get("value")
                    if symptomName in ('time_happen', 'sex', 'frequence', 'degree'):
                        box_main['type'] = 'single'
                    else:
                        box_main['type'] = 'multiple'
                if card_content.get('attribute') and "mutex" in card_content.get('attribute'):
                    content_len = len(card_content.get("value"))
                    conflict_index = 0
                    conflict_list = []
                    if int(card_content.get('attribute').get("mutex")) < 0:
                        conflict_index = content_len + int(card_content.get('attribute').get("mutex"))
                    for i in range(content_len):
                        if i != conflict_index:
                            conflict_list_item = [i, conflict_index]
                            conflict_list.append(conflict_list_item)
                    box_main['conflict'] = conflict_list
                if card_content.get('attribute') and "need_input" in card_content.get('attribute'):
                    input_index = int(card_content.get('attribute').get('need_input'))
                    if input_index < 0:
                        input_index = len(card_content.get("value")) + input_index 
                    sub_box_key = card_content.get("value")[input_index]
                    box_1 = {}
                    box_1['type'] = 'text'
                    box_main['sub_box'] = {}
                    box_main['sub_box'][input_index] = box_1

                if symptomName in ('age'):
                    box_main['type'] = 'single'
                    for i in range(len(card_content.get("value"))):
                        box_1 = {}
                        box_1['type'] = 'text'
                        if not box_main.get('sub_box'):
                            box_main['sub_box'] = {}
                            box_main['sub_box'][i] = box_1
                        else:
                            box_main['sub_box'][i] = box_1
                if box_main:
                    boxs.append(box_main)
        return boxs


class InteractiveBoxGenerator(object):
    def build(self, data, **kwargs):
        result = []
        if data.get('slot'):
            result.extend(data['slot'])
        return result


class InteractiveBoxBuilderV2(object):
    # out_link 组装器,由active调用
    def __init__(self):
        pass

    def build(self, data, **kwargs):
        '''
        {'conf':[{'field':回传字段,'type':类型,1-单选框,2-复选框,3-文本框,'content':[]可选内容数组,无则需生成},]}
        :param data:
        :param intention_conf:
        :return:
        '''
        result = []
        if data.get(constant.QUERY_KEY_AI_DEPT) and 0 == data[constant.QUERY_KEY_AI_DEPT].get('isEnd', -1):
            # 代表科室分类需要填充数据
            box = InteractiveBoxAIDeptClassify({}).build(data)
            if box:
                result.append(box[0])
        return result


class InteractiveSkillRuleBuilder(object):
    # skill的交互框构建器
    def __init__(self):
        pass

    def build(self, data, result, **kwargs):
        interactive_box = data.get('interactiveBox')
        if interactive_box:
            result['interactive'] = interactive_box
        elif data.get('interactive'):
            result['interactive'] = data.get('interactive')
        return result


class InteractiveBoxBuilderV3(object):

    def __init__(self):
        pass

    @classmethod
    def generate(cls):
        result = cls()
        return result

    def build_3(self, data, environment):
        # 1. slot交互框构建
        result = {}
        slot = data.get('slot')
        if slot:
            result = build_age_sex_symptom_result(data)
            if not result and environment.intention in ('customerService',):
                # 客服意图交互框包装
                answer_code = slot[0]['answerCode']
                result['interactive'] = [{'answerCode': answer_code, 'options': slot}]
                if data.get('general_answer'):
                    result['answer'] = [{'code': answer_code, 'text': data.pop('general_answer')}]
            answer = result.pop('answer', None)
            if answer:
                data['answer'] = answer
        return result