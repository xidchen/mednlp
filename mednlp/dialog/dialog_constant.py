#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dialog_constant.py -- the constant of dialog
常量类,不进行处理
Author: renyx <renyx@guahao.com>
Create on 2018-08-21 Tuesday.
"""
import string
import global_conf
from ailib.utils.crypto_util import AesUtil
from ailib.client.ai_service_client import AIServiceClient
from mednlp.utils.utils import unicode2str
from ailib.utils.log import GLLog

aes_util = AesUtil('we__pre_diagnose', 16)  # key=we__pre_diagnose & ECB & zeropadding & 128位 & hex & utf-8
aisc = AIServiceClient(global_conf.cfg_path, 'AIService')


# 诊断参数字典
diagnose_params_dict = {
    'sex': {
        '男': 2,
        '女': 1
    }
}
# 日志生成 --start --
pre_diagnose_logger = GLLog('previous_diagnose_input_output', level='info',
                            log_dir=global_conf.log_dir).getLogger()
pre_diagnose_logger.info('previous_diagnose_input_output.log write successful !!!')

auto_diagnose_logger = GLLog('auto_diagnose_input_output', level='info',
                             log_dir=global_conf.log_dir).getLogger()
auto_diagnose_logger.info('auto_diagnose_input_output.log write successful !!!')
# 日志生成 --end --

en_punctuation = set(string.punctuation)
cn_punctuation = {',', '?', '、', '。', '“', '”', '《', '》', '！', '，', '：', '；', '？', '（', '）', '【', '】'}
punctuation = unicode2str(list(en_punctuation | cn_punctuation))

# service
service_distinct_order = 'distinct_order'

# ---slot相关字段 start---
# pre_handler > handler > post_handler
SLOT_NAME_FIELD = 'name'
SLOT_VALUE_FIELD = 'value'
SLOT_ASK_FIELD = 'ask'
SLOT_CONTENT_FIELD = 'content'
SLOT_ATTRIBUTE_FIELD = 'attribute'
SLOT_SUB_SLOT_FIELD = 'sub_slot'
SLOT_HANDLER_FIELD = 'handler'
SLOT_PRE_HANDLER_FIELD = 'pre_handler'
SLOT_PRE_HANDLER_PARAMS_FIELD = 'pre_handler_params'
SLOT_POST_HANDLER_FIELD = 'post_handler'
SLOT_TEXT_HANDLER_FIELD = 'text_handler'    # 文本处理
SLOT_CONDITION_FIELD = 'condition'  # 主问题的value为condition,则用其对应的conf
SLOT_CONF_FIELD = 'conf'
SLOT_SUB_MANAGER_FIELD = 'sub_manager'
SLOT_EXTENDS = 'extends'
SLOT_FLAG_FIELD = 'flag'
SLOT_FLAG_AGAIN = '1'  # 再次
# ---slot相关字段 end---

# ---属性相关字段 start ---
ATTR_DICTIONARY = 'dictionary'
ATTR_PER_SYMPTOM_MAX_COUNT = 'per_symptom_max_count'  # 每个症状最大问题数
ATTR_SYMPTOM_MAX_QUESTION_COUNT = 'symptom_question_max_count'  # 所有症状最大轮数
ATTR_NEED_INPUT = 'need_input'
ATTR_DEFAULT = 'default'
ATTR_MUTEX = 'mutex'

# ---属性相关字段 end ---

symptom_key = 'symptom'

# dialog
DIALOG_ORG_VALUE = 'org_value'

# ---业务表示字段 start
BIZ_FIELD = 'biz'
BIZ_TERMINATE_FIELD = 'terminate'
BIZ_DIALOGS = 'dialogs'
BIZ_LOGGER_FIELD = 'logger'
# 有些东西需要区分哪些是预问诊，哪些是自诊，现在所有常量都在constant里配置，然后根据标识区分需要各自的logger
BIZ_PRE_DIAGNOSE = 1    # 预问诊标识
BIZ_AUTO_DIAGNOSE = 2   # 自诊标识
DIAGNOSE_FL = 'diagnose_fl'
DIAGNOSE_PARAMS_FL = 'diagnose_params_fl'
DIAGNOSE_SOURCE = '10000'

BIZ_DICT = {
    BIZ_PRE_DIAGNOSE: {
        BIZ_LOGGER_FIELD: pre_diagnose_logger,
        'name': 'pre',
        DIAGNOSE_FL: {'disease_id': 'disease_id', 'disease_name': 'disease_name'}
    },
    BIZ_AUTO_DIAGNOSE: {
        BIZ_LOGGER_FIELD: auto_diagnose_logger,
        'name': 'auto',
        DIAGNOSE_FL: {'disease_id': 'disease_id', 'disease_name': 'disease_name',
                      'score': 'score', 'department': 'department', 'advice_code': 'advice',
                      'symptom_detail': 'symptom_detail'},
        DIAGNOSE_PARAMS_FL: 'department,advice_code,symptom_detail'
    }
}
# 诊断建议字典映射
DIAGNOSE_ADVICE_DICT = {
    '10': '非紧急',
    '20': '非紧急',
    '30': '紧急'
}
# ---业务表示字段 end

# --exception 模板 start --
# [symptom_check_handler]的[entity_extra]异常,params: json串
EXCEPTION_REMOTE = '[%s]的[%s]异常,params: %s'
# --exception 模板 end --

# ---选项区域 start---
# 性别选项词
OPTION_SEX_MALE = '男'
OPTION_SEX_FEMALE = '女'

# 时间相关备选项
OPTION_TIME_HOUR_INTERVAL = '小时'     # 小时间隔
OPTION_TIME_DAY = '天'
OPTION_TIME_MONTH = '月'
OPTION_TIME_YEAR = '年'
OPTION_TIME_YEAR_OF_AGE = '岁'

# 模糊词
OPTION_FUZZY_OTHER = '其他'
OPTION_FUZZY_NOT_ALL = '以上都不是'
OPTION_FUZZY_NOT_KNOW = '不清楚'
OPTION_FUZZY_NOT = '无'
OPTION_FUZZY_NO_CAUSE = '不明原因'
OPTION_FUZZY_NO_FACTORY = '不明因素'

OPTION_HAVE = '有'
OPTION_NOT_HAVE = '无'

# 内容性别值
CONTENT_VALUES_SEX = [OPTION_SEX_MALE, OPTION_SEX_FEMALE]   # 性别
CONTENT_VALUES_AGE = [OPTION_TIME_YEAR_OF_AGE, OPTION_TIME_MONTH, OPTION_TIME_DAY]  # 年龄
CONTENT_VALUES_OTHER_SYMPTOM = [OPTION_FUZZY_NOT, OPTION_FUZZY_OTHER]   # 其他症状
CONTENT_GENERAL_VALUES_HAVE_OR_NOT = [OPTION_HAVE, OPTION_NOT_HAVE]  # 通用有无
# ---选项区域 end---


def load_dict(file_name):
    # 发烧;time|1天,1周,1月|{%s}持续多久;degree|37,38,39,39以上|{%s}多少度
    # file_name = global_conf.dialog_data_path
    result = {}
    with open(file_name) as f:
        for line in f:
            if line and line[-1:] == '\n':
                line = line[:-1]
            info = line.split('@')
            symptom_id = aes_util.encrypt(info[0])
            questions = []
            for question_temp in info[1:]:
                question_option = question_temp.split('|')  # time|请问发烧持续多久了?|1天#1周#1月  name | ask | value
                name = 'symptom|%s|%s' % (symptom_id, question_option[0])   # 名字
                ask = question_option[1]        # 问题
                question_dict = {SLOT_NAME_FIELD: name, SLOT_ASK_FIELD: ask}
                # content 值
                question_content_dict = {}
                if question_option[2]:
                    content = question_option[2].split('#')  # 内容 1天#1周#1月   'content': [{'value': ['岁', '月', '天']}]
                    question_content_dict[SLOT_VALUE_FIELD] = content
                if question_option[3]:
                    question_attr = question_option[3].split('#')
                    question_attr_dict = {}
                    for temp in question_attr:
                        if temp:
                            attr_key, attr_value = temp.split(':')
                            question_attr_dict[attr_key] = attr_value
                    question_content_dict[SLOT_ATTRIBUTE_FIELD] = question_attr_dict
                if question_content_dict:
                    question_dict[SLOT_CONTENT_FIELD] = [question_content_dict]
                questions.append(question_dict)
            result[unicode2str(info[0])] = questions
    return result


def load_exclude_symptom(file_name):
    result = set()
    with open(file_name) as f:
        for line in f:
            if not line:
                continue
            symptom = line.strip()
            result.add(symptom)
    return result


def build_filled_slots_dict(slots):
    """
    构建槽字典
    """
    slot_dict = {}
    for slot in slots:
        slot_dict[slot[SLOT_NAME_FIELD]] = slot
    return slot_dict


# 加载字典
previous_dialog_dict = load_dict(global_conf.dialog_data_path)  # 预问诊
auto_dialog_dict = load_dict(global_conf.auto_data_path)  # 自诊
exclude_symptom_dict = load_exclude_symptom(global_conf.exclude_auto_diagnose_symptom)
