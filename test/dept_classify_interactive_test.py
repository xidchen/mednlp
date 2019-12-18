#!/usr/bin/python
# -*- coding:utf8 -*-
import sys
import os
import global_conf
from ailib.client.ai_service_client import AIServiceClient
import pandas as pd
import codecs

base_path = os.path.abspath(os.path.dirname(__file__))
# test_file = os.path.join(base_path, 'consult_test_20180110_new.txt')
# test_file = os.path.join(base_path, 'medical_record_dept_test.txt')
test_file = os.path.join('/ssddata/testdata/mednlp/dept_classify', 'dept_classify_test_20180705_label_union.txt')
cfg_path = global_conf.cfg_path
search = AIServiceClient(cfg_path=cfg_path, service='AIService', port=3000)
base_path = os.path.dirname(__file__)
test_path = os.path.join(base_path, 'interactive_accuracy_result.csv')


class Test(object):
    def __init__(self):
        self.querys = []
        self.dept_names = []
        self.second_dept_names = []
        self.ages = []
        self.sexs = []
        self.pred_dept_names = []
        self.accuracy = {'confidence': [], 'all_count': [], 'pred_count': [], 'un_pred_count': [], 'converage': [],
                         'top1_accuracy': [], 'top2_accuracy': []}
        self.get_data()

    def set_test_file(self, file=test_file):
        return file

    def get_test_file(self):
        return self.set_test_file()

    def get_data(self):
        test_input = open(self.get_test_file(), 'r')
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
            age = str(int(line[3])*365)
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
        for content in contents:
            if type == 2:
                t = search.query({'q': content, 'mode': 2}, service='dept_classify_interactive')
            else:
                t = search.query({'q': content}, service='dept_classify_interactive')
            if 'data' in t and t.get('data').get('depts')[0].get('dept_name') != 'unknow':
                data = t.get('data')
                pre_dept_name = data.get('depts')[0].get('dept_name')
                pre_score = data.get('depts')[0].get('score')
                pred_dept_names.append([pre_dept_name, pre_score])
            else:
                pred_dept_names.append(['unknow', 0])
        self.pred_dept_names = pred_dept_names

    def get_accuracy_dict(self):
        test_data = codecs.open(test_path, 'r', encoding='utf-8')
        count = 0
        for line in test_data:
            if count > 0 and count <= 50:
                line = line.strip().split(',')
                score = int(float(line[0]) * 100 + 0.1)
                accuracy = line[-1]
                line = str(score) + '\t' + accuracy + '\n'
            count = count + 1
        line = str(100) + '\t' + '99.00%' + '\n'
        test_data.close()

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

            if pred_dept_name[0] != 'unknow' and pred_dept_name[1] >= confidence:
                pred_count = pred_count+1
                if pred_dept_name[0] == dept_name:
                    top1_count = top1_count + 1
                    top2_count = top2_count + 1
                else:
                    if pred_dept_name[0] == second_dept_name:
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
        result.to_csv(path, index=False, columns=['confidence', 'all_count', 'pred_count', 'un_pred_count','converage',
                                                  'top1_accuracy', 'top2_accuracy'])


if __name__ == '__main__':
    test = Test()
    # test.get_accuracy_dict()
    test.get_pred_dept_name(type=1)
    test.compute_accuracy()
    # test.get_pred_sex_dept_name(type=1)
    # test.compute_accuracy()
    # test.get_pred_sex_age_dept_name(type=1)
    # test.compute_accuracy()
    test.save_csv(test_path)
    # test.get_accuracy_dict()
