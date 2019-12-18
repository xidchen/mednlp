#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
aiserver_client.py -- the client of aiserver

Author: geeq <geeq@guahao.com>
Create on 2018-03-15 Monday.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import urllib
import json
import pdb
from mednlp.service.ai_medical_service import common
from mednlp.service.ai_medical_service import ai_constant
import copy
from mednlp.dao.ai_service_dao import ai_services
from mednlp.utils.utils import transform_dict_data

if not sys.version > '3':
    import urllib2
else:
    import urllib.request as urllib2
    import urllib.parse as urllib


def __query(url, params, **kwargs):
    url = url + urllib.urlencode(params)
    print('Query URL:', url)
    if kwargs.get('debug'):
        print('Query URL:', url)
        sys.stdout.flush()
    attempts = 0
    success = False
    s = '{}'
    while attempts < 3 and not success:
        try:
            s = urllib2.urlopen(url, timeout=5).read()
            success = True
        except:
            attempts += 1
            if attempts == 3:
                print('Query URL error, the url is %s' % url)
                break
    return json.loads(s)


def get_entity(q, holder):
    result = []
    if not q:
        return result
    params = {
        'q': q
    }
    data = holder.query(params, 'entity_extract')
    if data.get('data') and isinstance(data['data'], list):
        result = data['data']
    return result


def build_dialogue_service_res(data, result, request):
    intention = data.get('intention')
    intention_details = data.get('intention_details')
    intention_combine = intention
    if intention == 'keyword' and intention_details:
        intention_combine = '%s_%s' % (intention, intention_details[0])
    if intention_combine == 'department':
        department_classify_build_dialogue_service(data, result)
    elif intention_combine == 'auto_diagnose':
        auto_diagnose_build_dialogue_service(data, result, request)
    elif intention_combine in ('keyword_department', 'keyword_doctor', 'keyword_disease', 'doctor', 'doctorQuality'):
        doctor_build_dialogue_service(data, result, request)
    elif intention_combine in ('departmentConfirm', 'departmentAmong', 'departmentSubset'):
        department_build_dialogue_service(data, result)
    elif intention_combine in ('hospital', 'hospitalQuality'):  #
        hospital_build_dialogue_service(data, result, request)
    elif intention_combine in ('hospitalDepartment', ):
        hospital_dept_build_dialogue_service(data, result, request)
    elif intention_combine in ('recentHaoyuanTime', 'register', 'haoyuanRefresh'):
        doctor_build_dialogue_service(data, result, request)
    elif intention_combine in ('keyword_hospital', ):
        keyword_hospital_build_dialogue_servie(data, result, request)
    elif intention_combine in ('keyword_treatment', 'content', 'other', 'keyword_examination', 'keyword_medical_word',
                               'Keyword_symptom', 'keyword_medicine', 'keyword_city', 'keyword_province',
                               'keyword_body_part'):
        post_build_dialogue_service(data, result)
    elif intention_combine in ('customerService',):
        customer_build_dialogue_service(data, result)
    elif intention_combine in ('corpusGreeting', 'greeting', 'guide', 'sensitive'):
        general_answer_build_dialogue_service(data, result, request)
    return result


def check_entity(entity, **kwargs):
    # 是否存在实体
    """
    entity_service:
    1.存在实体的标识
    2.是否显示极速问诊和一病多问
    :return
    exist_entity: 1:存在实体, 0-不存在实体
    service_list: 1.极速问诊, 2.一病多问
    """
    result = {'exist_entity': 0}
    entity_service = kwargs.get('entity_service', [])
    entity_type = ['symptom', 'disease', 'std_department', 'hospital_department', 'hospital',
                   'body_part', 'medicine', 'doctor', 'physical', 'examination']
    for temp in entity:
        if 1 in entity_service and temp.get('type') in entity_type and (not result.get('exist_entity')):
            result['exist_entity'] = 1
        if 2 in entity_service and temp.get('type') in ('symptom', 'body_part')\
                and (not result.get('service_list')):
            # 结束的时候若问句里有症状、身体部位词, 推荐极速问诊和一病多问
            result['service_list'] = [1, 2]
    return result


def compare_transform_answer_keywords_data(origin, dest, field_tuples):
    # 把answer里的keyword转换到dest里
    for (origin_key, origin_value, dest_key) in field_tuples:
        if origin.get(origin_key) == dest_key:
            dest[dest_key] = origin.get(origin_value)


def transform_card_content2dict_2(origin_list):
    result = []
    for card in origin_list:
        card_dict = {}
        for key, value in card.items():
            card_dict.update(value)
        result.append(card_dict)
    return result

def transform_card_content2dict(origin_list):
    result = []
    for card in origin_list:
        card_dict = {}
        for key, value in card.items():
            card_dict.update(value)
        result.append(card_dict)
    return result


def get_fields_from_extends(result, data):
    if not data.get('extends'):
        return
    extends = data.get('extends')
    for temp in ai_constant.RESULT_EXTENDS_FIELDS:
        if extends.get(temp):
            result[temp] = extends[temp]


def query(params, input_params, query_obj='doctor', url='', **kwargs):
    debug = False
    if input_params.get('debug'):
        debug = True
    url_suffix = ai_constant.url_dict.get(query_obj)
    base_url = common.get_outer_service_url() + url_suffix
    if url:
        base_url = url + url_suffix
    return __query(base_url, params, debug=debug)

def ai_to_search_params(ai_result, request_object, input_params={}):
    params = {}
    if request_object:
        params_dict = ai_constant.ai_search_params_dict.get(request_object)
        if input_params:
            params_dict = input_params
        for key, value in params_dict.items():
            if ai_result.get(key):
                params[value] = ','.join(ai_result.get(key)[0:30])
        return params

