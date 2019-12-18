#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ailib.client.ai_service_client import AIServiceClient
from mednlp.utils.utils import pretty_print
import global_conf

client_ai_service = AIServiceClient(global_conf.cfg_path, 'AIService')
client_search_service = AIServiceClient(global_conf.cfg_path, 'SearchService')


def ai_services(param, sv_name, method):
    """
    调用AI服务，服务异常时捕获并返回空
    :param param: 非空字典,str类型的数据编码为utf8，参数详情见各服务文档
    :param sv_name: 目前支持dialogue_analysis、dept_classify_interactive、entity_extract
    :param method: post、get
    :return: response_data, err_msg
    """
    err_msg = dict()
    try:
        response = client_ai_service.query(param, sv_name, method=method)
        assert response, 'response empty data'
    except Exception as e:
        err_msg[sv_name] = 'API未正常返回数据'
        return None, err_msg
    client_ai_service.clear_url()
    return response.get('data'), err_msg


def greeting_service(q='你好冠心病'):
    """
    调用greeting_service，服务异常时捕获并返回空
    :param q: 非空
    :return: []
    """
    err_msg = dict()
    param = {'q': q.encode('utf8'),
             'fl': '*'}
    try:
        data = client_search_service.query(param, 'greeting_service', method='get')
        assert data, 'response empty data'

    except Exception as e:
        err_msg['greeting_service'] = str(e)
        return [], err_msg
    client_search_service.clear_url()
    return data.get('data'), err_msg


def transform_area_old(segs=[]):
    """
    将extract_entity输出的area字段，分解为city,province两个字段
    :param segs: [实体,]
    :return: [实体,]
    """
    for seg in segs:
        if seg.get('type') == 'area':
            areaid = seg.get('entity_id')
            if len(areaid) == 3:
                seg['type'] = 'city'
            elif len(areaid) in {1, 2}:
                seg['type'] = 'province'

            seg['entity_id'] = areaid
            seg['entity_id_all'] = seg.get('entity_id_all')
            type_all = seg.get('type_all')
            type_all.remove('area')
            type_all.append(seg.get('type'))
            seg['type_all'] = type_all

    return segs


def transform_area(segs=[]):
    """
        将extract_entity输出的area字段，分解为city,province两个字段
        :param segs: [实体,]
        :return: [实体,]
        """
    for seg in segs:
        if seg.get('type') == 'area':
            seg['type'] = seg.get('sub_type')
            type_all = seg.get('type_all')
            type_all.remove('area')
            type_all.append(seg.get('sub_type'))
            seg['type_all'] = type_all
    return segs


def transform_area_qa(segs=[]):
    """
    依据qa的id,将输出的area字段，分解为city,province两个字段
    :param segs: [实体,]
    :return: [实体,]
    """
    for seg in segs:
        if seg.get('type') == 'area':
            areaid = seg.get('uuid')
            if len(areaid) == 3:
                seg['type'] = 'city'
            elif len(areaid) in {1, 2}:
                seg['type'] = 'province'
    return segs


def transform_qa(segs):
    def transform_single(seg):
        """
        将qa中有id的形式和entity_extract对齐
        对某些值进行特殊优化
        :param seg: 待转变的实体
        :return: 实体
        """

        def enlarge_doctor_id_all(seg):
            if seg.get('type') == 'doctor' and seg.get('doctor_hospital'):
                return list({i.split('|')[0] for i in seg.get('doctor_hospital')})

        def enlarge_hospital_id_all(seg):
            if seg.get('type') == 'hospital' and seg.get('hospital_uuid'):
                return seg.get('hospital_uuid')

        if seg.get('uuid'):
            seg['entity_id'] = seg.pop('uuid')
            seg['entity_id_all'] = [seg.get('entity_id')]
            seg['entity_name'] = seg.pop('key')
            if enlarge_doctor_id_all(seg):
                seg['entity_id_all'] = enlarge_doctor_id_all(seg)
            if enlarge_hospital_id_all(seg):
                seg['entity_id_all'] = enlarge_hospital_id_all(seg)
        return seg

    return [transform_single(seg) for seg in transform_area_qa(segs)]


if __name__ == '__main__':
    if 0:
        import json

        # data = classify_department_interactive({'q': '头痛挂什么号'})
        # data = extract_entity('挂号男科')
        # data = transform_area(extract_entity('上海头痛傅雯雯怎么重庆北京天津杭州长沙湖南内蒙古滨江区'))

        # 测 dialogue_analysis debug
        q = json.dumps({
            "source": 1,
            "input": [
                {"q": "傅雯雯如何", "symptomName": "神经衰弱,耳鸣,焦虑"}
            ]
        })
        data, err_msg = ai_services({'q': q}, 'dialogue_analysis', 'get')

        # data, err_msg = ai_services({'q': '头痛挂什么号'}, 'dept_classify_interactive', 'post')

        pretty_print(err_msg)
        pretty_print(data)

    if 1:
        # 测试 greeting
        pretty_print(greeting_service('你好'))
