#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mednlp.dialog.configuration import logger
from mednlp.dialog.generator_manager.generator_manager import GeneratorManager
import json
import copy
import traceback
from mednlp.dialog.general_util import get_service_data, transform_answer_keyword
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, search_sc
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.component_config import departmentNameAnswerKeyword, confirmAnswerKeywod, amongAnswerKeywod, \
    accuracyAnswerKeywod, queryContentAnswerKeywod, areaAnswerKeyword

cgm = GeneratorManager()


def distinct_entity(key, origin_obj_list):
    result = set()
    for obj_list in origin_obj_list:
        candidate = set(temp[key] for temp in obj_list if temp.get(key))
        result.update(candidate)
    return list(result)


def q_entity_assemble(environment, param_set=constant.q_default_params_set):
    q_list = []
    result = ''
    for key in param_set:
        candidate = distinct_entity('name', [environment.entity_dict.get(key, []),
                                             environment.user_entity_dict.get(key, [])])
        if candidate:
            q_list.extend(candidate)
    if q_list:
        result = ' '.join(q_list)
    return result


def q_entity_area(environment):
    q_list = []
    result = ''
    city_candidate = distinct_entity('name', [environment.entity_dict.get('city_default', [])])
    if city_candidate:
        q_list.append(city_candidate[0])
    if not q_list:
        province_candidate = distinct_entity('name', [environment.entity_dict.get('province_default', [])])
        if province_candidate:
            q_list.append(province_candidate[0])
    if q_list:
        result = ' '.join(q_list)
    return result


def deal_q(environment, q_type=1, **kwargs):
    """
    :arg
        param_set: list
    q_type=1: 返回输入的q
    q_type=2：若不存在param_set, 按照默认的params_set组装
                若param_set存在，遍历param_set
    return_q:True返回原始的q
    """
    if q_type == constant.Q_TYPE_ENTITY_ASSEMBLE:
        param_set_list = kwargs.get('param_set')
        result = ''
        if not param_set_list:
            result = q_entity_assemble(environment)
        else:
            for temp in param_set_list:
                result = q_entity_assemble(environment, param_set=temp)
                if result:
                    break
        if not result:
            result = q_entity_area(environment)
        if not result and kwargs.get('return_q'):
            result = environment.input_dict.get('q')
        return result
    return environment.input_dict.get('q')


def fill_department_classify_params(input_dict, params):
    # 填充科室分类参数
    dept_params = {
        'age': 'age',
        'sex': 'sex',
        'symptomName': 'symptom'
    }
    if input_dict.get('confirm_information'):
        params['confirm_patient_info'] = 1
    for item in dept_params.keys():
        value = input_dict.get(item)
        if value is not None:
            if item == 'symptomName' and value in ('都没有',):
                value = '-1'
            params[dept_params[item]] = value


def is_valid_auto_diagnose(params):
    # 默认无效自诊
    result = False
    if params:
        res = get_service_data(json.dumps(params, ensure_ascii=False), ai_sc, 'auto_diagnose', result={})
        is_valid = res.get('extends', {}).get('valid_auto_diagnose')
        if is_valid == 1:
            result = True
    return result


def get_area_params(environment, attr):
    # 若confirm_area=1, 不考虑问句中识别的地区，用city和province的值
    result = {}
    for (param_key, entity_key) in (('city', 'city_default'), ('province', 'province_default')):
        value = environment.get_entity('entity_dict', entity_key, attr)
        value = ','.join(value)
        if value:
            result[param_key] = str(value)
    return result


def request_post(params):
    post_params = copy.deepcopy(constant.post_fixed_params)
    post_params.update(params)
    result = get_service_data(post_params, search_sc, service_name='post_service', method='get')
    return result


def request_doctor(params):
    # 请求医生
    doctor_params = copy.deepcopy(copy.deepcopy(constant.doctor_fixed_params))
    doctor_params.update(params)
    result = extend_area_search_2(doctor_params, search_sc, 'doctor_search', data_key='docs', method='get')
    return result