def ai_to_q_params(ai_result={}, need_area=True, in_params_set={}):
    """
    ai的结果转化成搜索的q参数
    ai_result: ai的返回结果
    need_area: 是否把区域参数加入到搜索参数中去
    in_params_set: 过滤ai查询参数的范围，空的时候默认查询所有ai返回的字段
    """
    params = {}
    q_content = get_keyword_q_params(ai_result, in_params_set)
    if q_content:
        params['q'] = q_content
    if need_area:
        if ai_result.get('cityId'):
            params['city'] = ','.join(ai_result.get('cityId'))
        if ai_result.get('provinceId'):
            params['province'] = ','.join(ai_result.get('provinceId'))
    return params, q_content

def get_keyword_q_params(ai_result={}, in_params_set={}):
    """
    ai_result: ai的结果
    通过ai的结果转化成q参数的具体方法
    具体原理: 首先扫描所有实体，具体对应实体在keyword_q_param_name中
                把所有的实体通过空格组合成一个q参数
                如果q参数依然为空，把区域参数作为实体传入q参数中
    """
    params_set = ai_constant.keyword_q_param_name
    if in_params_set:
        params_set = in_params_set
    q_list = []
    q_content = ''
    for param in params_set:
        if ai_result.get(param):
            q_list.append(' '.join(ai_result.get(param)))
    if q_list:
        q_content = ' '.join(q_list)
    elif ai_result.get('cityName'):
        q_content = ' '.join(ai_result.get('cityName'))
    elif ai_result.get('provinceName'):
        q_content = ' '.join(ai_result.get('provinceName'))
    return q_content


def get_hospital_search_params(params={}, input_params={}, fl_list=[], default_params={}):
    """
    params: 输入到fq的参数列表
    input_params: 用户输入参数
    fl_list: 需要返回的列表
    default_params: 默认的搜索的参数列表
    """
    search_params = copy.deepcopy(ai_constant.default_search_params_dict.get('hospital'))
    default_fl_list = copy.deepcopy(ai_constant.return_list_dict.get('hospital'))
    if default_params:
        search_params = default_params
    for key,value in params.items():
        search_params[key] = value
    if not fl_list:
        fl_list = default_fl_list
    search_params['fl'] = ','.join(fl_list)
    if (input_params and input_params.get('input')
        and input_params['input'].get('longitude')
        and input_params['input'].get('latitude')):
        search_params['longitude'] = input_params['input'].get('longitude')
        search_params['latitude'] = input_params['input'].get('latitude')
    return search_params, fl_list

def get_search_params(params=None, input_params=None, return_obj='doctor', fl_list=None, default_params=None):
    """
    params: 输入到fq的参数列表
    input_params: 用户输入参数
    return_obj:标签参数
    fl_list: 需要返回的列表
    default_params: 默认的搜索的参数列表
    """
    if not params:
        params = {}
    if not input_params:
        input_params = {}
    if not fl_list:
        fl_list = []
    if not default_params:
        default_params = {}
    search_params = copy.deepcopy(ai_constant.default_search_params_dict.get(return_obj))
    default_fl_list = copy.deepcopy(ai_constant.return_list_dict.get(return_obj))
    if default_params:
        search_params = default_params
    for key,value in params.items():
        search_params[key] = value
    if not fl_list:
        fl_list = default_fl_list
    search_params['fl'] = ','.join(fl_list)
    return search_params, fl_list


def get_hospital_obj(response, ai_result, fl_list):
    #solr_hospital_response, area = self.get_extend_solr_response(params, False, 'hospital')
    #solr_hospital_response = self.solr.solr_search(params, 'hospital', handler='search')
    hospital_response = response
    hospital_obj_list = []
    if hospital_response and hospital_response['count'] > 0:
        for doc in hospital_response['hospital']:
            obj_item_list = []
            for params_item in fl_list:
                if params_item == 'hospital_name':
                    if not ai_result.get('hospitalName'):
                        ai_result['postHospitalName'] = []
                        ai_result['postHospitalName'].append(doc.get('hospital_name'))
                if params_item == 'hospital_hot_department':
                    hospital_hot_department = doc.get(
                                        'hospital_hot_department', '')
                    new_hospital_hot_department = []
                    if hospital_hot_department:
                        for index, value in enumerate(hospital_hot_department):
                            new_hospital_hot_department.append(value.split('|')[1])
                    new_hospital_hot_department = ','.join(new_hospital_hot_department)
                    obj_item_list.append(new_hospital_hot_department)
                    continue
                if params_item == 'hospital_standard_department':
                    tag = '0'
                    standard_department = doc.get('hospital_standard_department', [])
                    hospital_department = doc.get('hospital_department', [])
                    if 'departmentName' in ai_result:
                        for d_name in ai_result['departmentName']:
                            if d_name in standard_department or d_name in hospital_department:
                                tag = '1'
                    obj_item_list.append(tag)
                    continue
                if params_item == 'hospital_department':
                    continue
                obj_item_list.append(str(doc.get(params_item, '')))
            hospital_obj_list.append('|'.join(obj_item_list))
    return hospital_obj_list


