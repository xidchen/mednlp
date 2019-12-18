#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_test.py -- the test of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2019-11-22 星期三.
"""

import sys
import os
import global_conf
from ailib.client.ai_service_client import AIServiceClient
import pandas as pd
import codecs

test30_path = '/ssddata/testdata/mednlp/dept_classify'
test28_path = '/data/testdata/mednlp/dept_classify'
cfg_path = global_conf.cfg_path
# search = AIServiceClient(cfg_path=cfg_path, service='AIService', port=6446)
base_path = os.path.dirname(__file__)
test_path = os.path.join(base_path, 'accuracy_result.csv')
accuracy_path = os.path.join(base_path, '../data/dict/evaluate_accuracy.txt')


class Test(object):
    def __init__(self, port=3000, level=1, test_file=''):
        self.search = AIServiceClient(cfg_path=cfg_path, service='AIService', port=port)
        self.level = level
        self.querys = []
        self.test_file = test_file
        self.dept_names = []
        self.second_dept_names = []
        self.ages = []
        self.sexs = []
        self.pred_dept_names = []
        self.accuracy = {'confidence': [], 'all_count': [], 'pred_count': [], 'un_pred_count': [], 'converage': [],
                         'top1_accuracy': [], 'top2_accuracy': []}
        self.get_data()

    def get_data(self):
        test_input = open(self.test_file, 'r')
        querys = []
        dept_names = []
        second_dept_names = []
        ages = []
        sexs = []
        for line in test_input:
            line = list(line.strip().split('\t'))
            query = line[0]
            dept_name = line[1]
            second_dept_name = line[2]
            age = str(int(line[3]) * 365)
            sex = line[4]
            querys.append(query)
            dept_names.append(dept_name)
            second_dept_names.append(second_dept_name)
            ages.append(age)
            sexs.append(sex)
        self.querys = querys
        self.dept_names = dept_names
        self.second_dept_names = second_dept_names
        self.ages = ages
        self.sexs = sexs

    def get_pred_dept_name(self, type=1):
        pred_dept_names = []
        contents = self.querys
        for i, content in enumerate(contents):
            if i % 10 == 0:
                print('the {}th has started'.format(i))
            if type == 4:
                t = self.search.query({'q': content, 'dept_set': 3},
                                      service='dept_classify')
                print(type)
            elif type == 2:
                t = self.search.query({'q': content, 'mode': 2, 'level': self.level}, service='dept_classify')
            else:
                t = self.search.query({'q': content, 'level': self.level},
                                      service='dept_classify')
            if 'data' in t and t.get('data')[0].get('dept_name') != 'unknow':
                data = t.get('data')
                pred_dept_name = []
                pre_score = []
                for line in data:
                    pred_dept_name.append(line.get('dept_name'))
                    pre_score.append(line.get('score'))
                pred_dept_names.append([pred_dept_name, pre_score])
            else:
                pred_dept_names.append([['unknow'], [0]])
        self.pred_dept_names = pred_dept_names

    def get_pred_sex_dept_name(self, type=1):
        pred_dept_names = []
        contents = self.querys
        sexs = self.sexs
        for content, sex in zip(contents, sexs):
            if type == 2:
                t = self.search.query({'q': content, 'sex': sex, 'mode': 2},
                                      service='dept_classify')
            else:
                t = self.search.query({'q': content, 'sex': sex}, service='dept_classify')
            if 'data' in t and t.get('data')[0].get('dept_name') != 'unknow':
                data = t.get('data')
                pred_dept_name = []
                pre_score = []
                for line in data:
                    pred_dept_name.append(line.get('dept_name'))
                    pre_score.append(line.get('score'))
                pred_dept_names.append([pred_dept_name, pre_score])
            else:
                pred_dept_names.append([['unknow'], [0]])
        self.pred_dept_names = pred_dept_names

    def get_accuracy_dict(self):
        test_data = codecs.open(test_path, 'r', encoding='utf-8')
        accuracy_data = codecs.open(accuracy_path, 'w', encoding='utf-8')
        count = 0
        for line in test_data:
            if count > 0 and count <= 50:
                line = line.strip().split(',')
                score = int(float(line[0]) * 100 + 0.1)
                accuracy = line[-1]
                line = str(score) + '\t' + accuracy + '\n'
                accuracy_data.write(line)
            count = count + 1
        line = str(100) + '\t' + '99.00%' + '\n'
        accuracy_data.write(line)
        test_data.close()
        accuracy_data.close()

    def get_pred_sex_age_dept_name(self, type=1):
        pred_dept_names = []
        contents = self.querys
        sexs = self.sexs
        ages = self.ages
        for i, (content, sex, age) in enumerate(zip(contents, sexs, ages)):
            if i % 10 == 0:
                print('the {}th has started'.format(i))
            if type == 4:
                t = self.search.query({'q': content, 'sex': sex, 'age': age, 'dept_set': 3},
                                      service='dept_classify')
            elif type == 2:
                t = self.search.query({'q': content, 'sex': sex, 'age': age,
                                       'mode': 2}, service='dept_classify')
            else:
                t = self.search.query({'q': content, 'sex': sex, 'age': age}
                                      , service='dept_classify')
            if 'data' in t and t.get('data')[0].get('dept_name') != 'unknow':
                data = t.get('data')
                pre_dept_name = data[0].get('dept_name')
                pre_score = data[0].get('score')
                pred_dept_names.append([pre_dept_name, pre_score])
            else:
                pred_dept_names.append(['unknow', 0])
        self.pred_dept_names = pred_dept_names

    def compute_accuracy(self):
        # numbers = np.arange(0, 1, 0.02)
        # confidences = [round(number, 2) for number in numbers]
        confidences = [float(i) / 10 for i in range(0, 10)]
        for confidence in confidences:
            self.compute_confidence_accuracy(confidence)

    def compute_confidence_accuracy(self, confidence=0):
        all_count = len(self.dept_names)
        pred_count = 0
        top1_count = 0
        top2_count = 0
        for pred_dept_name, dept_name, second_dept_name in zip(self.pred_dept_names, self.dept_names,
                                                               self.second_dept_names):
            if 'unknow' not in pred_dept_name[0] and pred_dept_name[1] >= confidence:
                pred_count = pred_count + 1
                if dept_name in pred_dept_name[0]:
                    top1_count = top1_count + 1
                    top2_count = top2_count + 1
                else:
                    if second_dept_name in pred_dept_name[0]:
                        top2_count = top2_count + 1
        un_pred_count = all_count - pred_count
        if pred_count > 0:
            self.accuracy['confidence'].append(confidence)
            self.accuracy['all_count'].append(all_count)
            self.accuracy['pred_count'].append(pred_count)
            self.accuracy['un_pred_count'].append(un_pred_count)
            self.accuracy['converage'].append(str(round(float(pred_count) / all_count * 100, 2)) + '%')
            self.accuracy['top1_accuracy'].append(str(round(float(top1_count) / pred_count * 100, 2)) + '%')
            self.accuracy['top2_accuracy'].append(str(round(float(top2_count) / pred_count * 100, 2)) + '%')
        else:
            self.accuracy['confidence'].append(confidence)
            self.accuracy['all_count'].append(all_count)
            self.accuracy['pred_count'].append(pred_count)
            self.accuracy['un_pred_count'].append(un_pred_count)
            self.accuracy['converage'].append(str(round(float(pred_count) / all_count * 100, 2)) + '%')
            self.accuracy['top1_accuracy'].append(str(0) + '%')
            self.accuracy['top2_accuracy'].append(str(0) + '%')

    def save_csv(self, path='result_test.csv'):
        result = pd.DataFrame(self.accuracy)
        result.to_csv(path, index=False, columns=['confidence', 'all_count', 'pred_count', 'un_pred_count', 'converage',
                                                  'top1_accuracy', 'top2_accuracy'])


if __name__ == '__main__':
    command = '\npython %s [-p port -t type -l level]' % sys.argv[0]
    from optparse import OptionParser

    parser = OptionParser(usage=command)
    parser.add_option('-p', '--port', dest='port', help='the port of service')
    parser.add_option('-t', '--type', dest='type', help='测试函数的类型，1 咨询模式  2  病例模式')
    parser.add_option('-l', '--level', dest='level', help='测试科室分诊的level参数')
    parser.add_option('--source_test', dest='source_test', help='测试数据的源头 1，咨询模式测试数据 2 病例模式测试数据 '
                                                                '3、医生可分数据测试数据 默认为1')
    parser.add_option('--source_type', dest='source_type', help='测试数据来源于那个服务器 1，28 2 30 默认为1')

    (options, args) = parser.parse_args()
    port = 10801
    type = 1
    level = 1
    source_test = 1
    source_type = 2
    if options.port:
        port = options.port
        port = int(port)
    if options.type:
        type = options.type
        type = int(type)

    if options.level:
        level = options.level
        level = int(level)
    if options.source_test:
        source_test = options.source_test
        source_test = int(source_test)
    if options.source_type:
        source_type = options.source_type
        source_type = int(source_type)

    if source_type == 2:
        test_base_path = test30_path
    else:
        test_base_path = test28_path

    record_test_file = os.path.join(test_base_path, 'medical_record_dept_test.txt')
    consult_test_file = os.path.join(test_base_path, 'dept_classify_test_20180705_label_union.txt')
    doctor_split_file = os.path.join(test_base_path, 'dept_classify_doctor_split_20181206.txt')
    if source_test == 1:
        test_file = consult_test_file
    elif source_test == 2:
        test_file = record_test_file
    elif source_test == 3:
        test_file = doctor_split_file
    else:
        test_file = consult_test_file
    test = Test(port=port, level=level, test_file=test_file)
    # test.get_accuracy_dict()
    # test.get_pred_dept_name(type=type)
    # test.compute_accuracy()
    # test.get_pred_sex_dept_name(type=1)
    # test.compute_accuracy()
    test.get_pred_sex_age_dept_name(type=1)
    test.compute_accuracy()
    test.save_csv('accuracy_result2.csv')
