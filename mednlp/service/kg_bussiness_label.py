#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
知识图谱-业务服务标签服务
Author: FH <fenghui@guahao.com>
Created  on 2019/08/22 22:33
Modified on 2019/09/03 10:50
"""
import json
import traceback

from ailib.service.parameter import escape_solr
from ailib.utils.exception import AIServiceException
from mednlp.service.base_request_handler import BaseRequestHandler


class KgBusinessLabel(BaseRequestHandler):

    not_none_field = ['org']
    biz_list_keys = {'biz_id', 'biz_id_type'}

    def initialize(self, runtime=None, **kwargs):
        super(KgBusinessLabel, self).initialize(runtime, **kwargs)

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
        rows = 10
        params = {'q': '*:*', 'fl': 'label:label_s,', 'start': 0, 'rows': rows}

        # 0202、根据入参组装成solr需要的fq参数

        org_id = request_obj.get('org')
        biz_list = request_obj.get('biz')
        biz_orders = request_obj.get('biz_orders')

        # 查询字段，以逗号进行分隔
        fl_set = set()
        fl_set.update(['org_id:org_id_s', 'biz_id:biz_id_s', 'biz_id_type:biz_type_s'])
        params['fl'] += ','.join(fl_set)

        # 过滤字段字典，同时进行转义处理
        fq_dict = {'org_id_s': escape_solr(org_id), 'is_deleted_i': 0}
        if biz_list:
            biz_id = [escape_solr(biz.get('biz_id'))
                      for biz in biz_list
                      if biz.get('biz_id')]
            biz_type = [escape_solr(biz.get('biz_id_type'))
                        for biz in biz_list
                        if biz.get('biz_id_type')]
            fq_dict['biz_id_s'] = '{0}'.format('_'.join(biz_id))
            fq_dict['biz_type_s'] = '{0}'.format('_'.join(biz_type))

        # 根据biz_orders拼接biz_type
        biz_types = []
        if biz_orders:
            try:
                biz_types = ['_'.join(biz_order)
                             for biz_order in biz_orders]
            except TypeError:
                traceback.print_exc()
                raise AIServiceException

        # 03、根据不同的biz_order去solr匹配数据，匹配到结果则返回，未匹配到则返回空
        solr_result = {}
        if biz_types:
            for biz_type in biz_types:
                fq_dict['biz_type_s'] = escape_solr(biz_type)
                solr_result = self.solr_query(fq_dict, **params)
                if not solr_result.get('data'):
                    continue
                else:
                    break
        else:
            solr_result = self.solr_query(fq_dict, **params)

        # 0301、根据获取到的结果判断是否获取完全
        #      主要为了避免只查询默认rows条可能不能完全覆盖到所有的标签
        total_cnt = solr_result.get('total', 0)
        if total_cnt > rows:
            params['rows'] = total_cnt
            solr_result = self.solr_query(fq_dict, **params)

        # 0302、过滤结果
        # 需要跟传入的参数进行完全匹配过滤
        solr_data = solr_result.get('data')

        # 030201、完全匹配org_id，过滤biz_id、biz_type有值的情况
        if org_id and not biz_list:
            solr_data = [each_data
                         for each_data in solr_data
                         if not any([each_data.get('biz_id'), each_data.get('biz_type')])]

        # 04、过滤并返回结果，仅仅返回标签
        label_list = [each_data.get('label') for each_data in solr_data]
        result = {'data': {'label': set(label_list)}}
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

        # 检测biz_list
        # 01、检测biz_list中的参数是否为dict
        # 02、检测biz_id、biz_type是否成对出现
        # 03、检测biz_list中的dict中的keys是否符合要求
        biz_list = parameters.get('biz_list', [])
        if biz_list:
            for biz_param in biz_list:
                if not isinstance(biz_param, dict) \
                        or not all(biz_param.values()) \
                        or set(biz_param.keys()) != self.biz_list_keys:
                    raise AIServiceException

        # 检测biz_orders
        # 01、检测biz_list or biz_orders是否为list
        # 02、检测biz_orders中的数据是否为list
        biz_orders = parameters.get('biz_orders', [])

        if not isinstance(biz_list, list) \
                or not isinstance(biz_orders, list):
            raise AIServiceException

        if biz_orders:
            for biz_order in biz_orders:
                if not isinstance(biz_order, list):
                    raise AIServiceException

    def solr_query(self, fq_dict: dict, **kwargs) -> dict:
        """
        通过solr云平台进行查询，便于多次查询使用重复的代码
        :param fq_dict: filter query字典
        :return: solr查询后的结果 or 抛出异常
        """
        try:
            solr_result = self.cloud_search.solr_search(kwargs['q'],
                                                        'ai_kg_business_label2',
                                                        fq_dict=fq_dict,
                                                        **kwargs)
        except Exception as ex:
            traceback.print_exc()
            raise Exception('Solr exception, the reason is: {}'.format(ex))
        return solr_result


if __name__ == '__main__':
    handlers = [(r'/kg_business_label', KgBusinessLabel)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
