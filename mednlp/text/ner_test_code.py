#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import codecs
import global_conf
import numpy as np
import pandas as pd
from mednlp.utils.utils import Encode, print_time
from ailib.client.ai_service_client import AIServiceClient
from mednlp.text.entity_extract import Entity_Extract
from mednlp.utils.data_prepare import AiServiceResult
from time import time

##初始化路径
# test_data_path = '/home/yinwd/work/mednlp/data/test/'
cfg_path = global_conf.cfg_path
#### 抽取实体对 ####
### method：启用自己虚拟环境的服务
model_service = AiServiceResult(port=2138, service_name='entity_extract', service_q='q')
port = 2148
## 实体识别结果：选取结果获取方式和 统一化结果
def extract_result_ner(cut_content, new=False, port=port):
    # ai_content = AIServiceClient(cfg_path=cfg_path, service='AIService', port=port)
    # data_dict = ai_content.query({'q': cut_content}, service='entity_extract')
    # result_ls = data_dict.get('data')
    result_ls = model_service.web_result(cut_content)
    result_entities = []
    for results in result_ls:
        if results['type'] in ['area', 'body_part', 'disease', 'symptom', 'hospital', 'std_department', 'treatment',
                'doctor', 'medicine', 'hospital_department', 'examination', 'physical']:
            result_entities.append(results)
        else:
            pass

    result = []
    for words_keys in result_entities:
        result_dict = words_keys
        # print result_dict
        entity_name = result_dict['entity_name']
        if new:  #新的测试集标注中，科室统一为department
            if result_dict["type"] in ['hospital_department', 'std_department']:
                entity_type = 'department'
            else:
                entity_type = result_dict["type"]
            if result_dict["type"] == 'body_part':
                entity_type = 'bodypart'
        else:  #老的测试集中，科室统一为std_department
            if result_dict["type"] == 'hospital_department':
                # print result_dict
                entity_type = 'std_department'
            else:
                entity_type = result_dict["type"]
        result.append({entity_type:entity_name})
    return result

@print_time
def statistics_result(all_result, new=False):
    # ner_result这两个里面都是[[{entity_type:entity_name},{entity_type:entity_name}],[{},{}]] 格式
    # 返回一个字典，各个实体的频数
    if new:
        GROUND_TRUTH_LABELS = {'symptom': 0, 'disease': 0, 'department': 0, 'hospital': 0,
                            'bodypart': 0, 'treatment': 0, 'medicine': 0, 'area': 0, 'doctor': 0,
                            'examination': 0, 'physical': 0}
    else:
        GROUND_TRUTH_LABELS = {'symptom': 0, 'disease': 0, 'std_department': 0, 'hospital': 0,
                            'body_part': 0, 'treatment': 0, 'medicine': 0, 'area': 0, 'doctor': 0}
    key_list = list(GROUND_TRUTH_LABELS.keys())
    for result_ls in  all_result:
        if result_ls:  #可能有空的列表
            for dict in result_ls:
                for key in key_list:
                    if  key in dict:
                        GROUND_TRUTH_LABELS[key] += 1

    return GROUND_TRUTH_LABELS

