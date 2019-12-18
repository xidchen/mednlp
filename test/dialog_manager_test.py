#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.dialog_manager import PreviousDiagnoseDialog

from mednlp.dialog.slot import BaseSlotManager
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from mednlp.utils.comman_units import Encode
import json
import yaml
symptom_key = 'symptom'

aisc = AIServiceClient(global_conf.cfg_path, 'AIService')


# 症状核对
def symptom_check_handler(slot, dialogs):
    template_slots = {
        '1': {'name': 'symptom_%s_time', 'ask': '请问{%s}最早出现在什么时候?'},
        '2': {'name': 'symptom_%s_body', 'ask': '请问{%s}最早出现在什么部位?'},
        '3': {'name': 'symptom_%s_ease', 'ask': '请问{%s}在什么情况下会缓解?'},
        '4': {'name': 'symptom_%s_sense', 'ask': '请问{%s}在什么情况下出现?'},
        '5': {'name': 'symptom_%s_frequency', 'ask': '请问{%s}出现的频次符合以下哪种描述？?'},
        '6': {'name': 'symptom_%s_other_symptom', 'ask': '请问是否还有其他症状?'},
        '7': {'name': 'symptom_%s_description', 'ask': '请问{%s}符合以下哪种描述?'},
        '8': {'name': 'symptom_%s_aggravate', 'ask': '请问{%s}在什么情况下会加重?'},
    }
    source_data = {
        'F45272432E48E65DE040A8C00F017153': {
            'name': '失眠', 'key': 'symptom_F45272432E48E65DE040A8C00F017153',
            'conf': {
                'slot_code': ['1', '2', '3', '4']
            }
        }
    }
    symptom_value = ''
    symptom_index = -1
    # 识别出的实体
    entities = []
    for index, dialog_temp in enumerate(dialogs):
        if symptom_key == dialog_temp.get('key'):
            symptom_value = dialog_temp['value']
            symptom_index = index
            break
    # get symptom_dialog end
    # 调用命名实体识别,若无值,则返回filled_slot 和 blank_slot
    params = {'q': symptom_value}
    a = aisc.query(params, 'entity_extract')
    docs = a.get(u'data', [])
    for doc_temp in docs:
        if u'symptom' == doc_temp.get(u'type'):
            entities.append({ field: doc_temp[field] for field in [u'entity_name', u'entity_id'] if doc_temp.get(field)})
    if not entities:
        #  如果识别不出症状,则重置conf
        slot['conf'] = {
            'slot': [{'name': 'symptom', 'ask': '无法识别 [' + symptom_value + '] 请输入症状，如“头晕”，“头晕，小腿痉挛”：',
                     'style': {'type': 'text'}, }]}
        print('1')
    else:
        # 查询该症状的信息,拼装成conf
        entity_slots = []
        for entity_temp in entities:
            entity_id = entity_temp.get(u'entity_id')   # F45272432E48E65DE040A8C00F017153
            entity_name = entity_temp.get('entity_name')
            entity_source_data = source_data.get(entity_id)
            if not entity_source_data:
                continue
            entity_conf = entity_source_data.get('conf')        # 配置
            for slot_code_temp in entity_conf.get('slot_code', []):
                entity_slot = template_slots.get(slot_code_temp)
                entity_slot['name'] = entity_slot['name'] % (entity_id)
                entity_slot['ask'] = entity_slot['ask'] % (entity_name)
                entity_slots.append(entity_slot)
        slot['conf'] = entity_slots
        print('2')
        print(slot)
        # print(entities)
    print('finally')


def base_test(request):
    """
    基础测试
    :param request:
    :return: 输出相关问题
    """
    dialog = PreviousDiagnoseDialog()
    answer = dialog.answer(request)
    print('输出:\n', answer)

def test_sex():
    """
    测试性别sex
    :return: {'answer': '请选择性别：', 'card_type': 'sex'}
    """
    request = []
    base_test(request)


def test_symptom():
    """
    测试症状symptom
    :return: {'answer': '请输入症状，如“头晕”，“头晕，小腿痉挛”：', 'card_type': 'symptom'}
    """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},]
    base_test(request)


def test_symptom_headache_body():
    """
    测试头痛部位,动态生成
    :return: {'answer': '请问头痛部位？', 'card_type': 'symptom_headache_body'}
    """
    # 正常测试request
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},]
    # request的先后顺序打乱 情况
    # request = [{'key': 'sex', 'value': 3},
    #            {'key': 'age', 'value': 15},
    #            {'key': 'symptom', 'value': '头痛'},
    #            {'key': 'symptom_headache_degree', 'value': '一般'}]
    base_test(request)


def test_symptom_headache_degree():
    """
    测试头痛程度,动态生成
    :return: {'answer': '请问头痛到什么程度？', 'card_type': 'symptom_headache_degree'}
    """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'}]
    base_test(request)


def test_is_treatment():
    """
    测试是否治疗
    :return:{'answer': '请问是否做过治疗？', 'card_type': 'is_treatment'}
    """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},]
    base_test(request)


def test_treatment_false():
    """
    测试没有受过治疗，条件模式
    {'key': 'is_treatment', 'value': 2},] value = 1：才会调用TreatmentSlotManager
    :return: {'answer': '请问是否有以下疾病史？', 'card_type': 'past_medical_history'}
    """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 2},]
    base_test(request)


