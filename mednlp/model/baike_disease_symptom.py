#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import re
import sys
import json
import time
import jieba
import codecs
import requests
import global_conf
import numpy as np
import pandas as pd
import jieba.posseg as psg
from mednlp.utils.utils import Encode

if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding("utf-8")
requests.adapters.DEFAULT_RETRIES = 5

train_data_path = os.path.dirname(__file__) + '/' + 'data/traindata/'

def disease_symptom(inputfile, pattern, split_char, outputfile):
    split_index = []
    for index, sen in enumerate(inputfile):
        if re.findall(pattern, sen):
            split_index.append(index)
        else:
            pass
    print('obtain %d disease'%len(split_index))
    lensi = len(split_index)-1

    dis_txt = codecs.open(outputfile, 'w', encoding='utf8')
    for i in range(lensi):
        disease = inputfile[split_index[i]].strip()
        # print disease
        disease = re.split(split_char, disease)[-1]
        # print disease
        for li in range(split_index[i], split_index[i+1]):
            if li % 2 == 0:
                sen = inputfile[li].strip()
                sen = re.sub('\t', ' ', sen)
                if sen:
                    dis_txt.write(disease + '\t' + sen +'\n')
    dis_txt.close()


def disease_symptom2(inputfile, pattern, split_char, outputfile):
    split_index = []
    for index, sen in enumerate(inputfile):
        if re.findall(pattern, sen):
            split_index.append(index)
        else:
            pass
    print('obtain %d disease'%len(split_index))
    lensi = len(split_index)-1

    dis_txt = codecs.open(outputfile, 'w', encoding='utf8')
    for i in range(lensi):
        disease = inputfile[split_index[i]].strip()
        disease = re.split('\s', disease)[0]
        disease = re.split(split_char, disease)[-1]
        # print disease
        for li in range(split_index[i], split_index[i+1]):
                sen = inputfile[li].strip()
                sen = re.sub('\t', ' ', sen)
                if sen:
                    dis_txt.write(disease + '\t' + sen +'\n')
    dis_txt.close()


def alter_hd():
    ## 其中 hd百科需要额外处理，其文本相对其他文本有差异，文本获取错位。
    path_hd = os.path.join(train_data_path, 'baike_hd.utf8')
    path_hd2 = os.path.join(train_data_path, 'baike_hd_new.utf8')
    hd_file = codecs.open(path_hd, 'r', encoding='utf8').readlines()
    new_hd = codecs.open(path_hd2, 'w', encoding='utf8')
    dis_list = []
    sen_list = []
    for index, data in enumerate(hd_file):
        dis, sen = re.split('\t', data)
        if len(dis) < 15:
            if not re.findall(u'院|》|，|。', dis):
                dis_list.append(dis)
                sen_list.append(sen)

    for i in range(1,len(dis_list)):
        try:
            dis = dis_list[i]
            if  dis != dis_list[i-1]:
                if re.findall(dis.decode('utf8'), sen_list[i-1].decode('utf8')):
                    dis_list[i-1] = dis
                else:
                    pass
            else:
                pass
        except:
            continue

    for i in range(len(dis_list)):
        new_hd.write(dis_list[i] + '\t' + sen_list[i])

    new_hd.close()


def alter_rw():
    # 人卫知网百科数据，疾病获取中其他类数据较多，需删除。
    path_rw = os.path.join(train_data_path, 'baike_rwzw.utf8')
    path_rw2 = os.path.join(train_data_path, 'baike_rwzw_new.utf8')
    rw_file = codecs.open(path_rw, 'r', encoding='utf8').readlines()
    new_rw = codecs.open(path_rw2, 'w', encoding='utf8')
    for index, data in enumerate(rw_file):
        dis, sen = re.split('\t', data)
        if len(dis) < 15:
            if not re.findall(u'(治疗|概|并发|检查|处理|案例|研究|病因|诊|预防|病理|发病|分类|影响|机制|特点|》|？|，|。)', dis):
                new_rw.write(dis + '\t' + sen)

    new_rw.close()