def get_hospital_json_obj(response, ai_result, fl_list):
    hospital_response = response
    hospital_json_list = []
    if hospital_response and hospital_response['count'] > 0:
        for doc in hospital_response['hospital']:
            hospital_json = {}
            for params_item in fl_list:
                if params_item == 'hospital_name':
                    if not ai_result.get('hospitalName'):
                        ai_result['postHospitalName'] = []
                        ai_result['postHospitalName'].append(doc.get('hospital_name'))
                if params_item == 'hospital_hot_department':
                    hospital_hot_department = doc.get(
                                        'hospital_hot_department', [])
                    if hospital_hot_department:
                        for index, value in enumerate(hospital_hot_department):
                            hospital_hot_department[index] = value.split('|')[1]
                    hospital_json['hospital_hot_department'] = hospital_hot_department
                    continue
                if params_item == 'hospital_standard_department':
                    tag = 0
                    standard_department = doc.get('hospital_standard_department', [])
                    hospital_department = doc.get('hospital_department', [])
                    if 'departmentName' in ai_result:
                        for d_name in ai_result['departmentName']:
                            if d_name in standard_department or d_name in hospital_department:
                                tag = 1
                    hospital_json['conclude_department'] = tag
                    continue
                if params_item == 'hospital_department':
                    continue
                if params_item in doc:
                    hospital_json[params_item] = doc[params_item]
            hospital_json_list.append(hospital_json)
    return hospital_json_list

def get_dept_rank(department_uuid=''):
    response = []
    if department_uuid:
        params = {'department': department_uuid,
                  'row': 1,
                  'fl': 'department_country_rank, department_province_rank'}
        dept_response = query(params, {}, 'search_dept')
        if dept_response.get('department'):
            response = dept_response.get('department')
    return response

def get_department(params={}):
    response = {}
    if params:
        dept_response = query(params, {}, 'search_dept')
        if dept_response.get('department'):
            response = dept_response
    return response

def get_service_package_code(expert_id=None):
    package_code = ''
    if expert_id:
        params = {'rows':1,
                  "fl": "package_code",
                  "sort": "general",
                  "expert": expert_id
                  }
        response = query(params, {}, 'service_package')
        if len(response['data']) > 0:
            data_item = response['data'][0]
            package_code = data_item['package_code']
    return package_code

def get_ai_dept(ai_params={}, input_params={}):
    response = {}
    if ai_params:
        url = common.get_ai_service_url()
        response = query(ai_params, input_params, 'ai_dept', url)
    return response


def get_std_dept(search_params={}, input_params={}):
    response = {}
    if search_params:
        response = query(search_params, input_params, 'std_dept')
    return response

def get_sentence_similar(ai_params={}, input_params={}):
    response = {}
    if ai_params:
        url = common.get_ai_service_url()
        response = query(ai_params, input_params, 'sentence_similarity', url)
    return response

def get_service_package_code_dict(expert_ids=[]):
    expert_package_dict = {}
    if expert_ids:
        params = {'rows':100,
                  "fl": "expert_id,package_code",
                  "sort": "general",
                  "expert": ','.join(expert_ids)
                  }
        response = query(params, {}, 'service_package')
        if len(response['data']) > 0:
            for data_item in response['data']:
                expert_id = data_item.get('expert_id')
                package_code = data_item.get('package_code')
                if expert_id and package_code and expert_id not in expert_package_dict:
                    expert_package_dict[expert_id] = package_code
    return expert_package_dict

def get_doctor_uuid_list(response):
    doctor_uuid_list = []
    doctor_response = response
    if doctor_response and doctor_response['count'] > 0:
        for doc in doctor_response['docs']:
            doctor_uuid = doc.get('doctor_uuid')
            if doctor_uuid:
                doctor_uuid_list.append(doctor_uuid)
    return doctor_uuid_list

