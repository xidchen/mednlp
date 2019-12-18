#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
check_classify.py -- the service of check_prescription_model

Author: caoxg <caoxg@guahao.com>
Create on 2018-07-02 星期一.
"""


import global_conf
import os
import sys
import time
from base_request_handler import BaseRequestHandler
from mednlp.model.check_prescription_model import CheckPrescriptionModel
from ailib.utils.exception import ArgumentLostException
from ailib.utils.log import GLLog
import json
import random
import ast
import logging


check_prescription = CheckPrescriptionModel(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_MODEL')

gray_rate = 20

logger = GLLog('checkprescription', log_dir=global_conf.out_log_dir, level='info').getLogger()

def set_gray(gray_rate_set):
    global gray_rate
    gray_rate = int(gray_rate_set)


class CheckPrescription(BaseRequestHandler):
    not_none_field = ['age', 'sex', 'pregnancy_status']

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        result = {'data': {'is_ok': 0}}
        source = str(self.get_argument('source', ''))
        log_template = '###interfaceStart###%s###interfaceEnd###'
        query_list = {}
        if source:
            doctor_user = str(self.get_argument('doctor_user', ''))
            sex = int(self.get_argument('sex', -1))
            age = int(self.get_argument('age', -1))
            pregnancy_status = int(self.get_argument('pregnancy_status', -1))
            diagnosis = str(self.get_argument('diagnosis', ''))
            medicine = self.get_argument('medicine', [])
            try:
                medicine = ast.literal_eval(medicine)
            except Exception:
                return result
        else:
            query_str = self.request.body
            try:
                query_list = json.loads(query_str, encoding='utf-8')
            except Exception:
                print('data is error')
                return result
            doctor_user = str(query_list.get('doctor_user'))
            sex = int(query_list.get('sex', -1))
            age = int(query_list.get('age', -1))
            pregnancy_status = int(query_list.get('pregnancy_status', -1))
            diagnosis = str(query_list.get('diagnosis', ''))
            medicine = query_list.get('medicine', [])
        self.check_parameter(query_list)
        query_list['interface'] = '智能审方'
        reason = '药品数量不等于1'
        if len(medicine) == 1:
            medicine = medicine[0]
            check_result, reason = check_prescription.predict(doctor_user_id=doctor_user, sex=sex, age=age, diagnosis=diagnosis,
                                                      pregnancy_status=pregnancy_status, medicine=medicine)
            result['data']['is_ok'] = check_result
        # if random.randint(0, 100) > gray_rate:
        #     return result
        query_list['reason'] = reason
        query_list['result'] = result['data']['is_ok']
        logger.info(log_template % json.dumps(query_list, ensure_ascii=False))
        return result

    def check_parameter(self, parameters):
        for field in self.not_none_field:
            if self.get_argument('source', ''):
               if not self.get_argument(field, ''):
                   raise ArgumentLostException([field])
            else:
                if field not in parameters:
                    raise ArgumentLostException([field])


if __name__ == '__main__':
    handlers = [(r'/check_prescription', CheckPrescription, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
