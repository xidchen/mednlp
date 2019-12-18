#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
statistics.py -- the statistics module of consistency

Author: chenxd <chenxd@guahao.com>
Create on 2018-07-21 Saturday
"""

from __future__ import print_function

import codecs
import optparse
import global_conf
from ailib.storage.db import DBWrapper
from mednlp.dao.data_loader import Key2Value
from mednlp.dao.kg_dao import KGDao
from mednlp.text.mmseg import MMSeg


def diagnose_performance(params):
    kgd = KGDao()
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'MySQLDB')
    rd_db = DBWrapper(global_conf.cfg_path, 'mysql', 'RDMySQLDB')
    disease_alias = kgd.load_prod_xy_disease_alias(db)
    hospital_diagnose_data = kgd.load_prod_xy_diagnose_data(rd_db, params)
    k2v_1 = Key2Value(path=global_conf.disease_dict_path, v_is_int=False)
    icd_diseases = k2v_1.load_dict()
    k2v_2 = Key2Value(path=global_conf.disease_classify_dict_path)
    diagnosable_diseases = k2v_2.load_dict()
    d_seg = MMSeg(dict_type=['disease'])
    count, icd_count, diagnosable_count = 0, 0, 0
    top, top_alias, top_ner = [0] * 6, [0] * 6, [0] * 6
    f = codecs.open(global_conf.RELATIVE_PATH + 'diff_diagnose.txt', 'w')
    if params['show_diff']:
        f.write('diagnose\tai_diagnose\tchief_complaint\tmedical_history\t'
                'sex\tage\tpast_medical_history\tphysical_examination\t'
                'general_info\n')
    for row in hospital_diagnose_data:
        prediction_list = []
        diagnosis, ai_diagnosis = row['diagnose'], row['ai_diagnose']
        diagnosis = transform_text(diagnosis)
        if eval(ai_diagnosis) and eval(ai_diagnosis).get('disease'):
            ai_diagnosis_list = eval(ai_diagnosis)['disease']
            for x in ai_diagnosis_list:
                prediction_list.append(x['diseaseName'])
            if diagnosis and prediction_list:
                count += 1
                for i in [1, 3, 5]:
                    if diagnosis in prediction_list[:i]:
                        top[i] += 1
                if diagnosis in disease_alias:
                    diagnosis = disease_alias[diagnosis]
                for i in [1, 3, 5]:
                    if diagnosis in prediction_list[:i]:
                        top_alias[i] += 1
                if diagnosis in icd_diseases:
                    icd_count += 1
                if diagnosis in diagnosable_diseases:
                    diagnosable_count += 1
                    if params['show_diff']:
                        print_diff_diagnose(diagnosis, prediction_list, row, f)
                for i in [1, 3, 5]:
                    for d in d_seg.cut(diagnosis):
                        if d in prediction_list[:i]:
                            top_ner[i] += 1
                            break
    f.close()
    print('诊断总数:', count, ',',
          '符合ICD命名的诊断总数:', icd_count, ',',
          '可诊断600疾病的诊断总数:', diagnosable_count)
    if count and icd_count:
        for i in [1, 3, 5]:
            print('Top ' + str(i), end=', ')
            print('诊断命中率:', '{0:.2f}'.format(float(top[i])/count), end=', ')
            print('诊断包含别名的命中率:',
                  '{0:.2f}'.format(float(top_alias[i])/count), end=', ')
            print('ICD诊断的命中率:',
                  '{0:.2f}'.format(float(top[i])/icd_count), end=', ')
            print('可诊断600疾病的命中率:',
                  '{0:.2f}'.format(float(top[i])/diagnosable_count), end=', ')
            print('原始诊断抽取疾病后的命中率:',
                  '{0:.2f}'.format(float(top_ner[i])/count))


def print_diff_diagnose(diagnosis, prediction_list, mr, f):
    if diagnosis not in prediction_list[:5]:
        f.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
            diagnosis, prediction_list[:5],
            transform_text(mr['chief_complaint']),
            transform_text(mr['now_medical_history']),
            transform_text(mr['sex']),
            transform_text(mr['age']),
            transform_text(mr['past_medical_history']),
            transform_text(mr['physical_examination']),
            transform_text(mr['general_info'])
        ))


def transform_text(text):
    return str(text, encoding='utf8').replace('\t', '') if isinstance(
        text, bytes) else text


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-f', '--from', dest='date_from', help='date from')
    parser.add_option('-t', '--till', dest='date_till', help='date till')
    parser.add_option('-d', '--diff', dest='show_diff', help='show difference')
    parameters = {'date_from': '20180101', 'date_till': 'now()', 'show_diff': 0}
    (options, args) = parser.parse_args()
    if options.date_from:
        parameters['date_from'] = options.date_from
    if options.date_till:
        parameters['date_till'] = options.date_till
    if options.show_diff:
        parameters['show_diff'] = 1
    diagnose_performance(parameters)