def request_hospital(params, **kwargs):
    # fixed_params: 固定参数
    hospital_params = kwargs.get('fixed_params', copy.deepcopy(constant.hospital_fixed_params))
    hospital_params.update(params)
    result = extend_area_search_2(hospital_params, search_sc, 'hospital_search', data_key='hospital', method='get')
    return result


def format_doctor(data):
    # 解析搜索的医生数据
    doctor_uuid_list = [temp['doctor_uuid'] for temp in data if temp.get('doctor_uuid')]
    doctor_package_dict = get_service_package_code_dict(doctor_uuid_list)


def extend_area_search_2(params, holder, service_name, **kwargs):
    # city ->  province -all 逐次搜索数据
    data_key = kwargs.get('data_key', 'data')
    method_params = {'method': kwargs.get('method', 'post'), 'return_response': True, 'result': {}}
    city_key = kwargs.get('city_key', 'city')
    province_key = kwargs.get('province_key', 'province')
    if city_key in params:
        res = get_service_data(params, holder, service_name, **method_params)
        if res and res.get('code') == 0 and len(res.get(data_key)) > 0:
            return {'res': res, 'search_params': params, 'area': 'city'}
        params.pop(city_key, None)
    if province_key in params:
        res = get_service_data(params, holder, service_name, **method_params)
        if res and res.get('code') == 0 and len(res.get(data_key)) > 0:
            return {'res': res, 'search_params': params, 'area': 'province'}
        params.pop(province_key, None)
    res = get_service_data(params, holder, service_name, **method_params)
    return {'res': res, 'search_params': params, 'area': 'all'}


def extend_area_search(params, holder, target, **kwargs):
    # 扩展搜索
    res = {}
    area = 'all'
    data_key = kwargs.get('data_key', 'data')
    method = kwargs.get('method', 'post')
    if 'city' in params:
        res = holder.query(params, target, method=method)
        if res['code'] == 0 and len(res.get(data_key)) > 0:
            return res, 'city'
        params.pop('city', None)
    if 'province' in params:
        res = holder.query(params, target, method=method)
        if res['code'] == 0 and len(res.get(data_key)) > 0:
            return res, 'province'
        params.pop('province', None)
    res = holder.query(params, target, method=method)
    return res, 'all'


def get_service_package_code_dict(expert_ids, holder):
    expert_package_dict = {}
    if expert_ids:
        params = {
            'rows': 100,
            "fl": "expert_id,package_code",
            "sort": "general",
            "expert": ','.join(expert_ids)
        }
        res = get_service_data(params, holder, 'service_package', method='get', return_response=True)
        if res:
            for data_item in res['data']:
                expert_id = data_item.get('expert_id')
                package_code = data_item.get('package_code')
                if expert_id and package_code and expert_id in expert_package_dict:
                    expert_package_dict[expert_id] = package_code
    return expert_package_dict


def get_dept_rank(department_uuid, holder):
    response = []
    if department_uuid:
        params = {
            'department': department_uuid,
            'row': 1,
            'fl': 'department_country_rank, department_province_rank'}
        dept_response = holder.query(params, 'department_search', method='get', return_response=True)
        if dept_response.get('department'):
            response = dept_response.get('department')
    return response


def get_consult_doctor(response):
    # 咨询信息
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


def deal_xwyz_hospital_answer(environment, data):
    result = []
    base_answer = '%(part_1)s下面是给您推荐的%(area)s医院'
    department_name = environment.get_entity(source=['entity_dict'] * 2, key=['department_classify', 'department'],
                                             attr='name', is_break=True)
    answer_text_params = {'part_1': '', 'area': ''}
    if department_name:
        answer_text_params['part_1'] = '小微推荐您去%s哦,' % department_name[0]
    area_range = data.get('area')
    area_name = environment.get_entity('entity_dict', '%s_default' % area_range, 'name')
    if area_name:
        answer_text_params['area'] = '%s的' % area_name[0]
    answer = base_answer % answer_text_params
    result.append({'text': answer})
    return result


def deal_auto_diagnose_answer(environment, data):
    result = []
    base_answer = '以下是小微为您找到的%(area)s%(doctor_name)s专家'
    pass

