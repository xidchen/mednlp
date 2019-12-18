#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cg_constant.py -- 记录内容生成器的常量
Author: renyx <renyx@guahao.com>
Create on 2019-06-25 Tuesday.
"""
import global_conf
from ailib.utils.log import GLLog

logger = GLLog('content_generation_input_output', level='info', log_dir=global_conf.log_dir).getLogger()


array_field = [
        'time', 'reason',
        'degree', 'body_part', 'frequency',
        'serious_reason', 'relief_reason', 'accompany_symptom',
        'medicine_detail', 'past_medical_history', 'allergy_history',
        'sbp', 'dbp', 'fasting_plasma_glucose',
        'fasting_plasma_glucose_2hour', 'medicine_effect', 'symptom_property',
        'accompany_symptom_property', 'menstruation_last_time', 'menstruation_interval_time',
        'property_added', 'frequency_added', 'first_body_part',
        'description', 'quantity'
    ]

REQUEST_IS_OK = 200


if __name__ == '__main__':
    print('ok')
