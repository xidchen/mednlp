#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
entity_extract.py -- extract medical entities from content via priority order
Author : gaozp
Create on 2017.12.28 Wed
"""

import os
import global_conf
import ailib.utils.ioutil as ioutil
from ailib.storage.db import DBWrapper


base_path = os.path.join(os.path.dirname(__file__), '../../')
# dic_base_path = os.path.join(base_path, './data/dict/mmseg/')
dic_base_path = global_conf.dict_mmseg_path


def filter_doctor_dict(verbose=False):
        
    bad_pattern_str = '1234567890'
    bad_pattern_path = os.path.join(dic_base_path, './../bad_name_pattern.txt')
    first_name_str = ''
    first_name_path = os.path.join(dic_base_path, './../common_chinese_first_name.txt')

    with open(bad_pattern_path, "r") as bad_pattern_file:
        for bad_pattern in bad_pattern_file:
            bad_pattern = bad_pattern.strip()
            if len(bad_pattern) < 4:
                bad_pattern_str += bad_pattern

    with open(first_name_path, "r") as first_name_file:
        for first_name in first_name_file:
            first_name = first_name.strip()
            first_name_str += first_name

    # print(first_name_str)
    
    doctor_dic_path = os.path.join(dic_base_path, './doctor.dic')
    doctor_dic_filter_path = os.path.join(dic_base_path, './doctor_filter.dic')
    doctor_dic_error_path = os.path.join(dic_base_path, './doctor_error.dic')

    doctor_dic = open(doctor_dic_path, "r")
    doctor_dic_filter = open(doctor_dic_filter_path, "w")
    doctor_dic_error = open(doctor_dic_error_path, "w")
    for line in doctor_dic:
        try :
            doctor_name, _  = line.strip().split("\t")
            
            if len(doctor_name) >= 4 or len(doctor_name) <=1:
                doctor_dic_error.write("1 " + line)
                pass
            elif doctor_name in bad_pattern_str:
                doctor_dic_error.write("2 " + line)
                pass
            elif doctor_name[0] not in first_name_str:
                doctor_dic_error.write("3 " + line)
                pass  
            elif len(doctor_name)>2 and doctor_name[1:] in bad_pattern_str:
                doctor_dic_error.write("4 " + line)
                pass
            elif len(doctor_name)>2 and doctor_name[:-1] in bad_pattern_str:
                doctor_dic_error.write("5 " + line)
                pass
            elif doctor_name[-1] in "0123456789":
                doctor_dic_error.write("6 " + line)
                pass
            else :
                # print line 
                if verbose:
                    print(doctor_name, len(doctor_name), type(doctor_name))
                doctor_dic_filter.write(line)
        except:
            continue

    doctor_dic.close()
    doctor_dic_filter.close()
    doctor_dic_error.close()
    ioutil.file_replace(doctor_dic_filter_path, doctor_dic_path)        
    pass


def extend_area(line):
    """
    扩展area信息.
    参数:
    line->area字典,结构:{'name':, 'id':}
    返回值->扩展的area数组.
    """

    area, area_id = line['name'], line['id']
    if area in ('北京', '上海', '天津', '重庆') and area_id > 10:
        return None
    areas = [line]
    area_unicode = area
    # extend for province 
    if area_id <= 35:
        # 处理直辖市
        if area in ('北京', '上海', '天津', '重庆'):
            area_extend = area + '市' 
        # 处理特别行政区
        elif area in ('香港', '澳门'):
            area_extend = area + '特别行政区'
        # 处理自治区
        elif area in ['宁夏', '新疆', '西藏', '广西', '内蒙古']:
            zzq_dict = {'宁夏':'回族', '新疆':'维吾尔', '西藏':'',
                        '广西':'壮族', '内蒙古':''}
            area_extend = area + zzq_dict[area] + '自治区'
        # 其他省份
        else:
            area_extend = area + '省'
        areas.append({'name': area_extend, 'id': area_id})
    # extend for city
    elif area_id <= 581:
        if not area.endswith('自治州'):
            area_extend = area + '市'
            areas.append({'name': area_extend, 'id': area_id})
        # extend for country
    else :
        if area.endswith('新区') and len(area_unicode)>3:
            area_base = area_unicode[:-2]
            areas.append({'name': str(area_base), 'id': area_id})
        elif len(area_unicode) > 2:
            if area.endswith('县') or area.endswith('市') or area.endswith('区'):
                area_base = area_unicode[:-1]
                areas.append({'name': str(area_base), 'id': area_id})
    return areas


def extend_symptom(verbose=False):
    
    # 用同义词扩展symptom
    symptom_wy_path = os.path.join(dic_base_path, './symptom_wy.dic')
    symptom_wy_synonym_path = os.path.join(dic_base_path, './../synonym/wy_symptom_name.dic.default')
    symptom_wy_extend_path = os.path.join(dic_base_path, './symptom_wy_synonym_extend.dic')

    if os.path.exists( symptom_wy_extend_path ):
        os.remove( symptom_wy_extend_path )

    # print symptom_wy_synonym_path
    symptom_wy_synonym_dict = {}
    with open(symptom_wy_synonym_path, 'r') as symptom_wy_synonym:

        for line in symptom_wy_synonym:
            key, value = line.strip().split('\t')
            key = key.strip()
            value = str( value.strip() ) 
            if key in symptom_wy_synonym_dict:
                values = symptom_wy_synonym_dict[key]
                values.append(value)
            else :
                values = [value]
            symptom_wy_synonym_dict[key] = values


    for k, v in symptom_wy_synonym_dict.items():
        synonym_list = v
        synonym_pairs = [(s1, s2) for s1 in synonym_list for s2 in synonym_list if s1 != s2]
        
        for pair in synonym_pairs:
            search_pattern = str( pair[0].strip() )
            replace_pattern = str( pair[1].strip() )
            
            with open(symptom_wy_path, 'r') as symptom_wy, \
                open(symptom_wy_extend_path, 'a') as symptom_wy_extend:

                for line in symptom_wy:

                    symptom, symptom_id = line.strip().split('\t')

                    if search_pattern in symptom:
                        new_symptom = symptom.replace(search_pattern, replace_pattern)
                        
                        if verbose:
                            print(search_pattern, replace_pattern, symptom, new_symptom)
                        
                        symptom_wy_extend.write(new_symptom + '\t' + symptom_id + '\n')


def extend_core():
    pass


def load_entity_info():
    """
    加载实体信息.
    """
    sql = """
    SELECT
        e.entity_name name,
        e.entity_uuid id
    FROM ai_union.entity e
    where e.entity_type = 'oFw6zran'
    """
    model = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')
    rows = model.get_rows(sql)
    return list(rows)

def get_dict_from_sql(entity_type):
    filename = 'mmseg/' + entity_type + '_kg_custom.dic'
    entity_path = os.path.join(global_conf.dict_path, filename)
    print(entity_path)
    output_file = open(entity_path, "w", encoding='utf-8')
    for dict_one in load_entity_info():
        output_file.write(dict_one.get('name') + '\t' + dict_one.get('id') + '\n')
    output_file.close()


if __name__ == "__main__":
    
    # filter_doctor_dict(verbose=False)
    # extend_area_dict(verbose=True)
    # extend_symptom(verbose=True)
    result = load_entity_info()
    print(type(result))
    get_dict_from_sql('inspection')