#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dict_tool.py -- some tool for dict

Author: maogy <maogy@guahao.com>
Create on 2017-05-27 Saturday.
"""


import os
import sys
from optparse import OptionParser
from ailib.storage.db import DBWrapper


base_path = os.path.join(os.path.dirname(__file__), "..")
cfg_path = base_path + '/etc/cdss.cfg'


def check_icd10_disease(diseases):
    sql_base = """
    SELECT
        d.id
    from ai_medical_knowledge.disease d 
    where d.disease_type=1 and d.name ='%s'
    """
    db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')
    disease_icd10 = set()
    disease_not_icd10 = set()
    for disease in diseases:
        sql = sql_base % disease
        rows = db.get_rows(sql)
        if rows:
            disease_icd10.add(disease)
        else:
            disease_not_icd10.add(disease)
    return disease_icd10, disease_not_icd10

def check_icd10_disease_nos(diseases):
    sql_base = """
    SELECT
        d.id
    from ai_medical_knowledge.disease d 
    where d.disease_type=1 and d.name ='%s'
    """
    db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')
    disease_icd10 = set()
    disease_not_icd10 = set()
    for disease in diseases:
        sql = sql_base % (disease + ' NOS')
        rows = db.get_rows(sql)
        if rows:
            disease_icd10.add(disease + ' NOS')
        else:
            disease_not_icd10.add(disease)
    return disease_icd10, disease_not_icd10


def check_icd10_disease_alia(diseases):
    sql_base = """
    SELECT
        d.name
    from ai_medical_knowledge.disease d
    LEFT join ai_medical_knowledge.disease_alias da on da.disease_uuid=d.id
    where d.disease_type=1 and (da.alias = '%s' or d.name_common = '%s')
    """
    db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')
    disease_icd10 = set()
    disease_not_icd10 = set()
    for disease in diseases:
        sql = sql_base % (disease, disease)
        rows = db.get_rows(sql)
        if rows:
            # names = [row['name'] for row in rows]
            disease_icd10.add(rows[0]['name'])
        else:
            disease_not_icd10.add(disease)
    return disease_icd10, disease_not_icd10

def check_icd10_disease_alia_like(diseases):
    sql_base = """
    SELECT
        DISTINCT d.name
    from ai_medical_knowledge.disease d
    LEFT join ai_medical_knowledge.disease_alias da on da.disease_uuid=d.id
    where d.disease_type=1 and (da.alias like '%s' or d.name_common like '%s' or d.name like '%s')
    """
    db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')
    disease_icd10 = set()
    disease_not_icd10 = set()
    for disease in diseases:
        disease_like = '%' + disease + '%'
        sql = sql_base % (disease_like, disease_like, disease_like)
        rows = db.get_rows(sql)
        if rows:
            names = [row['name'] for row in rows]
            disease_icd10.add('%s:%s' % (disease, '|'.join(names)))
        else:
            disease_not_icd10.add(disease)
    return disease_icd10, disease_not_icd10


def process_disease(filepath):
    diseases = set()
    for line in open(filepath, 'r'):
        line = line.strip()
        diseases.add(line)
    icd10, not_icd10 = check_icd10_disease(diseases)
    # icd10, not_icd10 = check_icd10_disease_alia(diseases)
    # icd10, not_icd10 = check_icd10_disease_alia_like(diseases)
    # icd10, not_icd10 = check_icd10_disease_nos(diseases)
    print('disease icd10')
    for d in icd10:
        print(d)
    print('disease not format')
    for d in not_icd10:
        print(d)
    return


if __name__ == '__main__':
    command = """\npython %s [-t type -c config_file]""" % sys.argv[0]

    parser = OptionParser(usage=command)
    parser.add_option('-c', '--config', dest='config', help='the config file',
                      metavar='FILE')
    parser.add_option('-t', '--type', dest='type', help='the type of operate')
    parser.add_option('-i', '--input', dest='input',
                      help='the input')
    operate_type = 'medical_dict'
    dict_dict = {}
    (options, args) = parser.parse_args()
    if options.config is None:
        options.config = cfg_path
    process_disease(options.input)
    # if options.type:
    #     operate_type = options.type
    # if operate_type == 'medical_dict':
    #     dict_dict = build_medical_dict()
    # elif operate_type == 'medical_jieba_dict':
    #     dict_dict = build_medical_dict()
    #     dict_dict = add_jieba_dict(dict_dict, options.jieba)
    # dict_output(dict_dict)
