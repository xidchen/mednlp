#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
treatment_plan_recommend.py -- 推荐治疗方案接口服务

Author: chenxk <chenxk@guahao.com>
Create on 2019-10-15 星期二.
"""


import global_conf
import os
import sys
import time
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.utils.exception import AIServiceException
from ailib.utils.exception import ArgumentLostException
from mednlp.dao.treatment_plan_recommend_dao import TreatmentPlanRecommendDao
from ailib.utils.log import GLLog
import json
import random
import ast
import logging
import copy

logger = GLLog('treatment_plan_recommend', log_dir=global_conf.out_log_dir, level='info').getLogger()
treatment_plan_recommend_dao = TreatmentPlanRecommendDao(logger)


class TreatmentPlanRecommend(BaseRequestHandler):
    not_none_field = ['source', 'disease', 'drug_store_id']

    def initialize(self, runtime=None, **kwargs):
        super(TreatmentPlanRecommend, self).initialize(runtime, **kwargs)

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
        result = {'data': []}
        log_template = '###interfaceStart###%s###interfaceEnd###'
        input_obj['interface'] = '推荐治疗方案接口'
        treatment_plans = []
        # 1、根据主诊断获取标准的疾病名称
        standard_disease = treatment_plan_recommend_dao.query_standard_name(input_obj.get('disease'), ['disease'], logger=logger)
        input_obj['standard_disease'] = [entity['name'] for entity in standard_disease]
        # 2、根据主诊断、症状、检查、检验等信息获取治疗方案的ID
        treatment_plans = treatment_plan_recommend_dao.query_treatment_plan_id_by_condition([entity['name'] for entity in standard_disease], logger=logger, **input_obj.get('assist_info', {}))
        # 3、根据治疗方案ID获取治疗方案内容，包含处方等信息
        treatment_plan_ids = []
        add_atc = []
        remove_atc = []
        for treatment_plan in treatment_plans:
            if treatment_plan.get('remedy_plan_id'):
                treatment_plan_ids.extend(treatment_plan.get('remedy_plan_id'))
            if treatment_plan.get('add_atc'):
                add_atc.extend(treatment_plan.get('add_atc'))
            if treatment_plan.get('remove_atc'):
                remove_atc.extend(treatment_plan.get('remove_atc'))
        treatment_plan_infos, all_atc_code, atc_map = treatment_plan_recommend_dao.query_treatment_plan_by_id(treatment_plan_ids, add_atc, remove_atc, logger=logger)
        # 4、根据患者ID、医生ID、药店ID、药品ATC编码进行搜索药品
        medicine_info = treatment_plan_recommend_dao.query_medicine_by_condition(all_atc_code, logger=logger, **input_obj)
        # 5、将搜索到的药品按照治疗方案填充
        for treatment_plan_info in treatment_plan_infos:
            atc_codes = treatment_plan_info['prescription']
            treatment_plan_info['prescription'] = []
            for code in atc_codes:
                atc_obj = {
                    'name': atc_map.get(code, {}).get('name', ''),
                    'code': code,
                    'medicine': medicine_info.get(code, [])
                }
                treatment_plan_info['prescription'].append(atc_obj)
        result['data'] = treatment_plan_infos
        input_obj['result'] = result['data']
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
                elif isinstance(parameters.get(field), list) and not parameters.get(field):
                    raise ArgumentLostException([field])


if __name__ == '__main__':
    handlers = [(r'/treatment_plan_recommend', TreatmentPlanRecommend, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