def get_doctor_obj(response, ai_result):
    default_fl_list = copy.deepcopy(ai_constant.return_list_dict.get('doctor'))
    #solr_doctor_response = self.solr.solr_search(params, 'doctor', handler='search')
    array_field = ['hospital_department_detail', 'specialty_disease']
    #获取医生服务包字典
    doctor_uuid_list = get_doctor_uuid_list(response)
    doctor_package_dict = get_service_package_code_dict(doctor_uuid_list)
    doctor_obj_list = []
    doctor_response = response
    if doctor_response and doctor_response['count'] > 0:
        for doc in doctor_response['docs']:
            obj_item_list = []
            for params_item in default_fl_list:
                if params_item == 'doctor_name':
                    if not ai_result.get('doctorName'):
                        ai_result['postDoctorName'] = []
                        ai_result['postDoctorName'].append(doc.get('doctor_name'))
                if params_item == 'is_service_package':
                    package_code = doctor_package_dict.get(doc.get('doctor_uuid'), '')
                    obj_item_list.append(package_code)
                    continue
                if params_item == 'doctor_recent_haoyuan_detail':
                    doctor_haoyuan_detail = doc.get('doctor_recent_haoyuan_detail', '')
                    if doctor_haoyuan_detail:
                        doctor_haoyuan_list = doctor_haoyuan_detail.split('|')
                        for index in [1, 2, 5, 6]:
                            obj_item_list.append(doctor_haoyuan_list[index])
                    else:
                        obj_item_list.extend(['','','',''])
                    continue
                if params_item == 'doctor_haoyuan_time':
                    doctor_haoyuan_time = doc.get('doctor_haoyuan_time', [])
                    if doctor_haoyuan_time:
                        doctor_haoyuan_time = doctor_haoyuan_time[0]
                    else:
                        doctor_haoyuan_time = ''
                    obj_item_list.append(doctor_haoyuan_time)
                    continue
                if params_item == 'doctor_haoyuan_detail':
                    doctor_haoyuan_list = doc.get('doctor_haoyuan_detail', [])
                    new_haoyuan_list = []
                    for doctor_haoyuan in doctor_haoyuan_list[0:5]:
                        if doctor_haoyuan:
                            haoyuan = doctor_haoyuan.replace('|','¦')
                            new_haoyuan_list.append(haoyuan)
                    if new_haoyuan_list:
                        obj_item_list.append(','.join(new_haoyuan_list))
                    else:
                        obj_item_list.append('')
                    continue
                if params_item in array_field:
                    item_value = doc.get(params_item, '')
                    if item_value:
                        if params_item == 'specialty_disease':
                            new_item_value = []
                            for index,value in enumerate(item_value):
                                new_item_value.append(value.replace('|','¦'))
                            item_value_temp = ','.join(new_item_value)
                            obj_item_list.append(item_value_temp)
                            continue
                        if params_item == 'hospital_department_detail':
                            hospital = ''
                            department = ''
                            hospital_level = ''
                            item_value_return = []
                            if 'departmentName' in ai_result and 'hospitalNmae' in ai_result:
                                for detail in item_value:
                                    department_param = detail.split('|')[3]
                                    hospital_param = detail.split('|')[1]
                                    if (department_param in ai_result['departmentName']
                                        and hospital_param in ai_result['hospitalName']):
                                        hospital = detail.split('|')[1]
                                        department = detail.split('|')[3]
                                        hospital_level = detail.split('|')[12]
                                if not hospital:
                                    for detail in item_value:
                                        department_param = detail.split('|')[5]
                                        hospital_param = detail.split('|')[1]
                                        if (department_param in ai_result['departmentName']
                                            and hospital_param in ai_result['hospitalName']):
                                            hospital = detail.split('|')[1]
                                            department = detail.split('|')[3]
                                            hospital_level = detail.split('|')[12]
                            if not hospital:
                                if 'departmentName' in ai_result:
                                    for detail in item_value:
                                        department_param = detail.split('|')[3]
                                        if department_param in ai_result['departmentName']:
                                            hospital = detail.split('|')[1]
                                            department = detail.split('|')[3]
                                            hospital_level = detail.split('|')[12]
                                    if not hospital:
                                        for detail in item_value:
                                            department_param = detail.split('|')[5]
                                            if department_param in ai_result['departmentName']:
                                                hospital = detail.split('|')[1]
                                                department = detail.split('|')[3]
                                                hospital_level = detail.split('|')[12]
                            if not hospital:
                                detail = item_value[0]
                                hospital = detail.split('|')[1]
                                department = detail.split('|')[3]
                                hospital_level = detail.split('|')[12]
                            item_value_return.append(hospital)
                            item_value_return.append(department)
                            item_value_return.append(hospital_level)
                            obj_item_list.extend(item_value_return)
                            continue
                    elif params_item == 'hospital_department_detail':
                        item_value_return = ['','','']
                        obj_item_list.extend(item_value_return)
                        continue
                    obj_item_list.append(item_value)
                    continue
                obj_item_list.append(str(doc.get(params_item, '')))
            doctor_obj_list.append('|'.join(obj_item_list))
    return doctor_obj_list


def get_doctor_json_obj(response, ai_result):
    default_fl_list = copy.deepcopy(ai_constant.return_list_dict.get('doctor'))
    #solr_doctor_response = self.solr.solr_search(params, 'doctor', handler='search')
    #获取医生服务包字典
    doctor_uuid_list = get_doctor_uuid_list(response)
    doctor_package_dict = get_service_package_code_dict(doctor_uuid_list)
    doctor_json_list = []
    doctor_response = response
    if doctor_response and doctor_response['count'] > 0:
        for doc in doctor_response['docs']:
            doctor_json_obj = {}
            for params_item in default_fl_list:
                if params_item == 'doctor_name':
                    if not ai_result.get('doctorName'):
                        ai_result['postDoctorName'] = []
                        ai_result['postDoctorName'].append(doc.get('doctor_name'))
                if params_item == 'is_service_package':
                    package_code = doctor_package_dict.get(doc.get('doctor_uuid'), '')
                    doctor_json_obj['service_package_id'] = package_code
                    continue
                if params_item == 'doctor_recent_haoyuan_detail':
                    doctor_haoyuan_detail = doc.get('doctor_recent_haoyuan_detail', '')
                    if doctor_haoyuan_detail:
                        doctor_haoyuan_list = doctor_haoyuan_detail.split('|')
                        doctor_json_obj['recent_haoyuan_date'] = doctor_haoyuan_list[1]
                        doctor_json_obj['recent_haoyuan_time'] = doctor_haoyuan_list[2]
                        doctor_json_obj['haoyuan_fee'] = doctor_haoyuan_list[5]
                        doctor_json_obj['haoyuan_remain_num'] = doctor_haoyuan_list[6]
                    continue
                if params_item == 'doctor_haoyuan_time':
                    doctor_haoyuan_time = doc.get('doctor_haoyuan_time', [])
                    if doctor_haoyuan_time:
                        doctor_haoyuan_time = doctor_haoyuan_time[0]
                        doctor_json_obj['recent_haoyuan_refresh'] = doctor_haoyuan_time
                    continue
                if params_item == 'doctor_haoyuan_detail':
                    doctor_haoyuan_list = doc.get('doctor_haoyuan_detail', [])
                    if doctor_haoyuan_list:
                        doctor_json_obj['doctor_haoyuan_detail'] = doctor_haoyuan_list[0:5]
                    continue
                if params_item == 'hospital_department_detail':
                    item_value = doc.get(params_item, [])
                    if not item_value:
                        continue
                    hospital = ''
                    department = ''
                    hospital_level = ''
                    department_uuid = ''
                    hospital_uuid = ''
                    hospital_province = ''
                    if 'departmentName' in ai_result and 'hospitalNmae' in ai_result:
                        for detail in item_value:
                            department_param = detail.split('|')[3]
                            hospital_param = detail.split('|')[1]
                            if (department_param in ai_result['departmentName']
                                and hospital_param in ai_result['hospitalName']):
                                hospital_uuid = detail.split('|')[0]
                                hospital = detail.split('|')[1]
                                department = detail.split('|')[3]
                                hospital_level = detail.split('|')[12]
                                department_uuid = detail.split('|')[2]
                                hospital_province = detail.split('|')[10]
                        if not hospital:
                            for detail in item_value:
                                department_param = detail.split('|')[5]
                                hospital_param = detail.split('|')[1]
                                if (department_param in ai_result['departmentName']
                                    and hospital_param in ai_result['hospitalName']):
                                    hospital_uuid = detail.split('|')[0]
                                    hospital = detail.split('|')[1]
                                    department = detail.split('|')[3]
                                    hospital_level = detail.split('|')[12]
                                    department_uuid = detail.split('|')[2]
                                    hospital_province = detail.split('|')[10]
                    if not hospital:
                        if 'departmentName' in ai_result:
                            for detail in item_value:
                                department_param = detail.split('|')[3]
                                if department_param in ai_result['departmentName']:
                                    hospital_uuid = detail.split('|')[0]
                                    hospital = detail.split('|')[1]
                                    department = detail.split('|')[3]
                                    hospital_level = detail.split('|')[12]
                                    department_uuid = detail.split('|')[2]
                                    hospital_province = detail.split('|')[10]
                            if not hospital:
                                for detail in item_value:
                                    department_param = detail.split('|')[5]
                                    if department_param in ai_result['departmentName']:
                                        hospital_uuid = detail.split('|')[0]
                                        hospital = detail.split('|')[1]
                                        department = detail.split('|')[3]
                                        hospital_level = detail.split('|')[12]
                                        department_uuid = detail.split('|')[2]
                                        hospital_province = detail.split('|')[10]
                    if not hospital:
                        detail = item_value[0]
                        hospital = detail.split('|')[1]
                        department = detail.split('|')[3]
                        hospital_level = detail.split('|')[12]
                        department_uuid = detail.split('|')[2]
                        hospital_uuid = detail.split('|')[0]
                        hospital_province = detail.split('|')[10]
                    if hospital:
                        doctor_json_obj['hospital_name'] = hospital
                    if department:
                        doctor_json_obj['department_name'] = department
                    if hospital_level:
                        doctor_json_obj['hospital_level'] = hospital_level
                    if department_uuid:
                        doctor_json_obj['department_uuid'] = department_uuid
                        dept_response = get_dept_rank(department_uuid)
                        if dept_response:
                            doctor_json_obj.update(dept_response[0])
                    if hospital_uuid:
                        doctor_json_obj['hospital_uuid'] = hospital_uuid
                    if hospital_province:
                        doctor_json_obj['hospital_province'] = hospital_province
                    continue
                if params_item in doc:
                    doctor_json_obj[params_item] = doc[params_item]
            deal_doctor_consult(doctor_json_obj)
            doctor_json_list.append(doctor_json_obj)
    return doctor_json_list