def deal_xwyz_doctor_quality_answer(environment, data):
    result = []
    base_answer = '以下是小微为您找到的%(doctor_name)s医生'
    doctor_name = environment.get_entity(source=['entity_dict'], key=['doctor'], attr='name', is_break=True)
    answer_text_params = {}
    if doctor_name:
        answer_text_params['doctor_name'] = doctor_name[0]
    answer = base_answer % answer_text_params
    result.append({'text': answer})
    return result


def deal_xwyz_doctor_answer(environment, data):
    # keyword_department
    result = []
    base_answer = '以下是小微为您推荐的%(area)s%(department_name)s相关专家'
    department_name = environment.get_entity(source=['entity_dict'] * 2, key=['department', 'department'],
                                             attr='name', is_break=True)
    answer_text_params = {'department_name': '', 'area': '全国'}
    if department_name:
        answer_text_params['department_name'] = department_name[0]
    area_range = data.get('area')
    area_name = environment.get_entity('entity_dict', '%s_default' % area_range, 'name')
    if area_name:
        answer_text_params['area'] = '%s的' % area_name[0]
    answer = base_answer % answer_text_params
    result.append({'text': answer})
    return result


def deal_xwyz_department_confirm_answer(environment, data):
    """
            confirm=1:是的，小微的意见与您一致，准确度为98.94%,以下是为您推荐的神经内科专家：
            among=1:经过小微的智能判断，推荐就诊神经内科，准确度为98.93%,以下是为您推荐的神经内科专家：
            confirm和among都无:
            小微有不同的看法呢，推荐就诊神经内科，准确度为98.93%,以下是为您推荐的神经内科专家：
            departmentSubset：
            小微推荐就诊神经内科，准确度为98.94%,以下是为您推荐的神经内科专家：

            accuracy 准确率
            departmentId
            departmentName
            department_updated 是否更新
            confirm = 1
            among = 1
            """
    result = []
    confirm = 0
    among = 0
    intention = environment.intention_combine
    department_classify_names = environment.get_entity('entity_dict', constant.ENTITY_DEPARTMENT_CLASSIFY, 'name')
    department_names = environment.get_entity('entity_dict', constant.ENTITY_DEPARTMENT, 'name')
    if set(department_classify_names) & set(department_names):
        if environment.intention_combine == constant.INTENTION_DEPARTMENT_CONFIRM:
            confirm = 1
            data['confirm'] = 1
        elif environment.intention_combine == constant.INTENTION_DEPARTMENT_AMONG:
            among = 1
            data['among'] = 1
    # print('among', among)
    # print('confirm', confirm)
    department_confirm_answer_dict = {'keyword': []}
    answer_text_params = {'part_1': '', 'part_2': '', 'accuracy_part': '', 'area': '全国', 'department_name': ''}
    base_answer = '%(part_1)s%(part_2)s%(accuracy_part)s以下是为您推荐的%(area)s%(department_name)s专家:'
    if department_classify_names:
        candidate_dept = department_classify_names
    elif department_names:
        candidate_dept = department_names
    if candidate_dept:
        # 必须放在第一个,confirm会重置  part_2
        department_name = candidate_dept[0]
        answer_text_params['part_2'] = '推荐就诊%s，' % department_name
        answer_text_params['department_name'] = department_name
        # 添加keyword
        transform_answer_keyword(departmentNameAnswerKeyword, department_confirm_answer_dict['keyword'],
                                 {'text': department_name})
    area_range = data.get('area')
    area_name = environment.get_entity('entity_dict', '%s_default' % area_range, 'name')
    if area_name:
        answer_text_params['area'] = area_name[0]
    if intention == 'departmentSubset':
        answer_text_params['part_1'] = '小微'
    elif confirm == 1:
        answer_text_params['part_1'] = '是的，小微的意见与您一致，'
        answer_text_params['part_2'] = ''
    elif among == 1:
        answer_text_params['part_1'] = '经过小微的智能判断，'
    else:
        answer_text_params['part_1'] = '小微有不同的看法呢，'
    if data.get('accuracy'):
        answer_text_params['accuracy_part'] = '准确度为%s，' % data['accuracy']
    department_confirm_answer_dict['text'] = base_answer % answer_text_params
    result.append(department_confirm_answer_dict)
    return result


