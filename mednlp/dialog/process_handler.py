#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
process_handler.py -- handler类
pre_handler,handler,post_handler等方法,主要在填槽过程中的动态处理
Author: renyx <renyx@guahao.com>
Create on 2018-08-10 Friday.
"""
import sys
import json
from mednlp.dialog.slot import BaseSlotManager
from copy import deepcopy
from mednlp.utils.utils import unicode2str
import mednlp.dialog.dialog_constant as constant
from mednlp.dialog.dialog_deal import deal_diagnose_service_age, deal_other_symptom_mutex
import traceback
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')


previous_slots = [
    {'name': 'symptom|%s|time_happen', 'ask': '请问{%s}最早出现在什么时候?',
     'content': [{'value': ['小时', '天', '月', '年']}]},
]

auto_slots = [
    {'name': 'symptom|%s|time_happen', 'ask': '请问{%s}持续多久了?',
     'content': [{'value': ['1天以内', '1天-1周', '1周-1月', '1月-半年', '半年-1年', '1年以上']}]},
]


def symptom_create_pre_handler(slot_manager, dialogs, **kwargs):
    """
    创建症状子问题的预处理器
    :param slot_manager:
    :param dialogs:
    :param kwargs:
    :return:
    """
    biz = kwargs[constant.BIZ_FIELD]
    logger = constant.BIZ_DICT[biz][constant.BIZ_LOGGER_FIELD]
    # 识别出的实体
    entities = []
    entity_slots = []
    symptom_value = []
    symptom_index = -1
    dictionary = kwargs.get(constant.ATTR_DICTIONARY)   # 字典
    per_symptom_max_count = kwargs.get(constant.ATTR_PER_SYMPTOM_MAX_COUNT, 100)  # 每个症状最大数量,保底写死100
    # 所有症状最大轮数
    symptom_question_max_count = kwargs.get(constant.ATTR_SYMPTOM_MAX_QUESTION_COUNT, 100)
    for index, dialog_temp in enumerate(dialogs):
        if constant.symptom_key == dialog_temp.get('key'):
            symptom_value = dialog_temp['value']
            symptom_index = index
            break
    # get symptom_dialog end
    params = {}
    try:
        params = {'q': symptom_value[0]}
        entity_extract_result = constant.aisc.query(params, 'entity_extract')
    except Exception as err:
        logger.exception(err)
        logger.error(constant.EXCEPTION_REMOTE % (
            'symptom_create_pre_handler', 'entity_extract', json.dumps(params, ensure_ascii=False)))
        raise Exception('症状预处理异常')
    docs = entity_extract_result.get('data', [])
    for doc_temp in docs:
        if 'symptom' == doc_temp.get('type') and doc_temp.get(
                'entity_name') and doc_temp['entity_name'] not in constant.exclude_symptom_dict:
            entities.append(doc_temp.get('entity_name'))
    # get entity end
    for entity_temp in entities:     # 失眠(has), 胃疼
        entity_name = entity_temp
        entity_data = dictionary.get(entity_name)
        if entity_data:
            # 图谱里有
            entity_slots.extend(dictionary.get(entity_name)[:per_symptom_max_count])
        else:
            # 图谱里无
            default_slots = previous_slots
            # default_slots默认已预问诊为主，若是自诊，切换成自诊的默认slot,自诊总轮数不超过12轮，因此症状最多9轮
            if biz == constant.BIZ_AUTO_DIAGNOSE:
                default_slots = auto_slots
            for entity_slot_temp in default_slots:
                entity_slot = deepcopy(entity_slot_temp)
                entity_slot['name'] = entity_slot['name'] % constant.aes_util.encrypt(entity_name)
                entity_slot['ask'] = entity_slot['ask'] % entity_name
                entity_slots.append(entity_slot)
    slot_manager.conf['slot'] = entity_slots[:symptom_question_max_count]
    dialogs[symptom_index]['symptom_slot_count'] = len(slot_manager.conf['slot'])


def symptom_check_handler(slot, dialogs, **kwargs):
    """
    症状核对处理器
    :param slot:
    :param dialogs:
    :return:
    """
    biz = kwargs[constant.BIZ_FIELD]
    logger = constant.BIZ_DICT[biz][constant.BIZ_LOGGER_FIELD]
    symptom_value = []
    symptom_index = -1
    # 识别出的实体
    entities = []
    for index, dialog_temp in enumerate(dialogs):
        if constant.symptom_key == dialog_temp.get('key'):
            symptom_value = dialog_temp['value']
            symptom_index = index
            break
    # get symptom_dialog end
    params = {}
    try:
        params = {'q': symptom_value[0]}
        entity_extract_result = constant.aisc.query(params, 'entity_extract')
    except Exception as err:
        # 添加log,抛出异常
        logger.exception(err)
        logger.error(constant.EXCEPTION_REMOTE % (
            'symptom_check_handler', 'entity_extract', json.dumps(params)))
        raise Exception('症状核对异常')
    docs = entity_extract_result.get('data', [])
    for doc_temp in docs:
        if 'symptom' == doc_temp.get('type') and doc_temp.get(
                'entity_name') and doc_temp['entity_name'] not in constant.exclude_symptom_dict:
            entities.append(doc_temp.get('entity_name'))
    # alter dialogs
    if not entities:
        slot[constant.SLOT_ASK_FIELD] =\
            '无法识别 [' + symptom_value[0] + '] 请输入症状如“头晕”，“头晕，小腿痉挛”：'
        slot.setdefault(constant.SLOT_EXTENDS, {})[constant.SLOT_FLAG_FIELD] = constant.SLOT_FLAG_AGAIN
        slot.pop('value', None)
        return False
    else:
        # 修正后的症状词
        dialogs[symptom_index][constant.DIALOG_ORG_VALUE] = dialogs[symptom_index]['value']
        dialogs[symptom_index]['value'] = [' '.join(entities)]
    return True


def default_post_handler(filled_slots, slots, dialogs, **kwargs):
    del slots[0]


def other_symptom_post_handler(filled_slots, slots, dialogs, **kwargs):
    """
    其他症状后置处理器
      1.若other_symptom有值,则跳过此问题
      2.获取key=symptom的值，拼装成主诉，现病史，请求诊断服务，显示第一个疾病的相关症状
      3.若请求失败或者无相关症状，则跳过 其他症状  这个问题
    :param filled_slots: 已有答案的slots
    :param slots: 空白slots
    :param dialogs: 对话信息
    :return:
    """
    biz = kwargs[constant.BIZ_FIELD]
    logger = constant.BIZ_DICT[biz][constant.BIZ_LOGGER_FIELD]
    # 进入post_handler，都是slots有值,对slots[0]进行处理
    slot = slots[0]
    slot_dict = constant.build_filled_slots_dict(filled_slots)
    symptom_slot = slot_dict.get('symptom')
    if not symptom_slot:
        raise Exception('其他症状无symptom异常')
    # 症状值
    symptom_value = unicode2str(symptom_slot.get('value'))
    diagnose_fields = {'age': 'age',
                       'sex': 'sex',
                       'diagnose_chief_complaint': 'chief_complaint',  # 主诉
                       # 'chief_complaint': 'chief_complaint',  # 主诉
                       'medical_history': 'medical_history',  # 现病史
                       }
    params = {
        'rows': 1,
        'mode': 0,
        'fl': 'symptom_detail',
        'source': constant.DIAGNOSE_SOURCE
    }
    # 诊断疾病结果
    diagnose_symptom = []
    try:
        answer = symptom_slot.get(constant.SLOT_SUB_MANAGER_FIELD).build_answer(slots, dialogs, slot_dict, biz=biz)
        for answer_field, diagnose_field in diagnose_fields.items():
            # 1.来源为slot_dict, 结构是dict {'age': {'value': []}}
            diagnose_slot_temp = slot_dict.get(answer_field)
            # 2.来源为symptom的answer,结构是dict {'chief_complaint':'chief_complaint values'}
            answer_temp = answer.get(answer_field)
            if diagnose_slot_temp and diagnose_slot_temp.get(constant.SLOT_VALUE_FIELD):
                if 'age' == answer_field:
                    params[diagnose_field] = deal_diagnose_service_age(
                        unicode2str(diagnose_slot_temp['value'][0]), biz=biz)
                elif 'sex' == answer_field:
                    params[diagnose_field] = constant.diagnose_params_dict['sex'].get(
                        unicode2str(diagnose_slot_temp['value'][0]))
                else:
                    params[diagnose_field] = ' '.join(diagnose_slot_temp[constant.SLOT_VALUE_FIELD])
            elif answer_temp:
                params[diagnose_field] = unicode2str(answer_temp)
        diagnose_query = constant.aisc.query(params, 'diagnose_service', method='get')
        if diagnose_query and diagnose_query.get('data') and diagnose_query['data'][0].get('symptom_detail'):
            diagnose_symptom = unicode2str([symptom_detail_temp.split(
                '|')[1] for symptom_detail_temp in diagnose_query['data'][0]['symptom_detail']])
    except Exception as err:
        # 打印日志,不抛出异常
        logger.exception(err)
        logger.error(constant.EXCEPTION_REMOTE % (
            'other_symptom_post_handler', 'diagnose_service', json.dumps(params)))
    # get 伴随症状，去除互包含的症状选项
    diagnose_symptom = deal_other_symptom_mutex(symptom_value, diagnose_symptom, biz=biz)
    if diagnose_symptom:
        slot['content'] = [{'value': diagnose_symptom[:4] + constant.CONTENT_VALUES_OTHER_SYMPTOM,
                            constant.SLOT_ATTRIBUTE_FIELD: {constant.ATTR_NEED_INPUT: '-1',
                                                            constant.ATTR_MUTEX: '-2'}}]
    else:
        # 日志
        del slots[0]

def is_valid_auto_diagnose(dialogs, result):
    """
    1.没有症状词 返回False
    2.字典里没有该症状词,返回False
    :param dialogs:
    :param result:
    :return:
    """
    result = True
    symptom_input = None
    entities = []
    for temp in dialogs:
        if temp.get('key') == 'symptom':
            symptom_input = temp
            break
    if symptom_input:
        symptom_value = symptom_input.get(constant.SLOT_VALUE_FIELD)
        try:
            params = {'q': symptom_value[0]}
            entity_extract_result = constant.aisc.query(params, 'entity_extract')
            docs = entity_extract_result.get('data', [])
            for doc_temp in docs:
                if 'symptom' == doc_temp.get('type') and doc_temp.get(
                        'entity_name') and doc_temp['entity_name'] not in constant.exclude_symptom_dict:
                    entities.append(doc_temp.get('entity_name'))
        except Exception as err:
            traceback.print_exception()
    if not entities:
        result = False
        return result
    for temp in entities:
        # 所有实体里,有一个症状词有问句规则，就表示有效
        result = False
        if constant.auto_dialog_dict.get(temp):
            result = True
            break
    return result


def get_auto_diagnose_progress(dialogs, filled_slots_count, progress):
    # 得到进度
    count = 4  # 总的问题数
    if progress > 1:
        progress = 0
    symptom_input = None
    symptom_slot_count = 0
    for temp in dialogs:
        if temp.get('key') == 'symptom':
            symptom_input = temp
            break
    if symptom_input:
        symptom_slot_count = symptom_input.get('symptom_slot_count', 0)
    if not symptom_slot_count:
        symptom_slot_count = 4
    count += symptom_slot_count
    fill_slot_count = float(filled_slots_count)  # 已填槽数
    process_now = fill_slot_count / float(count)  # 当前进度
    if process_now >= 1:
        process_now = progress
    if process_now < progress:
        if progress + 0.1 < 1:
            process_now +=0.1
        else:
            process_now = progress
    return process_now


def general_text_handler(values, **kwargs):
    """
    通用文本处理器
    若文本中出现[以上都不是,不清楚],返回None
    """
    if len(set(unicode2str(values)).intersection(
            set(unicode2str([constant.OPTION_FUZZY_NOT_ALL])))) > 0:
        return ['无']
    return values


def other_symptom_text_handler(values, **kwargs):
    # 伴随症状文本处理
    orig_answer = kwargs['orig_answer']
    biz = kwargs['biz']
    medical_history = orig_answer.get('medical_history', '')
    # 仅在自诊的时候,现病史加入伴随症状
    if values and constant.BIZ_AUTO_DIAGNOSE == biz:
        medical_history_temp = medical_history + '有相关伴随症状：' + '、'.join(values)
        if medical_history_temp[-1] not in constant.punctuation:
            medical_history_temp += '。'
            orig_answer['medical_history'] = medical_history_temp
    return values


if __name__ == '__main__':
    symptom_check_handler(BaseSlotManager(), [{'key': 'symptom', 'value': '失眠 15 头痛'}])
    pass
