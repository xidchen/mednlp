#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
medical_record_tool.py -- some tools of medical record process

Author: maogy <maogy@guahao.com>
Create on 2017-07-11 Tuesday.
"""


import os
import sys
from optparse import OptionParser
from xml.dom.minidom import parse
import xml.etree.ElementTree as ET
from ailib.storage.db import DBWrapper
import global_conf as global_conf

def format_medical_record(inputpath, n_limit=10):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    base_sql = """
    INSERT IGNORE INTO medical_data.medical_record(hospital_name,hospital_record_id,
        disease_name,disease_name_org,sex,age,`type`,chief_complaint,medical_history,
        past_medical_history,personal_history,obstetrical_history,menstrual_history,
        family_history,state,gmt_created,gmt_modified,create_staff,modify_staff)
    VALUES('甘肃省武威肿瘤医院','%(hospital_record_id)s','%(disease_name)s','%(disease_name)s',
        %(sex)s,%(age)s,%(type)s,'%(chief_complaint)s','%(medical_history)s',
        '%(past_medical_history)s','%(personal_history)s','%(obstetrical_history)s',
        '%(menstrual_history)s','%(family_history)s',1,now(),now(),'eagle','eagle')
    """
    count = 0
    medical_record = {}
    type_dict = {'门诊': 1, '住院': 2}
    record_count = 0
    count_step = 50
    for rootdir, dirs, files in os.walk(inputpath, True):
        # print rootdir
        count += 1
        if count > n_limit:
            break
        disease_name = parse_disease(rootdir, dirs, files)
        # print disease_name
        if disease_name:
            medical_record = {}
            parse_patient_info(medical_record, rootdir, dirs, files)
            if not medical_record.get('hospital_record_id'):
                continue
            # print medical_record.get('hospital_record_id')
            medical_record['disease_name'] = disease_name.replace(medical_record['hospital_record_id'], '')
            record_type_name = os.path.basename(os.path.dirname(rootdir))
            medical_record['type'] = type_dict.get(record_type_name, 1)
            # print 'type:',medical_record['type']
            # print medical_record['disease_name']
        is_desc = parse_desc(medical_record, rootdir, files)
        if is_desc:
            # print medical_record
            record_count += 1
            # if record_count < 22500:
            #     continue
            if record_count % count_step == 0:
                print('%s has finished!!' % record_count)
                print('%(hospital_record_id)s|||%(disease_name)s|||%(sex)s|||%(age)s|||%(type)s|||\
                    %(chief_complaint)s|||%(medical_history)s|||%(past_medical_history)s' % medical_record)
            if not medical_record.get('hospital_record_id'):
                continue
            sql = base_sql % medical_record
            # print sql
            db.execute(sql)
            db.commit()
    db.close()
        # print rootdir, dirs, files

def parse_disease(rootdir, dirs, files):
    if dirs and 'EMR' in dirs and 'PACS' in dirs:
        disease = os.path.basename(rootdir)
        return disease

def parse_patient_info(record, rootdir, dirs, files):
    patient_info_file = 'PatientEntity.xml'
    if patient_info_file in files:
        patient_info_path = os.path.join(rootdir, patient_info_file)
        tree = ET.parse(patient_info_path)
        root = tree.getroot()
        field_dict = {'Sex': 'sex', 'Age': 'age', 'FID': 'hospital_record_id'}
        for xml_field, field in field_dict.items():
            xml_values = root.findall(xml_field)
            if field == 'age':
                record[field] = -1
            elif field == 'sex':
                record[field] = 3
            if not xml_values:
                continue
            text_value = xml_values[0].text
            if not text_value:
                continue
            record[field] = text_value
            # print field,':',record[field]
    return record

def parse_desc(record, rootdir, files):
    if 'AllEMRData.xml' in files:
        emr_path = os.path.join(rootdir, 'AllEMRData.xml')
        tree = ET.parse(emr_path)
        root = tree.getroot()
        field_dict = {'FCHIEF_COMPLAINT': 'chief_complaint',
                      'FCURRENT_MEDICAL_HISTORY': 'medical_history',
                      'FPAST_HISTORY': 'past_medical_history',
                      'FPERSONAL_HISTORY':'personal_history',
                      'FOBSTETRICAL_HISTORY':'obstetrical_history',
                      'FMENSTRUAL_HISTORY':'menstrual_history',
                      'FFAMILY_HISTORY':'family_history'}
        response = root.findall('response')
        for xml_field, field in field_dict.items():
            xml_values = response[0].findall(xml_field)
            text_value = ''
            if xml_values:
                text_value_tmp = xml_values[0].text
                if text_value_tmp:
                    text_value_tmp = text_value_tmp.replace("'",'')
                    text_value_tmp = text_value_tmp.replace('"','')
                    text_value = text_value_tmp
            record[field] = text_value
        return True
    return False

if __name__ == '__main__':
    command = '\npython %s [-t type -n number]' % sys.argv[0]

    parser = OptionParser(usage=command)
    parser.add_option('-c', '--config', dest='config', help='the config file',
                      metavar='FILE')
    parser.add_option('-t', '--type', dest='type', help='the type of operate')
    parser.add_option('-n', '--number', dest='number',
                      help='the number limit of data')
    parser.add_option('-i', '--input', dest='input', help='the input')
    parser.add_option('-o', '--output', dest='output', help='the output')
    operate_type = 'format_medical_record'
    n_limit = sys.maxint
    (options, args) = parser.parse_args()
    if options.type:
        operate_type = options.type
    if options.number:
        n_limit = int(options.number)
    if operate_type == 'format_medical_record':
        format_medical_record(options.input, n_limit=n_limit)