def deal_doctor_consult(doctor_json_obj):
    # 处理医生咨询相关信息
    if doctor_json_obj.pop('is_consult_phone', None) == 1:
        doctor_json_obj['is_consult_phone'] = 1
    for consult_detail_temp in doctor_json_obj.pop('doctor_consult_detail', []):
        consult_details = consult_detail_temp.split('|')
        if int(consult_details[0]) == 0 and int(consult_details[1]) == 1:
            doctor_json_obj['is_image_text'] = 1
            if int(consult_details[2]) != -1:
                doctor_json_obj['imagetext_fee'] = int(consult_details[2])
        if int(consult_details[0]) == 3 and int(consult_details[1]) == 1:
            doctor_json_obj['is_diagnosis'] = 1
            if int(consult_details[2]) != -1:
                doctor_json_obj['diagnosis_fee'] = int(consult_details[2])
    lowest_consult_fee = None
    highest_consult_fee = None
    # 问诊类目、该问诊是否可约
    price_dict = {
        'imagetext_fee': 'is_image_text',
        'phone_consult_fee': 'is_consult_phone',
        'diagnosis_fee': 'is_diagnosis'
    }
    for price_key in price_dict.keys():
        price = None
        if doctor_json_obj.get(price_dict[price_key]) == 1:
            price = doctor_json_obj.pop(price_key, None)
        if price is None:
            continue
        if lowest_consult_fee is None:
            lowest_consult_fee = price
        if highest_consult_fee is None:
            highest_consult_fee = price
        if price < lowest_consult_fee:
            lowest_consult_fee = price
        if price > highest_consult_fee:
            highest_consult_fee = price
    if lowest_consult_fee is not None:
        doctor_json_obj['lowest_consult_fee'] = lowest_consult_fee
    if highest_consult_fee is not None:
        doctor_json_obj['highest_consult_fee'] = highest_consult_fee
    serve_type = doctor_json_obj.pop('serve_type', [])
    if 8 in serve_type:
        doctor_json_obj['accurate_package'] = 1
    return doctor_json_obj



def get_post_obj(response, ai_result, fl_list):
    post_response = response
    post_obj_list = []
    if post_response and post_response['totalCount'] > 0:
        for doc in post_response['data']:
            obj_item_list = []
            for params_item in fl_list:
                value = str(doc.get(params_item, ''))
                if params_item in ('title', 'topic_content_nohtml', 'topic_nick_name',
                                   'title_highlight', 'content_highlight'):
                    value = value.replace('|', '')
                obj_item_list.append(value)
            post_obj_list.append('|'.join(obj_item_list))
    return post_obj_list

def get_post_json_obj(response, ai_result, fl_list):
    post_response = response
    post_json_list = []
    if post_response and post_response['totalCount'] > 0:
        for doc in post_response['data']:
            obj_item_dict = {}
            for params_item in fl_list:
                if params_item in doc:
                    obj_item_dict[params_item] = doc.get(params_item)
            post_json_list.append(obj_item_dict)
    return post_json_list