def test_treatment():
    """
        测试受过治疗，第二层sub_slot的第一个问题
        {'key': 'is_treatment', 'value': 1},] value = 1：才会调用TreatmentSlotManager
        :return: {'answer': '请问做过哪些治疗？', 'card_type': 'treatment'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1}, ]
    base_test(request)


def test_treatment_degree():
    """
        测试受过治疗，第二层sub_slot的第二个问题
        {'key': 'is_treatment', 'value': 1},] value = 1：才会调用TreatmentSlotManager
        :return: {'answer': '请问治疗到什么程度？', 'card_type': 'treatment_degree'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1},
               {'key': 'treatment', 'value': '针灸'},
               {'key': 'third_treatment', 'value': 'third'},
               {'key': 'third_treatment_degree', 'value': 'third_degree'},
               ]
    base_test(request)


def test_third_treatment():
    """
        测试受过治疗，第三层sub_slot的第一个问题
        {'name': 'treatment', 'value': 针灸},] value = 针灸：才会调用TreatmentSlotManager
        :return:  {'answer': '请问做过哪些third_treatment？', 'card_type': 'third_treatment'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1},
               {'key': 'treatment', 'value': '针灸'},
               ]
    base_test(request)


def test_third_treatment_degree():
    """
        测试受过治疗，第三层sub_slot的第二个问题
        {'name': 'treatment', 'value': 针灸},] value = 针灸：才会调用TreatmentSlotManager
        :return:  {'answer': '请问third_treatment到什么程度？', 'card_type': 'third_treatment_degree'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1},
               {'key': 'treatment', 'value': '针灸'},
               {'key': 'third_treatment', 'value': 'third'},
               ]
    base_test(request)


def test_past_medical_history():
    """
        测试疾病史，一种是 test_treatment_false，因为false，
        治疗的问题都不会提问，一种是true，并且以上问题都回答完毕
        :return:   {'answer': '请问是否有以下疾病史？', 'card_type': 'past_medical_history'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1},
               {'key': 'treatment', 'value': '针灸'},
               {'key': 'third_treatment', 'value': 'third'},
               {'key': 'third_treatment_degree', 'value': 'third_degree'},
               {'key': 'treatment_degree', 'value': '包治百病'},
               ]
    base_test(request)


def test_allergy():
    """
        测试过敏史
        :return:    {'answer': '请问是否有以下过敏史？', 'card_type': 'allergy'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1},
               {'key': 'treatment', 'value': '针灸'},
               {'key': 'third_treatment', 'value': 'third'},
               {'key': 'third_treatment_degree', 'value': 'third_degree'},
               {'key': 'treatment_degree', 'value': '包治百病'},
               {'key': 'past_medical_history', 'value': '糖尿病'}
               ]
    base_test(request)


def test_finally():
    """
        输出最后病历
        :return:     {'sex': 3, 'age': 15, 'symptom': '头痛',
        'symptom_headache_body': '右边头部', 'symptom_headache_degree': '一般',
        'is_treatment': 1, 'treatment': '针灸', 'third_treatment': 'third',
        'third_treatment_degree': 'third_degree', 'treatment_degree': '包治百病',
         'past_medical_history': '糖尿病', 'allergy': '青霉素',
         'answer': '感谢您的回答，已为您生成预问诊表单并提交医生啦~',
         'card_type': 'medical_record'}
        """
    request = [{'key': 'sex', 'value': 3},
               {'key': 'age', 'value': 15},
               {'key': 'symptom', 'value': '头痛'},
               {'key': 'symptom_headache_body', 'value': '右边头部'},
               {'key': 'symptom_headache_degree', 'value': '一般'},
               {'key': 'is_treatment', 'value': 1},
               {'key': 'treatment', 'value': '针灸'},
               {'key': 'third_treatment', 'value': 'third'},
               {'key': 'third_treatment_degree', 'value': 'third_degree'},
               {'key': 'treatment_degree', 'value': '包治百病'},
               {'key': 'past_medical_history', 'value': '糖尿病'},
               {'key': 'allergy', 'value': '青霉素'}
               ]
    base_test(request)



if __name__ == '__main__':
    # test_sex()            # 测试性别
    # test_symptom()        # 测试症状
    # test_symptom_headache_body()  # 测试头痛部位,动态生成
    # test_symptom_headache_degree() # 测试头痛程度,动态生成
    # test_is_treatment()   # 测试是否治疗
    # test_treatment_false()        # 测试没有受过治疗，条件模式
    # test_treatment()      # 测试受过治疗，第二层sub_slot的第一个问题
    # test_treatment_degree()   # 测试受过治疗，第二层sub_slot的第二个问题
    # test_third_treatment()    # 测试受过治疗，第三层sub_slot的第一个问题
    # test_third_treatment_degree() # 测试受过治疗，第三层sub_slot的第二个问题
    # test_past_medical_history()  # 测试疾病史，一种是 test_treatment_false，因为false，治疗的问题都不会提问，一种是true，并且以上问题都回答完毕
    # test_allergy()    # 测试过敏史
    # test_finally()  # 测试最后结束输出
    symptom_check_handler(BaseSlotManager(), [{'key': 'symptom', 'value': '失眠  15 头晕'}])
    pass

