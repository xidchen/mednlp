# ！/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dept_classify_merge_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-03-08 星期四.
"""

from mednlp.utils.utils import dept_classify_max_prop
from mednlp.text.vector import Dept2Vector
import global_conf
import codecs
from ailib.client.ai_service_client import AIServiceClient
import os


def dept_classify_filter_sex(data, sex=-1):
    """
    对预测结果进行性别方面的过滤，比方说如果就诊人是男性，不能出现妇科疾病，如果就诊人是女性，也不能出现男科
    :param data:科室分诊模型预测结果，结果如下[[预测科室姓名，预测科室概率，科室id]]
    :param sex: 患者性别  sex=2 男性，sex=1  女性
    :return: 返回过滤性别以后的结果
    """
    filter_sex_result = []
    if sex == 2:
        for line in data:
            if line[0] in ['妇科', '产科', '妇产科']:
                filter_sex_result.append([line[0], 0, line[2]])
            else:
                filter_sex_result.append(line)
    elif sex == 1:
        for line in data:
            if line[0] in ['男科']:
                filter_sex_result.append([line[0], 0, line[2]])
            else:
                filter_sex_result.append(line)

    else:
        filter_sex_result = data
    return filter_sex_result


def dept_classify_filter_age(data, age=-1):
    """
    对科室预测结果，进行年龄方面的预测，主要是儿科和新生儿科的处理
    :param data: 科室分诊模型预测结果，结果如下[[预测科室名，预测科室概率，科室id]]
    :param age: 患者年龄
    :return: 返回过滤年龄以后的结果
    """
    max_prop = dept_classify_max_prop(data)
    filter_age = []
    if age >= 0 and age < 14*365:
        for line in data:
            if line[0] == '儿科':
                # line[1] = max_prop * 1.2
                filter_age.append([line[0], max_prop*1.2, line[2]])
            else:
                filter_age.append(line)
        return filter_age
    elif age > 16*365:
        for line in data:
            if line[0] == '儿科':
                # line[1] = 0
                filter_age.append([line[0], 0, line[2]])
            else:
                filter_age.append(line)
        return filter_age
    else:
        return data


def get_origin_dept(depts, sex):
    """
    :param depts:  模型预测出科室
    :return: 40标准科室
    """
    dept_40 = {}
    dept_other_5 = {}
    for dept in depts:
        dept_name = dept[0]
        if dept_name in ('生殖与遗传', '手外科', '口腔颌面外科', '肿瘤外科', '关节外科'):
            dept_other_5[dept_name] = dept
        else:
            dept_40[dept_name] = dept

    if '骨科' in dept_40:
        dept_40['骨科'][1] += dept_other_5.get('手外科', [0, 0, 0])[1]
        dept_40['骨科'][1] += dept_other_5.get('关节外科', [0, 0, 0])[1]
    if '肿瘤科' in dept_40:
        dept_40['肿瘤科'][1] += dept_other_5.get('肿瘤外科', [0, 0, 0])[1]
    if sex == 1 and '妇科' in dept_40:
        dept_40['妇科'][1] += dept_other_5.get('生殖与遗传', [0, 0, 0])[1]
    if sex == 2 and '男科' in dept_40:
        dept_40['男科'][1] += dept_other_5.get('生殖与遗传', [0, 0, 0])[1]

    # 口腔颌面外科 对应
    _score = dept_40.get('口腔颌面外科', [0, 0, 0])[1]
    sub_score_1 = dept_40.get('骨科', [0, 0, 0])[1]
    sub_score_2 = dept_40.get('口腔科', [0, 0, 0])[1]
    sub_score_sum = sub_score_1 + sub_score_2
    if sub_score_sum > 0 and _score > 0:
        if '骨科' in dept_40:
            dept_40['骨科'][1] += (sub_score_1) * 1.0 / sub_score_sum * _score
        if '口腔科' in dept_40:
            dept_40['口腔科'][1] += (sub_score_2) * 1.0 / sub_score_sum * _score

    res = list(dept_40.values())
    score_sum = sum((dept[1] for dept in res))
    for dept in res:
        dept[1] = dept[1] / score_sum
    return res


def get_internet_dept(depts):
    """
    :param depts:实现标注科室和互联网医院科室的对应关系
    :return:返回对应以后的科室预测结果
    """
    stard2internet = {}
    internet2id = {}
    file = codecs.open(global_conf.standard_transform_internet_dept_path, 'r', encoding='utf-8')
    for line in file:
        lines = line.strip().split('=')
        if lines[0] not in stard2internet:
            stard2internet[lines[0]] = lines[1]
        if lines[1] not in internet2id:
            internet2id[lines[1]] = lines[2]
    result = [[stard2internet.get(dept[0]), dept[1], dept[2]] for dept in depts if dept[0] in stard2internet]
    depts_dict = {}
    for dept in result:
        if dept[0] not in depts_dict:
            depts_dict[dept[0]] = dept[1]
        else:
            depts_dict[dept[0]] += dept[1]
    depts_sort = [[key, value, internet2id.get(key)] for key, value in depts_dict.items()]
    sum = 0
    for line in depts_sort:
        sum = sum + line[1]
    for line in depts_sort:
        line[1] = float(line[1]) / sum
    return depts_sort


class TransInspection(object):

    def __init__(self):
        self.aisc = AIServiceClient(global_conf.cfg_path, 'AIService')

    def transform_inspection_data(self, content):
        """
        :param content: 要请求的内容
        :return:把检查检验的数值改为升高和降低
        """
        try:
            entity_result = self.aisc.query({'q': content, 'type': 'physical,examination', 'property': 'value'},
                                            'entity_extract')
        except:
            return content
        if not entity_result.get('data'):
            return content

        entities = {}
        for entity in entity_result.get('data'):
            if entity.get('type') in ('examination', 'physical') and entity.get('property'):
                if entity.get('property').get('value_status'):
                    entities[entity.get('entity_text')] = entity.get('entity_name') + entity.get('property').\
                        get('value_status')
        for org_text, rep_text in entities.items():
            content = content.replace(org_text, rep_text)
        return content


def dept_filter_error(value, default=1):
    """
    :param value: 传入值
    :param default:值不正确默认值
    :return:返回值
    """
    try:
        value = int(value)
    except:
        return default
    return value


class DiseaseDept(object):
    def __init__(self):
        self.load_dict()

    def load_dict(self):
        """
        加载疾病-科室、科室-科室id对应关系的文件
        :return: 无
        """
        f = codecs.open(global_conf.dept_disease_dept_id_path, 'r', encoding='utf-8')
        self.disease_dept = {}
        self.dept_id = {}
        for line in f:
            lines = line.strip().split('=')
            disease = lines[0]
            dept = lines[1]
            deptid = lines[2]
            if disease not in self.disease_dept:
                self.disease_dept[disease] = dept
            if dept not in self.dept_id:
                self.dept_id[dept] = deptid

    def predict(self, disease):
        """
        :param disease: 疾病
        :return: 返回疾病所对应的科室信息，具体形式如[科室，score，科室id]
        """
        result = []
        if not disease:
            return result
        dept = self.disease_dept.get(disease)
        if not dept:
            return result
        dept_id = self.dept_id.get(dept)
        if not dept_id:
            return disease
        result.append([dept, 0.7, dept_id])
        return result


def get_file_rows(input_train_file):
    """
    :param input_train_file: 输出训练数据
    :return: 返回训练数据的所有行数
    """
    if not input_train_file:
        return 0
    file_nrows = len([1 for line in codecs.open(input_train_file, 'r', encoding='utf-8')])
    return file_nrows


def check_train_path(input_file_path):
    """
    根据input_file_path按照在文件名后面加入train和test生成训练文件目录和测试文件目录
    :param input_file_path: 输入文件名
    :return: 返回原始文件目录，训练文件目录，测试文件目录
    """
    if os.path.split(input_file_path)[0]:
        file_path = input_file_path
    else:
        file_path = global_conf.train_data_path + input_file_path
    return file_path
