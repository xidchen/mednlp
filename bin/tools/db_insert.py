#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
db_insert.py -- insert data to db

Author: maogy <maogy@guahao.com>
Create on 2017-06-30 Friday.
"""


import sys
import codecs
import json
from ailib.storage.db import DBWrapper
from optparse import OptionParser
import global_conf as global_conf
from mednlp.dao.kg_dao import KGDao
import ailib.utils.text as text
from ailib.utils.text import HTMLParser


def process(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.symptom(id,name,state,gmt_created,gmt_modified)
    SELECT uuid(),'%s',1,now(),now()
    FROM ai_medical_knowledge.symptom s
    WHERE NOT EXISTS(
          SELECT *
          FROM ai_medical_knowledge.symptom s2
          WHERE s2.name = '%s'
    ) LIMIT 1
    """
    data_tuple_list = []
    count = 0
    for line in codecs.open(filepath, 'r', 'utf-8'):
        count += 1
        line = line.strip()
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        data_tuple_list.append((line, line))
        db.execute(sql % (line, line))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


# def process_disease_rate(filepath):
#     db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
#     base_sql = """
#     UPDATE ai_medical_knowledge.disease d  
#     SET rate=%s
#     WHERE d.id='%s'
#     """
#     data_tuple_list = []
#     count = 0
#     for sentence in codecs.open(filepath, 'r', 'utf-8'):
#         count += 1
#         sentence = unicode(sentence.strip())
#         if count % 100 == 0:
#             print '%s has finished, word:%s' % (count, sentence)
#         disease, rate = sentence.split('|')
#         sql = base_sql % (rate, disease)
#         # print sql
#         # sys.exit(0)
#         db.execute(sql)
#         # break
#     # db.executemany_by_page(sql, data_tuple_list)
#     db.commit()
#     db.close()    


