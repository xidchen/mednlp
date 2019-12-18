#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
process_check_prescription.py --

Author: caoxg <caoxg@guahao.com>
Create on 2019-04-03 Saturday.
"""
import codecs
import numpy as np
import pandas as pd
import re
import xlwt
from ailib.storage.db import DBWrapper
import global_conf
import xlrd
import datetime


def read_xls():
    """
    把数据导入备用数据库
    :return:无
    """
    data = xlrd.open_workbook('/home/caoxg/work/mednlp/bin/training/check_prescription_20190401.xls')
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    table = data.sheet_by_index(0)
    nrows = table.nrows
    ncols = table.nrows
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(0, nrows):
        department_name = table.cell(i, 0).value
        patient_sex = int(table.cell(i, 1).value)
        diagnosis = table.cell(i, 2).value
        common_preparation = table.cell(i, 3).value
        specification = table.cell(i, 4).value
        number = table.cell(i, 5).value
        administration_route = table.cell(i, 6).value
        dose = table.cell(i, 7).value
        frequency = table.cell(i, 8).value
        days = table.cell(i, 9).value
        allergic = table.cell(i, 10).value
        sql = """INSERT INTO  ai_medical_knowledge.a (department_name, patient_sex, diagnosis
, common_preparation_uuid, specification, number, administration_route, dose,frequency, days,allergic,is_deleted,
gmt_created, gmt_modified, create_staff,modify_staff)  values ('{}',{},'{}','{}','{}','{}','{}','{}','{}','{}',{},{},
'{}','{}', '{}','{}')""".format(department_name, patient_sex, diagnosis, common_preparation, specification, number,
                                administration_route, dose, frequency, days, allergic, 0, dt, dt, 'mednlp', 'mednlp')
        execute = db.execute(sql)
        db.commit()
    db.close()


def read_data():
    """
    读取审方数据
    :return:
    """
    file = '/home/caoxg/work/mednlp/data/traindata/check_prescription/check_prescription2.csv'
    data = pd.read_csv(file, header=None, index_col=0)
    data.columns = ['department_name',
                'patient_sex',
                'diagnosis',
                'common_preparation_uuid',
                'specification',
                'number',
                'administration_route',
                'dose',
                'frequency',
                'days',
                'allergic',
                'is_deleted',
                'gmt_created',
                'gmt_modified',
                'create_staff',
                'modify_staff',
                'common_name']
    return data


def get_workbook():
    """
    建立xls文件工作簿
    :return:返回xls文件句柄
    """
    file = xlwt.Workbook()
    return file


def get_replace_specification(line):
    """
    处理规格字段，并对规格中的符号进行替换
    :param line: 规格字段
    :return: 返回替换后的规格字段
    """
    label_dict = {"d": "袋", "s": "粒", "t": "片", "T": "片", "w": "丸", "克": "g", "升": "l"}
    rep = re.compile('[dstTw克升]')
    words = line.strip().split('*')
    word = words[-1]
    after_word = ""
    left_words = words[:-1]
    if re.search(rep, word):
        index_label = re.search(rep, word).group()
        loc = re.search(rep, word).span()
        last = word[:loc[0]]
        last_label = label_dict.get(index_label)
        last_word = str(last) + str(last_label)
        left_words.append(last_word)
        after_word = "*".join(left_words)
    return after_word


def save_data(data):
    """
    :param data: 原来的审方数据
    :return: 返回规格转换以后的数据
    """
    workbook = xlwt.Workbook()
    table1 = workbook.add_sheet("replace")
    table2 = workbook.add_sheet("origin")
    count = 0
    for i in range(data.shape[0]):
        department_name = data.iloc[i, [0]].values[0]
        # print(department_name)
        patient_sex = int(data.iloc[i, [1]].values[0])
        diagnosis = data.iloc[i, [2]].values[0]
        common_preparation_uuid = data.iloc[i, [3]].values[0]
        specification = data.iloc[i, [4]].values[0]
        number = int(data.iloc[i, [5]].values[0])
        administration_route = data.iloc[i, [6]].values[0]
        dose = data.iloc[i, [7]].values[0]
        frequency = data.iloc[i, [8]].values[0]
        days = data.iloc[i, [9]].values[0]
        allergic = int(data.iloc[i, [10]].values[0])
        is_deleted = int(data.iloc[i, [11]].values[0])
        gmt_created = data.iloc[i, [12]].values[0]
        gmt_modified = data.iloc[i, [13]].values[0]
        create_staff = data.iloc[i, [14]].values[0]
        modify_staff = data.iloc[i, [15]].values[0]
        common_name = data.iloc[i, [16]].values[0]
        specification_after = get_replace_specification(specification)
        if specification_after:
            # print(specification)
            # print(specification_after)
            table1.write(count, 0, department_name)
            table1.write(count, 1, patient_sex)
            table1.write(count, 2, diagnosis)
            table1.write(count, 3, common_preparation_uuid)
            table1.write(count, 4, specification_after)
            table1.write(count, 5, number)
            table1.write(count, 6, administration_route)
            table1.write(count, 7, dose)
            table1.write(count, 8, frequency)
            table1.write(count, 9, days)
            table1.write(count, 10, allergic)
            table1.write(count, 11, is_deleted)
            table1.write(count, 12, gmt_created)
            table1.write(count, 13, gmt_modified)
            table1.write(count, 14, create_staff)
            table1.write(count, 15, modify_staff)
            table1.write(count, 16, common_name)
            table2.write(count, 0, department_name)
            table2.write(count, 1, patient_sex)
            table2.write(count, 2, diagnosis)
            table2.write(count, 3, common_preparation_uuid)
            table2.write(count, 4, specification)
            table2.write(count, 5, number)
            table2.write(count, 6, administration_route)
            table2.write(count, 7, dose)
            table2.write(count, 8, frequency)
            table2.write(count, 9, days)
            table2.write(count, 10, allergic)
            table2.write(count, 11, is_deleted)
            table2.write(count, 12, gmt_created)
            table2.write(count, 13, gmt_modified)
            table2.write(count, 14, create_staff)
            table2.write(count, 15, modify_staff)
            table2.write(count, 16, common_name)
            count = count + 1

    workbook.save('check_prescription_20190401.xls')


def concate_table():
    """
    对sql语句进行转换，加上表明
    :return:
    """
    file = '/home/caoxg/work/mednlp/data/traindata/check_prescription/check_prescription_new.sql'
    out_file = '/home/caoxg/work/mednlp/data/traindata/check_prescription/check_prescription_new_clear.sql'
    f = codecs.open(file, 'r', encoding='utf-8')
    f_out = codecs.open(out_file, 'w', encoding='utf-8')
    for line in f:
        lines = re.split("\`{2}", line)
        clear_line = lines[0] + str("std_prescription") + lines[1]
        f_out.write(clear_line)


if __name__ == '__main__':
    # data = read_data()
    # save_data(data)
    # read_xls()
    concate_table()
    # read_xls()