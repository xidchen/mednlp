#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
generator_manager.py -- the manager of generator and run strategy

Author: maogy <maogy@guahao.com>
Create on 2019-01-19 Saturday.
"""

from mednlp.dialog.generator_manager.full_code_config_strategy import FullCodeConfigStrategy
from mednlp.dialog.configuration import get_organization_dict, Constant as constant


class GeneratorManager(object):
    dzt_conf = {
        'symptom_relevant': {
            'strategy_name': 'full_code_conf',
            'card_type': constant.GENERATOR_CARD_FLAG_DEPARTMENT,
            'execute': [
                {
                    'generator': 'department_classify_interactive',
                    'input': ['q', 'confirm_patient_info', 'return_type'],
                    'output_card': ['department_id', 'department_name', 'accuracy'],
                }
            ]
        },
        'hospital': {
            'strategy_name': 'full_code_conf',
            'execute': [
                {
                    'generator': 'department_classify_interactive',
                    'input': ['sex', 'age', 'q'],
                    'output': ['department_name'],
                },
                {
                    'generator': 'hospital_search',
                    'input': ['department_name', 'city_id', 'province_id', 'sort', 'rows'],
                    'output_card': [
                        'hospital_id', 'hospital_name', 'photo',
                        'hospital_level', 'register_count', 'weiyi_rank',
                        'feature_department', 'distance_desc']
                }
            ]
        },
        'keyword_treatment': {
            'card_type': constant.GENERATOR_CARD_FLAG_POST_BAIKE,
            'strategy_name': 'full_code_conf',
            'execute': [
                {
                    'generator': 'sentence_similar',
                    'input': ['q', 'match_type', 'rows'],
                    'output': [constant.GENERATOR_EXTEND_SEARCH_PARAMS, constant.GENERATOR_EXTEND_QUERY_CONTENT],
                    'output_card': [
                        'topic_id', 'topic_type', 'topic_title', 'topic_title_highlight',
                        'topic_content_nohtml', 'topic_content_nohtml_highlight',
                        'post_content', 'post_content_highlight', 'topic_nick_name',
                        'topic_technical_title', 'topic_vote_count', 'topic_view_count',
                        'post_vote_count', 'post_view_count', 'post_nick_name',
                        'help_show_type', 'post_technical_title_name', constant.GENERATOR_CARD_FLAG
                    ]
                },
                {
                    'generator': 'baike_search',
                    'input': ['q', 'rows'],
                    'output_card': [
                        'word_id', 'word_name', 'word_name_highlight', 'word_introduction',
                        'word_type', 'card_flag'
                    ]
                }
            ]
        },
        'greeting': {
            'strategy_name': 'full_code_conf',
            'card_type': constant.GENERATOR_CARD_FLAG_QUESTION,
            'execute': [
                {
                    'generator': 'greeting',
                    'input': ['q', 'sort', 'customer_service_category', 'organization_code'],
                    'output': ['general_answer', 'match_type', 'standard_question_id'],
                    'output_card': ['question', 'question_type', constant.GENERATOR_CARD_FLAG]
                }
            ]
        },
        'find_doctor_doctor': {
            'strategy_name': 'full_code_conf',
            'card_type': constant.GENERATOR_CARD_FLAG_DOCTOR,
            'execute': [
                {
                    'generator': 'doctor_search',
                    'input': ['q', 'start', 'rows', 'sort',
                              'serve_type', 'is_public', 'hospital_level', 'doctor_title',
                              'std_dept_3d_haoyuan', 'is_doctor_on_rank', 'order_count_range',
                              'total_praise_rate_range', 'city_id', 'province_id', 'contract_price_range',
                              'consult_price_range', 'hospital_name', 'department_name',
                              'consult_service_type', 'extend_area'],
                    'output_card': ['service_package_id', 'recent_haoyuan_date', 'recent_haoyuan_time',
                                    'haoyuan_fee', 'haoyuan_remain_num', 'recent_haoyuan_refresh',
                                    'doctor_haoyuan_detail', 'hospital_name', 'department_name',
                                    'hospital_level', 'department_id', 'hospital_id',
                                    'hospital_province', 'doctor_name', 'doctor_id',
                                    'doctor_photo', 'doctor_technical_title',
                                    'specialty_disease', 'comment_score', 'is_health',
                                    'sns_user_id', 'total_order_count', 'is_patient_praise',
                                    'base_rank', 'contract_register', 'is_consult_serviceable',
                                    'doctor_introduction', 'feature', 'card_flag',
                                    'is_image_text', 'is_diagnosis', 'is_consult_phone',
                                    'lowest_consult_fee', 'highest_consult_fee', 'accurate_package',
                                    'accurate_package_price', 'accurate_package_code'],
                    'output': [constant.GENERATOR_EXTEND_SEARCH_PARAMS, constant.GENERATOR_EXTEND_IS_CONSULT,
                               constant.GENERATOR_AREA]
                }
            ]
        },
        'find_hospital_hospital': {
            'strategy_name': 'full_code_conf',
            'card_type': constant.GENERATOR_CARD_FLAG_HOSPITAL,
            'execute': [
                {
                    'generator': 'hospital_search',
                    'input': ['q', 'sort', 'start', 'rows', 'department_name',
                              'hospital_level', 'hospital_type', 'std_dept_3d_haoyuan',
                              'authority', 'order_count_range', 'praise_rate_range',
                              'city_id', 'province_id', 'longitude', 'latitude', 'extend_area',
                              'department_name'],
                    'output_card': ['hospital_id', 'hospital_name', 'hospital_photo_absolute',
                                    'hospital_level', 'order_count', 'hospital_hot_department',
                                    'distance_desc', 'hospital_rule',
                                    'conclude_department', 'authority', 'dept_standard_name',
                                    'dept_province_top_rank', 'dept_city_top_rank', 'dept_country_top_rank',
                                    'dept_city_name', 'dept_province_name', constant.GENERATOR_CARD_FLAG],
                    'output': [constant.GENERATOR_EXTEND_SEARCH_PARAMS, constant.GENERATOR_CARD_FLAG,
                               constant.GENERATOR_AREA]
                }
            ]
        },
        'department_classify_interactive': {
            'strategy_name': 'full_code_conf',
            'execute': [
                {
                    'generator': 'department_classify_interactive',
                    'input': ['sex', 'age', 'q', 'confirm_patient_info', 'symptom'],
                    'output_card': ['department_id', 'department_name']
                },
            ]
        }
    }
    merge_search_conf = {
        'keyword_symptom': {
            'strategy_name': 'full_code_conf',
            'card_type': constant.GENERATOR_CARD_FLAG_DEPARTMENT,
            'execute': [
                {
                    'generator': 'department_classify',
                    'input': ['q', 'level'],
                    'output_card': ['department_id', 'department_name', 'accuracy']
                }
            ]
        }
    }

    component_conf = {
        'department_classify_interactive': {    # 科室分类
            'strategy_name': 'full_code_conf',
            'execute': [
                {
                    'generator': 'department_classify_interactive',
                    'input': ['q', 'sex', 'age', 'level', 'symptom', 'confirm_patient_info', 'return_type'],
                    'output_card': ['department_id', 'department_name', 'accuracy']
                },
            ]
        }
    }
    conf = {
        '68a5364faca7422db4a28d422ae3bc2a': dzt_conf,
        'b96d4a21d9994eca8a6ff293d6558ce6': merge_search_conf,  # merge_search线上
        '0b8ed5e3c86949b09ed54534f56d7629': merge_search_conf   # merge_search线下
    }
    strategys = {
        'full_code_conf': FullCodeConfigStrategy
    }

    def __init__(self, **kwargs):
        organization_dict = get_organization_dict()
        self.conf[organization_dict[constant.VALUE_MODE_XWYZ]] = self.dzt_conf
        self.conf[organization_dict[constant.VALUE_MODE_XWYZ_DOCTOR]] = self.dzt_conf

    def get_strategy(self, organization, intention, input_obj, **kwargs):
        strategy_conf = self.conf[organization][intention]
        strategy_name = strategy_conf['strategy_name']
        strategy = self.strategys[strategy_name](strategy_conf)
        return strategy.run(input_obj, **kwargs)

    def get_strategy_by_name(self, strategy_conf_name, input_obj, **kwargs):
        # 处理器也可以有标准的输入和输出, 可直接调用生成器
        strategy_conf = self.component_conf[strategy_conf_name]
        strategy_name = strategy_conf['strategy_name']
        strategy = self.strategys[strategy_name](strategy_conf)
        return strategy.run(input_obj, **kwargs)

cgm = GeneratorManager()

if __name__ == '__main__':
    import json

    cgm = GeneratorManager()
    result = cgm.get_strategy('20e69819207b4b359f5f67a990454027', 'keyword_treatment', {'q': '头痛'})
    print(json.dumps(result, indent=True))
