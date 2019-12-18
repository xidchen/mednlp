#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ailib.client.ai_service_client import AIServiceClient
import global_conf
from mednlp.dialog.processer.ai_search_common import query

ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')


def query_entity_dict(input_params):
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
            :return: {}
            """
    entity_map = {
        'std_department': {'departmentName': 'entity_name',
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
        'medical_word': {'medicalWordName': 'entity_name',
                         'medicalWordId': 'entity_id'},
        'examination': {'examinationName': 'entity_name',
                        'examinationId': 'entity_id'},
        'area': {'city': {'cityName': 'entity_name',
                          'cityId': 'entity_id'},
                 'province': {'provinceName': 'entity_name',
                              'provinceId': 'entity_id'}
                 }
    }

    input_change_params = {
        'hospital': 'hospitalId',
        'doctor': 'doctorId',
        'hospitalName': 'hospitalName',
        'doctorName': 'doctorName',
        'symptomName': 'symptomName',
        'sex': 'sex',
        'age': 'age'
    }

    entity_dict = {}
    if input_params.get('input', {}).get('q'):
        q = input_params['input']['q']
        params = {'q': str(q)}
        entity_result = ai_client.query(params, 'entity_extract')
        if entity_result and entity_result.get('data'):
            for entity_obj in entity_result.get('data'):
                if entity_map.get(entity_obj.get('type')):
                    entity_map_item = entity_map.get(entity_obj.get('type'))
                    for item in entity_map_item:
                        sub_type = entity_obj.get('sub_type')
                        if sub_type and entity_obj.get('type') == 'area':
                            if sub_type == item:
                                for sub_item in entity_map_item[sub_type]:
                                    if entity_obj.get(entity_map_item[item][sub_item]):
                                        entity_dict.setdefault(sub_item, []).append(entity_obj.get(entity_map_item[item][sub_item]))
                            continue
                        if entity_obj.get(entity_map_item[item]):
                            entity_dict.setdefault(item, []).append(entity_obj[entity_map_item[item]])
    for param in input_change_params:
        if input_params['input'].get(param):
            value = input_params['input'].get(param)
            if value in ('都没有',):
                continue
            if isinstance(value, str):
                value = value.split(',')
            entity_temp = entity_dict.setdefault(input_change_params[param], [])
            if isinstance(value, list):
                entity_temp.extend(value)
            else:
                # 输入本身是非 list, str类型的数据
                entity_temp.append(value)
    query_with_area = False
    area_entity_params = {
        'city': ({'cityName': 'name', 'cityId': 'entity_id'},
                 {'fl': 'entity_id,name,tag_type', 'tag_type': '17'}),
        'province': ({'provinceName': 'name', 'provinceId': 'entity_id'},
                     {'fl': 'entity_id,name,tag_type', 'tag_type': '16'}),
    }
    # 若query里city 或者 省份有,不再利用参数里的city和params了
    if entity_dict.get('cityId') or entity_dict.get('provinceId'):
        query_with_area = True
    for key_temp, (entity_key_temp, params_temp) in area_entity_params.items():
        if not query_with_area and input_params['input'].get(key_temp):
            # 若实体里已有entity_key_temp or 输入无key_temp, 不进行tag查询
            params_temp['entity'] = input_params['input'][key_temp]
            tag_result = query(params_temp, input_params, 'tag_service')
            tag_data = None
            if tag_result and tag_result.get('data'):
                tag_data = tag_result['data']
            if tag_data and len(tag_data) >= 1:
                for area_key_temp, tag_key_temp in entity_key_temp.items():
                    if tag_data[0].get(tag_key_temp):
                        entity_dict.setdefault(area_key_temp, []).append(tag_data[0][tag_key_temp])
    return entity_dict


if __name__ == '__main__':
    input_dict = {
        'input': {'q': '怎样挂号赞北京的华西医院内分泌科'}
    }
    result = query_entity_dict(input_dict)
    print(result)