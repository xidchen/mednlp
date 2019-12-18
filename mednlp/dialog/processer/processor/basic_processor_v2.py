# !/usr/bin/env python
# encoding=utf-8

import json
from mednlp.dialog.configuration import Constant as constant, deal_input
import global_conf
from mednlp.dialog.configuration import IntentionConf
import copy
from ailib.client.ai_service_client import AIServiceClient
from mednlp.dialog.processer.ai_search_common import query
from mednlp.dialog.medical_dialogue_common import query_entity_dict


class BasicProcessor(object):
    """
    基础意图处理类.
    用来处理不同意图的方法
    """

    def __init__(self, **kwargs):
        self.intention_conf = None
        # 构造函数
        if kwargs.get('intention_conf'):
            self.intention_conf = kwargs.get('intention_conf')
        self.ai_sc = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.search_sc = AIServiceClient(global_conf.cfg_path, 'SearchService')
        self.initialize()

    def get_intention_conf(self):
        return self.intention_conf

    def initialize(self):
        pass

    def process(self, query, **kwargs):
        """
        query:{
                    'dialogue': {},
                    'input': {
                                'q': '头痛是挂内科吗',
                                'province': 24,
                                'city': 552,
                                'sex':2,
                                'hospital'
                                .....
                            },
                    'mode': str,
                    'organization': str,
                    'source': str
                }
        :param query:
        :param kwargs:
        :return: (process_data={}, control_info={})
        返回1个元祖, process_data是 处理的数据, control_info是逻辑控制
        {
            doctor_search:[],
            is_end:1,
            code:0
        }
        """
        pass

    def set_params(self, query, **kwargs):
        """
        query:{
            'dialogue': {},
            'input': {
                        'q': '头痛是挂内科吗',
                        'province': 24,
                        'city': 552,
                        'sex':2,
                        'hospital'
                        .....
                    },
            'mode': str,
            'organization': str,
            'source': str
        }
        """
        _input_params = self.get_input_params(query)
        self.input_params = _input_params
        _ai_result = kwargs.get('ai_result')
        if not _ai_result:
            _ai_result = self.get_entity_dict(_input_params)
        self.ai_result = _ai_result

    def set_dialogue_info(self, result):
        dialogue = result.setdefault(constant.QUERY_FIELD_DIALOGUE, {})
        dialogue[constant.QUERY_FIELD_DIALOGUE_PREVIOUS_Q] = self.input_params['input']['q']

    def get_input_params(self, query=None):
        """
        解析输入的内容
        :param query: 输入的内容,string类型
        :return: {}
        """
        params = {}
        if query:
            params = copy.deepcopy(query)
            params['input'] = deal_input(params)
        return params

    def get_entity_dict(self, input_params):
        return query_entity_dict(input_params)

    def set_intention_conf(self, intention_conf):
        self.intention_conf = intention_conf

    def basic_set_rows(self, card_type, **kwargs):
        """
        返回卡片数量,默认返回2个,
        1.数据库的card_num为-1,实际为12个
        2.数据库的card_num > -1,以数据库的配置为准
        3.数据库的card_num 设置为默认值 2个
        """
        # 默认返回2个卡片
        default_rows = kwargs.get('default_rows', 2)
        result = default_rows
        card_dict = self.intention_conf.card_dict
        if card_dict:
            for card_id, info in card_dict.items():
                card_type_temp = info.get('type')
                if card_type_temp == card_type:
                    card_num = info.get('card_num')
                    if card_num is None:
                        card_num = default_rows
                    elif -1 == card_num:
                        # card_num设置为-1, 卡片数量返回12个
                        card_num = 12
                    elif card_num < -1:
                        card_num = default_rows
                    result = card_num
                    break
        return result

    # def __init__(self):
    #     """
    #     构造函数.
    #     """
    #     self.ai_result = {}  # 存储key:value,初始化的时候存储 实体识别后的q以及city等入参
    #     self.input_params = {}  # query全部数据  (把input从list变成{})
    #     self.response_data = {}  # [{}] 存在数据
    #     self.ai_server = AIServiceClient(global_conf.cfg_path, 'AIService')
    #     self.intention_conf = None