def get_doctor_json_obj(doctors, ai_result, holder, fl_list, **kwargs):
    doctor_uuid_list = [temp['doctor_uuid'] for temp in doctors if temp.get('doctor_uuid')]
    # 获取医生服务包字典
    doctor_package_dict = get_service_package_code_dict(doctor_uuid_list, holder=holder)
    doctor_json_list = []
    for doc in doctors:
        doctor_json_obj = {}
        for params_item in fl_list:
            if params_item == 'is_service_package':
                if doctor_package_dict.get(doc.get('doctor_uuid')):
                    doctor_json_obj['service_package_id'] = doctor_package_dict[doc.get('doctor_uuid')]
            elif params_item == 'doctor_haoyuan_detail':
                doctor_haoyuan_detail = doc.get('doctor_haoyuan_detail', [])
                haoyuan_range = kwargs.get('haoyuan_range')
                if haoyuan_range:
                    haoyuan_range = sorted([float(
                        haoyuan_price_temp) for haoyuan_price_temp in haoyuan_range.split('|')])
                haoyuan_result = None
                for temp in doctor_haoyuan_detail:
                    if not haoyuan_range:
                        haoyuan_result = temp
                        break
                    doctor_haoyuan_list = temp.split('|')
                    if len(haoyuan_range) == 2 and float(doctor_haoyuan_list[5]) >= haoyuan_range[0] and \
                            float(doctor_haoyuan_list[5]) <= haoyuan_range[1]:
                        haoyuan_result = temp
                        break
                if haoyuan_result:
                    doctor_haoyuan_list = haoyuan_result.split('|')
                    doctor_json_obj['recent_haoyuan_date'] = doctor_haoyuan_list[1]
                    doctor_json_obj['recent_haoyuan_time'] = doctor_haoyuan_list[2]
                    doctor_json_obj['haoyuan_fee'] = doctor_haoyuan_list[5]
                    doctor_json_obj['haoyuan_remain_num'] = doctor_haoyuan_list[6]
            elif params_item == 'doctor_haoyuan_time':
                if doc.get('doctor_haoyuan_time'):
                    doctor_json_obj['recent_haoyuan_refresh'] = doc.get('doctor_haoyuan_time')[0]
            elif params_item == 'doctor_haoyuan_detail':
                if doc.get('doctor_haoyuan_detail'):
                    doctor_json_obj['doctor_haoyuan_detail'] = doc.get('doctor_haoyuan_detail')[0:5]
            elif params_item == 'hospital_department_detail':
                item_value = doc.get(params_item)
                if not item_value:
                    continue
                hospital = ''
                department = ''
                hospital_level = ''
                department_uuid = ''
                hospital_uuid = ''
                hospital_province = ''
                if 'departmentName' in ai_result and 'hospitalName' in ai_result:
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
                            break
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
                                break
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
                                break
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
                                    break
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
                    dept_response = get_dept_rank(department_uuid, holder=holder)
                    if dept_response:
                        doctor_json_obj.update(dept_response[0])
                if hospital_uuid:
                    doctor_json_obj['hospital_uuid'] = hospital_uuid
                if hospital_province:
                    doctor_json_obj['hospital_province'] = hospital_province
            elif params_item == 'doctor_name':
                # 未理解,待定
                if doc.get('doctor_name'):
                    doctor_json_obj[params_item] = doc[params_item]
                    if not ai_result.get('doctorName'):
                        ai_result['postDoctorName'] = []
                        ai_result['postDoctorName'].append(doc.get('doctor_name'))
            elif params_item in doc:
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


