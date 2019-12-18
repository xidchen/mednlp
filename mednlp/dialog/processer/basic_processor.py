# !/usr/bin/python
# encoding=utf-8

import json
from ailib.client.ai_service_client import AIServiceClient
import global_conf
from mednlp.dialog.configuration import IntentionConf
import copy


class BasicProcessor(object):
    """
    基础意图处理类.
    用来处理不同意图的方法
    """

    def __init__(self):
        """
        构造函数.
        """
        self.ai_result = {}  # 存储key:value,初始化的时候存储 实体识别后的q以及city等入参
        self.input_params = {}  # query全部数据  (把input从list变成{})
        self.response_data = {}  # [{}] 存在数据
        self.ai_server = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.intention_conf = None

    def set_intention_conf(self, intention_conf):
        self.intention_conf = intention_conf

    def set_params(self, query, **kwargs):
        # print(input_params)
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
        self.input_params = self.get_input_params(query)
        entity_dict = self.get_entity_dict(self.input_params)
        self.ai_result.update(entity_dict)

    def get_input_params(self, query=None):
        """
        解析输入的内容
        :param query: 输入的内容,string类型
        :return:
        """
        params = {}
        if query:
            params = copy.deepcopy(query)
            if params.get('input'):
                input_dict = {}
                for input_item in params.get('input'):
                    input_dict.update(input_item)
                params['input'] = input_dict
        return params

    def process(self, query, **kwargs):
        """
        处理对应的数据，返回应有的结果。
        """
        self.set_params(query)
        return self.get_intention_result()

    def get_search_result(self):
        """
        处理对应的数据，返回应有的结果。
        可依赖的数据只有self.ai_result = {}和self.input_params
        """
        pass

    def get_default_result(self):
        pass

    def add_docs(self):
        pass

    def get_intention_result(self):
        return self.get_search_result()

    def get_entity_dict(self, input_params):
        """
        input中的q通过实体识别转换为各种类型的Name和id,以及input中的city,province参数转换
        格式:
        {
            'key': [],
            'departmentName': [],
            'departmentId': []
            'cityId': []
        }
        :param input_params:
        :return:
        """
        entity_map = {'std_department': {'departmentName': 'entity_name',
                                         'departmentId': 'entity_id'},
                      'doctor': {'doctorName': 'entity_name',
                                 'doctorId': 'entity_id'},
                      'symptom': {'symptomName': 'entity_name',
                                  'symptomId': 'entity_id'},
                      'disease': {'diseaseName': 'entity_name',
                                  'diseaseId': 'entity_id'},
                      'hospital_department': {'departmentName': 'entity_name',
                                              'departmentId': 'entity_id'},
                      'hospital': {'hospitalName': 'entity_name',
                                   'hospitalId': 'entity_id'},
                      'body_part': {'bodyPartName': 'entity_name',
                                    'bodyPartId': 'entity_id'},
                      'treatment': {'treatmentName': 'entity_name',
                                    'treatmentId': 'entity_id'},
                      'medicine': {'medicineName': 'entity_name',
                                   'medicineId': 'entity_id'},
                      'area': {'city': {'cityName': 'entity_name',
                                        'cityId': 'entity_id'},
                               'province': {'provinceName': 'entity_name',
                                            'provinceId': 'entity_id'}
                               }
                      }

        input_change_params = {'city': 'cityId',
                               'province': 'provinceId',
                               'hospital': 'hospitalId',
                               'doctor': 'doctorId',
                               'hospitalName': 'hospitalName',
                               'doctorName': 'doctorName',
                               'symptomName': 'symptomName',
                               'sex': 'sex',
                               'age': 'age'
                               }

        entity_dict = {}
        if 'q' in input_params['input']:
            q = input_params['input']['q']
            params = {'q': str(q)}
            entity_result = self.ai_server.query(params, 'entity_extract')
            if entity_result and entity_result.get('data'):
                for entity_obj in entity_result.get('data'):
                    if entity_map.get(entity_obj.get('type')):
                        entity_map_item = entity_map.get(entity_obj.get('type'))
                        for item in entity_map_item:
                            sub_type = entity_obj.get('sub_type')
                            if sub_type and entity_obj.get('type') == 'area':
                                if sub_type == item:
                                    for sub_item in entity_map_item[sub_type]:
                                        if sub_item in entity_dict and entity_obj.get(entity_map_item[item][sub_item]):
                                            entity_dict[sub_item].append(
                                                entity_obj.get(entity_map_item[item][sub_item]))
                                        elif entity_obj.get(entity_map_item[item][sub_item]):
                                            entity_dict[sub_item] = []
                                            entity_dict[sub_item].append(
                                                entity_obj.get(entity_map_item[item][sub_item]))
                                continue
                            if item in entity_dict:
                                entity_dict[item].append(entity_obj.get(entity_map_item[item]))
                            else:
                                entity_dict[item] = []
                                entity_dict[item].append(entity_obj.get(entity_map_item[item]))
        for param in input_change_params:
            if input_params['input'].get(param):
                value = input_params['input'].get(param)
                entity_dict[input_change_params[param]] = []
                entity_dict[input_change_params[param]].append(value)
        return entity_dict
