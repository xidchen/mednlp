#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
file_operation.py -- build dictionary from file

Author: chenxd <chenxd@guahao.com>
Created on 2018-03-06 Tuesday
"""


import csv
import codecs
import global_conf


def get_disease_id():
    f = codecs.open(global_conf.disease_id_name_path)
    dictionary = {row[1]: row[0] for row in csv.reader(f)}
    return dictionary

def get_disease_id_add():
    f = codecs.open(global_conf.disease_id_name_add_path)
    dictionary = {row[1]: row[0] for row in csv.reader(f)}
    return dictionary

def get_disease_name():
    f = codecs.open(global_conf.disease_id_name_path)
    dictionary = {row[0]: row[1] for row in csv.reader(f)}
    return dictionary

def get_disease_name_add():
    f = codecs.open(global_conf.disease_id_name_add_path)
    dictionary = {row[0]: row[1] for row in csv.reader(f)}
    return dictionary

def get_disease_dept():
    f = codecs.open(global_conf.disease_name_dept_path)
    dictionary = {row[0]: row[1] for row in csv.reader(f)}
    return dictionary


def get_disease_advice():
    f = codecs.open(global_conf.disease_name_advice_path)
    dictionary = {row[0]: row[1] for row in csv.reader(f)}
    return dictionary


def get_disease_advice_code():
    f = codecs.open(global_conf.disease_name_advice_code_path)
    dictionary = {row[0]: row[1] for row in csv.reader(f)}
    return dictionary


def get_disease_code_conversion():
    """
    d1: {disease: insurance_id}
    d2: {disease: insurance_code}
    d3: {disease: insurance_name}
    :return: d1, d2, d3
    """
    f = codecs.open(global_conf.disease_code_conversion_path)
    d1, d2, d3 = {}, {}, {}
    for row in csv.reader(f):
        d1[row[0]] = row[2]
        d2[row[0]] = row[3]
        d3[row[0]] = row[4]
    return d1, d2, d3


def get_disease_sex_filter():
    f = codecs.open(global_conf.disease_sex_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        if row[0] in dictionary:
            dictionary[row[0]][row[1]] = float(row[2])
        else:
            dictionary[row[0]] = {}
            dictionary[row[0]][row[1]] = float(row[2])
    return dictionary


def get_disease_age_filter():
    f = codecs.open(global_conf.disease_age_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        if row[0] in dictionary:
            dictionary[row[0]][row[1]] = float(row[2])
        else:
            dictionary[row[0]] = {}
            dictionary[row[0]][row[1]] = float(row[2])
    return dictionary


def get_disease_body_part_filter():
    f = codecs.open(global_conf.disease_body_part_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        dictionary[row[0]] = row[1].split('|')
    return dictionary


def get_disease_inspection_filter():
    f = codecs.open(global_conf.disease_inspection_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        dictionary[row[0]] = row[1].split('|')
    return dictionary


def get_disease_physical_exam_filter():
    f = codecs.open(global_conf.disease_physical_exam_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        dictionary[row[0]] = row[1].split('|')
    return dictionary


def get_disease_past_medical_history_filter():
    f = codecs.open(global_conf.disease_past_medical_history_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        dictionary[row[0]] = row[1].split('|')
    return dictionary


def get_disease_symptom_filter():
    f = codecs.open(global_conf.disease_symptom_filter_path)
    dictionary = {}
    for row in csv.reader(f):
        dictionary[row[0]] = row[1].split('|')
    return dictionary


def get_disease_symptom_enhancer():
    f = codecs.open(global_conf.disease_symptom_enhancer_path)
    dictionary = {}
    for row in csv.reader(f):
        dictionary[row[0]] = row[1].split('|')
    return dictionary


def get_symptom_name():
    f = codecs.open(global_conf.symptom_wy_dict_path)
    dictionary = {}
    for row in f:
        row = row.strip().split('\t')
        dictionary[row[1]] = row[0]
    return dictionary


def get_kg_docs():
    f = codecs.open(global_conf.kg_docs_path)
    dictionary = {}
    for row in f:
        dictionary = eval(row.strip())
    return dictionary


def get_unit_name():
    f = codecs.open(global_conf.unit_dict_path)
    dictionary = {}
    for row in f:
        row = row.strip().split('\t')
        dictionary[row[0]] = row[1]
    return dictionary


if __name__ == '__main__':
    pass
