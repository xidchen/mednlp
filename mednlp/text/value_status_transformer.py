#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
value_status_transformer.py -- value to status transformer

Author: chenxd <chenxd@guahao.com>
Create on 2019-02-15 Friday
"""

import json
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from mednlp.text.neg_filter import remove_redundant_punctuation


class ValueStatusTransformer(object):

    def __init__(self):
        self.ai = AIServiceClient(global_conf.cfg_path, 'AIService')

    def base_transform(self, mr):
        """
        Transform value to value status
        :param mr: medical record
        :return: new medical record
        """
        params = dict()
        params['q'] = mr
        params['property'] = 'value'
        params_str = json.dumps(params)
        new_mr = ''
        try:
            query_result = self.ai.query(params_str, 'entity_extract')
            for entity in query_result['data']:
                if 'entity_text' in entity and 'property' in entity:
                    if entity['property']['value_status'] in ['上升', '下降']:
                        new_mr += entity['entity_text'].replace(
                            entity['property']['value'],
                            entity['property']['value_status'])
                    else:
                        continue
                else:
                    new_mr += entity['entity_name']
        except (BaseException, RuntimeError):
            new_mr = mr
        new_mr = remove_redundant_punctuation(new_mr)
        return new_mr

    def body_temperature_transform(self, temperature):
        """
        Transform body temperature value to status
        :param temperature: value
        :return: temperature: status
        """
        if temperature:
            try:
                temperature = float(temperature)
            except ValueError:
                temperature = 36.5
            if temperature <= 36:
                temperature = '体温过低'
            elif 36 < temperature <= 37.2:
                temperature = ''
            elif 37.2 < temperature < 38:
                temperature = '体温上升有低热'
            elif 38 <= temperature:
                temperature = '体温过高发高热'
        return temperature

    def systolic_transform(self, blood_pressure):
        """
        Transform systolic blood pressure value to status
        :param blood_pressure: value
        :return: blood_pressure: status
        """
        if blood_pressure:
            try:
                blood_pressure = float(blood_pressure)
            except ValueError:
                blood_pressure = 115
            if blood_pressure <= 90:
                blood_pressure = '收缩压过低'
            elif 90 < blood_pressure < 140:
                blood_pressure = ''
            elif 140 <= blood_pressure:
                blood_pressure = '收缩压过高'
        return blood_pressure

    def diastolic_transform(self, blood_pressure):
        """
        Transform diastolic blood pressure value to status
        :param blood_pressure: value
        :return: blood_pressure: status
        """
        if blood_pressure:
            try:
                blood_pressure = float(blood_pressure)
            except ValueError:
                blood_pressure = 75
            if blood_pressure <= 60:
                blood_pressure = '舒张压过低'
            elif 60 < blood_pressure < 90:
                blood_pressure = ''
            elif 90 <= blood_pressure:
                blood_pressure = '舒张压过高'
        return blood_pressure


if __name__ == '__main__':
    text = '体温36.5℃，HR80次/分，血压130/80mmHg。'
    vst = ValueStatusTransformer()
    print(vst.base_transform(text))