def get_consult_doctor(response, ai_result):
    is_consult = 0
    consult_facet = response['doctor_facet']
    if consult_facet.get('contract_register'):
        facets = consult_facet.get('contract_register')
        for facet_item in facets:
            item_type = int(facet_item.split('|')[0])
            if item_type == 1:
                item_count = int(facet_item.split('|')[1])
                if item_count > 0:
                    is_consult = 1
    return is_consult

def get_extend_response(params, input_params, request_object, city_name='city', province_name='province'):
    """
    扩展全国的功能
    params: 查询参数
    request_object: 返回标签
    """
    response = {}
    area = ''
    if params.get(city_name):
        response = query(params, input_params, request_object)
        json_name = ai_constant.return_json.get(request_object)
        if len(response[json_name]) == 0:
            params.pop(city_name)
            if params.get(province_name):
                response = query(params, input_params, request_object)
                json_name = ai_constant.return_json.get(request_object)
                if len(response[json_name]) == 0:
                    params.pop(province_name)
                    response = query(params, input_params, request_object)
                    json_name = ai_constant.return_json.get(request_object)
                    area = 'all'
                else:
                    area = 'province'
            else:
                response = query(params, input_params, request_object)
                json_name = ai_constant.return_json.get(request_object)
                area = 'all'
        else:
            area = 'city'
    else:
        if params.get(province_name):
            response = query(params, input_params, request_object)
            json_name = ai_constant.return_json.get(request_object)
            if len(response[json_name]) == 0:
                params.pop(province_name)
                response = query(params, input_params, request_object)
                json_name = ai_constant.return_json.get(request_object)
                area = 'all'
            else:
                area = 'province'
        else:
            response = query(params, input_params, request_object)
            json_name = ai_constant.return_json.get(request_object)
            area = 'all'
    return response, area

def check_location(input_params):
    flag = False
    if (input_params and input_params.get('input')
        and input_params['input'].get('longitude')
        and input_params['input'].get('latitude')):
        flag = True
    return flag

def get_doctor_post(post_response):
    is_post = 0
    if post_response and post_response['totalCount'] > 0:
        is_post = 1
    return is_post

def department_interact(input_params={}, ai_result={}):
    """
    科室交互
    :param input_param:输入参数
    :param ai_result: 包含意图和实体的字典,实体形式为checkout后的样子
    :return:分科句式交互结果，{isEnd:1,accuracy:,...}
    """

    param = {'rows': 1}
    param['source'] = input_params.get('source')
    param['q'] = input_params.get('input').get('q').encode('utf8')
    if input_params.get('input').get('symptomName'):
        param['symptom'] = input_params.get('input').get('symptomName').encode('utf8')
    if input_params.get('input').get('sex'):
        param['sex'] = input_params.get('input').get('sex')
    if input_params.get('input').get('age'):
        param['age'] = input_params.get('input').get('age')
    if not input_params.get('input').get('confirm_information'):
        param['interactive'] = 2
    interrupt = True if input_params.get('input').get('isEnd') else False
    fl = {'isEnd': 0}
    dept_data, err_msg = ai_services(param, 'dept_classify_interactive', 'post')
    if not dept_data:
        fl['err_msgs'] = err_msg
        fl['isHelp'] = 1
        fl['isEnd'] = 1
        return fl

    dept_result = dept_data.get('depts')[0]
    dept_name = dept_result.get('dept_name')

    stop_interact = dept_data.get('isEnd') or interrupt
    if stop_interact and dept_name == 'unknow':
        fl['isHelp'] = 1
        fl['isEnd'] = 1
        return fl

    if stop_interact:
        fl['accuracy'] = dept_result.get('accuracy')
        fl['departmentId'] = [dept_result.get('dept_id')]
        fl['departmentName'] = [dept_name]
        fl['department_updated'] = True
        dept_in_query = True if dept_result.get('dept_id') in ai_result.get('departmentId', []) else False
        if dept_in_query:
            if ai_result.get('intention') == 'departmentConfirm':
                fl['confirm'] = 1
            if ai_result.get('intention') == 'departmentAmong':
                fl['among'] = 1
        fl['isEnd'] = 1
        return fl

    if not stop_interact:
        if dept_data.get('isSex') or dept_data.get('isAge'):
            fl['needSexAge'] = 1
        if dept_data.get('symptoms'):
            fl['departmentSymptom'] = dept_data.get('symptoms')
        return fl


def general_build_dialogue_service(data, result):
    result['intention'] = data.get('intention')
    result['intentionDetails'] = data.get('intention_details', [])
    result['intention_details'] = data.get('intention_details', [])
    result['dialogue'] = data.get('dialogue', {})
    result['isEnd'] = data.get('is_end', 1)
    transform_dict_data(result, data, {
        'registered': 'registered', 'area': 'area', 'isHelp': 'is_help', 'search_params': 'search_params',
        'query_content': 'query_content', 'exist_entity': 'exist_entity', 'service_list': 'service_list',
        'greeting_num': 'greeting_num', 'valid_auto_diagnose': 'valid_auto_diagnose',
        'auto_diagnose_merge': 'auto_diagnose_merge', 'accuracy': 'accuracy', 'among': 'among',
        'confirm': 'confirm', 'show_guiding': 'show_guiding'
    })
    out_link = data.get('out_link', [])
    patient_group_out_link = [temp for temp in out_link if temp.get('name') == '微医病友群']
    if patient_group_out_link:
        result.setdefault('out_link', []).extend(patient_group_out_link)
    transformer_keys = {
        "departmentId": "departmentId", "departmentName": "departmentName",
        "doctorId": "doctorId", "doctorName": "doctorName",
        "diseaseId": "diseaseId", "diseaseName": "diseaseName",
        "hospitalId": "hospitalId", "hospitalName": "hospitalName",
        "treatmentId": "treatmentId", "treatmentName": "treatmentName",
        "medicineId": "medicineId", "medicineName": "medicineName",
        "symptomId": "symptomId", "symptomName": "symptomName",
        "cityId": "cityId", "cityName": "cityName",
        "provinceId": "provinceId", "provinceName": "provinceName"}
    transform_dict_data(result, data, transformer_keys)


