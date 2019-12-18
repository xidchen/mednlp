# !/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import global_conf
from ailib.utils.log import GLLog
from ailib.storage.db import DBWrapper

# AIMySQLDB 地址是192.168.4.30
# MySQLDB 地址是192.168.3.26


db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')

def get_data(sql_code):
    rows = db.get_rows(sql_code)
    return list(rows)

if __name__ == '__main__':
    sql_code = '''
        select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
        where disease_name LIKE '支气管炎'
        and LENGTH(medical_history)>2
        AND chief_complaint != '便民开药'
        AND medical_history != '无特殊不适'
        LIMIT 10
    '''
    result = get_data(sql_code)
    print(result)