@print_time
def statistics_evaluation(real_result, pred_result, new=False):
    real_statistics_result = statistics_result(real_result, new = new)
    pred_result = drop_area(pred_result)
    pred_statistics_result = statistics_result(pred_result, new = new)
    if new:
        pred_correct_label = {'symptom': 0, 'disease': 0, 'department': 0, 'hospital': 0,
                            'bodypart': 0, 'treatment': 0, 'medicine': 0, 'area': 0, 'doctor': 0,
                            'examination': 0, 'physical': 0}
    else:
        pred_correct_label =  {'symptom': 0, 'disease': 0, 'std_department': 0, 'hospital': 0,
                            'body_part': 0, 'treatment': 0, 'medicine': 0, 'area': 0, 'doctor': 0}
    key_list = list(pred_correct_label.keys())
    for index, pred_ls in  enumerate(pred_result):
        # print index,Encode(pred_ls)
        for dict in pred_ls:
            if dict in real_result[index]:
                pred_correct_label[list(dict.keys())[0]] += 1

    prf_df = pd.DataFrame(key_list, columns=['key_name'])

    real_label = [real_statistics_result[x] for x in key_list]
    pred_label = [pred_statistics_result[x] for x in key_list]
    correct_label = [pred_correct_label[x] for x in key_list]

    prf_df['real_label'] = real_label
    prf_df['pred_label'] = pred_label
    prf_df['correct_label'] = correct_label
    # #当老的数据集时，可以启用
    # prf_df['Precision'] = np.array(correct_label) * 100.00 / np.array(pred_label)
    # prf_df['Recall'] = np.array(correct_label) * 100.00 / np.array(real_label)
    # prf_df['F'] = 2 * prf_df['Precision'] * prf_df['Recall']/(prf_df['Precision'] + prf_df['Recall'])

    return prf_df

### 实体识别中从医院中再次提取了一次地区，这些在标注中不会标注出来，因此统计的时候需要去掉这部分地域
def drop_area(pred_result):
    count = 0
    if pred_result:
        for result_ls in pred_result:
            if result_ls:#可能有空的列表
                for index, dict in enumerate(result_ls):
                    if index>0 and 'area' in  dict:
                        # print(dict['area'], result_ls[index-1].values()[0],type(result_ls[index-1].values()[0]))
                        # data_content = ",".join([x.values()[0] for x in result_ls[0:index-1]])
                        if re.findall(dict['area'], list(result_ls[index-1].values())[0]):
                            count += 1
                            # print '++++need drop++++%d'%(count)
                            result_ls.remove(dict)

    return pred_result

@print_time
def  no_extract_analysis(real_result, pred_result, content_ls, out_file):
    ## 将未提取的结果 写出，便于分析添加规则优化
    diff = []
    rind_ls = []
    for rind, res in  enumerate(real_result):
        for dict in res:
            if dict not in pred_result[rind]:
                rind_ls.append(rind)
                diff.append(dict)

    diff_df = pd.DataFrame(diff)
    diff_df['index'] =  rind_ls
    diff_df['content'] =  [content_ls[x] for x in rind_ls]
    diff_df.to_excel(out_file)

@print_time
### 新的测试集：brat 标注数据转化
def get_data_brat(n_list):
    data_write = codecs.open('ner_test_sample.utf8', 'w', encoding='utf-8')
    for n in n_list:
        data_path = '/home/yinwd/work/brat-v1.3_Crunchy_Frog/data/brat_entity_label/data{}/'.format(n)
        if n == 2700:
            n_low = 2600
            n_up = 2737
        else:
            n_low = n-200
            n_up = n
        for m in range(n_low, n_up):
            result_list = []
            print('----------data{}----------'.format(m))
            ## brat标注的结果
            brat_ont_path = data_path + 'data{}.ann'.format(m)
            ## brat标注的原文本
            brat_text_path = data_path + 'data{}.txt'.format(m)
            brat_data_list = codecs.open(brat_ont_path, 'r', encoding='utf8').readlines()
            brat_text_sentence = codecs.open(brat_text_path, 'r', encoding='utf8').readlines()
            sentence = brat_text_sentence[0].strip()
            brat_result_tran = []

            if brat_data_list :
                for bratdata in brat_data_list:
                    brat_dict = {}
                    data_split = re.split('\t', bratdata.strip())
                    types, start, end = re.split('\s', data_split[1])
                    brat_dict[types] = data_split[2]
                    result_list.append(brat_dict)
            result_dict = json.dumps([m, sentence, result_list], ensure_ascii=False)
            # print result_dict
            data_write.write(result_dict + '\n')
    data_write.close()