def get_hospital_json_obj(datas, ai_result, fl_list):
    # 得到医院对象
    hospital_json_list = []
    if not datas:
        return hospital_json_list
    for doc in datas:
        hospital_json = {}
        for params_item in fl_list:
            if params_item == 'hospital_hot_department':
                hospital_hot_department = doc.get('hospital_hot_department', [])
                if hospital_hot_department:
                    for index, value in enumerate(hospital_hot_department):
                        hospital_hot_department[index] = value.split('|')[1]
                hospital_json['hospital_hot_department'] = hospital_hot_department
                continue
            elif params_item == 'hospital_standard_department':
                tag = 0
                standard_department = doc.get('hospital_standard_department', [])
                hospital_department = doc.get('hospital_department', [])
                if 'departmentName' in ai_result:
                    for d_name in ai_result['departmentName']:
                        if d_name in standard_department or d_name in hospital_department:
                            tag = 1
                hospital_json['conclude_department'] = tag
                continue
            elif params_item == 'hospital_department':
                continue
            if params_item in doc:
                hospital_json[params_item] = doc[params_item]
        hospital_json_list.append(hospital_json)
    return hospital_json_list


def set_department_rank(hospital_json_list=None, department_name=''):
    # 添加地区排名
    if not hospital_json_list:
        hospital_json_list = []
    hospital_uuid = [temp.get('hospital_uuid') for temp in hospital_json_list]
    hospital_uuid_str = ','.join(hospital_uuid)
    dept_fl = ['standard_name', 'country_top_rank', 'province_top_rank',
               'city_top_rank', 'hospital_uuid', 'city_name', 'province_name']
    department_search_params = {'standard_name': department_name,
                                'sort': 'fudan_country',
                                'hospital_uuid': hospital_uuid_str,
                                'fl': 'standard_name, country_top_rank, province_top_rank, city_top_rank, hospital_uuid, city_name, province_name'}
    res_dict = extend_area_search_2(
        department_search_params, search_sc, 'department_search', data_key='docs', method='get', city_key='city_id',
        province_key='province_id')
    res = res_dict['res']
    if res and res.get('code') == 0 and res.get('department'):
        for dept_obj in res['department']:
            if dept_obj.get('hospital_uuid') in hospital_uuid:
                index = hospital_uuid.index(dept_obj.get('hospital_uuid'))
                new_obj = {}
                for item in dept_fl:
                    if item in dept_obj:
                        key = 'dept_' + item
                        new_obj[key] = dept_obj[item]
                hospital_json_list[index].update(new_obj)


def build_age_sex_symptom_result(data):
    result = {}
    slot = data.get('slot')[0]
    if slot.get('name') in ('age', 'sex'):
        result['interactive'] = [{
            'answerCode': slot['name'],
            'options': [
                {
                    "conflict": [],
                    'field': slot['name'],
                    'preDesc': '',
                    'type': 'age_sex',
                    'content': '',
                    'defaultContent': '',
                    'desc': '',
                    'defaultDesc': '',
                    'isSpecialOption': 0,
                    'validator': '1'
                }
            ]
        }]
        result['answer'] = [{
            'code': slot['name'],
            "keyword": [],
            "text": "请输入年龄性别："
        }]
    elif slot.get('name') == 'symptom':
        options = [{
            'conflict': [temp + 1 for temp in range(len(slot.get('content')))],
            'field': 'symptomName',
            'preDesc': '',
            'type': 'multiple',
            'content': '都没有',
            'defaultContent': '',
            'desc': '',
            'defaultDesc': '',
            'isSpecialOption': 0,
            'validator': '1'
        }]
        for index, content_temp in enumerate(slot.get('content')):
            options.append({
                'conflict': [0],
                'field': 'symptomName',
                'preDesc': '',
                'type': 'multiple',
                'content': content_temp,
                'defaultContent': '',
                'desc': '',
                'defaultDesc': '',
                'isSpecialOption': 0,
                'validator': '1'
            })
        result['interactive'] = [{
            'answerCode': 'symptomName',
            'options': options
        }]
        result['answer'] = [{
            'code': 'symptomName',
            "keyword": [],
            "text": "请问您还有以下症状吗？请挑选出来哦~"
        }]
    return result


