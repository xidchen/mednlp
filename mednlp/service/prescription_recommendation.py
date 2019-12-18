#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: FH <fenghui@guahao.com>
Created on 2019/10/29 13:35
中药推荐方剂
需求：
(1)、根据知识图谱中 方剂、草药、方剂-草药数据 实现通过方剂名称搜索方剂和方剂包含的具体的草药信息
(2)、其中返回的草药名称和草药ID需要使用处方共享平台的名称和ID
(此处涉及到将草药实体ID换为药品库的药品ID，药品ID在实体的标签中存放)
(3)、功能上支持根据方剂名称模糊搜索，数据存放可以放在云搜索上
"""
import json
import traceback

from ailib.service.parameter import escape_solr
from ailib.utils.exception import AIServiceException
from mednlp.service.base_request_handler import BaseRequestHandler


class PrescriptionRecommendation(BaseRequestHandler):

    not_none_field = ['prescription_name', 'page_index']

    def initialize(self, runtime=None, **kwargs):
        super(PrescriptionRecommendation, self).initialize(runtime, **kwargs)

    def post(self):
        try:
            if self.request.body:
                request_obj = json.loads(self.request.body)
                self.get(request_obj=request_obj)
        except Exception:
            raise AIServiceException(self.request.body)

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self, **kwargs):
        request_obj = kwargs.get('request_obj')

        # 01、检测请求的字段是否包含必填字段
        self.check_parameters(request_obj)

        # 02、组装solr需要的参数

        # 0201、默认solr需要的参数
        prescription_name = request_obj.get('prescription_name')
        page_index = request_obj.get('page_index') or 1
        page_size = request_obj.get('page_size') or 10
        start = 0 if page_index < 1 else (page_index - 1) * page_size
        rows = page_size

        params = {'q': '*:*',
                  'fl': 'prescription_id:prescription_id,'
                        'recipe_name:recipe_name,'
                        'herbal_medicine_uuid:herbal_medicine_uuid,'
                        'herbal_medicine_name:herbal_medicine_name,'
                        'drug_id:drug_id',
                  'start': start,
                  'rows': rows}

        fq_dict = {'recipe_name': escape_solr(prescription_name)}

        # 03、从搜索云平台查询数据
        try:
            solr_result = self.cloud_search.solr_search(params['q'],
                                                        'ai_prescription_recommendation',
                                                        fq_dict=fq_dict,
                                                        **params)
        except Exception as ex:
            traceback.print_exc()
            raise Exception('Solr exception, the reason is: {}'.format(ex))

        # 04、处理并返回结果
        total_cnt = solr_result.get('total', 0)
        solr_data = solr_result.get('data')

        # 处理结果
        # 由于搜索云平台需要保持主表ID是唯一的，所以需要过滤一下草药中的重复数据
        prescription_list = []
        for each_data in solr_data:
            processed_list = []
            drug_list = []
            prescription_id = each_data.get('prescription_id')
            recipe_name = each_data.get('recipe_name')
            herbal_medicine_name_list = each_data.get('herbal_medicine_name', '').split(',')
            drug_id_list = each_data.get('drug_id', '').split(',')
            for herbal_medicine_name, drug_id in zip(herbal_medicine_name_list, drug_id_list):
                if herbal_medicine_name in processed_list:
                    continue
                drug = {"id": drug_id, "name": herbal_medicine_name, "quantity": "", "unit": ""}
                processed_list.append(herbal_medicine_name)
                drug_list.append(drug)
            prescription = {"id": prescription_id, "name": recipe_name, "drug": drug_list}
            prescription_list.append(prescription)

        # 返回结果
        result = {'data': {"total": total_cnt,
                           "page_index": page_index,
                           "page_size": page_size,
                           "prescription": prescription_list}}
        return result

    def check_parameters(self, parameters):
        """
        检测请求输入的参数是否包含必填参数
        :param parameters: 参数list
        :return: 如果不包含必填参数，则抛出异常
        """
        # 检测必传参数org_id
        for field in self.not_none_field:
            if field not in parameters:
                raise AIServiceException


if __name__ == '__main__':
    handlers = [(r'/prescription_recommendation', PrescriptionRecommendation)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