def hospital_build_dialogue_service(data, result, request):
    general_build_dialogue_service(data, result)
    has_interactive = transform_interactive_age_sex_symptom(data, result)
    result['valid_object'] = ['hospital']
    result['json_hospital'] = []
    if has_interactive:
        return result
    card = data.get('card', [])
    for card_temp in card:
        if str(card_temp.get('type')) == '3' and card_temp.get('content'):
            type_result = card_temp['content']
            result['json_hospital'] = type_result
    return result


def general_answer_build_dialogue_service(data, result, request):
    general_build_dialogue_service(data, result)
    answer = data.get('answer', [])
    if answer and answer[0].get('text'):
        result['answer'] = answer[0]['text']
    intention = result.get('intention')
    if intention in ('corpusGreeting', 'greeting', 'guide'):
        result['intention'] = 'greeting'
        result.setdefault('dialogue', {})['intention'] = 'greeting'
    return result


def hospital_dept_build_dialogue_service(data, result, request):
    general_build_dialogue_service(data, result)
    result['valid_object'] = ['hospital']
    result['json_hospital'] = []
    card = data.get('card', [])
    for card_temp in card:
        if str(card_temp.get('type')) == '3' and card_temp.get('content'):
            type_result = card_temp['content']
            result['json_hospital'] = type_result
            result['valid_object'] = ['hospital']
            break
        elif str(card_temp.get('type')) == '1' and card_temp.get('content'):
            type_result = card_temp['content']
            result['json_doctor'] = type_result
            result['valid_object'] = ['doctor']
            break
    return result


def department_build_dialogue_service(data, result):
    general_build_dialogue_service(data, result)
    answer = data.get('answer', [])
    get_fields_from_extends(result, data)
    has_interactive = transform_interactive_age_sex_symptom(data, result)
    result['valid_object'] = ['doctor']
    result['json_doctor'] = []
    if has_interactive:
        return result
    # 返回卡片文案之类的.
    out_link = data.get('out_link', [])
    for temp in out_link:
        if temp.get('id') == 'no_consult_id':
            # 有去问诊按钮 is_consult=1
            result['is_consult'] = 1
    for temp in answer:
        if temp.get('id') == '%s_no_id' % data.get('intention'):
            keywords = temp.get('keyword', [])
            for keyword_temp in keywords:
                # if keyword_temp.get('id') == 'accuracy':
                #     result['accuracy'] = keyword_temp.get('text')
                # if keyword_temp.get('id') == 'query_content':
                #     result['query_content'] = keyword_temp.get('text')
                # if keyword_temp.get('id') == 'confirm':
                #     result['confirm'] = 1
                # if keyword_temp.get('id') == 'among':
                #     result['among'] = 1
                # if keyword_temp.get('id') == 'area':
                #     result['area'] = keyword_temp.get('text')
                pass
    card = data.get('card', [])
    for card_temp in card:
        if str(card_temp.get('type')) == '1' and card_temp.get('content'):
            doctor_result = card_temp['content']
            result['json_doctor'] = doctor_result
    return result


def greeting_build_dialogue_service(data, result):
    general_build_dialogue_service(data, result)
    answer = data.get('answer', [])
    interactive = data.get('interactive', [])
    if 'greeting_num' in data:
        result['greeting_num'] = data['greeting_num']
    if 'show_guiding' in data:
        result['show_guiding'] = data['show_guiding']
    if interactive:
        result['interactive'] = interactive
        result['answer'] = answer
    if not result.get('answer') and answer and answer[0].get('text'):
        result['answer'] = answer[0]['text']
    return result


def customer_build_dialogue_service(data, result):
    general_build_dialogue_service(data, result)
    answer = data.get('answer', [])
    interactive = data.get('interactive', [])
    if interactive:
        interactive = interactive[0]['options']
        interactive_dict = {}
        interactive_content = []
        if interactive[0].get('options', [{}])[0].get('field'):
            interactive_dict['field'] = interactive[0].get('options', [{}])[0].get('field')
        if interactive[0].get('options', [{}])[0].get('type'):
            interactive_dict['type'] = interactive[0].get('options', [{}])[0].get('type')
        if interactive[0].get('options', [{}])[0].get('display'):
            interactive_dict['display'] = interactive[0].get('options', [{}])[0].get('display')
        for temp in interactive:
            option_content = temp.get('options', [{}])[0].get('content')
            if option_content:
                interactive_content.append(option_content)
        interactive_dict['content'] = interactive_content
        result['interactive_box'] = [interactive_dict]
    if answer and answer[0].get('text'):
        result['answer'] = answer[0]['text']
    if data.get('card') and data['card'][0].get('content'):
        type = data['card'][0]['type']
        if type == 9:
            result['question'] = data['card'][0]['content']
            result['valid_object'] = ['question']
    if data.get('standard_question_id'):
        result['standard_question_id'] = data['standard_question_id']
    return result


