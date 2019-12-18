#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dialog_manager.py -- the manager of dialog

Author: maogy <maogy@guahao.com>
Create on 2018-08-04 Saturday.
"""


from mednlp.dialog.slot import SymptomSlotManager, TreatmentSlotManager,\
    PreviousDiagnoseSlotManager, slot_manager_factory
import mednlp.dialog.process_handler as handler
import mednlp.dialog.dialog_constant as constant
from mednlp.utils.utils import distinct_list_dict


def print_list(data, flag):
    print('--------', flag, ' start-------')
    for temp in data:
        print(temp)
    if flag:
        print(flag, ' len = ', len(data))
    print('------', flag, ' end---------\n\n')


class PreviousDiagnoseDialog(object):
    """
    预问诊对话管理.
    """
    # 第三层treatment配置
    third_conf = {
        'manager': TreatmentSlotManager,
        'slot': [
            {'name': 'third_treatment_cost', 'ask': '请问治疗费用如何?', },
            {'name': 'third_treatment_place', 'ask': '请问在哪里治疗？'}
        ]
    }

    # 第二次treatment配置
    treatment_slot_conf = {
        'manager': TreatmentSlotManager,
        'slot': [
            {'name': 'treatment', 'ask': '请问做过哪些治疗？',
             # 'sub_slot': [{'condition': '针灸', 'conf': third_conf}]},
             #  {'name': 'treatment_degree', 'ask': '请问治疗到什么程度？'
             }
        ]
    }

    # 第二层symptom配置
    symptom_slot_conf = {
        'manager': SymptomSlotManager,
        'pre_handler': handler.symptom_create_pre_handler,
        'pre_handler_params': {constant.ATTR_DICTIONARY: constant.previous_dialog_dict, }
        # 'slot': [
        #     {'name': 'treatment', 'ask': '请问做过哪些治疗？',
        #      'sub_slot': [{'condition': '针灸', 'conf': test_conf}]},
        #     {'name': 'treatment_degree', 'ask': '请问治疗到什么程度？'}
        # ]
    }

    # 第一层配置
    diagnose_slot_conf = {
        'manager': PreviousDiagnoseSlotManager,
        'slot': [
            {'name': 'sex', 'ask': '请选择性别：',
             'content': [{'value': constant.CONTENT_VALUES_SEX}, ], },
            {'name': 'age', 'ask': '请输入年龄：',
             'content': [{'value': constant.CONTENT_VALUES_AGE,
                          constant.SLOT_ATTRIBUTE_FIELD: {constant.ATTR_DEFAULT: '0'}, }], },
            {'name': 'symptom', 'ask': '请输入症状，如“头晕”，“头晕，小腿痉挛”',
             'handler': handler.symptom_check_handler,
             'sub_slot': [{'conf': symptom_slot_conf}], },
            {'name': 'other_symptom', 'ask': '请问是否还有其他症状？',
             'post_handler': handler.other_symptom_post_handler, },
            {'name': 'is_treatment', 'ask': '请问是否做过治疗？',
             'content': [{'value': constant.CONTENT_GENERAL_VALUES_HAVE_OR_NOT}],
             'sub_slot': [{'condition': constant.OPTION_HAVE, 'conf': treatment_slot_conf}],
             },
            {'name': 'past_medical_history', 'ask': '请问是否有以下疾病史？',
             'text_handler': handler.general_text_handler,
             'content': [{'value': ['高血压', '糖尿病', '心脏病', '脑血管病', '外伤史',
                                    constant.OPTION_FUZZY_NOT, constant.OPTION_FUZZY_OTHER],
                          constant.SLOT_ATTRIBUTE_FIELD: {constant.ATTR_NEED_INPUT: '-1',
                                                          constant.ATTR_MUTEX: '-2'}, }], },
            {'name': 'allergic_history', 'ask': '请问是否有以下过敏史？',
             'text_handler': handler.general_text_handler,
             'content': [{'value': ['花粉过敏', '青霉素过敏', '红霉素过敏', '头孢类药物过敏', '乳制品过敏',
                                    constant.OPTION_FUZZY_NOT_KNOW, constant.OPTION_FUZZY_NOT,
                                    constant.OPTION_FUZZY_OTHER],
                          constant.SLOT_ATTRIBUTE_FIELD: {constant.ATTR_NEED_INPUT: '-1',
                                                          constant.ATTR_MUTEX: '-2,-3'}}], },
        ]}

    def __init__(self):
        pass

    def answer(self, dialogs, **kwargs):
        dialogs = distinct_list_dict(dialogs, key='key', order_key=constant.service_distinct_order)
        biz = kwargs[constant.BIZ_FIELD]
        diagnose_sm = slot_manager_factory.get_slot_manager(self.diagnose_slot_conf, biz=biz)
        filled_slots, blank_slots = diagnose_sm.fill_slot(dialogs, biz=biz)
        # print_list(filled_slots, 'filled_slots')
        # print_list(blank_slots, 'blank_slots')
        # result = {}
        if not blank_slots:
            slot_dict = constant.build_filled_slots_dict(filled_slots)
            result = diagnose_sm.build_answer(filled_slots, dialogs, slot_dict, biz=biz)
            result['answer'] = '感谢您的回答，已为您生成预问诊表单并提交医生啦~'
            result['card_type'] = 'medical_record'
        else:
            result = diagnose_sm.build_slot_answer(blank_slots, dialogs, biz=biz)
        return result


class AutoDiagnoseDialog(object):
    """
    自诊对话管理.
    """

    # 第二层symptom配置
    symptom_slot_conf = {
        'manager': SymptomSlotManager,
        'pre_handler': handler.symptom_create_pre_handler,
        'pre_handler_params': {constant.ATTR_DICTIONARY: constant.auto_dialog_dict,
                               # constant.ATTR_PER_SYMPTOM_MAX_COUNT: 3
                               # constant.ATTR_SYMPTOM_MAX_QUESTION_COUNT: 8
                               }
    }

    # 第一层配置
    diagnose_slot_conf = {
        'manager': PreviousDiagnoseSlotManager,
        'slot': [
            {'name': 'sex', 'ask': '请选择性别：',
             'content': [{'value': constant.CONTENT_VALUES_SEX}, ], },
            {'name': 'age', 'ask': '请输入年龄：',
             'content': [{'value': constant.CONTENT_VALUES_AGE,
                          constant.SLOT_ATTRIBUTE_FIELD: {constant.ATTR_DEFAULT: '0'}, }, ], },
            {'name': 'symptom', 'ask': '请输入症状，如“头晕”，“头晕，小腿痉挛”',
             'handler': handler.symptom_check_handler,
             'sub_slot': [{'conf': symptom_slot_conf}], },
            {'name': 'other_symptom', 'ask': '请问是否还有其他症状？',
             'post_handler': handler.other_symptom_post_handler,
             'text_handler': handler.other_symptom_text_handler},
            # {'name': 'past_medical_history', 'ask': '请问是否有以下疾病史？',
            #  'text_handler': handler.general_text_handler,
            #  'content': [{'value': ['高血压', '糖尿病', '心脏病', '脑血管病', '外伤史',
            #                         constant.OPTION_FUZZY_NOT, constant.OPTION_FUZZY_OTHER],
            #               constant.SLOT_ATTRIBUTE_FIELD: {constant.ATTR_NEED_INPUT: '-1',
            #                                               constant.ATTR_MUTEX: '-2'}}], },
        ]
    }

    def __init__(self):
        pass

    def answer(self, dialogs, **kwargs):
        dialogs = distinct_list_dict(dialogs, key='key', order_key=constant.service_distinct_order)
        # 自诊进度
        progress = float(kwargs.get('dialogue', {}).get('auto_diagnose_progress', 0))
        biz = kwargs[constant.BIZ_FIELD]
        terminate = kwargs[constant.BIZ_TERMINATE_FIELD]
        diagnose_sm = slot_manager_factory.get_slot_manager(self.diagnose_slot_conf, biz=biz)
        filled_slots, blank_slots = diagnose_sm.fill_slot(dialogs, biz=biz)
        # print_list(filled_slots, 'filled_slots')
        # print_list(blank_slots, 'blank_slots')
        # result = {}
        if (not blank_slots) or 1 == terminate:
            slot_dict = constant.build_filled_slots_dict(filled_slots)
            result = diagnose_sm.build_answer(filled_slots, dialogs, slot_dict, biz=biz)
            result['answer'] = '感谢您的回答，欢迎此次自诊体验~'
            result['card_type'] = 'medical_record'
            result.setdefault(constant.SLOT_EXTENDS, {})['auto_diagnose_progress'] = str(1)
            if terminate:
                # 代表用户强制中断返回结果
                result.setdefault(constant.SLOT_EXTENDS, {})[constant.BIZ_TERMINATE_FIELD] = 1
        else:
            result = diagnose_sm.build_slot_answer(blank_slots, dialogs, biz=biz)
            # 得到进度
            progress_now = handler.get_auto_diagnose_progress(dialogs, len(filled_slots), progress)
            result.setdefault(constant.SLOT_EXTENDS, {})['auto_diagnose_progress'] = str(float('%.2f' % progress_now))
        if biz == constant.BIZ_AUTO_DIAGNOSE and handler.is_valid_auto_diagnose(dialogs, result):
            result.setdefault(constant.SLOT_EXTENDS, {})['valid_auto_diagnose'] = 1
        return result




if __name__ == '__main__':
    request = [
        {'key': 'sex', 'value': ['男']},
        {'key': 'age', 'value': ['15天']},
        {'key': 'symptom', 'value': ['胸闷挂什么科']},
        # {'key': 'symptom|21b6f4052dec615d1ce267bbd1a06704|time_happen', 'value': ['1天以内']},
        # {'key': 'symptom', 'value': ['糖尿病,头痛']},
        # {"value": ["24天"], "key": "symptom|1477c572f4146bc86802957f4a93eda8|time_happen"},
        # {"value": ["全头部", "头顶部"], "key": "symptom|1477c572f4146bc86802957f4a93eda8|body_part"},
        # {"value": ["紧张或大量工作", "活动或情绪激动"], "key": "symptom|1477c572f4146bc86802957f4a93eda8|cause"},
        # {"value": ["反复"], "key": "symptom|1477c572f4146bc86802957f4a93eda8|frequence"},
        # {"value": ["中等"], "key": "symptom|1477c572f4146bc86802957f4a93eda8|degree"},
        # {"value": ["劳累后"], "key": "symptom|1477c572f4146bc86802957f4a93eda8|exacerbation"},
        # {"value": ["脚痛", '鼻血'], "key": "other_symptom"},
        # {"value": ["有"], "key": "is_treatment"},
        # {"value": ["我昨天没有去做了针灸，好舒服，然后进行了掏耳朵拔罐"], "key": "treatment"},
        # {"value": ["高血压","外伤史"], "key": "past_medical_history"},
        # {"value": ["以上都不是"], "key": "past_medical_history"},
        # {"value": ["花粉过敏", "青霉素过敏"], "key": "allergic_history"},
        # {"value": ["不清楚"], "key": "allergic_history"},
    ]
    # dialog = PreviousDiagnoseDialog()
    # answer = dialog.answer(request, biz=constant.BIZ_PRE_DIAGNOSE)
    dialog = AutoDiagnoseDialog()
    answer = dialog.answer(request, biz=constant.BIZ_AUTO_DIAGNOSE, terminate=0, dialogue={})
    print(answer)
    # 'auto_diagnose_progress': 0.29
