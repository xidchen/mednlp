# !/usr/bin/env python
# encoding=utf-8

import json
import copy
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, logger, search_sc
from mednlp.dialog.dialogue_util import fill_department_classify_params
from mednlp.dialog.general_util import get_service_data
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.dialogue_util import get_area_params, deal_q, request_hospital, get_hospital_json_obj,\
    set_department_rank, deal_xwyz_hospital_answer


class XwyzHospitalProcessor(BasicProcessor):

    def process_2(self, environment):
        """
        1.获取科室id, 取值优先级为问句实体词、分科
        2.获取权威医院id, 逻辑：若有科室id，调用department_search，取第一个科室对应的uuid
        3.获取医院列表
        4.若医院列表里有权威医院id，该id置顶，若没有，查询该权威医院id，置顶
        :param environment:
        :return:
        """
        result = {'is_end': 1}
        department_name = environment.get_entity(
            source=['entity_dict'], key=['department'], attr='name')
        if not department_name:
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
            environment.add_entity(constant.ENTITY_DEPARTMENT_CLASSIFY, [transform_dict_data({}, temp, {
                'id': 'department_id', 'name': 'department_name'}) for temp in content])
            department_name = environment.get_entity(
                source=['entity_dict'], key=['department_classify'], attr='name')
        top_hospital_id = ''
        if department_name:
            # 获取权威医院信息
            dept_params = {
                'standard_name': department_name[0],
                'department_country_rank_range': '0|100',
                'rows': 1,
                'fl': 'hospital_uuid',
                'sort': 'fudan_country'}
            area_params = get_area_params(environment, 'id')
            transform_dict_data(dept_params, area_params, {'city_id': 'city', 'province_id': 'province'})
            dept_res = get_service_data(dept_params, search_sc, 'department_search', method='get', data_key='department')
            top_hospital_id = dept_res[0]['hospital_uuid'] if dept_res and dept_res[0].get('hospital_uuid') else ''
        area_params = get_area_params(environment, 'id')
        q_content = deal_q(environment, param_set=[['department_classify'], ['department']], q_type=2, return_q=True)
        area_params['q'] = q_content
        hospital_result = request_hospital(area_params)
        transform_dict_data(result, hospital_result, {'search_params': 'search_params', 'area': 'area'})
        result[constant.RESULT_FIELD_QUERY_CONTENT] = q_content
        res = hospital_result['res']
        if (not res) or res.get('code') != 0 or len(res.get('hospital', [])) == 0:
            result['card'] = [{'type': constant.CARD_FLAG_DICT['hospital'], 'content': []}]
            # result['answer'] = [{'text': '找不到'}]
            return result
        docs = res['hospital']
        ai_result = {'departmentName': department_name}
        content = get_hospital_json_obj(docs, ai_result, copy.deepcopy(constant.hospital_return_list))
        if top_hospital_id:
            hospital_uuid_list = [temp.get('hospital_uuid') for temp in content]    # 有None的存在
            top_hospital_index = 0
            if top_hospital_id in hospital_uuid_list:
                top_hospital_index = hospital_uuid_list.index(top_hospital_id)
                top_hospital = content.pop(top_hospital_index)
                content.insert(0, top_hospital)
                content[0]['authority'] = 1
            else:
                top_params = copy.deepcopy(area_params)
                top_params['hospital'] = top_hospital_id
                top_hospital_result = request_hospital(
                    top_params, fixed_params=copy.deepcopy(constant.top_hospital_fixed_params))
                top_res = top_hospital_result['res']
                if top_res and top_res.get('code') == 0 and top_res.get('docs'):
                    top_doc = get_hospital_json_obj(top_res['docs'], ai_result, constant.hospital_return_list)
                    top_doc.extend(content)
                    content = top_doc
                    content[0]['authority'] = 1
        if content:
            set_department_rank(content, department_name[0])
            result['card'] = [{'type': constant.CARD_FLAG_DICT['hospital'], 'content': content}]
            answer = deal_xwyz_hospital_answer(environment, result)
            result['answer'] = answer
        return result
