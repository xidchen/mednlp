#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
build_disease_symptom_relation.py -- build the relation of disease and symptom

Author: maogy <maogy@guahao.com>
Create on 2017-07-05 Wednesday.
"""

import sys
from optparse import OptionParser
from mednlp.text.mmseg import MMSeg


def build(filepath, limit_n):
    seger = MMSeg(['symptom'])
    disease_symptom_dict = {}
    disease_count = {}
    total_disease_count = 0
    disease_set = {}
    for line in open('/home/maogy/work/realdoctor/cdss/data/dict/disease.dic', 'r'):
        line = line.strip()
        item_list = line.split('\t')
        if len(item_list) > 1:
            disease_set[item_list[0]] = item_list[1]
    for count, line in enumerate(open(filepath, 'r')):
        if count > limit_n:
            break
        item_list = line.split('|')
        if len(item_list) != 2:
            continue
        disease = item_list[0].strip()
        if disease not in disease_set:
            continue
        disease = disease_set[disease]
        desc = item_list[1].strip()
        entities = seger.cut(desc)
        if not entities:
            continue
        disease_count.setdefault(disease, 0)
        disease_count[disease] += 1
        total_disease_count += 1
        for symptom in entities.keys():
            if symptom == disease:
                continue
            dis_sym = disease_symptom_dict.setdefault(disease, {})
            dis_sym[symptom] = dis_sym.get(symptom, 0) + 1
        if count % 10000 == 0:
            print('%s has finished!' % count)
    disease_symptom_list = {}
    for disease, symptoms in disease_symptom_dict.items():
        if disease_count[disease] < 30:
            continue
        for symptom, count in symptoms.items():
            symptom_list = disease_symptom_list.setdefault(disease, [])
            symptom_list.append((symptom, float(float(count)/disease_count[disease])))
    for disease, symptoms in disease_symptom_list.items():
        symptoms =  sorted(symptoms, key=lambda x: x[1], reverse=True)
        disease_symptom_list[disease] = symptoms
    for disease, symptoms in disease_symptom_list.items():
        symptom_list = []
        for count, symptom_obj in enumerate(symptoms):
            if count > 15:
                break
            symptom, weight = symptom_obj
            entities = seger.cut(symptom)
            if not entities:
                continue
            symptom = entities.values()[0]
            symptom_list.append('%s|%s' % (symptom, weight))
        # print disease,'\n\t', '\n\t'.join(symptom_list)
        # disease_id = disease_set.get(disease)
        # if not disease_id:
        #     continue
        for symptom in symptom_list:
            print('%s|%s' % (disease, symptom))
    for disease, count in disease_count.items():
        print('%s|%s' % (disease, int(float(count)/float(total_disease_count)*100000000)))
        # print '%s:%s' % (disease, '-'.join(symptom_list))

if __name__ == '__main__':
    command = '\npython %s [-t type -n number -c config_file]' % sys.argv[0]

    parser = OptionParser(usage=command)
    parser.add_option('-n', '--number', dest='number',
                      help='the number limit of data')
    parser.add_option('-i', '--input', dest='input', help='the file input')
    n_limit = sys.maxsize
    (options, args) = parser.parse_args()
    if options.number:
        n_limit = int(options.number)
    build(options.input, n_limit)
