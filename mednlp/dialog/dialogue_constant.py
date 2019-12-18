#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
常量类
"""
import json
import copy
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from mednlp.dialog.generator_manager.generator_manager import GeneratorManager
from ailib.storage.db import DBWrapper
import configparser
from ailib.utils.log import GLLog
from mednlp.utils.utils import read_config_info

cgm = GeneratorManager()
db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB', autocommit=True)
ai_sc = AIServiceClient(global_conf.cfg_path, 'AIService')
search_sc = AIServiceClient(global_conf.cfg_path, 'SearchService')
logger = GLLog('dialogue_service_input_output', level='info', log_dir=global_conf.log_dir).getLogger()

log_stat_dict = read_config_info(sections=['DataStatistics'])
stat_logger = GLLog('dialogue_service_stat', log_dir=log_stat_dict['DataStatistics']['log_dir'], level='info').getLogger()
stat_logger.info('dialogue_service_stat ok!!!')


def get_organization_dict():
    organization_dict = {}
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(global_conf.cfg_path)
    xwyz_organization = config.items('XwyzOrganization')[0][1]
    question_config_organization = config.items('XwyzOrganization')[1][1]
    xwyz_doctor_organization = config.items('XwyzDoctorOrganization')[0][1]
    organization_dict['xwyz'] = xwyz_organization
    organization_dict['xwyz_doctor'] = xwyz_doctor_organization
    organization_dict['question_config_organization'] = question_config_organization
    return organization_dict


class Constant(object):

    # 配置意图的相关属性
    UN_CREATE_INTENTION_ID = 'no_id'
    UN_CREATE_INTENTION_SET_ID = 'no_intention_set_id'

    INTENTION_KEYWORD = 'keyword'  # 关键词意图
    INTENTION_OTHER = 'other'  # 其他意图
    INTENTION_CORPUS_GREETING = 'corpusGreeting'
    INTENTION_GREETING = 'greeting'
    INTENTION_GUIDE = 'guide'
    INTENTION_CUSTOMER_SERVICE = 'customerService'
    INTENTION_AUTO_DIAGNOSE = 'auto_diagnose'
    INTENTION_DEPARTMENT_CONFIRM = 'departmentConfirm'
    INTENTION_DEPARTMENT_AMONG = 'departmentAmong'

    # 伴随意图
    accompany_intention_set = ['patient_group']

    # mode常量
    VALUE_MODE_AI_QA = 'ai_qa'
    VALUE_MODE_JD_BOX = 'loudspeaker_box'
    VALUE_MODE_XWYZ = 'xwyz'
    VALUE_MODE_XWYZ_DOCTOR = 'xwyz_doctor'
    # 门户包含 xwyz 和 xwyz_doctor
    VALUE_MODE_MENHU = (VALUE_MODE_XWYZ, VALUE_MODE_XWYZ_DOCTOR)

    # intention_conf ---start---
    out_link_dict_key = {
        '1': 'intention',
        '2': 'answer',
        '3': 'card'
    }

    keyword_dict_key = {
        '1': 'answer',
        '2': 'card',
        '3': 'out_link'
    }
    # intention_conf ---end---

    # q组装逻辑
    Q_TYPE_FIXED = 1  # 原来的输入
    Q_TYPE_ENTITY_ASSEMBLE = 2  # 实体组装

    q_default_params_set = ('symptom', 'disease', 'department', 'hospital',
                            'treatment', 'medicine', 'doctor', 'body_part',
                            'medical_word', 'examination')

    # generator
    GENERATOR_CARD_FLAG = 'card_flag'
    GENERATOR_CARD_FLAG_TOPIC = 'topic'  # 帖子
    GENERATOR_CARD_FLAG_HELP = 'help'  # 大家帮
    GENERATOR_CARD_FLAG_POST = 'post'  # 帖子 + 大家帮
    GENERATOR_CARD_FLAG_POST_BAIKE = 'post_baike'  # 帖子+大家帮+百科
    GENERATOR_CARD_FLAG_BAIKE = 'baike'  # 百科
    GENERATOR_CARD_FLAG_DOCTOR = 'doctor'  # 医生
    GENERATOR_CARD_FLAG_HOSPITAL = 'hospital'  # 医院
    GENERATOR_CARD_FLAG_DEPARTMENT = 'department'  # 科室
    GENERATOR_CARD_FLAG_QUESTION = 'question'  # 问句

    GENERATOR_EXTEND = 'extend'
    GENERATOR_EXTEND_SEARCH_PARAMS = 'search_params'
    GENERATOR_EXTEND_QUERY_CONTENT = 'query_content'
    GENERATOR_EXTEND_IS_CONSULT = 'is_consult'
    GENERATOR_AREA = 'area'

    CARD_FLAG_DICT = {
        'doctor': 1,
        'department': 2,
        'hospital': 3,
        'topic': 4,
        'help': 5,
        'post': 7,
        'post_baike': 8,
        'question': 9
    }

    # query 代表 request.body，是一个字符串
    QUERY_FIELD_ORIGIN_INPUT = 'origin_input'
    QUERY_FIELD_INPUT = 'input'
    QUERY_FIELD_MODE = 'mode'
    QUERY_FIELD_ORGANIZATION = 'organization'
    QUERY_FIELD_INPUT_PARAMS = 'input_params'
    QUERY_FIELD_DEL_KEYS = 'del_keys'
    QUERY_FIELD_DIALOGUE = 'dialogue'
    QUERY_FIELD_DIALOGUE_PREVIOUS_Q = 'previous_q'

    RESULT_FIELD_SEARCH_PARAMS = 'search_params'
    RESULT_FIELD_QUERY_CONTENT = 'query_content'
    RESULT_FIELD_SHOW_GUIDING = 'show_guiding'
    RESULT_FIELD_GREETING_NUM = 'greeting_num'

    deal_result_dict = {
        'is_end': 1,
        'isEnd': 1,
        'is_help': 0,
        'isHelp': 0
    }

    # query_result
    QUERY_KEY_AI_DEPT_XWYZ = 'ai_dept_xwyz'
    QUERY_KEY_AI_DEPT = 'ai_dept'  # 科室分类
    QUERY_KEY_DOCTOR_SEARCH = 'doctor_search'  # 医生搜索
    QUERY_KEY_DEPT_SEARCH = 'dept_search'  # 科室搜索
    QUERY_KEY_HOSPITAL_SEARCH = 'hospital_search'  # 医生搜索
    QUERY_KEY_POST_SEARCH = 'post_search'  # post查询
    QUERY_KEY_BAIKE_SEARCH = 'baike_search'  # 百科查询
    QUERY_KEY_GREETING = 'greeting'  # 先预料,再默认语句
    QUERY_KEY_GUIDE = 'guide'  # 默认语句
    QUERY_KEY_CUSTOMER_SERVICE = 'customerService'  # 客服意图

    QUERY_KEY_DEPARTMENT_CONFIRM_INFO = 'department_confirm_info'

    PROCESS_FIELD_CEIL_PROCESS_INFO = 'ceil_process_info'

    ENTITY_DEPARTMENT_CLASSIFY = 'department_classify'
    ENTITY_DEPARTMENT = 'department'

    department_classify_entity_transform_dict = {'id': 'department_id', 'name': 'department_name'}

    doctor_return_list = ['doctor_uuid', 'doctor_photo_absolute',
                          'doctor_name', 'doctor_technical_title',
                          'hospital_department_detail',
                          'specialty_disease', 'doctor_recent_haoyuan_detail',
                          'doctor_haoyuan_time', 'doctor_haoyuan_detail',
                          'is_service_package', 'is_health', 'sns_user_id',
                          'comment_score', 'total_order_count', 'is_patient_praise',
                          'base_rank', 'contract_register',
                          'is_consult_serviceable', 'doctor_introduction', 'feature',
                          'doctor_consult_detail', 'is_consult_phone', 'phone_consult_fee',
                          'serve_type', 'accurate_package_code', 'accurate_package_price'
                          ]

    hospital_return_list = ['hospital_uuid', 'hospital_name', 'hospital_level',
                            'hospital_photo_absolute', 'order_count',
                            'hospital_hot_department', 'distance_desc',
                            'hospital_rule', 'hospital_standard_department',
                            'hospital_department']

    post_return_list = ['topic_id', 'title', 'topic_content_nohtml',
                        'topic_nick_name', 'topic_technical_title',
                        'view_count', 'vote_count',
                        'title_highlight', 'topic_content_nohtml_highlight',
                        'nick_name', 'topic_type', 'content', 'content_highlight',
                        'help_show_type', 'technical_title_name',
                        'topic_vote_count', 'topic_view_count']

    doctor_fixed_params = {
        'start': '0',
        'rows': '18',
        # 'rows': '4',
        'do_spellcheck': '1',
        'travel': '0',
        'sort': 'general',
        'secondsort': '0',
        'aggr_field': 'contract_register',
        'opensource': '9',
        'fl': ','.join(copy.deepcopy(doctor_return_list))
    }

    hospital_fixed_params = {
        'rows': '3',
        'start': '0',
        'do_spellcheck': '1',
        'dynamic_filter': '1',
        'opensource': '9',
        'wait_time': 'all',
        'fl': ','.join(copy.deepcopy(hospital_return_list))
    }

    top_hospital_fixed_params = {
        'rows': '1',
        'start': '0',
        'do_spellcheck': '1',
        'dynamic_filter': '1',
        'opensource': '9',
        'wait_time': 'all',
        'haoyuan': '-1',
        'fl': ','.join(copy.deepcopy(hospital_return_list))
    }

    post_fixed_params = {
        'rows': '50',
        'start': '0',
        'sort': 'help_general',
        'topic_type': '1,3',
        'exclude_type': '2',
        'highlight': '1',
        'highlight_scene': '1',
        'exclude_post_heat_status': '1',
        'digest': '2',
        'fl': ','.join(copy.deepcopy(post_return_list))
    }

    organization_dict = get_organization_dict()

    # 引导语列表
    guiding_list = [{'list': [{'text': '头痛发烧'},
                              {'text': '失眠挂什么科'},
                              {'text': '骨科上海哪家医院好'},
                              {'text': '糖尿病哪位医生好'},
                              {'text': '哪个医院看颈椎病好'},
                              {'text': '幽门螺旋杆菌怎么治疗'},
                              {'text': '傅雯雯医生什么时候放号'},
                              {'text': '张平医生怎么样'},
                              ]},
                    {'title': '分科', 'list': [{'text': '头疼挂什么科'}],
                     'introduction': '告诉我症状，为您匹配对应的就诊科室'},
                    {'title': '选医院', 'list': [{'text': '上海肿瘤哪家医院好'}]},
                    {'title': '找医生', 'list': [{'text': '糖尿病哪位医生好'}]},
                    {'title': '查资讯', 'list': [{'text': '过敏性鼻炎注意事项'}, ]}
                    ]
