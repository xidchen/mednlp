# !/usr/bin/env python
# encoding=utf-8

import json
import copy
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, logger, search_sc
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.dialogue_util import get_area_params, deal_q, request_hospital, get_hospital_json_obj


class xwyzHospitalQualityProcessor(BasicProcessor):

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
        area_params = get_area_params(environment, 'id')
        q_content = deal_q(environment, q_type=2, return_q=True)
        area_params['q'] = q_content
        hospital_result = request_hospital(area_params)
        transform_dict_data(result, hospital_result, {'search_params': 'search_params', 'area': 'area'})
        result[constant.RESULT_FIELD_QUERY_CONTENT] = q_content
        res = hospital_result['res']
        if not res or res.get('code') != 0 or len(res.get('hospital', [])) == 0:
            result['card'] = [{'type': constant.CARD_FLAG_DICT['hospital'], 'content': []}]
            return result
        docs = res['hospital']
        department_name = environment.get_entity(source=['entity_dict'], key=['department'], attr='name')
        ai_result = {'departmentName': department_name}
        content = get_hospital_json_obj(docs, ai_result, constant.hospital_return_list)
        result['card'] = [{'type': constant.CARD_FLAG_DICT['hospital'], 'content': content}]
        result['answer'] = [{'text': '以下是为您找到的医院主页，您可以点击下面按钮进行相应操作'}]
        return result
