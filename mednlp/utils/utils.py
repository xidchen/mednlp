#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
utils.py
"""

import re
import json
import time
import codecs
import sys   # todo
from mednlp.text.mmseg import MMSeg
import copy
import global_conf
import jieba
import xlrd
import configparser


id_dept = {'生殖与遗传': ['男科', '妇科'], '手外科': ['骨科'], '口腔颌面外科': ['口腔科'], '肿瘤外科': ['肿瘤科'],
                         '关节外科': ['骨科']}
insert_dict = {
    '身体部位左侧': '$LBP$',
    '身体部位右侧': '$RBP$'
}


def unicode2str(data, encode="UTF-8"):
    # list,set 格式
    if isinstance(data, list):
        for index, temp in enumerate(data):
            if isinstance(temp, str):
                data[index] = temp

    else:
        if isinstance(data, str):
            return data
    return data


def byte2str(str_temp, encode='utf-8'):
    result = str_temp
    if isinstance(str_temp, bytes):
        result = str(str_temp, encoding=encode)
    return result


def row_byte2str(row, fields, encode='utf-8'):
    if not fields:
        return row
    for field in fields:
        if row.get(field) or isinstance(row.get(field), bytes):
            row[field] = str(row[field], encoding=encode)
    return row


def transform_dict_data(result, origin, field_mappings):
    """
    把origin里的 key=location_temp的值放入result['location'],
    get_dict_data(origin, result, {'location_temp': 'location'}):
    :param origin: 原数据字典
    :param result: 目的数据字典
    :param field_mappings: 原数据字典 到目的数据字典的映射
    :return:
    """
    if not field_mappings:
        return result
    for destination, source in field_mappings.items():
        if source in origin:
            result[destination] = origin[source]
    return result


def read_config_info(sections=None):
    """
    读取配置文件global_conf.cfg_path
    :param sections: list, 若指定sections,按指定的读取,否则读取全部
    """
    config_dict = {}
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(global_conf.cfg_path)
    if not sections:
        sections =config.sections()
    for section_temp in sections:
        items = config.items(section_temp)
        section_obj = config_dict.setdefault(section_temp, {})
        for item_temp in items:
            section_obj[item_temp[0]] = item_temp[1]
    return config_dict


def print_logger(message, logger=None, debug=0):
    # 打印日志
    if not logger or not message:
        return
    if debug:
        logger.info(message)


def pretty_print(data):
    """
    按好看的格式打印python数据对象
    对象中的中文以中文形式打印出来，而非编码。
    :param data: list,dict,set
    """
    print(json.dumps(
        data, ensure_ascii=False, separators=(',', ':')))


def load_json(path):
    """
    加载json文件
    :param path:文件路径
    :return: 数据
    """
    with codecs.open(path, 'r') as f:
        data = json.load(f)
    print("【load json data】\n{}".format(path))
    return data


def match_patterns(s, patterns):
    """
    判断string是否能匹配模式集中的至少一条
    :param string: 需要寻找模式的string
    :param patterns: 模式集合,set or list.
    :return: True or False
    """
    for pattern in patterns:
        mat_obj = re.search(pattern, s)
        if mat_obj:
            return True
    return False

def get_search_plat_keys(section_key):
    result = {}
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(global_conf.cfg_path)
    options = config.items(section=section_key)
    for (key, value) in options:
        result[key] = value
    return result

def dept_classify_normal(data):
    """
    科室分诊模型预测结果进行标准化，主要是对于预科科室概率进行标准化
    :param data: 科室分诊模型返回数据集，数据格式如下[[预测科室名，预测科室概率，科室id]]
    :return: 对预测结果的概率进行标准化
    """
    sum = 0
    for line in data:
        sum = sum + line[1]
    normal_result = [[line[0], line[1] / sum, line[2]] for line in data]
    return normal_result


def dept_classify_max_prop(result):
    """
    :param result: 科室分诊模型返回数据集，数据格式如下[[预测科室名，预测科室概率，科室id]]
    :return: 返回预测结果的最大概率
    """
    max_prop = 0
    for line in result:
        if line[1] >= max_prop:
            max_prop = line[1]
    return max_prop


def strip_all_punctuations(s):
    if not s:
        return ''
    s = s.strip()
    begin_index = 0
    end_index = -1
    get_begin_pos = False

    for i, c in enumerate(s):
        if re.match(u'[a-zA-Z0-9\u4e00-\u9fa5]', c):
            begin_index = i
            get_begin_pos = True
            break

    if not get_begin_pos:
        return ''

    ls_revert = list(s)
    ls_revert.reverse()

    for i, c in enumerate(ls_revert):
        if re.match(u'[a-zA-Z0-9\u4e00-\u9fa5]', c):
            end_index = len(s) - i
            break

    return s[begin_index:end_index]


def Encode(data):
    data = json.dumps(data, ensure_ascii=False)
    return data


# 装饰器查看 模型运行时间
def print_time(func):
    def warp(*args, **kwargs):
        time_start = time.time()
        fun_result = func(*args, **kwargs)
        time_end = time.time()
        print('The model costs time is %.2f s' % (time_end - time_start))
        return fun_result
    return warp


# 以某种特殊字符切割句子
@print_time
def split_sen_add_char(sen, split_char):
    split_char_now = "(" + split_char + ")"
    sp_char = re.split(split_char_now, sen)
    for word in sp_char:
        split_char = split_char.replace('\\', '')
        if word not in split_char:
            sw = [w for w in word]
            for si in sw:
                yield si
        else:
            yield word


def precoess_line(content, key_words=u'生活', insert_left=insert_dict[u'身体部位左侧'],
                  insert_right=insert_dict[u'身体部位右侧']):
    """
    :param content: 原来的内容
    :param key_words: 需要插入的关键字
    :param insert_left: 插入关键字左边的字符
    :param insert_right: 插入关键字右边的字符
    :return: 返回添加左右分隔字的整个字符
    """
    left = insert_left
    right = insert_right
    split_word = '(' + key_words + ')'
    result = re.split(re.compile(split_word), content)
    line = ''
    # result = list(content.split(key_words))
    for index, word in enumerate(result):
        if index % 2:
            line = line + left + word + right
        else:
            line = line + word
    return line


def get_split_result(lines):
    """
    :param lines: 已经添加左右分隔符的句子
    :return: 整个句子按照单词拆开，其中左右分隔符各是一个字符
    """
    result = []
    results = re.split(r'(\$LBP\$|\$RBP\$)', lines)
    for words in results:
        # if '$' not in words:
        if words not in ['$LBP$', '$RBP$']:
            words = [word for word in words]
            result.extend(words)
        else:
            result.append(words)
    return result


def get_char_body_part(mmseg, content, dict_type=['body_part']):
    """
    :param mmseg: 分隔器 mmseg
    :param content: 原理的内容
    :param dict_type: 需要按照某种实体进行分隔
    :return: 返回根据实体添加左右分隔符，所有单词构成的一个列表
    """
    entities = mmseg.cut(content, maximum=500)
    dict_result = []
    for k, v in entities.items():
        dict_result.append(k)
    for key in dict_result:
        content = precoess_line(content, key_words=key)
    result = get_split_result(content)
    return result


def distinct_list_dict(dialogs, **kwargs):
    """
    列表字典去重,且列表有先后顺序。因为dialogs里有重复的,应该选择最新的数据
    :param dialogs: [{}, {}, {}]
    :param kwargs:
    key; key会重复
    order_key:指定排序的索引名
    :return:
    """
    key = kwargs.get('key', 'key')
    order_key = kwargs.get('order_key', 'distinct_order')
    result_dict = {}
    for index, dialog_temp in enumerate(dialogs):
        dialog_key = dialog_temp[key]
        dialog_temp[order_key] = index
        result_dict[dialog_key] = dialog_temp
    result = list(result_dict.values())
    result.sort(key=lambda d: d.get(order_key))
    return result

def pasttime_by_seconds(seconds=0, fmt='%Y-%m-%d %H:%M:%S'):
    timestamp = int(time.time())
    if seconds != 0:
        timestamp -= seconds
        return time.strftime(fmt, time.localtime(timestamp))


def string_wraper(elements, wrap="'"):
    if isinstance(elements, (list, set, tuple)):
        return ['%s%s%s' % (wrap, e, wrap) for e in elements]
    elif isinstance(elements, str):
        return '%s%s%s' % (wrap, elements, wrap)
    return elements


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
        if isinstance(value, (list, tuple, set)) and isinstance(field, str):
            value_str = ','.join(value)
        operator = 'AND'
        if 'operator' in kwargs:
            operator = kwargs['operator']
        clause_format = ' %s %s IN (%s) '
        if isinstance(field, str):
            where_clause = clause_format % (operator, field, value_str)
        else:
            clause_list = []
            for sql_field, id_field in field.items():
                value_id = value.get(id_field)
                if value_id:
                    value_str = ','.join(string_wraper(value_id, wrap))
                    clause = clause_format % (operator, sql_field, value_str)
                    clause_list.append(clause)
            where_clause = ''.join(clause_list)
    return where_clause

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
        if isinstance(mysql_time, str):
            return time.strftime(solr_format, time.strptime(mysql_time, mysql_format))
        else:
            return mysql_time.strftime(solr_format)
    else:
        return None

def load_xlsx_data(r_path, sheet_index=0, **kwargs):
    # 读取xlsx数据
    data = xlrd.open_workbook(r_path)
    table = data.sheets()[sheet_index]
    rows = table.nrows
    cols = table.ncols
    result = []
    for row_num in range(kwargs.get('start', 0), rows):
        row_data = table.row_values(row_num)
        result.append(row_data)
    return result

def _trans(s):
    digit = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    num = 0
    if s:
        idx_q, idx_b, idx_s = s.find('千'), s.find('百'), s.find('十')
        if idx_q != -1:
            num += digit[s[idx_q - 1:idx_q]] * 1000
        if idx_b != -1:
            num += digit[s[idx_b - 1:idx_b]] * 100
        if idx_s != -1:
            # 十前忽略一的处理
            num += digit.get(s[idx_s - 1:idx_s], 1) * 10
        if s[-1] in digit:
            num += digit[s[-1]]
    return num


if __name__ == '__main__':
    a = u'我爱$brp$中国$end$，我在$brp$杭州$end$'
    split_char = '\$brp\$|\$end\$'
    sen_split = split_sen_add_char(a, split_char)
    for s in sen_split:
        print(s)
    dict_type = ['body_part']
    mmseg = MMSeg(dict_type, uuid_all=False, is_uuid=True, update_dict=False, is_all_word=False)
    content1 = '我脑袋有问题,我屁股有点疼'
    content2 = '我喜欢中国，我喜欢杭州'
    content3 = '3月22日进行手术切除，肝右叶原发性细胞癌，肉瘤样型，部分区伴胆管上皮分化，慢性乙肝，癌胚细胞均正常，目前未发现转移' \
               '，东方肝胆建议术后一个月进行预防介入。目前术后腹胀，一天比一天腹胀减少，人乏力，胃口还行，请问何时可以中药治疗'
    result1 = get_char_body_part(mmseg, content1, dict_type=dict_type)
    print(content1)
    for word in result1:
        print(word)
    result2 = get_char_body_part(mmseg, content2, dict_type=dict_type)
    print(content2)
    for word in result2:
        print(word)
    print(content3)
    result3 = get_char_body_part(mmseg, content3, dict_type=dict_type)
    for word in result3:
        print(word)