def alter_require_box(result, **kwargs):
    result['interactiveBox'] = [{
        'answerCode': 'alter_require',
        'options': [
            {
                "conflict": [],
                'field': 'alter_require',
                'preDesc': '',
                'type': 'single',
                'content': kwargs.get('content'),
                'defaultContent': '',
                'desc': '',
                'defaultDesc': '',
                'isSpecialOption': 0,
                'validator': '1'
            }
        ]
    }]
    return result


def reset_box_type(rule_result, box_type='text_q'):
    # 重置交互框的type为text_q, 应用端收到这个type, 把输入的数据放入q里
    for temp in rule_result.get('interactiveBox', [{}])[0].get('options', []):
        temp['type'] = box_type
    return rule_result


def add_option_attribute(rule_result, params):
    for temp in rule_result.get('interactiveBox', [{}])[0].get('options', []):
        temp.update(params)
    return rule_result


def set_placeholder(rule_result, content):
    # 设置placeholder
    for temp in rule_result.get('interactiveBox', [{}])[0].get('options', []):
        temp['placeholder'] = content


def doctor_card_transform(card):
    if not card:
        return
    field_trans = {
        'hospital_uuid': 'hospital_id',
        'doctor_photo_absolute': 'doctor_photo',
        'doctor_uuid': 'doctor_id',
        'department_uuid': 'department_id'
    }
    for temp in card:
        for target, source in field_trans.items():
            if source in temp:
                value_temp = temp.pop(source, None)
                temp[target] = value_temp


def parse_q(data_dict, keys):
    result = None
    for temp in keys:
        if data_dict.get(temp):
            result = data_dict[temp]
            # 特殊处理
            if temp == 'find_hospital_is_has':
                if result[0] == '没有':
                    result = None
            break
    return result


def parse_input(input_list, keys):
    result = None
    for index in range(len(input_list) - 1, -1, -1):
        temp = input_list[index]
        q = parse_q(temp, keys)
        if q:
            result = q
            break
    return result


def add_area_params(params, entity):
    if entity.get('city_default') and entity['city_default'][0].get('id'):
        params['city_id'] = entity['city_default'][0].get('id')
    if entity.get('province_default') and entity['province_default'][0].get('id'):
        params['province_id'] = entity['province_default'][0].get('id')


def trans_entity_input(input_dict, **kwargs):
    # 把list 转为 逗号分隔
    trans_entity_list = kwargs.get('trans_entity_list', ['symptomName'])
    for temp in trans_entity_list:
        entity_temp = input_dict.get(temp)
        if entity_temp and isinstance(entity_temp, list):
            input_dict[temp] = ','.join(entity_temp)


def trans_area(input_dict, **kwargs):
    # 地区选择不限传-1
    area_key = ['city', 'province']
    for temp in area_key:
        if input_dict.get(temp) == '0':
            input_dict.pop(temp, None)


def del_params(input_dict, **kwargs):
    # 删除指定为空的key, 包括 空[]
    key = kwargs.get('key')
    if not key:
        return
    for temp in key:
        if not input_dict.get(temp):
            input_dict.pop(temp, None)


def greeting_interactive(environment, process_result, data):
    # 包含guide、greeting、corpusGreeting, 无实体 & 没有匹配语料库回答, 第一次返回提示引导语,第二次返回交互框
    entity_type = {'symptom', 'disease', 'department',
                   'hospital', 'body_part', 'medicine', 'doctor', 'physical', 'examination'}
    greeting_num = int(environment.input_dict.get('greeting_num', 0))
    entity_keys = set(environment.entity_dict.keys())
    exist_entity = 0
    if entity_keys & entity_type:
        exist_entity = 1
    match_type = process_result.get('match_type')
    if exist_entity == 0 and match_type == 2:
        if greeting_num == 0:
            data['show_guiding'] = 1
            greeting_num = 1
        elif greeting_num >= 1:
            data['show_guiding'] = 2
            greeting_num = 2
    else:
        # 有实体 或者 匹配上语料库回答,重置
        greeting_num = 0
    data['greeting_num'] = greeting_num


