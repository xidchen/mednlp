#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.utils.utils import transform_dict_data
import mednlp.dialog.processer.common as common
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dao.ai_service_dao import ai_services
from mednlp.dialog.processer.processor.xwyz_doctor_processor import XwyzDoctorProcessor
from mednlp.dialog.processer.processor.department_classify_processor import DepartmentClassifyProcessor
import copy
from mednlp.dialog.general_util import get_service_data
import json
from mednlp.dialog.dialogue_util import deal_q, get_area_params, request_doctor, get_doctor_json_obj,\
    get_consult_doctor, deal_xwyz_department_confirm_answer, fill_department_classify_params
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, logger, search_sc


class XwyzDepartmentConfirmProcessor(BasicProcessor):
    # 只处理门户科室分类结果

    def __init__(self):
        super(XwyzDepartmentConfirmProcessor, self).__init__()
        self.department_classify = DepartmentClassifyProcessor()
        self.doctor_process = XwyzDoctorProcessor()

    def set_intention_conf(self, intention_conf):
        self.intention_conf = intention_conf
        self.department_classify.set_intention_conf(intention_conf)
        self.doctor_process.set_intention_conf(intention_conf)

    def process_2(self, environment):
        result = {'is_end': 1}
        classify_dept_params = {
            'source': 188,
            'generator': 'department_classify_interactive',
            'method': 'generate',
            'parameter': {
                'q': environment.input_dict['q'],
                'return_type': 1,
                'fl': ['department_id', 'department_name', 'accuracy', 'slot']
            }
        }
        fill_department_classify_params(environment.input_dict, classify_dept_params['parameter'])
        res = get_service_data(json.dumps(classify_dept_params, ensure_ascii=False), ai_sc,
                               'content_generation', throw=True, logger=logger)
        if res.get('slot'):
            result['is_end'] = 0
            result['slot'] = res['slot']
            return result
        content = res.get('content', [])[:1]
        if content:
            environment.add_entity(constant.ENTITY_DEPARTMENT_CLASSIFY, [
                transform_dict_data({}, temp, constant.department_classify_entity_transform_dict) for temp in content])
            if content[0].get('accuracy'):
                result['accuracy'] = content[0].get('accuracy')
        # 查医生 1.组装q、 2.获取医生卡片信息
        q_content = deal_q(environment, param_set=[['department_classify'], ['department']], q_type=2, return_q=True)
        area_params = get_area_params(environment, 'id')
        area_params['q'] = q_content
        doctor_result = request_doctor(area_params)
        transform_dict_data(result, doctor_result, {'search_params': 'search_params', 'area': 'area'})
        result[constant.RESULT_FIELD_QUERY_CONTENT] = q_content
        res = doctor_result['res']
        if (not res) or res.get('code') != 0 or len(res.get('docs', [])) == 0:
            result['card'] = [{'type': constant.CARD_FLAG_DICT['doctor'], 'content': []}]
            # result['answer'] = [{'text': '找不到'}]
            return result
        content = res['docs']
        ai_result = {}
        for (_v1, _v2) in (('department_classify', 'departmentName'), ('hospital', 'hospitalName')):
            ai_entity_temp = environment.get_entity('entity_dict', _v1, 'name')
            if ai_entity_temp:
                ai_result[_v2] = ai_entity_temp
        content = get_doctor_json_obj(content, ai_result, search_sc, constant.doctor_return_list,
                                      haoyuan_range=environment.input_dict.get('contract_price_range'))
        result['is_consult'] = get_consult_doctor(res)
        result['card'] = [{'type': constant.CARD_FLAG_DICT['doctor'], 'content': content}]
        answer = deal_xwyz_department_confirm_answer(environment, result)
        result['answer'] = answer
        return result

    def process(self, query, **kwargs):
        result = {}
        department_classify_result = self.department_classify.process(query)
        result.update(department_classify_result)
        if department_classify_result.get('is_end') == 1:
            # 查医生
            doctor_query = copy.deepcopy(query)
            ceil_process_info = doctor_query.setdefault(constant.PROCESS_FIELD_CEIL_PROCESS_INFO, {})
            ceil_process_info['params_set'] = ['departmentName']
            if self.department_classify.ai_result:
                ceil_process_info['ai_result'] = self.department_classify.ai_result
            doctor_result = self.doctor_process.process(doctor_query)
            result.update(doctor_result)
            ai_search_common.extends_progress_result(result, self.department_classify.ai_result)
        return result