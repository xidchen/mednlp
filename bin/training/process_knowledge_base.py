# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/1/22 11:04
# @Auther:caoxg@guahao.com
# @File:process_knowledge_base.py


import json
import codecs
import xlrd
import random
import global_conf
from optparse import OptionParser
import sys
import re

medical_count_file = global_conf.train_data_path + 'medical_record_count_new.txt'


def add_br(content):
    """
    :param content: 需要处理的内容
    :return:若其中出现\n直接替换成<br/>
    """
    if not content:
        return content
    if re.search('<br/>', content):
        content = content.strip().split('\n')
        content = "".join(content)
        return content
    content = content.strip().split('\n')
    content = "<br/>".join(content)
    return content


def save_json(result, file):
    """
    :param result: 需要的保存的dict对象
    :return: 无返回
    """
    with codecs.open(file, 'w', encoding='utf-8') as f:
        # json.dump(result, f)
        ner_result_dict = json.dumps(result, ensure_ascii=False, indent=1)
        f.write(ner_result_dict)


def load_data(file):
    """
    :return: 返回dict对象
    """
    f = codecs.open(file, 'r', encoding='utf-8')
    data = json.load(f)
    return data


def get_diagnosis_biasis(file):
    """
    :return: 返回疾病和诊断依据的关系以dict返回
    """
    # file = "/home/caoxg/work/mednlp/data/dict/check_20190225.xlsx"
    f = xlrd.open_workbook(file)
    sheet1 = f.sheet_by_index(0)
    nrows = sheet1.nrows
    result = {}
    for i in range(1, nrows):
        disease_name = sheet1.cell_value(i, 0)
        value = sheet1.cell_value(i, 1)
        value = add_br(value)
        if disease_name not in result:
            result[disease_name] = value
    return result


def get_data(file):
    """
    :return: 返回包含鉴别诊断和诊断依据的所有数据已dict存储
    """
    diagnosis_basis = get_diagnosis_biasis(file)
    disease_id = get_disease_id()
    # file = "/home/caoxg/work/mednlp/data/dict/check_20190225.xlsx"
    f = xlrd.open_workbook(file)
    sheet1 = f.sheet_by_index(1)
    nrows = sheet1.nrows
    result = {'disease': []}
    for i in range(1, nrows):
        disease_result = {'disease_name': '', 'differential_diagnosis': [], 'diagnosis_basis': '', 'disease_id': ''}
        disease_name = sheet1.cell_value(i, 0).strip()
        key = sheet1.cell_value(i, 1).strip()
        try:
            value = sheet1.cell_value(i, 2)
        except Exception:
            value = ''
        value = add_br(value)
        temp_result = {}
        if result.get('disease') and disease_name == result.get('disease')[-1].get('disease_name'):
            temp_result['disease_name'] = key
            temp_result['differential_content'] = value
            result.get('disease')[-1].get('differential_diagnosis').append(temp_result)
        else:
            disease_result['disease_name'] = disease_name
            disease_result['diagnosis_basis'] = diagnosis_basis.get(disease_name)
            disease_result['disease_id'] = disease_id.get(disease_name)
            temp_result['disease_name'] = key
            temp_result['differential_content'] = value
            disease_result.get('differential_diagnosis').append(temp_result)
            result['disease'].append(disease_result)

    return result


def get_disease_id():
    """
    :return: 返回疾病和疾病id之间的关系，以dict返回
    """
    file = '/home/caoxg/work/mednlp/data/dict/mmseg/disease.dic'
    f = codecs.open(file, 'r', encoding='utf-8')
    customer_file = '/home/caoxg/work/mednlp/data/dict/mmseg/disease_custom.dic'
    customer_f = codecs.open(customer_file, 'r', encoding='utf-8')
    disease_id = {}
    for line in f:
        lines = line.strip().split('\t')
        if len(lines) == 2:
            if str(lines[0]).strip() in disease_id:
                print(line)
                continue
            disease_id[str(lines[0]).strip()] = lines[1]
    for line in customer_f:
        lines = line.strip().split('\t')
        if len(lines) == 2:
            if str(lines[0]).strip() in disease_id:
                print(line)
                continue
            disease_id[str(lines[0]).strip()] = lines[1]
    return disease_id


