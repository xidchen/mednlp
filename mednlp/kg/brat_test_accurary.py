#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
brat_test_accuracy.py -- structuralization : the accuracy of structuration
Author : yinwd
Create on 2018.08.10
"""
import re
import os
import codecs
import numpy as np
import pandas as pd
import json
from mednlp.utils.utils import print_time

###
### method：启用自己虚拟环境的服务
import requests
def get_web_data(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        return u'请求失败'

## 分词
def web_structuration(inputdata):
    url = 'http://172.27.249.130:2838/medical_record?medical_history='
    url = url + inputdata
    outdata = get_web_data(url)
    segment_dict =  eval(outdata)##返回字典格式
    data_list = segment_dict['data']
    return data_list
###
'''
### method：启用测试服务器上线的服务
import global_conf
from mednlp.dao.ai_service_dao import ai_services

def web_structuration(medical_history):
    param = {'medical_history': medical_history}
    tokens, err_msg = ai_services(param, 'medical_record', 'post')
    return tokens
'''
### brat 标注数据转化
@print_time
def get_data_brat(n_list, entity_name, R_put=False, A_put=False):
    result_list = []
    for n in n_list:
        data_path = '/home/yinwd/work/brat-v1.3_Crunchy_Frog/data/bart_ner/data{}/'.format(n)
        # result_list = []
        for m in range(n-100, n):
            # print('----------data{}----------'.format(m))
            ## brat标注的结果
            brat_ont_path = data_path + 'data{}.ann'.format(m)
            brat_data_list = codecs.open(brat_ont_path, 'r', encoding='utf8').readlines()
            brat_result_tran = []
            property = []
            char_relation = []
            status_relation = []
            if brat_data_list :
                for bratdata in brat_data_list:
                    brat_dict = {}
                    prop_dict = {}
                    data_split = re.split('\t', bratdata.strip())
                    if 'T' in data_split[0]:
                        type_words, start, end = re.split('\s', data_split[1])
                        if  type_words == entity_name.upper():
                            brat_dict['type'] = entity_name
                            brat_dict['start'] = int(start)
                            brat_dict['name'] = data_split[2]
                            brat_dict['id'] = data_split[0]
                            brat_result_tran.append(brat_dict)
                        else:
                            prop_dict['type'] = type_words.lower().replace('frequence', 'frequency')
                            prop_dict['text'] = data_split[2]
                            prop_dict['position'] = [int(start), int(end)-1]
                            prop_dict['rid'] = data_split[0]
                            property.append(prop_dict)
                    else:
                        pass

                    if R_put:
                        if 'R' in data_split[0]:
                            char_content = re.sub('CHARACTER|Arg1|Arg2|:', '', data_split[1])
                            char_sp = re.split('\s', char_content)
                            char_relation.append(char_sp)
                        else:
                            pass
                    if A_put:
                        if 'A' in data_split[0]:
                            status_content = re.sub('Category', '', data_split[1])
                            status_sp = re.split('\s', status_content)
                            status_relation.append(status_sp)
                        else:
                            pass
                ### 利用关系的对应组，合并成为是实体对应的属性字典列表
                for brat_dict in brat_result_tran:
                    relation_rid_list = [x[1] for x in char_relation if x[2]==brat_dict['id']]
                    ## 当状态也和实体连线则不需要这里的status_list进行补充
                    # status_list = [{'text':u'无', 'type': 'status'} for x in status_relation if (x[1]==brat_dict['id'] and x[2]=='-')]
                    # print brat_dict['id'], relation_rid_list
                    property_dict = []
                    if relation_rid_list:
                        for relation_rid in relation_rid_list:
                            rid_dict = [x for x in property if x['rid']==relation_rid]
                            property_dict.extend(rid_dict)
                    else:
                        pass
                    # if status_list:
                            # property_dict.extend(status_list)
                    # else:
                        # pass
                    brat_dict['property'] = property_dict
            brat_result_tran = sorted(brat_result_tran,  key=lambda x: x['start'])
            result_list.append(brat_result_tran)
    return result_list

### web 结构化服务
def get_data_webservice_new(n_list):
    # 注意当 结构化发生变动的时候，要删除 该文件重新生成
    data_write = open('structuration_result.txt', 'w', encoding='utf-8')
    for n in n_list:
        data_path = '/home/yinwd/work/brat-v1.3_Crunchy_Frog/data/bart_ner/data{}/'.format(n)
        for m in range(n-100,n):
            print('----------data{}----------'.format(m))
            data_one_path = data_path + 'data{}.txt'.format(m)
            data_txt = "".join(codecs.open(data_one_path, 'r', encoding='utf8').readlines())
            data_txt = re.sub('\n', u'。', data_txt)
            ## 结构化服务的结构
            web_result = web_structuration(data_txt)
            if web_result:
                structuration = web_result["medical_history"]
                result_dict = json.dumps([m, structuration], ensure_ascii=False)
                # print result_dict
            else:
                result_dict = json.dumps([m, 'no_result'], ensure_ascii=False)
            data_write.write(result_dict + '\n')
    data_write.close()


@print_time
def get_entitytype_result(n_list, entity_name):

    if entity_name == 'physical': entity_name = 'physical_examination'
    if entity_name == 'examination': entity_name = 'inspection'
    if entity_name == 'cure': entity_name = 'treatment'
    if not os.path.isfile("structuration_result.txt"):
        get_data_webservice_new(n_list)
    result_entity_list = []
    result_data = codecs.open('structuration_result.txt', 'r', encoding='utf-8').readlines()
    for result in result_data:
        result = eval(result)
        if result:
            if result[1] != 'no_result':
                structuration_entity = []
                for entity_dict in result[1]:
                    if entity_dict.get('type') == entity_name:
                        structuration_entity.append(entity_dict)
                result_entity_list.append(structuration_entity)
            else:
                result_entity_list.append([])
    return result_entity_list

@print_time
def get_data_webservice(n_list, entity_name):
    result_list = []
    for n in n_list:
        data_path = '/home/yinwd/work/brat-v1.3_Crunchy_Frog/data/bart_ner/data{}/'.format(n)
        if entity_name == 'physical': entity_name = 'physical_examination'
        if entity_name == 'examination': entity_name = 'inspection'
        if entity_name == 'cure': entity_name = 'treatment'

        for m in range(n-100,n):
            # rint('----------data{}----------'.format(m))
            data_one_path = data_path + 'data{}.txt'.format(m)
            data_txt = "".join(codecs.open(data_one_path, 'r', encoding='utf8').readlines())
            data_txt = re.sub('\n', u'。', data_txt)
            ## 结构化服务的结构
            web_result = web_structuration(data_txt)
            if web_result:
                structuration = web_result["medical_history"]
                structuration_entity = []
                for entity_dict in structuration:
                    if entity_dict.get('type') == entity_name:
                        structuration_entity.append(entity_dict)
                    else:
                        pass
                # print Encode(structuration)
                result_list.append(structuration_entity)
                # print result_dict
            else:
                result_list.append([])
    return result_list

### 准确率
def accuracy_structuration(n_list, entity_name, R_put=False, A_put=False):
    '''
    逻辑：首先判断两个结果的长度是否相等，如果不等则代码存在问题。
    其次，对每一个文本两个结果（标注结果和结构化结果）进行一一比较，比较的逻辑是标注的症状在结构化的症状中（因为标注拆分的症状细）
    如果对应多个，则按照先后排序一一对应。
    最后，对对应上的实体的属性进行比较，完全相等则记为正确结构化属性。分不同属性统计其准确率、召回率。
    '''
    brat_result = get_data_brat(n_list, entity_name, R_put=True, A_put=False)
    print('===========brat_result is finished============')
    ### 此处 webservice_result 是获取全部实体的结果
    # webservice_result = get_data_webservice(n_list, entity_name)
    webservice_result = get_entitytype_result(n_list, entity_name)
    print('===========model_result is finished============')
    char_all = ['time_happen', 'time_endurance', 'frequency', 'bodypart', 'size', 'num', 'degree', 'nature', 'cause',
    'exacerbation', 'alleviate', 'smell', 'color', 'status', 'period', 'efficacy', 'administration_route', 'dosage', 'effect', 'value']

    web_dict_all = {}
    brat_dict_all = {}
    acc_dict_all = {}
    web_sym_all = 0
    brat_sym_all = 0
    acc_sym_all = 0
    for char in char_all:
        web_dict_all[char] = 0
        brat_dict_all[char] = 0
        acc_dict_all[char] = 0
    print(len(brat_result), len(webservice_result))
    if len(brat_result)!= len(webservice_result):
        raise ValueError
    else:
        logical_result = logical_accuracy_structuration(brat_result, webservice_result, char_all, entity_name)
        for index, char_dict_list in enumerate(webservice_result):
            brat_dict_list = brat_result[index]
            # brat_sym_keys = [x['name'] for x in brat_dict_list if x['type']=='symptom']
            # web_sym_keys = [x['text'] for x in char_dict_list if x['type']=='symptom']
            len_web = len(char_dict_list)
            web_sym_all += len_web
            len_brat = len(brat_dict_list)
            brat_sym_all += len_brat
            compare_dict_list = []
            for web_dict in char_dict_list:
                web_sym = web_dict['text']
                web_pos = web_dict['position']
                if web_pos:
                    web_posi = web_pos[1]
                    web_posb = web_pos[0]
                else:
                    web_posi = 0
                    web_posb = 0
                compare_dict = {}
                for brat_dict in brat_dict_list:
                    brat_sym = brat_dict['name']
                    brat_posi = brat_dict['start']
                    ## 以为有些brat标注不完全，如症状 一般没有把部位标注在一起
                    if brat_sym in web_sym and int(web_posi)-4 <= brat_posi <= int(web_posi)+4:
                        compare_dict['web'] = web_dict
                        compare_dict['brat'] = brat_dict
                        compare_dict_list.append(compare_dict)
                    elif brat_sym in web_sym and int(web_posb)-2 <= brat_posi <= int(web_posb)+2:
                        compare_dict['web'] = web_dict
                        compare_dict['brat'] = brat_dict
                        compare_dict_list.append(compare_dict)
                    else:
                        pass
            len_acc = len(compare_dict_list)
            acc_sym_all += len_acc
            index_n = index + n_list[-1] - len(n_list) * 100
            write_entity(index_n, char_dict_list, brat_dict_list, compare_dict_list, entity_name)
            #print '--------data{}-------'.format(index_n)
            #print Encode(compare_dict_list)
            #print '==================================='
            ### 计算 各种属性变量的值
            web_pro_text = []
            brat_pro_text = []
            acc_pro_text = []
            for compare_dt in compare_dict_list:
                web_property = compare_dt['web']['property']
                brat_property = compare_dt['brat']['property']
                if web_property:
                    web_pro_list = []
                    for x in web_property:
                        if entity_name == 'physical':
                            web_pro_list.append(['value', str(x['text']).replace('\\','')])
                            # print Encode(['value', str(x['text']).replace('\\','')])
                        elif entity_name == 'examination':
                            if x['type'] not in ['bodypart', 'time_happen']:
                                web_pro_list.append(['value', str(x['text']).replace('\\','')])
                            else:
                                web_pro_list.append([str(x['type']), str(x['text'])])
                        else:
                            if x['type'] in ['exacerbation', 'alleviate']:
                                web_pro_list.append([str(x['type']), str(x['value'])])
                            # 因为有\存在
                            elif x['type'] in ['dosage', 'frequency', 'size', 'num']:
                                web_pro_list.append([str(x['type']), str(x['text']).replace('\\','')])
                            else:
                                web_pro_list.append([str(x['type']), str(x['text'])])
                    # web_pro_list = [[str(x['type']), str(x['text'])] for x in web_property]
                else:
                    web_pro_list = []
                if brat_property:
                    brat_pro_list = [[str(x['type']), str(x['text'])] for x in brat_property]
                else:
                    brat_pro_list = []
                # web_dict_pro = _dict_add(web_pro_list)
                # brat_dict_pro = _dict_add(brat_pro_list)
                acc_pro_list = []
                for wp in web_pro_list:
                    if wp in brat_pro_list:
                       acc_pro_list.append(wp)
                    else:
                        pass
                # acc_dict_pro =  _dict_add(acc_pro_list)
                web_pro_text.extend(web_pro_list)
                brat_pro_text.extend(brat_pro_list)
                acc_pro_text.extend(acc_pro_list)

            write_character(index_n, web_pro_text, brat_pro_text, acc_pro_text, entity_name)

            web_dict_all = _dict_add_two(web_pro_text, web_dict_all)
            brat_dict_all =  _dict_add_two(brat_pro_text, brat_dict_all)
            acc_dict_all =  _dict_add_two(acc_pro_text, acc_dict_all)
        # return web_dict_all, brat_dict_all, acc_dict_all
        match_result_df = dict_dataframe(web_dict_all, brat_dict_all, acc_dict_all)
        p_sym = round(acc_sym_all/float(web_sym_all), 4)
        r_sym = round(acc_sym_all/float(brat_sym_all), 4)
        f_sym = 2 * p_sym * r_sym / (r_sym + p_sym)
        sym_df = pd.DataFrame([entity_name, brat_sym_all, web_sym_all, acc_sym_all, p_sym, r_sym, f_sym]).T
        sym_df.columns = ['character', 'match_brat', 'match_web', 'match_acc', 'Precision', 'Recall', 'F-Measure']
        # print sym_df
        match_result_df = match_result_df.append(sym_df)
        match_result_df.index = [x for x in range(match_result_df.shape[0])] ## 防止由于index相同导致删除多了
        # print match_result_df
        match_result_df = drop_dataframe(match_result_df)
        # print match_result_df
        result_df = pd.merge(logical_result, match_result_df, how='left', on='character')
        result_df.to_excel('structuration_result_df_new.xlsx')
        return result_df

def logical_accuracy_structuration(brat_result, webservice_result, char_all, entity_name):
    '''
    ## 新修改20180710
    逻辑：首先判断两个结果的长度是否相等，如果不等则代码存在问题。
    其次，对每一个文本两个结果（标注结果和结构化结果）进行一一比较，比较的逻辑是标注的症状在结构化的症状中（因为标注拆分的症状细）
    如果对应多个，则按照先后排序一一对应。
    最后，对所有的实体的属性进行比较，完全相等则记为正确结构化属性。分不同属性统计其准确率、召回率。
    '''
    '''
    brat_result = get_data_brat(n_list, entity_name, R_put=True, A_put=False)
    print('=======================')
    ### 此处 webservice_result 是获取全部实体的结果
    webservice_result = get_data_webservice(n_list, entity_name)
    print('++++++++++++++++++++++')

    char_all = ['time_happen', 'time_endurance', 'frequency', 'bodypart', 'size', 'num', 'degree', 'nature', 'cause',
    'exacerbation', 'alleviate', 'smell', 'color', 'status', 'period', 'efficacy', 'administration_route', 'dosage', 'effect', 'value']
    '''
    web_dict_all = {}
    brat_dict_all = {}

    web_sym_all = 0
    brat_sym_all = 0

    for char in char_all:
        web_dict_all[char] = 0
        brat_dict_all[char] = 0

    if len(brat_result)!= len(webservice_result):
        print(len(brat_result),len(webservice_result))
        return 'the code is wrong'
    else:
        for index, char_dict_list in enumerate(webservice_result):
            brat_dict_list = brat_result[index]
            # brat_sym_keys = [x['name'] for x in brat_dict_list if x['type']=='symptom']
            # web_sym_keys = [x['text'] for x in char_dict_list if x['type']=='symptom']
            len_web = len(char_dict_list)
            web_sym_all += len_web
            len_brat = len(brat_dict_list)
            brat_sym_all += len_brat

            #print '--------data{}-------'.format(index_n)
            #print Encode(compare_dict_list)
            #print '==================================='
            ### 计算 各种属性变量的值
            web_pro_text = []
            brat_pro_text = []
            ### 模型识别结果
            for char_dt in char_dict_list:
                web_property = char_dt['property']
                if web_property:
                    web_pro_list = []
                    for x in web_property:
                        if entity_name == 'physical':
                            web_pro_list.append(['value', str(x['text'])])
                        elif entity_name == 'examination':
                            if x['type'] not in ['bodypart', 'time_happen']:
                                web_pro_list.append(['value', str(x['text'])])
                            else:
                                web_pro_list.append([str(x['type']), str(x['text'])])
                        else:
                            if x['type'] in ['exacerbation', 'alleviate']:
                                web_pro_list.append([str(x['type']), str(x['value'])])
                            else:
                                web_pro_list.append([str(x['type']), str(x['text'])])
                    # web_pro_list = [[str(x['type']), str(x['text'])] for x in web_property]
                else:
                    web_pro_list = []
                web_pro_text.extend(web_pro_list)
            ## 标注结果
            for brat_dt in brat_dict_list:
                brat_property = brat_dt['property']
                if brat_property:
                    brat_pro_list = [[str(x['type']), str(x['text'])] for x in brat_property]
                else:
                    brat_pro_list = []
                brat_pro_text.extend(brat_pro_list)

            web_dict_pro = _dict_add(web_pro_text)
            brat_dict_pro = _dict_add(brat_pro_text)
            for key in web_dict_all:
                if key in web_dict_pro:
                    web_dict_all[key] += web_dict_pro[key]
                else:
                    pass
                if key in brat_dict_pro:
                    brat_dict_all[key] += brat_dict_pro[key]
                else:
                    pass
        result_df = pd.DataFrame(char_all, columns=['character'])
        result_df['brat'] = [brat_dict_all[x] for x in char_all]
        result_df['webservice'] = [web_dict_all[x] for x in char_all]
        entity_df = pd.DataFrame([[entity_name, brat_sym_all, web_sym_all]], columns = ['character', 'brat', 'webservice'])
        result_df = result_df.append(entity_df)
        result_df.index = [x for x in range(result_df.shape[0])] ## 防止由于index相同导致删除多了
        result_df = drop_dataframe(result_df)
        # result_df.to_excel('real_structuration_result.xlsx')
        return result_df

### 写出 没有识别出来的实体 和 未标注的实体
def write_entity(index, char_dict_list, brat_dict_list, compare_dict_list, entity_name):
    data_path = '/home/yinwd/work/mynlp/structuralization/error_analysis/{}'.format(entity_name)

    not_brat_entity = codecs.open(data_path+'_not_brat_entity.txt', 'a', encoding='utf8')
    not_web_entity = codecs.open(data_path+'_not_web_entity.txt', 'a', encoding='utf8')
    web_list = [x['web'] for x in compare_dict_list]
    brat_list = [x['brat'] for x in compare_dict_list]
    data_id = 'data{}'.format(index)
    for char_dict in char_dict_list:
        if char_dict not in web_list:
            not_brat_entity.write(data_id + '\t' + char_dict['text'] + '\n')
        else:
            pass
    for br_dict in brat_dict_list:
        if br_dict not in brat_list:
            not_web_entity.write(data_id + '\t' + br_dict['name'] + '\n')
        else:
            pass
    not_brat_entity.close()
    not_web_entity.close()

### 写出 没有识别出来的属性 和 未标注的属性
def write_character(index, web_pro_text, brat_pro_text, acc_pro_text, entity_name): 
    data_path = '/home/yinwd/work/mynlp/structuralization/error_analysis/{}'.format(entity_name)
    not_brat_character = codecs.open(data_path+'_not_brat_character.txt', 'a', encoding='utf8')
    not_web_character = codecs.open(data_path+'_not_web_character.txt', 'a', encoding='utf8')
    data_id = 'data{}'.format(index)

    for web in web_pro_text:
        if web not in acc_pro_text:
            not_brat_character.write(data_id + '\t' + (web[0]+':'+web[1]) + '\n')
            # not_brat_character.write(data_id + '\t' + "&".join([(x[0]+':'+x[1]) for x in web]) + '\n')
        else:
            pass
    for brat in brat_pro_text:
        if brat not in acc_pro_text:
            not_web_character.write(data_id + '\t' + (brat[0]+':'+brat[1]) + '\n')
            # not_web_character.write(data_id + '\t' + "&".join([(x[0]+':'+x[1]) for x in brat]) + '\n')
        else:
            pass
    not_brat_character.close()
    not_web_character.close()

### 累计不同属性的个数01
def _dict_add(data_list):
    dict = {}
    for dt in data_list:
        key = dt[0]
        if key in dict:
            dict[key] += 1
        else:
            dict[key] = 1
    return dict 

### 累计不同属性的个数02
def _dict_add_two(data_list, dict_need):
    if data_list:
        for dt_txt in data_list:
            # for dt in dt_txt:
            key = dt_txt[0]
            # print key
            if key in dict_need:
                dict_need[key] += 1
            else:
                pass
    else:
        pass
    return dict_need

### 计算属性的准确性，转为dataframe格式
def dict_dataframe(web_dict_all, brat_dict_all, acc_dict_all):
    keys_ls = list(web_dict_all.keys())
    values_web = [web_dict_all[x] for x in keys_ls]
    values_brat = [brat_dict_all[x] for x in keys_ls]
    value_acc = [acc_dict_all[x] for x in keys_ls]
    Precision = []
    Recall = []
    F_Measure = []
    for index, web_v in enumerate(values_web):
        brat_v = values_brat[index]
        acc_v = value_acc[index]
        if web_v != 0:
            Precision.append(round(acc_v/float(web_v), 4))
        else:
            Precision.append(0)
        if brat_v != 0:
            Recall.append(round(acc_v/float(brat_v), 4))
        else:
            Recall.append(0)
    for ind, p in enumerate(Precision):
        r = Recall[ind]
        if (p+r) != 0:
            F_Measure.append(2*p*r/(p+r))
        else:
            F_Measure.append(0)
    df = pd.DataFrame(keys_ls, columns=['character'])
    df['match_brat'] = values_brat
    df['match_web'] = values_web
    df['match_acc'] = value_acc
    df['Precision'] = Precision
    df['Recall'] = Recall
    df['F-Measure'] = F_Measure
    return df

### 删除全0行
def drop_dataframe(dataframe):
    lines = dataframe.shape[0]
    all_zero = []
    for line in range(lines):
        if sum(dataframe.iloc[line, 1:]) == 0:
           all_zero.append(line)
        else:
            pass
    dataframe.drop(dataframe.index[all_zero], inplace=True)
    return dataframe

if __name__ == '__main__':
    ner_type_list = ['symptom', 'disease', 'medicine', 'cure', 'examination', 'physical']
    for ner_type in ner_type_list:
        result_df = accuracy_structuration([100,200], ner_type, R_put=True, A_put=False)
        print('=============>', ner_type, '<===============')
        print(result_df)