def check_entity(environment, data):
    """
    exist_entity: 1:存在实体, 0-不存在实体
    service_list: 1.极速问诊, 2.一病多问
    """
    entity_type = {'symptom', 'disease', 'department', 'hospital_department', 'hospital',
                   'body_part', 'medicine', 'doctor', 'physical', 'examination'}
    entity_key_set = set(environment.entity_dict.keys())
    if entity_key_set & entity_type:
        data['exist_entity'] = 1  # 有entity_type里的实体类型
    if data.get('is_end') == 1 and entity_key_set & {'symptom', 'body_part'}:
        data['service_list'] = [1, 2]  # 结束的时候若问句里有症状、身体部位词, 推荐极速问诊和一病多问
    if not (data.get('intention') in ('greeting', 'corpusGreeting', 'guide')):
        data['greeting_num'] = 0
    if 'patient_group' in environment.accompany_intention:
        request_params = {'skill': 'question_answer', 'q': '微医病友群'}
        patient_group_out_link = {
            'name': '微医病友群',
            'action': 3,
            'type': 4,
            'location': 1,
            'text': json.dumps(request_params, ensure_ascii=False)
        }
        data.setdefault('out_link', []).append(patient_group_out_link)


def return_entity(environment, data):
    # 返回固定实体
    """
    departmentId、departmentName、doctorId、doctorName、diseaseId、diseaseName、hospitalId、hospitalName、
    treatmentId、treatmentName、medicineId、medicineName、symptomId、symptomName、cityId、cityName、
    provinceId、provinceName
    """
    entity_mapping = {
        'departmentId': [['department_classify', 'department'], 'id', {'is_break': True}, ['entity_dict'] * 2],
        'doctorId': ['doctor', 'id'],
        'diseaseId': ['disease', 'id'],
        'hospitalId': ['hospital', 'id'],
        'treatmentId': ['treatment', 'id'],
        'medicineId': ['medicine', 'id'],
        'symptomId': ['symptom', 'id'],
        'cityId': ['city_default', 'id'],
        'provinceId': ['province_default', 'id'],

        'departmentName': [['department_classify', 'department'], 'name', {'is_break': True}, ['entity_dict'] *2],
        'doctorName': ['doctor', 'name'],
        'diseaseName': ['disease', 'name'],
        'hospitalName': ['hospital', 'name'],
        'treatmentName': ['treatment', 'name'],
        'medicineName': ['medicine', 'name'],
        'symptomName': ['symptom', 'name'],
        'cityName': ['city_default', 'name'],
        'provinceName': ['province_default', 'name']
    }
    result = {}
    for key, params_list in entity_mapping.items():
        source = 'entity_dict'
        params = {}
        if len(params_list) > 2:
            params = params_list[2]
            source = params_list[3]
        entity_temp = environment.get_entity(source=source, key=params_list[0], attr=params_list[1], **params)
        if entity_temp:
            result[key] = entity_temp
    data.update(result)


def preprocess(query_dict):
    # 对xwyz、xwyz_doctor的机构强制设置mode,其他机构根据入参决定,可能为ai_qa、loudspeaker_box
    organization = query_dict.get(constant.QUERY_FIELD_ORGANIZATION)
    if organization == constant.organization_dict.get(constant.VALUE_MODE_XWYZ):
        query_dict[constant.QUERY_FIELD_MODE] = constant.VALUE_MODE_XWYZ
    elif organization == constant.organization_dict.get(constant.VALUE_MODE_XWYZ_DOCTOR):
        query_dict[constant.QUERY_FIELD_MODE] = constant.VALUE_MODE_XWYZ_DOCTOR
    query_dict[constant.QUERY_FIELD_ORIGIN_INPUT] = copy.deepcopy(query_dict[constant.QUERY_FIELD_INPUT])


def postprocess(environment, result):
    data = result['data']
    dialogue = data.setdefault('dialogue', {})
    if environment.skill:
        return result
    elif environment.intention_combine:
        transform_dict_data(dialogue, data, {
            'intention': 'intention', 'intentionDetails': 'intentionDetails'})
        # exist_entity、service_list、greeting_num
        check_entity(environment, data)
        return_entity(environment, data)
        data.pop('origin_input', None)
        return result


