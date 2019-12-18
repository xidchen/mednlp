#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import json

ComponentConfig = {
    'card': [
        {
            'intention': ['content'],
            'config': {
                'card_id': 100000,
                'card_num': 1,
                'content': ['word_id', 'name', 'introduction', 'name_highlight', 'type'],
                'type': 6
            }
        }
    ]
}

ModeIntention = {
    'mode': {
        'xwyz': {
            'sub_intention_set': [
                'auto_diagnose',
                'other',
                'keyword_city',
                'keyword_province',
                'keyword_body_part',
                'keyword_examination',
                'keyword_medical_word'
            ]
        },
        'xwyz_doctor': {
            'sub_intention_set': [
                'auto_diagnose',
                'other',
                'keyword_city',
                'keyword_province',
                'keyword_body_part',
                'keyword_examination',
                'keyword_medical_word'
            ]
        }
    }
}
# 共27个字段+1
xwyz_doctor_fields = [
    'doctor_uuid', 'doctor_photo_absolute', 'doctor_name', 'doctor_technical_title',
    'specialty_disease', 'comment_score', 'is_health', 'sns_user_id',
    'total_order_count', 'is_patient_praise', 'base_rank', 'recent_haoyuan_date',
    'recent_haoyuan_time', 'haoyuan_fee', 'haoyuan_remain_num', 'haoyuan_remain_num',
    'doctor_haoyuan_detail', 'service_package_id', 'hospital_uuid', 'hospital_name',
    'department_name', 'hospital_level', 'department_uuid', 'hospital_province',
    'contract_register', 'is_consult_serviceable', 'doctor_introduction', 'feature',
    'is_image_text', 'is_diagnosis', 'is_consult_phone', 'lowest_consult_fee',
    'highest_consult_fee', 'accurate_package', 'accurate_package_price', 'accurate_package_code'
]

ModeCard = {
    'xwyz': [
        {
            'intention': ['departmentConfirm', 'departmentAmong', 'departmentSubset', 'auto_diagnose'],
            'config': {
                'card_id': '11_departmentConfirm_doctor_no_card_id',
                'card_num': '18',
                'type': 1,
                'content': xwyz_doctor_fields
            }
        },
        {
            'intention': ['department'],
            'config': {
                'card_id': '13_department_no_card_id',
                'card_num': '2',
                'type': 2,
                'content': ['accuracy', 'department_name',
                            'common_disease', 'introduction', 'department_uuid']
            }
        },
        {
            'intention': ['keyword_symptom', 'keyword_treatment', 'keyword_medicine',
                          'keyword_city', 'keyword_province', 'keyword_body_part'],
            'config': {
                'card_id': '14_keyword_treatment_topic_no_card_id',
                'card_num': '1',
                'type': 4,
                'content': ['topic_id', 'topic_type', 'topic_title', 'topic_title_highlight',
                            'topic_content_nohtml', 'topic_content_nohtml_highlight',
                            'post_content', 'post_content_highlight', 'topic_nick_name',
                            'topic_technical_title', 'topic_vote_count', 'topic_view_count',
                            'post_vote_count', 'post_view_count', 'post_nick_name',
                            'help_show_type', 'post_technical_title_name']
            }
        },
        {
            'intention': ['doctor'],
            'config': {
                'card_id': '13_doctor_no_card_id',
                'card_num': '18',
                'type': 1,
                'content': xwyz_doctor_fields
            }
        }
    ],
    'xwyz_doctor': [
        {
            'intention': ['departmentConfirm', 'departmentAmong', 'departmentSubset', 'auto_diagnose'],
            'config': {
                'card_id': '11_departmentConfirm_doctor_no_card_id',
                'card_num': '18',
                'type': 1,
                'content': xwyz_doctor_fields
            }
        },
        {
            'intention': ['department'],
            'config': {
                'card_id': '13_department_no_card_id',
                'card_num': '2',
                'type': 2,
                'content': ['accuracy', 'department_name',
                            'common_disease', 'introduction', 'department_uuid']
            }
        },
        {
            'intention': ['keyword_symptom', 'keyword_treatment', 'keyword_medicine',
                          'keyword_city', 'keyword_province', 'keyword_body_part'],
            'config': {
                'card_id': '14_keyword_treatment_topic_no_card_id',
                'card_num': '1',
                'type': 4,
                'content': ['topic_id', 'topic_type', 'topic_title', 'topic_title_highlight',
                            'topic_content_nohtml', 'topic_content_nohtml_highlight',
                            'post_content', 'post_content_highlight', 'topic_nick_name',
                            'topic_technical_title', 'topic_vote_count', 'topic_view_count',
                            'post_vote_count', 'post_view_count', 'post_nick_name',
                            'help_show_type', 'post_technical_title_name']
            }
        },
        {
            'intention': ['doctor'],
            'config': {
                'card_id': '13_doctor_no_card_id',
                'card_num': '18',
                'type': 1,
                'content': xwyz_doctor_fields
                }
        }
    ]
}