def clinical_pred(fname, outname):
    txt_path = os.path.join(train_data_path, fname)
    dis_txt = codecs.open(txt_path, 'r', encoding='utf8').readlines()
    clinical_manifestation = [u'临床表现|具体表现|临床症状', 'clinical_manifestation']
    sen_ls = []
    disease_ls = []
    for index, txt in enumerate(dis_txt):
        disease, sen = re.split('\t', txt)
        if len(sen) > 10:
            sen_ls.append(sen.strip())
            disease_ls.append(disease)

    # print len(disease_ls)
    deep_label = []
    rule_label = []
    ###一次预测1000可以估计模型预测的总时间
    l = len(disease_ls)/1000
    for k in range(l+1):
        time0 = time.time()
        if k <=l:
            datasen = sen_ls[k*1000:(k*1000+1000)]##字符串列表
        else:
            datasen = sen_ls[k*1000:]
        Model = Clinical_Predict(datasen, clinical_manifestation)
        result_model = Model.deep_model_pred()
        result_rule = Model.rule_model_pred()
        time1 = time.time()
        print('====have compute %d samples and cost time %4.2f s'%(1000+k*1000, time1-time0))
        deep_label.extend(result_model)
        rule_label.extend(result_rule)

    df = pd.DataFrame(disease_ls, columns=['disease'])
    df['content'] = sen_ls
    df['label_deep_model'] = deep_label
    df['label_rule_model'] = rule_label
    df_path = os.path.join(train_data_path, outname)
    df.to_excel(df_path)


#### 抽取实体对 ####
def get_web_data(url):
    r = requests.get(url)
    if r.status_code==200:
        return r.content
    else:
        return u'请求失败'


def ner_extraction(inputdata):
    url = '	http://192.168.4.30:2148/entity_extract?q='
    url = url + inputdata
    outdata = get_web_data(url)
    data_list =  eval(outdata)##返回字典格式
    return data_list


def symtptom_obtain(inputdata):
    sym_list = []
    data_dict = ner_extraction(inputdata)
    list_dict = data_dict['data']
    for dict in list_dict:
        if dict['type'] == 'symptom':
           sym_list.append(dict['entity_name'])

    sym_result = ",".join(sym_list)
    return sym_result


def drop_false(listdata):
    drop_sym = [u'活动',u'增大',u'减小',u'先兆',u'消失',u'产后',u'胃型']
    new_list = []
    for m in listdata:
        if len(m) > 1 and m not in drop_sym:
           new_list.append(m)
    return new_list


def groupby_disease(inputfile, outputfile):
    output_path = os.path.join(train_data_path, outputfile)
    output_txt = codecs.open(output_path, 'w', encoding='utf8')
    dict = {}
    for index, data in enumerate(inputfile):
        # print data
        disease, symptom = re.split('\t', data.decode('utf8'))
        try:
            dict[disease] += symptom
        except:
            dict[disease] = symptom

    # print Encode(dict)
    disease_list = dict.keys()

    for dis in disease_list:
        symptom_all = dict[dis]
        symptom_sp = list(set(re.split(',|\n',symptom_all)))
        symptom = ",".join(drop_false(symptom_sp))
        # symptom = ",".join([x for x in symptom_sp if x])
        # print symptom
        output_txt.write(dis + '\t' + symptom + '\n')


def main(inputdata, outputfile):
    disease_list = inputdata['disease'].tolist()
    content_list = inputdata['content'].tolist()

    inputfile = []
    for index, content in enumerate(content_list):
        content = "".join(re.findall(u'[\u4e00-\u9fa5]|[，。\s\-]', content))
        if len(content) > 900: ###测试了一下，当文本长度在920+以上，请求的网页报错。
            content = content[0:900]

        symtptom_set = symtptom_obtain(content)
        inputfile.append(disease_list[index] + '\t' + symtptom_set)

    groupby_disease(inputfile, outputfile)


if __name__ == "__main__":
    output_path = os.path.join(train_data_path, 'baike_hd.xlsx')
    data_df = pd.read_excel(output_path, sheet_name='pred_clinical',encoding='utf8')
    print(data_df.shape)
    main(data_df, 'baike_hd_clinical_result.utf8')