def transform_interactive_age_sex_symptom(data, result):
    has_interactive = False
    interactive = data.get('interactive', [])
    if not interactive:
        return has_interactive
    candidate = interactive[0]
    answer_code = candidate.get('answerCode')
    answer = data.get('answer', [])
    answer_dict = {temp['code']: temp['text'] for temp in answer if 'code' in temp and 'text' in temp}
    if answer_code in ('age', 'sex', 'symptomName'):
        has_interactive = True
        result_answer = answer_dict.get(answer_code)
        if result_answer:
            result['answer'] = result_answer
        if answer_code in ('age', 'sex'):
            result['needSexAge'] = 1
        elif answer_code == 'symptomName':
            options = candidate.get('options')
            if options:
                content = [temp['content'] for temp in options if temp.get('content')]
                symptom_box = {'field': 'symptomName', 'type': 'multiple'}
                if content[0] != '都没有':
                    content.insert(0, '都没有')
                symptom_box['content'] = content
                content_length = len(content)
                symptom_box['conflict'] = [[0, index_temp] for index_temp in range(1, content_length)]
                result['interactive_box'] = [symptom_box]
    return has_interactive


def department_classify_build_dialogue_service(data, result):
    # dialogue_service请求的数据,包装成科室分类输出字段
    general_build_dialogue_service(data, result)
    result['valid_object'] = ['department']
    result['department'] = []
    cards = data.get('card', [])
    get_fields_from_extends(result, data)
    has_interactive = transform_interactive_age_sex_symptom(data, result)
    if has_interactive:
        return result
    for card_temp in cards:
        if str(card_temp.get('type')) == '2' and card_temp.get('content'):
            result['department'] = card_temp['content']
    out_links = data.get('out_link', [])
    for out_link_temp in out_links:
        if out_link_temp.get('id') == 'valid_auto_diagnose':
            result['valid_auto_diagnose'] = 1
    answer = data.get('answer', [])
    if answer and answer[0].get('text'):
        result['answer'] = answer[0]['text']
    return result


def doctor_build_dialogue_service(data, result, request):
    general_build_dialogue_service(data, result)
    result['valid_object'] = ['doctor']
    result['json_doctor'] = []
    for item in ('age', 'sex'):
        if result.get(item):
            result.pop(item)
    card = data.get('card', [])
    for card_temp in card:
        if str(card_temp.get('type')) == '1' and card_temp.get('content'):
            doctor_result = card_temp['content']
            result['json_doctor'] = doctor_result
    return result


def keyword_hospital_build_dialogue_servie(data, result, request):
    general_build_dialogue_service(data, result)
    if request.get('mode') == 'xwyz_doctor':
        result['json_doctor'] = []
        result['valid_object'] = ['doctor']
    else:
        result['json_hospital'] = []
        result['valid_object'] = ['hospital']
    card = data.get('card', [])
    for card_temp in card:
        if str(card_temp.get('type')) == '3' and card_temp.get('content'):
            type_result = card_temp['content']
            result['json_hospital'] = type_result
            result['valid_object'] = ['hospital']
            break
        elif str(card_temp.get('type')) == '1' and card_temp.get('content'):
            type_result = card_temp['content']
            result['json_doctor'] = type_result
            result['valid_object'] = ['doctor']
            break
    return result

def auto_diagnose_build_dialogue_service(data, result, request):
    # 自诊返回数据组装
    general_build_dialogue_service(data, result)
    interactive_box = data.get('interactive_box', [])
    if request.get('input').get('auto_diagnosis'):
        card = data.get('card', {})
        answer = data.get('answer', {})
        if interactive_box:
            result['interactive_box'] = interactive_box
        if answer:
            result['answer'] = answer.get('text')
        if card and str(card.get('type')) == 'diagnose':
            result['diagnosis'] = card['content']
            result['valid_object'] = ['diagnosis']
        if 'progress' in data:
            result['progress'] = data.get('progress')
        return result
    result['valid_object'] = ['doctor']
    result['json_doctor'] = []
    has_interactive = transform_interactive_age_sex_symptom(data, result)
    if has_interactive:
        return result
    # 返回卡片文案之类的.
    card = data.get('card', [])
    for card_temp in card:
        if str(card_temp.get('type')) == '1' and 'content' in card_temp:
            result['json_doctor'] = card_temp['content']
    return result


def post_build_dialogue_service(data, result):
    general_build_dialogue_service(data, result)
    result['valid_object'] = ['post', 'baike']
    result['json_post'] = []
    result['json_baike'] = []
    cards = data.get('card')
    if cards:
        for card_temp in cards:
            contents = card_temp.get('content', [])
            for content_temp in contents:
                flag = content_temp.pop('card_flag', None)
                if flag == 'post':
                    result['json_post'].append(transform_dialogue_service_card(
                        ai_constant.post_trans, content_temp))
                elif flag == 'baike':
                    result['json_baike'].append(transform_dialogue_service_card(
                        ai_constant.baike_trans, content_temp))
    answer = data.get('answer')
    if answer and answer[0].get('text'):
        result['answer'] = answer[0]['text']
    intention = data.get('intention')
    intention_details = data.get('intentionDetails', [])
    intention_combine = intention
    if intention == 'keyword' and intention_details:
        intention_combine = '%s_%s' % (intention, intention_details[0])
    if intention_combine in ('content', 'other', 'keyword_examination', 'keyword_medical_word'):
        result['intention'] = 'keyword'
        result['intentionDetails'] = ['treatment']
        result['intention_details'] = ['treatment']
        dialogue = result.setdefault('dialogue', {})
        dialogue['intention'] = 'keyword'
        dialogue['intentionDetails'] = ['treatment']
        dialogue['intention_details'] = ['treatment']
    return result


def transform_dialogue_service_card(mapping, obj):
    trans_dict = {v: k for k, v in mapping.items()}
    trans_keys = list(trans_dict.keys())
    result = {}
    for temp in obj:
        if temp not in trans_keys:
            continue
        result[trans_dict[temp]] = obj[temp]
    return result