ModeAnswer = {
    'xwyz': [
        {
            'intention': ['departmentConfirm', 'departmentAmong', 'departmentSubset', 'department'],
            'config': [
                {
                    'answer_id': None,
                    'intention_set_id': None,
                    'text': '为您推荐以下科室',
                    'type': '1'
                }
            ]
        }
    ]
}
# 问诊自定义按钮
consult_out_link = {
    'id': 'no_consult_id',
    'name': '去问诊',
    'text': 'q=%s',
    'action': 1,
    'type': 4
}

# 踩和赞的按钮
satisfy_out_link = {
    'id': 'satisfy_id',
    'name': '踩/赞',
    'type': 3,
    'text': ''
}

# 有效自诊按钮
valid_auto_diagnose_out_link = {
    'id': 'valid_auto_diagnose',
    'name': '疾病自诊',
    'type': '4',
    'text': ''
}

departmentNameAnswerKeyword = {'id': 'departmentName', 'type': '2', 'text': ''}
confirmAnswerKeywod = {'id': 'confirm', 'type': '2', 'text': ''}
amongAnswerKeywod = {'id': 'among', 'type': '2', 'text': ''}
accuracyAnswerKeywod = {'id': 'accuracy', 'type': '2', 'text': ''}
queryContentAnswerKeywod = {'id': 'query_content', 'type': '2', 'text': ''}
areaAnswerKeyword = {'id': 'area', 'type': '2', 'text': ''}

ModeKeyword = {
    'xwyz': [
        {
            'intention': ['departmentConfirm', 'departmentAmong', 'departmentSubset', 'department'],
            'config': [
                {
                    'ai_field': '',
                    'biz_id': '',
                    'intention_set_id': '',
                    'relation': '1',
                    'text': ''
                }
            ]
        }
    ]
}

ModeOutlink = {
    'xwyz': [
        # {
        #     'intention': ['departmentConfirm', 'departmentAmong', 'departmentSubset'],
        #     'config': [
        #         {
        #             'out_link_id': 'out_link_id',
        #             'name': '去问诊',
        #             'type': '4',
        #             'text': '',
        #             'relation': 1
        #         }
        #     ]
        # }
    ]
}

organization_intention_config = {
    # 线上merge_search
    'b96d4a21d9994eca8a6ff293d6558ce6': {
        'keyword_symptom': {
            'strategy': {
                'execute': True,
                'params': {
                    'level': 3
                }
            }
        }
    },
    '0b8ed5e3c86949b09ed54534f56d7629': {
        'keyword_symptom': {
            'strategy': {
                'execute': True,
                'params': {
                    'level': 3
                }
            }
        }
    },
}


def get_answer(mode, intention):
    pass


def get_config_card(mode, intention, intention_set_id):
    card_dict = {}
    for temp in ModeCard.get(mode, []):
        if intention in temp['intention']:
            config_temp = copy.deepcopy(temp['config'])
            config_temp['intention_set_id'] = intention_set_id
            card_dict[config_temp['card_id']] = config_temp
    return card_dict


if __name__ == '__main__':
    result = get_config_card('xwyz', 'departmentConfirm')
    print(json.dumps(result, indent=True))