def transform_count(count):
    """
    :param count: 病例数目
    :return:对病例数目进行数据处理，加上病例标签若大于10000显示1万+
    """
    label = ''
    if isinstance(count, int):
        count = count
    elif isinstance(count, str):
        try:
            count = int(count)
        except Exception:
            count = (random.randint(-2000, 2000) + 10000)
    else:
        count = random.randint(-2000, 2000) + 10000
    if count >= 10000:
        count = count
    else:
        count = random.randint(-2000, 2000) + 10000
    if count >= 10000:
        label = str(count // 10000) + '万+'
    else:
        label = str(count)
    if label:
        return count, label


def load_database_data(file):
    """
    :return: 返回dict对象
    """
    f = codecs.open(file, 'r', encoding='utf-8')
    data = json.load(f)
    return data


def get_diagnosis(database, disease_name):
    """
    :param file: 保存疾病和鉴别诊断和诊断依据的文件
    :param disease_name:疾病名
    :return:根据疾病名拿到鉴别诊断和诊断依据
    """
    data = database.get('disease')
    if not data:
        return
    for line in data:
        if line.get('disease_name') == disease_name:
            differential_diagnosis = line.get('differential_diagnosis')
            diagnosis_basis = line.get('diagnosis_basis')
            return differential_diagnosis, diagnosis_basis


def get_medical_record_count(input_file):
    """
    :param input_file: 疾病和相似病例数对应表
    :return: 结果为dict格式其中key为疾病 value 为相似病例数及相似病例数描述
    """
    f = codecs.open(input_file, 'r', encoding='utf-8')
    medical_count = {}
    for line in f:
        lines = line.strip().split('\t')
        if len(lines) == 2:
            number = lines[1]
            disease_name = lines[0]
            if not disease_name:
                # print(line)
                continue
            count, label = transform_count(number)
            medical_count[disease_name] = (count, label)
        # else:
        #     print(line)
    return medical_count


def get_result_json(file, input_file):
    """
    :param file: 保存疾病和鉴别诊断和诊断依据的文件
    :param input_file: 疾病和相似病例数对应表
    :return: 返回包含疾病、疾病id、相似病例数、相似病例数描述、鉴别诊断和诊断依据这些字段的数据
    """
    result = {'disease': []}
    print('get_disease_id start')
    disease_id = get_disease_id()
    print('get_disease_id end')
    print('get_medical_record_count start')
    medical_count = get_medical_record_count(input_file)
    print('get_medical_record_count end')
    database = get_data(file)
    for disease_name in disease_id:
            disease_result = {}
            if medical_count.get(disease_name):
                count, label = medical_count.get(disease_name)
                disease_result['disease_name'] = disease_name
                disease_result['medical_record_count'] = count
                disease_result['medical_record_count_desc'] = label
                disease_result['disease_id'] = disease_id.get(disease_name)
            else:
                # count, label = medical_count.get(disease_name)
                disease_result['disease_name'] = disease_name
                count, label = transform_count('')
                disease_result['medical_record_count'] = count
                disease_result['medical_record_count_desc'] = label
                disease_result['disease_id'] = disease_id.get(disease_name)
            if get_diagnosis(database, disease_name):
                differential_diagnosis, diagnosis_basis = get_diagnosis(database, disease_name)
                if differential_diagnosis and diagnosis_basis:
                    disease_result['differential_diagnosis'] = differential_diagnosis
                    disease_result['diagnosis_basis'] = diagnosis_basis
                elif diagnosis_basis:
                    disease_result['diagnosis_basis'] = diagnosis_basis
                elif differential_diagnosis:
                    disease_result['differential_diagnosis'] = differential_diagnosis
            result['disease'].append(disease_result)
    return result


if __name__ == '__main__':
    command = '\npython %s [-p port -t type -l level]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-i', '--input', dest='input_file', help='检查检验输入数据 ')
    parser.add_option('-o', '--output', dest='output_file', help='疾病知识库输出数据')
    (options, args) = parser.parse_args()
    input_file = "/home/chaipf/work/mednlp/data/dict/check_20190528.xlsx"
    output_file = '/home/chaipf/work/mednlp/data/dict/medical_record_count_20190409.b.json'
    if options.input_file:
        input_file = options.input_file
        print('input_file', input_file)
    if options.output_file:
        output_file = options.output_file
    print('get_result_json_start')
    result = get_result_json(file=input_file, input_file=medical_count_file)
    print('get_result_json_end')
    save_json(result, file=output_file)
