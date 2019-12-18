#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
standard_entity.py -- the standard name of entity

Author: yinwd <yinwd@guahao.com>
Create on 2019-03-19.
"""
import re
import json
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.exception import ArgumentLostException
from mednlp.kg.examination_conf import en_cn_match
import logging
from time import time

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

ai_content = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')


# range_data = json.load(open(global_conf.dict_path + 'examination_range.txt', 'r', encoding='utf-8'))

class StandardEntity(object):

    def __init__(self):
        super(StandardEntity, self).__init__()

    def get_stand_entity(self, entity_name, status):
        explanation = status + '_explanation'
        advice = status + '_advice'
        ef_value = ["name", "id", "standard_name", explanation, advice]
        params = {"name": [entity_name],
                  "type": ["inspection", "physical_examination"],
                  "ef": ef_value
                  }
        # 这里传入的时候将dict转化为json形式
        time_begin = time()
        entity_contnet = ai_content.query(params=json.dumps(params, ensure_ascii=False),
                                          service="entity_service", method='post')

        time_end = time()
        run_time = (time_end - time_begin) * 1000
        logging.info('接口名: entity_service 参数: ' + str(params) + ' 请求类型 : post' + ' 运行时间: %.2f ms' % run_time)

        entity_dict = entity_contnet.get('data')
        result = {}
        if entity_dict:
            result = entity_dict.get('entity')
            if result:
                result = result[0]
        return result


class DataTrans(object):

    def __init__(self):
        super(DataTrans, self).__init__()

    def data_trans(self, inputdata):
        '''
        :param inputdata: json 串
        :return:
        '''
        examination_list = []
        source = ''
        gender = ''
        ext = inputdata.get('ext')
        if ext and ext.get('source'):
            source = ext.get('source')
            print(type(source))
            gender = ext.get('gender')  ## 男1 女2
        else:
            raise ArgumentLostException(['lost source'])

        keys = list(inputdata.keys())
        if len(keys) > 1:
            keys = keys[1:]
            for key in keys:
                category_list = en_cn_match.get(key)
                if category_list:
                    category_name = category_list['cn_name']
                else:
                    category_name = ''
                value_data = inputdata[key]
                for name, value in value_data.items():
                    dict = {}
                    dict['source'] = source
                    dict['category_name'] = category_name
                    dict['gender'] = gender
                    if category_list and category_list.get(name):
                        name = category_list.get(name, name)
                    dict['name'] = name
                    dict['value'] = value
                    com_name = dict['category_name'] + '|' + dict['name']

                    # dict['reference'] = self.source_range_tran(range_data, com_name, source, gender)
                    examination_list.append(dict)
            print('==============')
            print('examination_list', examination_list)
            print('==============')
            return examination_list
        else:
            return ''

    def en_trans_cn(self, category_name, name):
        category_trans = en_cn_match.get(category_name)
        if category_trans:
            category_name = category_trans.get('cn_name')
            name = category_trans.get(name)

        return category_name, name

    def source_range_tran(self, range_data, name, source, gender=1):

        value_data = range_data.get(name)
        if value_data:
            if str(source) == '8':
                values = value_data.get('range3')  # '体检车'
            elif str(source) == '2':
                values = value_data.get('range2')  # '盖睿'
                if re.search(',', values):
                    values = eval(values)
                    if gender == 1:
                        values = values[0]
                    else:
                        values = values[1]
            else:
                values = value_data.get('range1')  # '1和其他来源全部默认工作站'
            return values
        else:
            return ''


if __name__ == '__main__':
    model = StandardEntity()
    result = model.get_stand_entity('肝功能|谷丙转氨酶', 'raise')
    print(result)
    dict_test = {
        "ext": {
            "source": 1
        },
        "garea_urine": {
            "alb": 100.00000,
            "pro": 3
        },
        "renal_function": {
            "cre": 71.100,
            "urea": 0.000
        }
    }
    data_model = DataTrans()
    result = data_model.data_trans(dict_test)
    print(result)
