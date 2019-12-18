#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
aiserver_client.py -- the client of aiserver

Author: geeq <geeq@guahao.com>
Create on 2018-03-15 Monday.
"""

import sys
import os
import urllib
import urllib2
import ujson
import pdb
import common
import ai_constant
import copy


def __query(url, params, **kwargs):
    url = url + urllib.urlencode(params)
    if kwargs.get('debug'):
        print 'Query URL:', url
        sys.stdout.flush()
    try:
        s = urllib2.urlopen(url, timeout=3).read()
    except Exception:
        print 'Query URL time out, the url is %s' % url
        s = '[]'
    return ujson.loads(s)

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
    if input_params and input_params.get('input'):
        if input_params['input'].get('longitude') and input_params['input'].get('latitude'):
            search_params['longitude'] = input_params['input'].get('longitude')
            search_params['latitude'] = input_params['input'].get('latitude')
	if input_params['input'].get('hospital'):
	    search_params['hospital'] = input_params['input'].get('hospital')
    return search_params, fl_list

def get_search_params(params={}, input_params={}, return_obj='doctor', fl_list=[], default_params={}):
    """
    params: 输入到fq的参数列表
    input_params: 用户输入参数
    return_obj:标签参数
    fl_list: 需要返回的列表
    default_params: 默认的搜索的参数列表
    """
    search_params = copy.deepcopy(ai_constant.default_search_params_dict.get(return_obj))
    default_fl_list = copy.deepcopy(ai_constant.return_list_dict.get(return_obj))
    if default_params:
        search_params = default_params
    for key,value in params.items():
        search_params[key] = value
    if not fl_list:
        fl_list = default_fl_list
    search_params['fl'] = ','.join(fl_list)
    if input_params and input_params.get('input'):
	for input_p in ('doctor', 'hospital'):
	    if input_params.get('input').get(input_p):
		search_params[input_p] = input_params.get('input').get(input_p)
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
                    if hospital_hot_department:
                        for index, value in enumerate(hospital_hot_department):
                            hospital_hot_department[index] = value.split('|')[1]
                        hospital_hot_department = ','.join(hospital_hot_department)
                    obj_item_list.append(hospital_hot_department)
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
    response = []
    if ai_params:
        url = common.get_ai_service_url()
        response = query(ai_params, input_params, 'ai_dept', url)
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
                    doctor_haoyuan_time = doc.get('doctor_haoyuan_time', '')
                    if doctor_haoyuan_time:
                        doctor_haoyuan_time = doctor_haoyuan_time[0]
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
                            for index,value in enumerate(item_value):
                                item_value[index] = value.replace('|','¦')
                            item_value_temp = ','.join(item_value)
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
					hospital_uuid = detail.split('|')[0]
                                        hospital = detail.split('|')[1]
					department_uuid = detail.split('|')[2]
                                        department = detail.split('|')[3]
                                        hospital_level = detail.split('|')[12]
                                if not hospital:
                                    for detail in item_value:
                                        department_param = detail.split('|')[5]
                                        hospital_param = detail.split('|')[1]
                                        if (department_param in ai_result['departmentName']
                                            and hospital_param in ai_result['hospitalName']):
					    hospital_uuid = detail.split('|')[0]
                                            hospital = detail.split('|')[1]
					    department_uuid = detail.split('|')[2]
                                            department = detail.split('|')[3]
                                            hospital_level = detail.split('|')[12]
                            if not hospital:
                                if 'departmentName' in ai_result:
                                    for detail in item_value:
                                        department_param = detail.split('|')[3]
                                        if department_param in ai_result['departmentName']:
					    hospital_uuid = detail.split('|')[0]
                                            hospital = detail.split('|')[1]
					    department_uuid = detail.split('|')[2]
                                            department = detail.split('|')[3]
                                            hospital_level = detail.split('|')[12]
                                    if not hospital:
                                        for detail in item_value:
                                            department_param = detail.split('|')[5]
                                            if department_param in ai_result['departmentName']:
					        hospital_uuid = detail.split('|')[0]
                                                hospital = detail.split('|')[1]
					        department_uuid = detail.split('|')[2]
                                                department = detail.split('|')[3]
                                                hospital_level = detail.split('|')[12]
                            if not hospital:
                                detail = item_value[0]
				hospital_uuid = detail.split('|')[0]
                                hospital = detail.split('|')[1]
				department_uuid = detail.split('|')[2]
                                department = detail.split('|')[3]
                                hospital_level = detail.split('|')[12]
			    item_value_return.append(hospital_uuid)
                            item_value_return.append(hospital)
			    item_value_return.append(department_uuid)
                            item_value_return.append(department)
                            item_value_return.append(hospital_level)
                            obj_item_list.extend(item_value_return)
                            continue
                    elif params_item == 'hospital_department_detail':
                        item_value_return = ['','','','','']
                        obj_item_list.extend(item_value_return)
                        continue
                    obj_item_list.append(item_value)
                    continue
                obj_item_list.append(str(doc.get(params_item, '')))
            doctor_obj_list.append('|'.join(obj_item_list))
    return doctor_obj_list

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


def doctor_to_json(doctor_str_list = []):
    doctors = []
    json_list = ['doctor_uuid', 'doctor_picture', 'doctor_name', 'doctor_title', 'hospital_uuid', 'hospital_name',
		'department_uuid', 'department_name', 'hsopital_level', 'specialty_disease', 'recent_haoyuan_date',
		'recent_haoyuan_time','haoyuan_fee', 'haoyuan_remain_num', 'recent_haoyuan_refresh',
		'haoyuan_all', 'service_package_id', 'is_health', 'topic_user_id', 'comment_score',
		'total_order_count']
    for doctor in doctor_str_list:
        if doctor:
	    item_dict = {}
	    doctor_items = doctor.split('|')
	    for i in range(0,20):
	        item_dict[json_list[i]] = doctor_items[i]
	    doctors.append(item_dict)
    return doctors    
	
def hospital_to_json(hospital_str_list = []):
    hospitals = []
    json_list = ['hospital_uuid', 'hospital_name', 'hospital_level', 'hospital_picture', 'order_num',
		'special_department_name', 'distance', 'rule', 'conclude_department']
    for hospital in hospital_str_list:
        if hospital:
	    item_dict = {}
	    hospital_items = hospital.split('|')
	    for i in range(0,9):
	        item_dict[json_list[i]] = hospital_items[i]
	    hospitals.append(item_dict)
    return hospitals    

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

def get_extend_response(params, input_params, request_object):
    """
    扩展全国的功能
    params: 查询参数
    request_object: 返回标签
    """
    response = {}
    area = ''
    if params.get('city'):
        response = query(params, input_params, request_object)
        json_name = ai_constant.return_json.get(request_object)
        if len(response[json_name]) == 0:
            params.pop('city')
            if params.get('province'):
                response = query(params, input_params, request_object)
                json_name = ai_constant.return_json.get(request_object)
                if len(response[json_name]) == 0:
                    params.pop('province')
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
        if params.get('province'):
            response = query(params, input_params, request_object)
            json_name = ai_constant.return_json.get(request_object)
            if len(response[json_name]) == 0:
                params.pop('province')
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

def process_jingong_doctor(doctor_response):
    return_answer = ''
    param_list = ['doctor_name', 'doctor_title', 'hospital_name', 'department_name']
    answer_temp = '第#_p{num}#_p位，#_p{doctor_name}#_p，#_p{doctor_title}#_p，#_p{hospital_name}#_p，#_p{department_name}#_p，#_p{specialty_disease}#_p。'
    if doctor_response :
	num = '一'
	for doctor in doctor_response[0:2]:
	    answer = ''
	    answer = answer_temp.replace('#_p{num}#_p', num)
	    for param in param_list:
		if param in doctor:
		    replace_str = '#_p{%s}#_p' % param
		    answer = answer.replace(replace_str, doctor[param])
		else:
		    answer = answer.replace(replace_str, '')
	    if doctor.get('specialty_disease'):
		disease_list = []
		specialty_disease = ''
		for disease in doctor['specialty_disease'].split(','):
		    disease_param = disease.split('¦')[1]
		    disease_list.append(disease_param)
		if len(disease_list) > 3:
		    specialty_disease = '%s等' % '、'.join(disease_list[0:3])
		else:
		    specialty_disease = '、'.join(disease_list)
		answer = answer.replace('#_p{specialty_disease}#_p', '擅长:%s' % (specialty_disease))
	    else:
		answer = answer.replace('#_p{specialty_disease}#_p', '')
	    num = '二'
	    return_answer = return_answer + answer
    if not return_answer:
    	return_answer = '很抱歉，小微还在学习，暂时无法解决您的问题'
    return return_answer			
     

def process_jingong_hospital(hospital_response):
    return_answer = ''
    param_list = ['hospital_level', 'hospital_name']
    answer_temp = '第#_p{num}#_p家，#_p{hospital_name}#_p，#_p{hospital_level}#_p。'
    if hospital_response :
	num = '一'
	for hospital in hospital_response[0:2]:
	    answer = ''
	    answer = answer_temp.replace('#_p{num}#_p', num)
	    for param in param_list:
		if param in hospital:
		    replace_str = '#_p{%s}#_p' % param
		    answer = answer.replace(replace_str, hospital[param])
		else:
		    answer = answer.replace(replace_str, '')
	    num = '二'
	    return_answer = return_answer + answer
    if not return_answer:
    	return_answer = '很抱歉，小微还在学习，暂时无法解决您的问题'
    return return_answer			
     
def process_jingong_post(post_response):
    return_answer = ''
    param_list = ['title', 'topic_content_nohtml']
    answer_temp = '第#_p{num}#_p篇，#_p{title}#_p，#_p{topic_content_nohtml}#_p。'
    if post_response :
	num = '一'
	for post in post_response[0:2]:
	    answer = ''
	    answer = answer_temp.replace('#_p{num}#_p', num)
	    for param in param_list:
		if param in post:
		    replace_str = '#_p{%s}#_p' % param
		    answer = answer.replace(replace_str, post[param])
		else:
		    answer = answer.replace(replace_str, '')
	    num = '二'
	    return_answer = return_answer + answer
    if not return_answer:
    	return_answer = '很抱歉，小微还在学习，暂时无法解决您的问题'
    return return_answer			
