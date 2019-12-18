#!/usr/bin/python
# -*- coding: utf-8 -*-

import string
import tempfile
import sys,os
import time, datetime
import re
from html.parser import HTMLParser
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

INCREMENTAL_TIME_FORMAT={
        'std_time_format':'%Y-%m-%d %H:%M:%S'
}
if sys.version > '3':
    basestring = str
else:
    basestring = (str, unicode)


def pasttime_interval_seconds(seconds=0, fmt='%Y-%m-%d %H:%M:%S'):
    timestamp = int(time.time())
    if seconds != 0:
        timestamp -= seconds
    return time.strftime(fmt, time.localtime(timestamp))

def format_time(mysql_time, solr_format='%Y-%m-%dT%H:%M:%SZ'):
    """
    格式化时间,通常用于将mysql的时间格式转为solr的格式.
    参数:
    mysql_time->mysql默认格式的时间.
    solr_format->默认值为solr的时间格式('%Y-%m-%dT%H:%M:%SZ').
    返回值:solr_format指定的格式的时间字符串.
    """
    mysql_format = '%Y-%m-%d %H:%M:%S'
    if mysql_time:
        if isinstance(mysql_time, basestring):
            return time.strftime(solr_format, time.strptime(mysql_time, mysql_format))
        else:
            return mysql_time.strftime(solr_format)
    else:
        return None

# 转换字符串为ascii码字符串
def native_to_ascii(native):
    if not native:
        return None
    return ''.join(['\\u%s' % hex(ord(ch))[2:].zfill(4) for ch in native])

if __name__=="__main__":
    pass

def is_empty_string(s, strict = False):
    if s is None:
        return True
    elif ((not strict) or isinstance(s, basestring)) and s.lower() in ('null', 'none'):
        return True
    elif ((not strict) or isinstance(s, basestring)) and len(s) == 0:
        return True
    else:
        return False

def normalize_name(name):
    # replace semiangle and SBC space
    name = name.replace("　","")
    name = name.replace(" ", "")
    # replace .
    name = name.replace(".","")
    name = name.replace("·", "")
    name = name.replace("．", "")
    # replace ()
    name = name.replace('（', '(')
    name = name.replace('）', ')')
    name = re.sub(r"\(.+\)", "", name)
    # replace number
    name = re.sub(r"[0-9]", "", name)

    return name

CONTROL_CHARS = ''
def remove_control_characters(s, ignore_chars = '\r\n'):
    global CONTROL_CHARS
    if len(CONTROL_CHARS) == 0:
        for i in range(32):
            c = chr(i)
            if c not in ignore_chars:
                CONTROL_CHARS += c
    return s.translate(string.maketrans(CONTROL_CHARS, ' ' * len(CONTROL_CHARS)))

def utf8_decode(s):
    if s is None:
        return s
    return s.decode('utf8')

def dump(s, f = sys.stdout, do_flush = False):
    f.write(s)
    if do_flush:
        f.flush()

def select_file_handler(dest_dir, prefix = '', filename=None):
    if dest_dir is None:
        return sys.stdout
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    if filename:
        return file(os.path.join(dest_dir, filename), 'w')
    else:
        return file(tempfile.mkstemp('.xml', prefix, dest_dir)[1], 'w')

def close_file_handler(filehandle):
    if filehandle != sys.stdout:
        filehandle.close()

def is_english_disease_name(name):
    name = re.sub(r" |-|、|,|，|'|’|/|\(|\)|]", '', name)
    return name.isalpha()

def cdata(s):
    if s is not None and isinstance(s,str):
        if isinstance(s, str):
            s = remove_control_characters(s)
            return '<![CDATA[' + s + ']]>'
        else:
            return s
    else:
        return s


DOCTOR_TECHNICAL_TITLE_ID_MAPPING = {}
def load_doctor_technical_title(db):
    global DOCTOR_TECHNICAL_TITLE_ID_MAPPING
    sql = """
        SELECT
            di.value id,
            di.name
        FROM
            hrsc_data.dict_item di
        WHERE
            di.code = "d_expert_title"
    """
    rows = db.get_rows(sql)
    for row in rows:
        DOCTOR_TECHNICAL_TITLE_ID_MAPPING[int(row['id'])] = row['name']

