# -*- coding: utf-8 -*-
# author:BerryHN
from ailib.storage.db import DBWrapper
import global_conf
import codecs
disease_id_dept_file = '/home/caoxg/work/mednlp/data/dict/disease_id_dept.csv'
disease_dept_train = '/home/caoxg/work/mednlp/data/traindata/medical_record_dept_train.txt'
disease_dept_test = '/home/caoxg/work/mednlp/data/traindata/medical_record_dept_test.txt'


def build_medical_record_train(disease_id_dept={}):
    """
    使用病例记录中的主诉和症状，然后通过症状和科室的对应关系，输出主诉和科室
    :param disease_id_dept: 症状和科室的对应关系
    :return: 无
    """
    sql = """
    select * from  
    (select  concat(chief_complaint,' ',medical_history) chief_complaint,sex,age,t1.disease_name from 
    medical_data.medical_record  t1  join medical_kg.disease  t2  on  t1.disease_name=t2.disease_name 
    where  common_level=1 and chief_complaint is not null 
    and chief_complaint <>''
    union 
    select  concat(chief_complaint,' ',medical_history) chief_complaint,sex,age,t1.disease_name from 
    medical_data.medical_record_data  t1  join medical_kg.disease  t2 on  t1.disease_name=t2.disease_name
    where  common_level=1 
    and chief_complaint is not null 
    and chief_complaint <>'') t
    """
    disease_id_dept = build_disease_id_dept(disease_id_dept_file)
    fout = codecs.open(disease_dept_train, 'w', encoding='utf-8')
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    rows = db.get_rows(sql)
    count = 1
    for row in rows:
        chief_complaint = row['chief_complaint'].replace('\t', '')
        sex = row['sex']
        age = row['age']
        disease_name = row['disease_name']
        chief_complaint = chief_complaint.strip()
        disease_name = disease_name.strip()
        chief_complaint = chief_complaint.decode('utf-8')
        sex = str(sex).decode('utf-8')
        age = str(age).decode('utf-8')
        if disease_name in disease_id_dept:
            dept_name = [dept.decode('utf-8') for dept in disease_id_dept[disease_name]]
            if len(disease_id_dept[disease_name]) > 1:
                line_one = chief_complaint + '\t' + sex + '\t' + age + '\t' + dept_name[0] + '\n'
                line_second = chief_complaint + '\t' + sex + '\t' + age + '\t' + dept_name[1] + '\n'
                fout.write(line_one)
                fout.write(line_second)
            elif len(disease_id_dept[disease_name]) == 1:
                line_one = chief_complaint + '\t' + sex + '\t' + age + '\t' + dept_name[0] + '\n'
                fout.write(line_one)
            else:
                continue
    fout.close()
    db.close()


def build_medical_record_test(disease_id_dept={}):
    """
    使用病例记录中的主诉和症状，然后通过症状和科室的对应关系，输出主诉和科室
    :param disease_id_dept: 症状和科室的对应关系
    :return: 无
    """
    sql = """
    select * from  
    (select  concat(chief_complaint,' ',medical_history) chief_complaint,sex,age,t1.disease_name from 
    medical_data.medical_record_benchmark  t1  join medical_kg.disease  t2  on  t1.disease_name=t2.disease_name 
    where  common_level=1 and chief_complaint is not null 
    and chief_complaint <>'') t
    """
    disease_id_dept = build_disease_id_dept(disease_id_dept_file)
    fout = codecs.open(disease_dept_test, 'w', encoding='utf-8')
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    rows = db.get_rows(sql)
    count = 1
    for row in rows:
        chief_complaint = row['chief_complaint'].replace('\t', '')
        sex = row['sex']
        age = row['age']
        disease_name = row['disease_name']
        chief_complaint = chief_complaint.strip()
        disease_name = disease_name.strip()
        chief_complaint = chief_complaint.decode('utf-8')
        sex = str(sex).decode('utf-8')
        age = str(age).decode('utf-8')
        if disease_name in disease_id_dept:
            dept_name = [dept.decode('utf-8') for dept in disease_id_dept[disease_name]]
            if len(disease_id_dept[disease_name]) > 1:
                line_one = chief_complaint + '\t' + sex + '\t' + age + '\t' + dept_name[0] + '\n'
                line_second = chief_complaint + '\t' + sex + '\t' + age + '\t' + dept_name[1] + '\n'
                fout.write(line_one)
                fout.write(line_second)
            elif len(disease_id_dept[disease_name]) == 1:
                line_one = chief_complaint + '\t' + sex + '\t' + age + '\t' + dept_name[0] + '\n'
                fout.write(line_one)
            else:
                continue
    fout.close()
    db.close()


def build_disease_id_dept(file_name=disease_id_dept_file):
    """
    根据疾病和科室的对应关系，生成字典
    :param file_name: 疾病和科室的对应关系配置文件
    :return: 返回疾病和科室对应关系字典
    """
    f = codecs.open(file_name, 'r', encoding='utf-8')
    disease_id_dept = {}
    count = 1
    for line in f:
        lines = line.strip().split(',')
        disease_name = lines[0].strip().encode('utf-8')
        dept_names = lines[-1].strip().split('|')
        dept_name = [dept_name.strip().encode('utf-8') for dept_name in dept_names]
        disease_id_dept[disease_name] = dept_name
        count = count + 1
    f.close()
    return disease_id_dept


# build_medical_record()
build_medical_record_train()
build_medical_record_test()
# build_disease_id_dept()
