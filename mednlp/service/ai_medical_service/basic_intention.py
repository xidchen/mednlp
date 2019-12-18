#!/usr/bin/python
#encoding=utf-8


import global_conf

import mednlp.service.ai_medical_service.client.ai_client as ai_client

from ailib.client.ai_service_client import AIServiceClient

from ailib.client.http_client import HttpClient
import copy
import json
from mednlp.service.ai_medical_service.ai_constant import logger
import mednlp.service.ai_medical_service.ai_search_common as ai_search_common
from mednlp.dialog.medical_dialogue_common import query_entity_dict


class BasicIntention(object):
    """
    基础意图处理类.
    用来处理不同意图的方法
    """

    aiserver = ai_client.AIClient(global_conf.cfg_path)
    ai_server = AIServiceClient(global_conf.cfg_path, 'AIService')

    def __init__(self):
        """
        构造函数.
        """

    def get_diagnose_service_resp(self):
        result = {}
        request_body = self.input_params.get('request_body')
        if not request_body:
            return result
        params = copy.deepcopy(request_body)
        try:
            result = self.ai_server.query(json.dumps(params), 'dialogue_service', method='post'
                                          )
                                          # , url='http://192.168.4.30:10000/dialogue_service')
                                          # , ip_port='http://192.168.3.28:10000')
            logger.info("进行dialogue_service, 参数:%s, result:%s" % (
                json.dumps(params, ensure_ascii=False), json.dumps(result, ensure_ascii=False)))
        except Exception as err:
            logger.exception(err)
        return result

    def set_params(self, ai_result, input_params, solr):
        """
        :param ai_result: {}
        :param input_params:{}
        :param solr:
        :return:
        """
        self.ai_result = ai_result
        self.input_params = input_params
        self.solr = solr
        # q里的实体以及input输入值放入ai_result
        entity_dict = self.get_entity_dict(ai_result, input_params)
        self.entity_dict = entity_dict
        self.ai_result.update(entity_dict)
        if self.ai_result.get('entities'):
            self.ai_result.pop('entities')
        self.kf = HttpClient(global_conf.cfg_path, 'WangXunKeFuService')

    def get_search_result(self):
        """
        处理对应的数据，返回应有的结果。
        """
        pass

    def data_output(self, return_type=1):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        return self.ai_result

    def checkout_result(self):
        return True

    def get_default_result(self):
        pass

    def get_data(self):
        pass

    def add_docs(self):
        pass

    def change_ai_result(self):
        pass

    def get_intention_result(self):
        self.get_data()
        if self.checkout_result():
            self.get_search_result()
        else:
            self.get_default_result()
        self.add_docs()
        if self.ai_result.get('isEnd') != 0:
            self.ai_result['isEnd'] = self.ai_result.get('isEnd', 1)
        self.change_ai_result()
        return self.data_output()

    def get_entity_dict(self, ai_result=None, input_params=None):
        if not ai_result:
            ai_result = {}
        if not input_params:
            input_params = {}
        return query_entity_dict(input_params)
