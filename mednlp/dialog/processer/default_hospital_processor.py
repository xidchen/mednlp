#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor
from mednlp.dialog.configuration import Constant as constant


class DefaultHospitalProcessor(BasicProcessor):
    """
    处理默认医院的意图
    """

    def get_search_result(self):
        result = {}
        # 获取hospital_relation
        hospital_relation = self.intention_conf.configuration.hospital_relation
        if not hospital_relation:
            return result
        hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if temp.get('hospital_uuid')]
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_hospital_search_params(ai_params, self.input_params)
        # 添加 医院筛选功能
        search_params['hospital'] = ','.join(hospital_ids)
        response, area = ai_search_common.get_extend_response(search_params, self.input_params, 'hospital')
        hospital_obj_list = ai_search_common.get_hospital_obj(response, self.ai_result, fl_list)
        hospital_json_list = ai_search_common.hospital_to_json(hospital_obj_list)
        result['code'] = response['code']
        result[constant.QUERY_KEY_HOSPITAL_SEARCH] = hospital_json_list
        result['search_params'] = ai_params
        result['is_end'] = 1
        return result

        # self.ai_result['area'] = area
        # self.ai_result['hospital'] = hospital_obj_list
        # self.ai_result['valid_object'] = ['hospital']
        # self.ai_result['query_content'] = q_content