def process_symptom(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.symptom(id,name,state,gmt_created,gmt_modified)
    SELECT uuid(),'%s',1,now(),now()
    FROM ai_medical_knowledge.symptom s
    WHERE NOT EXISTS(
          SELECT *
          FROM ai_medical_knowledge.symptom s2
          WHERE s2.name = '%s'
    ) LIMIT 1
    """
    data_tuple_list = []
    count = 0
    for line in codecs.open(filepath, 'r', 'utf-8'):
        count += 1
        line = line.strip()
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        data_tuple_list.append((line, line))
        db.execute(sql % (line, line))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_disease(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.disease_new(id,name,state,created_staffid,gmt_created,modify_staffid,gmt_modified,disease_type)
    SELECT uuid(),'%s',1,'eagle',now(),'eagle',now(),1
    FROM ai_medical_knowledge.disease_new dn
    WHERE NOT EXISTS(
        SELECT *
        FROM ai_medical_knowledge.disease_new dn2
        WHERE dn2.name = '%s'
    ) LIMIT 1
    """
    data_tuple_list = []
    count = 0
    for line in codecs.open(filepath, 'r', 'utf-8'):
        count += 1
        line = line.strip()
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
            print(sql % (line, line))
        data_tuple_list.append((line, line))
        db.execute(sql % (line, line))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_disease_alias(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    query_base_sql = """
    SELECT
    *
    FROM ai_medical_knowledge.disease_new dn
    WHERE dn.name='%s'
    """
    disease_sql = """
    INSERT INTO ai_medical_knowledge.disease_new(id,name,state,created_staffid,gmt_created,modify_staffid,gmt_modified,disease_type)
    SELECT ifnull(d.id,uuid()),'%s',1,'eagle',now(),'eagle',now(),4
    FROM ai_medical_knowledge.disease_new dn
    LEFT JOIN ai_medical_knowledge.disease d on d.name='%s'
    left join ai_medical_knowledge.disease_new dn2 on dn2.name='%s'
    WHERE dn2.id IS NULL
    LIMIT 1
    """
    relation_sql = """
    INSERT INTO ai_medical_knowledge.relation_info(entity_id_a, entity_id_b, type, state, gmt_created, gmt_modified, create_staff, modify_staff)
    SELECT dn.id, dn2.id, 1003, 1, NOW(), NOW(), 'eagle', 'eagle'
    FROM ai_medical_knowledge.disease_new dn
    LEFT JOIN ai_medical_knowledge.disease_new dn2 on dn2.name='%s'
    where dn.disease_type=4 and dn.name='%s'
    """
    data_tuple_list = []
    count = 0
    for line in codecs.open(filepath, 'r', 'utf-8'):
        count += 1
        line = line.strip()
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        name_list = line.split('::')
        if not name_list:
            continue
        std_name = name_list[0]
        alias = set()
        nos_name = parse_nos(std_name)
        if nos_name:
            alias.add(nos_name)
        if len(name_list) > 1:
            for name in name_list[1:]:
                alias.add(name)
                nos_name = parse_nos(name)
                if nos_name:
                    alias.add(nos_name)
        if not alias:
            continue
        print('std:%s, alias:%s' % (std_name, '|'.join(alias)))
        for alia in alias:
            sql = query_base_sql % alia
            rows = db.get_rows(sql)
            if rows:
                continue
            print('std:%s, alia:%s' % (std_name, alia))
            sql = disease_sql % (alia, alia, alia)
            db.execute(sql)
            db.commit()
            # print sql
            sql = relation_sql % (std_name, alia)
            db.execute(sql)
            db.commit()
            # print sql
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_disease_englist(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    base_sql = """
    update ai_medical_knowledge.disease_new dn
    set dn.disease_type=5
    where dn.name='%s'
    """
    count = 0
    for line in codecs.open(filepath, 'r', 'utf-8'):
        count += 1
        line = line.strip()
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))

        sql = base_sql % line
        db.execute(sql)
    db.commit()
    db.close()


def parse_nos(name):
    if name.endswith(' NOS'):
        return name.replace(' NOS', '')
    return None


def process_relation(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.relation_info 
    (entity_id_a, entity_id_b, weight, type, gmt_created, gmt_modified, create_staff, modify_staff)
    VALUES('%s','%s',%s,1,now(),now(),'eagle','eagle');
    """
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        disease_id, symptom_id, weight = line.split('|')
        db.execute(sql % (disease_id, symptom_id, int(float(weight) * 10000)))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def insert_disease_count(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.t_disease_count(disease_name, count,type)
    VALUES('%s', %s, %s);
    """
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        count, name = line.split('|')[0:2]
        try:
            count = int(count)
        except Exception as e:
            count = 0
        name = name.replace("'", '').replace('\\', '')
        # print sql % (name, count)
        db.execute(sql % (name, count, '4'))
    db.commit()
    db.close()


def insert_disease_name(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.t_disease_name(disease_name, disease_uuid, disease_type)
    VALUES('%s', '%s', %s);
    """
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        item_list = line.split('|')
        disease_id = ''
        disease_type = 2
        disease_name = item_list[0]
        # value = item_list[1]
        # print sql % (name, count)
        db.execute(sql % (disease_name.strip(), disease_id, disease_type))
    db.commit()
    db.close()


def insert_symptom_name(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.t_symptom_name(symptom_name, symptom_uuid, symptom_type)
    VALUES('%s', '%s', %s);
    """
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        item_list = line.split('|')
        symptom_id = ''
        symptom_type = 3
        symptom_name = item_list[0]
        # value = item_list[1]
        # print sql % (name, count)
        db.execute(sql % (symptom_name.strip(), symptom_id, symptom_type))
    db.commit()
    db.close()


def insert_relation(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql_base = """
    INSERT INTO ai_medical_knowledge.relation_info
    (entity_id_a, entity_id_b, type, state, gmt_created, gmt_modified, create_staff, modify_staff)
    SELECT '%(entity_id_a)s', '%(entity_id_b)s', %(type)s, 1, NOW(), NOW(), 'eagle', 'eagle'
    FROM (SELECT 1 aa) bb
    LEFT JOIN ai_medical_knowledge.relation_info ri
        ON ri.entity_id_a='%(entity_id_a)s' AND ri.entity_id_b='%(entity_id_b)s'
        AND ri.`type` = %(type)s AND ri.state=1
    WHERE ri.id IS NULL
    """
    data_tuple_list = []
    item_field = ['entity_id_a', 'entity_id_b', 'type']
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = unicode_python_2_3(line.strip())
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        item_list = line.split('|')
        field_dict = {}
        if len(item_list) < 3:
            continue
        for index, field in enumerate(item_field):
            field_dict[field] = item_list[index]
        sql = sql_base % field_dict
        db.execute(sql % field_dict)
    db.commit()
    db.close()


def process_mh_symptom_synonym(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.symptom(id,name,state,gmt_created,gmt_modified,`source`)
    SELECT uuid(),'%s',1,now(),now(),4
    FROM ai_medical_knowledge.symptom s
    LEFT JOIN ai_medical_knowledge.symptom s2 ON s2.name='%s'
    where s2.id is null
    LIMIT 1
    """
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        db.execute(sql % (line, line))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_symptom_synonym_group(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT IGNORE INTO ai_medical_knowledge.relation_info(entity_id_a, entity_id_b, type, state, gmt_created, gmt_modified, create_staff, modify_staff)
    VALUES('%s', '%s', 3000, 1, NOW(), NOW(), 'eagle', 'eagle')
    """
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        symptom_id, groups = line.split(',,,')
        group_list = groups.split('|')
        for group in group_list:
            db.execute(sql % (group, symptom_id))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_symptom_synonym_group2(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO ai_medical_knowledge.relation_info(entity_id_a, entity_id_b, type, state, gmt_created, gmt_modified, create_staff, modify_staff)
    SELECT '%s', '%s', 3000, 1, NOW(), NOW(), 'eagle', 'eagle'
    FROM ai_medical_knowledge.disease_new dn
    LEFT JOIN ai_medical_knowledge.relation_info ri3 on ri3.entity_id_a='%s' AND ri3.entity_id_b='%s'
    where ri3.id is null
    limit 1
    """
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        symptom_id, groups = line.split(',,,')
        group_list = groups.split('|')
        for group in group_list:
            db.execute(sql % (group, symptom_id, group, symptom_id))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_symptom_synonym_group3(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        group_id, symptoms_str = line.split('|||')
        symptoms = symptoms_str.split(',')
        symptom_name = [{'name': s} for s in symptoms]
        kg.insert_symptom(db, symptom_name)
        if not group_id:
            kg.insert_symptom_group_group(db, symptoms_str)
        else:
            print('update group:', group_id)
            kg.update_symptom_group(db, group_id, symptoms)
        # group_list = groups.split(',')
        # for group in group_list:
        #     db.execute(sql % (group, symptom_id, group, symptom_id))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_medical_synonym(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        group_id, symptoms_str = line.split('|||')
        symptoms = symptoms_str.split(',')
        symptom_name = [{'name': s} for s in symptoms]
        kg.insert_symptom(db, symptom_name)
        if not group_id:
            kg.insert_medical_synonym(db, symptoms_str)
        else:
            print('update group:', group_id)
            kg.update_medical_synonym(db, group_id, symptoms)
    db.commit()
    db.close()


def process_medical_synonym2(filepath):
    """
    医学同义词处理.
    参数->filepath,同义词文件
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        synonym_type, words_str = line.split('|||')
        words = words_str.split(',')
        if len(words) < 2:
            continue
        if synonym_type.strip() == '2':
            kg.insert_body_part(db, [{'body_part_name': s} for s in words])
            kg.insert_body_part_synonym_relation(db, words)
        elif synonym_type.strip() == '1':
            kg.insert_symptom(db, [{'name': s} for s in words])
            kg.insert_symptom_synonym_relation(db, words)

    db.commit()
    db.close()


def process_medical_record_score(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    sql = """
    INSERT INTO medical_data.medical_record_score(medical_record_id,score,state,create_staff,gmt_created,modify_staff,gmt_modified)
    SELECT %s,%s,1,'eagle',now(),'eagle',now()
    FROM medical_data.medical_record_score mrc
    LEFT JOIN medical_data.medical_record_score mrc2 on mrc2.medical_record_id=%s AND mrc2.state=1
    where mrc2.id is null
    limit 1
    """
    data_tuple_list = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, line))
        score, medical_record_id = line.split('|')
        if not score or not medical_record_id:
            continue
        score = int(float(score))
        db.execute(sql % (medical_record_id, score, medical_record_id))
        # break
    # db.executemany_by_page(sql, data_tuple_list)
    db.commit()
    db.close()


def process_medical_record(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['hospital_name', 'hospital_record_id', 'disease_name', 'sex',
                  'age', 'type', 'chief_complaint', 'medical_history',
                  'past_medical_history', 'personal_history', 'family_history',
                  'obstetrical_history', 'menstrual_history', 'body_check',
                  'create_time']
    error_count = 0
    his_line = ''
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        if count < 1:
            continue
        line = line.strip()
        # print sentence
        if not line:
            continue
        line = line.replace("'", '')
        line = line.replace('\\', '')
        if not his_line:
            his_line = line
            continue
        line = str(line)
        if line[0] != '"' or his_line[-1] != '"':
            his_line += line
            continue
        if count % 1000 == 0:
            print('%s has finished, word:%s' % (count, his_line))
        l_len = len(his_line)
        his_line = str(his_line[1:l_len - 1])
        his_line = his_line.strip()
        item = parse_line_for_process_verify_data(his_line, field_name, seg='","')
        # print '###,'.join(item.values())
        # break
        his_line = line
        if not item:
            error_count += 1
            continue
        if not item.get('disease_name'):
            continue
        item.pop('body_check', '')
        item.pop('create_time', '')
        if not item['sex']:
            item['sex'] = 3
        if not item['age']:
            item['age'] = 0
        if not item['type']:
            item['type'] = 1
        if not item['hospital_record_id']:
            continue
        # # item['count'] = count + 1000
        # # item['disease_name_org'] = item['disease_name']
        kg.insert_medical_record_data(db, [item])


def process_synonym_group_org(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    words_group = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item_list = line.split(' ')
        words = item_list[1:]
        words_group.append({'words': ','.join(words)})
    kg = KGDao()
    kg.insert_synonym_group(db, words_group)


def process_synonym_group(xxx):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    kg.update_synonym_relation(db)


def process_verify_data_critical(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_id', 'disease_name', 'rate_org', 'sex_org', 'sex',
                  'age_min_org', 'age_min', 'age_max_org', 'age_max',
                  'symptom_org', 'symptom', 'alias_org', 'alias']
    age_dict = {'age_min': 1202, 'age_max': 1204}
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name)
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        if not kg.check_disease(db, item['disease_name']):
            print(line)
            continue
        properties = [{'disease_name': item['disease_name'],
                      'property_type': 1, 'property_value': 'NULL'}]
        kg.insert_disease_property(db, properties)
        process_parsed_item(db, kg, item, field_name, age_dict)


def process_symptom_count(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item_list = line.split('|')
        if len(item_list) != 2:
            continue
        item = {'symptom_name': item_list[0], 'property_type': 2,
                'property_value': item_list[1]}
        kg.insert_symptom_property(db, [item])


def process_parsed_item(db, kg, item, field_name, age_dict={}):
    s_names = item['symptom'].split('|||')
    symptoms = [{'name': name.strip()} for name in s_names]
    kg.insert_symptom(db, symptoms)
    kg.insert_symptom_group(db, symptoms)
    kg.insert_symptom_group_relation(db, symptoms)
    ds_relation = build_disease_symptom_relation(
        item['disease_name'], s_names, 4, 8000)
    kg.insert_disease_symptom_relation(db, ds_relation)
    alias = item['alias'].split('|||')
    disease_alias = build_disease_alias(item['disease_name'],
                                        alias, 1)
    kg.insert_disease_alias(db, disease_alias)
    weight_rela = []
    if item.get('woman'):
        weight_rela.append(
            {'disease_name': item['disease_name'], 'value': 1,
             'type': 1102, 'weight': item['woman']})
    if item.get('man'):
        weight_rela.append(
            {'disease_name': item['disease_name'], 'value': 2,
             'type': 1102, 'weight': item['man']})
    for i in range(1, 7):
        age_field = 'age_%s' % i
        if item.get(age_field):
            weight_rela.append(
                {'disease_name': item['disease_name'], 'value': i,
                 'type': 1206, 'weight': item[age_field]})
    kg.insert_disease_weight_relation(db, weight_rela)
    sex = item.get('sex')
    d_sex_age_rela = []
    if sex and int(sex) in (1, 2):
        d_sex_age_rela.append({'disease_name': item['disease_name'],
                               'value': sex, 'type': 1101})
    for field, type_str in age_dict.items():
        value = item.get(field)
        if not value or not int(value):
            continue
        d_sex_age_rela.append({'disease_name': item['disease_name'],
                               'value': value, 'type': type_str})
    kg.insert_disease_sex_age_relation(db, d_sex_age_rela)


def process_verify_data(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_id', 'disease_name', 'sex_org', 'sex', 'age_min_org',
                  'age_min', 'age_min_pop', 'age_max_org', 'age_max',
                  'age_max_pop', 'symptom_org', 'symptom_a', 'symptom',
                  'alias_org', 'alias']
    age_dict = {'age_min': 1202, 'age_min_pop': 1204, 'age_max': 1203,
                'age_max_pop': 1205}
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name)
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        process_parsed_item(db, kg, item, field_name, age_dict)


def process_verify_data2(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_id', 'disease_name', 'sex', 'sex_no', 'age_min',
                  'age_min_no', 'age_max', 'age_max_no',
                  'symptom_org', 'symptom', 'alias_org', 'alias']
    age_dict = {'age_min': 1202, 'age_max': 1203}
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name)
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        process_parsed_item(db, kg, item, field_name, age_dict)


def process_verify_data3(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_id', 'disease_name', 'woman', 'man', 'age_1',
                  'age_2', 'age_3', 'age_4', 'age_5', 'age_6',
                  'symptom_org', 'symptom', 'alias_org', 'alias']
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name)
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        process_parsed_item(db, kg, item, field_name)


def process_verify_data4(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_id', 'disease_name', 'woman', 'man', 'age_1',
                  'age_2', 'age_3', 'age_4', 'age_5', 'age_6']
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name)
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        process_parsed_item(db, kg, item, field_name)


def process_critical_rate(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_id', 'disease_name', 'rate']
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name)
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        item['rate'] = int(item['rate']) * 10
        properties = [{'disease_name': item['disease_name'],
                      'property_type': 3, 'property_value': item['rate']}]
        kg.insert_disease_property(db, properties)


def process_disease_time(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_name', 'chronic', 'acute']
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name, seg='#')
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        properties = []
        if item.get('acute'):
            properties.append({
                'disease_name': item['disease_name'],
                'property_type': 6, 'property_value': item['acute']})
        if item.get('chronic'):
            properties.append({
                'disease_name': item['disease_name'],
                'property_type': 7, 'property_value': item['chronic']})
        kg.insert_disease_property(db, properties)


def process_disease_rate(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    field_name = ['disease_name', 'rate']
    error_count = 0
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, field_name, seg='\t')
        if not item or not item.get('disease_name'):
            error_count += 1
            continue
        item['rate'] = int(float(item['rate']) * 10)
        properties = [{'disease_name': item['disease_name'],
                      'property_type': 4, 'property_value': item['rate']}]
        kg.insert_disease_property(db, properties)


def process_disease_common(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = {'disease_name': line, 'common_level': 2}
        kg.update_disease_common(db, [item])


def process_disease_json(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    f_json = codecs.open(filepath, 'r', 'utf-8')
    diseases_str = f_json.read()
    diseases = json.loads(diseases_str)
    print('diseases:', len(diseases), ','.join(list(diseases.keys())))
    fields = ['disease_name_en', 'definition', 'cause', 'pathogenesis',
              'pathophysiological', 'clinical_manifestation', 'complication',
              'lab_check', 'other_check', 'diagnosis',
              'differential_diagnosis', 'treatment', 'prevention', 'prognosis']
    count = 0
    for name, detail in diseases.items():
        count += 1
        if count < 10:
            print('count', count)
            print('name:', name)
            print('detail', detail)
        detail['disease_name'] = name
        detail['source'] = 5
        exist_field_count = 0
        for field in fields:
            if not field in detail:
                detail[field] = ''
            else:
                exist_field_count += 1
            detail[field] = detail[field].replace("'", '"')
            detail[field] = detail[field].replace('||p||', '。\n')
        if exist_field_count > 2:
            kg.insert_disease_detail(db, [detail])
    f_json.close()


def process_disease_csv(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    fields = ['disease_uuid', 'disease_name', 'definition', 'cause', 'pathogenesis',
              'pathophysiological', 'clinical_manifestation', 'complication',
              'lab_check', 'other_check', 'diagnosis',
              'differential_diagnosis', 'treatment', 'prevention', 'prognosis']
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = line.replace('###', '\n')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        item = parse_line_for_process_verify_data(line, fields, seg='|')
        item['disease_name_en'] = ''
        item['source'] = 6
        kg.insert_disease_detail(db, [item])


def process_disease_baike(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    fields = ['disease_name', 'disease_name_en', 'definition', 'cause', 'pathogenesis',
              'pathophysiological', 'clinical_manifestation', 'complication',
              'lab_check', 'other_check', 'diagnosis',
              'differential_diagnosis', 'treatment', 'prevention', 'prognosis']
    disease_field_file, field_value_file = filepath.split(',')
    f_json = codecs.open(field_value_file, 'r', 'utf-8')
    diseases_str = f_json.read()
    diseases_str = text.remove_control_characters(diseases_str)
    diseases = json.loads(diseases_str)
    field_value = {}
    for record in diseases['RECORDS']:
        field_value[int(record['id'])] = record['content']
    code_field = {
        'ab11': 'definition', 'ac12': 'clinical_manifestation',
        'ac13': 'cause', 'ac14': 'lab_check', 'ac15': 'diagnosis',
        'ac16': 'treatment', 'ac17': 'prognosis', 'ac18': 'prevention'
    }
    html_parser = HTMLParser()
    for count, line in enumerate(codecs.open(disease_field_file, 'r', 'utf-8')):
        line = line.strip().replace("'", '')
        line = str(line)
        if count % 100 == 0:
            print('%s has finished, word:%s' % (count, line))
        disease_name, content = line.split('\t')
        baike = {}
        try:
            baike = json.loads(content)
        except Exception as e:
            continue
        item = {'disease_name': disease_name}
        for code, v_id in baike.items():
            code, v_id = str(code), int(v_id)
            if code in code_field:
                value = field_value.get(v_id)
                if not value:
                    continue
                html_parser.feed(value)
                item[code_field[code]] = html_parser.get_data().replace('"', '').replace("'", '')
        for field in fields:
            if field not in item:
                item[field] = ''
        item['source'] = 110
        # print item
        kg.insert_disease_detail(db, [item])


def build_disease_alias(disease_name, alias, type_str):
    relations = []
    for name in alias:
        if not name or not name.strip():
            continue
        name = name.strip()
        item = {}
        item['disease_name'] = disease_name
        item['alias'] = name
        item['type'] = type_str
        relations.append(item)
    return relations


def build_disease_symptom_relation(disease_name, symptoms, type_str, weight_max):
    length = float(len(symptoms))
    weight_max = float(weight_max)
    relations = []
    for count, symptom in enumerate(symptoms):
        rela = {}
        rela['weight'] = (length - count) / length * weight_max
        rela['disease_name'] = disease_name
        rela['type'] = type_str
        rela['symptom_name'] = symptom
        relations.append(rela)
    # print relations
    return relations


def parse_line_for_process_verify_data(line, field_list, **kwargs):
    seg = kwargs.get('seg', ',')
    try:
        item_list = line.split(seg)
        item = {}
        for count, value in enumerate(item_list):
            item[field_list[count]] = value.strip()
        if item.get('disease_name'):
            item['disease_name'] = item['disease_name'].replace('|||', ',')
        return item
    except Exception as e:
        print(sys.exc_info())
        print(line)
        return None


def process_body_part(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    body_parts = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        body_parts.append({'body_part_name': line})
    kg.insert_body_part(db, body_parts)


def process_medical_word(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    medical_words = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        medical_words.append({'medical_word_name': line})
    kg.insert_medical_word(db, medical_words)


def process_physical_examination(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    medical_words = []
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        items = line.split('|')
        if len(items) > 3 or len(items) < 2:
            print('parse error with:', line)
            continue
        name = items[1].replace("'", "\\'").strip()
        type = items[0]
        value = ''
        if len(items) == 3:
            value = items[2]
        kg.insert_physical_examination(
            db, [{'physical_examination_name': name}])
        properties = []
        item = {'physical_examination_name': name, 'property_type': 1,
                'property_value': type}
        properties.append(item)
        if type == '2':
            for option in value.split(';;'):
                item = {'physical_examination_name': name, 'property_type': 10,
                        'property_value': option}
                properties.append(item)
        if type == '3':
            item = {'physical_examination_name': name, 'property_type': 11,
                    'property_value': value}
            properties.append(item)
        kg.insert_physical_examination_property(db, properties)


def process_inspection(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    medical_words = []
    field_list = ['name1', 'name2', 'name_short', 'sex', 'age', 'value', 'unit']
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        item = parse_line_for_process_verify_data(line, field_list, seg='|')
        inspection_names = [{'inspection_name': item['name1']}]
        inspection_names.append({'inspection_name': item['name2']})
        kg.insert_inspection(db, inspection_names)
        inspection_properties = []
        inspection_properties.append({'inspection_name': item['name1'],
                                     'property_type': 1, 'property_value': 1})
        inspection_properties.append({'inspection_name': item['name2'],
                                     'property_type': 1, 'property_value': 2})
        inspection_parent_properties = []
        inspection_parent_properties.append(
            {'inspection_name': item['name2'],
             'property_type': 2, 'inspection_name_parent': item['name1']})
        inspection_properties.append({'inspection_name': item['name2'],
                                     'property_type': 3,
                                     'property_value': item['name_short']})
        inspection_properties.append({'inspection_name': item['name2'],
                                     'property_type': 4,
                                     'property_value': item['unit']})
        kg.insert_inspection_property(db, inspection_properties)
        kg.insert_inspection_parent_property(db, inspection_parent_properties)


def process_disease_physical_examination(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        items = line.split('#')
        disease_name = items[0]
        physical_examinations = [pe for pe in items[1:] if pe]
        names = [{'physical_examination_name': name} for name in physical_examinations]
        kg.insert_physical_examination(
            db, names)
        properties = []
        disease_relation = []
        for name in physical_examinations:
            item = {'physical_examination_name': name, 'property_type': 1,
                    'property_value': 1}
            properties.append(item)
            item = {'disease_name': disease_name,
                    'physical_examination_name': name}
            disease_relation.append(item)
        kg.insert_physical_examination_property(db, properties)
        kg.insert_disease_physical_examination(db, disease_relation)
        # sys.exit(0)


def process_disease_inspection(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        items = line.split('#')
        disease_name = items[0]
        inspections = [pe for pe in items[1:] if pe]
        names = [{'inspection_name': name} for name in inspections]
        kg.insert_inspection(db, names)
        properties = []
        disease_relation = []
        for name in inspections:
            item = {'inspection_name': name, 'property_type': 99,
                    'property_value': ''}
            properties.append(item)
            item = {'disease_name': disease_name,
                    'inspection_name': name}
            disease_relation.append(item)
        kg.insert_inspection_property(db, properties)
        kg.insert_disease_inspection(db, disease_relation)


def process_disease_inspection_level2(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        items = line.split('#')
        disease_name = items[0]
        inspections = [item for item in items[1:] if item]
        disease_insp = []
        for insp in inspections:
            item_list = insp.split('|||')
            kg.insert_inspection_parent(db, {'inspection_name': item_list[0]})
            insp = {'inspection_name': item_list[1],
                    'inspection_name_parent': item_list[0]}
            insp_id = kg.insert_inspection(db, insp)
            item = {'inspection_id': insp_id, 'disease_name': disease_name}
            if len(item_list) < 3:
                item['r_type'] = 6001
            elif len(item_list) == 3:
                item.update({'r_type': 6002, 'option': item_list[2]})
                kg.insert_inspection_property(
                    db, [{'inspection_id': insp_id,
                          'property_type': 5, 'property_value': item_list[2]}])
            elif len(item_list) == 5:
                item.update(
                    {'r_type': 6003, 'min': item_list[2],
                     'max': item_list[3], 'unit': item_list[4]})
                if item['min'] in ('x', 'X'):
                    del item['min']
                if item['max'] in ('x', 'X'):
                    del item['max']
                kg.insert_inspection_property(
                    db, [{'inspection_id': insp_id,
                          'property_type': 4, 'property_value': item_list[4]}])
            disease_insp.append(item)
        kg.insert_disease_inspection_full(db, disease_insp)


def process_disease_inspection_level1(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        items = line.split('#')
        disease_name = items[0]
        inspections = [item for item in items[1:] if item]
        disease_insp = []
        for insp in inspections:
            item_list = insp.split('|||')
            insp_id = kg.insert_inspection_parent(
                db, {'inspection_name': item_list[0]})
            item = {'inspection_id': insp_id, 'disease_name': disease_name}
            if len(item_list) < 2:
                item['r_type'] = 6001
            elif len(item_list) == 2:
                item.update({'r_type': 6002, 'option': item_list[1]})
                kg.insert_inspection_property(
                    db, [{'inspection_id': insp_id,
                          'property_type': 5, 'property_value': item_list[1]}])
            elif len(item_list) == 4:
                item.update(
                    {'r_type': 6003, 'min': item_list[1],
                     'max': item_list[2], 'unit': item_list[3]})
                if item['min'] in ('x', 'X'):
                    del item['min']
                if item['max'] in ('x', 'X'):
                    del item['max']
                kg.insert_inspection_property(
                    db, [{'inspection_id': insp_id,
                          'property_type': 4, 'property_value': item_list[3]}])
            disease_insp.append(item)
        kg.insert_disease_inspection_full(db, disease_insp)


def process_disease_complicated(filepath):
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    kg = KGDao()
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        if not line:
            continue
        item_list = line.split('|')
        disease_past = item_list[0].strip()
        disease_diagnose = item_list[1:]
        words = []
        for name in disease_diagnose:
            words.append({'disease_diagnose': name.strip(),
                          'disease_past': disease_past})
        kg.insert_disease_complicated(db, words)


def format_disease_count(filepath):
    disease_count = {}
    for count, line in enumerate(codecs.open(filepath, 'r', 'utf-8')):
        line = line.strip()
        item_list = line.split('|')
        if len(item_list) < 2:
            continue
        count = item_list[0].replace(',', '')
        if not count.isdigit():
            continue
        count = int(count)
        disease = item_list[1].replace('"', '').strip()
        if not disease:
            continue
        if disease in disease_count:
            disease_count[disease] += count
        else:
            disease_count[disease] = count
    for disease, count in disease_count.items():
        if count < 10:
            continue
        print('%s|%s' % (count, disease))


if __name__ == '__main__':
    command = """\npython %s [datafile]""" % sys.argv[0]

    parser = OptionParser(usage=command)
    parser.add_option("-f", "--file", dest="file", help="the file to process")
    parser.add_option("-t", "--type", dest="type", help="the type of process")
    (options, args) = parser.parse_args()
    if options.type is None:
        print(command)
        sys.exit(0)
    eval(options.type)(options.file)
    # process_verify_data(sys.argv[1])
    # process_verify_data_critical(sys.argv[1])
    # process_critical_rate(sys.argv[1])
    # process_synonym_group(sys.argv[1])