def list_equ(list1, list2):
    result = 0
    len1 = len(list1)
    len2 = len(list2)
    if len1 != len2:
        result = 1
    equ = 0
    for l1 in list1:
        if l1 in list2:
            equ += 1
    if equ == len2 and equ == len1:
        result = 0
    else:
        result = 1
    return result



## 评估实体识别模型的效果
def evaluation_model():
    if not os.path.isfile("ner_test_sample.utf8"):
        n_list = np.arange(200,2800,200).tolist()
        n_list.append(2700)
        get_data_brat(n_list)

    test_data = codecs.open('ner_test_sample.utf8', 'r', encoding='utf-8').readlines()
    reslut_compare = open('ner_test_reuslt_compare.utf8', 'w')
    time0 = time()
    print(len(test_data))
    ner_statistics_result = []
    brat_statistics_result = []
    content_ls = []
    for test_result in test_data:
        or_test_result = test_result
        test_result = eval(test_result)
        ind = test_result[0]
        sentence = test_result[1]
        brat_result = test_result[2]
        brat_statistics_result.append(brat_result)
        content_ls.append(sentence)
        ner_result = extract_result_ner(sentence, new=True, port=port)
        ner_statistics_result.append(ner_result)
        if list_equ(brat_result, ner_result) == 1:
            reslut_compare.write(or_test_result)
            ner_result_dict = json.dumps([ind, sentence, ner_result], ensure_ascii=False)
            reslut_compare.write(ner_result_dict + '\n')
        # print 'ner 结果+++', Encode(ner_result)
    ## 写出文件，未提取出来的实体和对应的句子
    no_extract_analysis(brat_statistics_result, ner_statistics_result, content_ls, 'diff_real_pred.xlsx')
    ## 写出文件，提取错误的实体和对应的句子
    no_extract_analysis(ner_statistics_result, brat_statistics_result, content_ls, 'error_pred_readl.xlsx')
    prf_df = statistics_evaluation(brat_statistics_result, ner_statistics_result, new=True)
    time1 = time()
    print('cost time %.2f'%(time1 - time0))
    print(prf_df)
    prf_df.to_excel('test_evaluate_df.xlsx')

def evaluation_model_old():
    ## 老的测试集测试代码
    ## 处理 测试文本
    content_ls = []
    real_result_ls = []
    # path_test = os.path.join(test_data_path, 'ground_truth.csv')

    NUM_LINES = sum(1 for line in codecs.open('ground_truth.utf8', 'r', encoding='utf8'))
    with codecs.open('ground_truth.utf8', 'r', encoding='utf8') as ground_truth:
        for m in range(int(NUM_LINES)):
            results = ground_truth.readline()
            # print results
            if m%2 == 0:
                content_ls.append(results)
            else:
                results = results.strip().strip('{').strip('}')
                re_ls = []
                if results:
                    result_ls = results.split(',')
                    for result in result_ls:
                        key, val = result.strip().split(':')
                        re_ls.append({val:key})
                real_result_ls.append(re_ls)

    # print Encode(real_result_ls)
    # print '===========real_result_freq==============='
    # print statistics_result(real_result_ls)

    real_result = real_result_ls
    ## 预测结果
    # print '===============pred_result================'
    pred_result = []
    for conind, cont in enumerate(content_ls):
        result = extract_result_ner(cont, port=port)
        print('----%d------'%conind)
        pred_result.append(result)

    # print Encode(pred_result)
    ## 写出文件，未提取出来的实体和对应的句子
    # no_extract_analysis(real_result, pred_result, content_ls, 'diff_real_pred.xlsx')
    ## 写出文件，提取错误的实体和对应的句子
    # no_extract_analysis(pred_result, real_result, content_ls, 'error_pred_readl.xlsx')
    ## 计算prf值
    prf_df = statistics_evaluation(real_result, pred_result)
    print(prf_df)
    prf_df.to_excel('prf_df.xlsx')



if __name__ == '__main__':
    ### 老的测试集
    evaluation_model_old()
    ### 新的测试集代码
    evaluation_model()