def get_technical_title(title_id):
    return DOCTOR_TECHNICAL_TITLE_ID_MAPPING.get(title_id, '未知')


def send_email(email, title, content, interval=600, last_email_time=0):
    email_time = time.time()
    if email_time - last_email_time > interval:
        email.send(title, content)
        return email_time
    return last_email_time

def build_dict_field(doc, dict_field, dict_info):
    """
    构建字典字段名称属性.
    参数:
    doc->需要处理的文档.
    dict_field->值字段和名称字段的关系.
    dict_info->字典信息表(Data.get_dict_info获取).
    """
    for field,name_field in dict_field.items():
        if dict_info.get(field):
            if isinstance(doc.get(field), (basestring, int)):
                if not doc.get(field):
                    continue
                if dict_info[field].get(str(doc[field])):
                    doc[name_field] = dict_info[field][str(doc[field])]
            elif isinstance(doc.get(field), (set, dict, list)):
                for value in doc[field]:
                    if not value:
                        continue
                    value = str(value)
                    name = dict_info[field].get(value)
                    if name:
                        doc.setdefault(name_field, set()).add(name)


#创建SQL的查询条件
def create_id_where_clause(value, field, **kwargs):
    """
    生成sql的where id过滤条件.
    参数:
    value:id值,单个id值或多个id列表(集合,元组).
    field:where筛选条件的字段.
    wrap:id值的首尾封装,默认无,一般字符串id需加单引号.
    首尾相同则直接传该字符串即可,否则首尾用逗号分隔,回避逗号封装.
    operator:逻辑操作符(and或or)
    返回值:对应的sql.
    """
    where_clause = ''
    if value:
        wrap = "'"
        if 'wrap' in kwargs:
            wrap = kwargs['wrap']
        value = string_wraper(value, wrap)
        value_str = value
        if (isinstance(value, (list, tuple, set))
            and isinstance(field, basestring)):
            value_str = ','.join(value)
        operator = 'AND'
        if 'operator' in kwargs:
            operator = kwargs['operator']
        clause_format = ' %s %s IN (%s) '
        if isinstance(field, basestring):
            where_clause = clause_format % (operator, field, value_str)
        else:
            clause_list = []
            for sql_field,id_field in field.items():
                value_id = value.get(id_field)
                if value_id:
                    value_str = ','.join(string_wraper(value_id,wrap))
                    clause = clause_format % (operator, sql_field, value_str)
                    clause_list.append(clause)
            where_clause = ''.join(clause_list)
    return where_clause



def field_copy(src, dst, fields=None):
    if not fields:
        fields = src.keys()
    for field in fields:
        dst[field] = src[field]
    return dst

def string_wraper(elements, wrap="'"):
    if isinstance(elements, (list, set, tuple)):
        return ['%s%s%s' % (wrap, e, wrap) for e in elements]
    elif isinstance(elements, str):
        return '%s%s%s' % (wrap, elements, wrap)
    return elements

# 返回最近天数的日期, 负数表示过去多少天，正数表示将来多少天
def recently_date(days):
    return str(datetime.date.today() + datetime.timedelta(days=days))

#获取最近N秒时刻的日期,时间字符串
def recently_time(seconds, fmt='%Y-%m-%d %H:%M:%S'):
    timestamp = int(time.time()) - seconds
    return time.strftime(fmt, time.localtime(timestamp))

HOSPITAL_LEVEL_MAPPING = {
        13 : u'一级甲等',
        12 : u'一级乙等',
        11 : u'一级丙等',
        10 : u'一级医院',
        23 : u'二级甲等',
        22 : u'二级乙等',
        21 : u'二级丙等',
        20 : u'二级医院',
        34 : u'三级特等',
        33 : u'三级甲等',
        32 : u'三级乙等',
        31 : u'三级丙等',
        30 : u'三级医院',
        2 : u'对外专科',
        3 : u'对外综合',
        1 : u'其他',
        }
def get_hospital_level(level):
    return HOSPITAL_LEVEL_MAPPING.get(level, '')

class HTMLParser(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self, reset=True):
        result = ' '.join(self.fed)
        if reset:
            self.fed = []
        return result
