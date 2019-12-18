#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
reason_medicine_check.py -- 合理用药检测接口服务

Author: chenxk <chenxk@guahao.com>
Create on 2019-08-07 星期三.
"""


import global_conf
import os
import sys
import time
from base_request_handler import BaseRequestHandler
from ailib.utils.exception import AIServiceException
from ailib.utils.exception import ArgumentLostException
from mednlp.dao.reason_medicine_check_dao import ReasonMedicineCheckDao
from ailib.utils.log import GLLog
import json
import random
import ast
import logging
import copy

reason_medicine_check_dao = ReasonMedicineCheckDao()
logger = GLLog('reason_medicine_check', log_dir=global_conf.out_log_dir, level='info').getLogger()

class ReasonMedicineCheck(BaseRequestHandler):
    not_none_field = ['age', 'sex', 'pregnancy_status']

    def initialize(self, runtime=None, **kwargs):
        super(ReasonMedicineCheck, self).initialize(runtime, **kwargs)

    def post(self):
        try:
            if self.request.body:
                input_obj = json.loads(self.request.body)
                self.get(input_obj=input_obj)
        except Exception:
            raise AIServiceException(self.request.body)

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self, **kwargs):
        input_obj = kwargs.get('input_obj')
        self.check_parameter(input_obj)
        result = {'data': {}}
        log_template = '###interfaceStart###%s###interfaceEnd###'
        for field in reason_medicine_check_dao.check_field.keys():
            result['data'][field] = copy.deepcopy(reason_medicine_check_dao.tip_level)
        symptoms = reason_medicine_check_dao.extract_symptom(input_obj.get('chief_complaint', ''))
        input_obj['symptoms'] = symptoms
        medicines = input_obj.get('medicine', [])
        if medicines:
            common_prescription_names = []
            medicine_ids = set()
            for medicine in medicines:
                if medicine.get('medicine_id'):
                    medicine_ids.add(medicine.get('medicine_id'))
                if medicine.get('common_name'):
                    common_prescription_names.append(medicine.get('common_name'))
            medicine_infos = {}
            if medicine_ids:
                medicine_infos = reason_medicine_check_dao.get_medicine_info(medicine_ids)  # 获取药品的详细信息
                for medicine in medicines:
                    if medicine_infos.get(medicine.get('medicine_id', '')):
                        if not medicine.get('common_name'):
                            medicine['common_name'] = medicine_infos.get(medicine.get('medicine_id', ''), {}).get('common_name', '')
                            common_prescription_names.append(medicine['common_name'])
                        if not medicine.get('specification'):
                            medicine['specification'] = medicine_infos.get(medicine.get('medicine_id', ''), {}).get('specification', '')
            input_obj['common_prescription_names'] = common_prescription_names
            reason_medicine_infos = reason_medicine_check_dao.get_data_from_local(set(common_prescription_names))  # 获取合理用药药品信息
            if reason_medicine_infos:
                for medicine in medicines:
                    result['data'] = reason_medicine_check_dao.check_all_field(medicine, medicine_infos, reason_medicine_infos, result['data'], **input_obj)
        input_obj['interface'] = '合理用药检测'
        input_obj['result'] = result['data']
        input_obj['is_tip'] = 0
        for tip_obj in result['data'].values():
            for tip in tip_obj.values():
                if tip:
                    input_obj['is_tip'] = 1
        logger.info(log_template % json.dumps(input_obj, ensure_ascii=False))
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
    handlers = [(r'/reason_medicine_check', ReasonMedicineCheck, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
