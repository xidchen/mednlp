#!/usr/bin/python
# encoding=utf-8
# -*- coding:utf8 -*-
import sys
import os
from optparse import OptionParser
import global_conf
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(os.path.join(os.path.dirname(__file__), '../../tmserver_common'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ailib'))
# reload(sys)
# sys.setdefaultencoding('utf8')
# import client.tmserver_client
# from client.agada_client import AgadaClient
from client.ai_service_client import AIServiceClient
# input_file = 'consult_test_20180110_new.txt'
input_file = '/home/caoxg/work/mednlp/data/traindata/traindata_dept_classify_false.txt'
# input_file = 'consult_test_new_ok_fix.txt'
max_number = sys.maxint
# host_port_a = 'localhost:7200'
# host_port_b = 'localhost:7206'
output1_file = 'result1.txt'
output2_file = 'result2.txt'
save_accuracy = 'save_accuracy.txt'
cfg_path = global_conf.cfg_path
tc_b = AIServiceClient(cfg_path=cfg_path, service='AIService')


def get_accuracy(file, count, count1, count2, conf=0):
    """
    
    :param count: =>咨询总次数
    :param count1: =》 预测咨询次数
    :param count2: =》 咨询正确次数
    :return: 
    """

    a = dict()
    a['confidence'] = str(conf)
    a['all_count'] = str(count)
    a['pred_count'] = str(count1)
    a['true_count'] = str(count2)
    a['coverage'] = str(round(float(count1)/count*100, 2))+'%'
    a['accuracy'] = str(round(float(count2)/count1*100, 2))+'%'
    format = 'confidence:%s,all_count:%s,pred_count:%s,true_count:%s,accuracy:%s,coverage:%s\n'
    buf = format % (a['confidence'], a['all_count'], a['pred_count'], a['true_count'], a['accuracy'], a['coverage'])
    output.write(buf.encode('utf-8'))
    print buf
    return a


def run_test():
    # tc_a = client.tmserver_client.TmserverClient()
    # tc_b = AIServiceClient()
    # tc_b = AgadaClient()
    input = open(input_file, 'r')
    output1 = open(output1_file, 'w')
    output2 = open(output2_file, 'w')
    count = 0
    count1 = 0
    count2 = 0
    for line in input:
        count = count + 1
        line = list(line.strip().split('\t'))
        content = line[0].decode('utf-8')
        dept_name = line[1].decode('utf-8')
        # classify_result_b = None
        try:
            classify_result_b = tc_b.query({'q': content.encode('utf-8')}, service='dept_classify')
        except:
            classify_result_b = None
        if classify_result_b is not None:
            data = classify_result_b.get('data')
            if data and data[0]:
                count1 = count1 + 1
                department_b = data[0].get('dept_name')
                department_b_prob = data[0].get('score')
            if dept_name != department_b:
                format = '%s||%s||%s||%s'
                buf = format % (content, dept_name, department_b, department_b_prob)
                # print buf.encode('utf-8')
                output1.write(buf.encode('utf-8'))
                output1.write('\n')
            else:
                format = '%s||%s||%s||%s'
                count2 = count2 + 1
                buf = format % (content, dept_name, department_b, department_b_prob)
                output2.write(buf.encode('utf-8'))
                output2.write('\n')
    accuracy_result = get_accuracy(count, count1, count2)
    for i, j in accuracy_result.items():
        print i, j


def run_test_new(output, confidence=0):
    """
    
    :param confidence:  confidnece >=0 and confidnece <1  
    :return: 
    """
    # tc_a = client.tmserver_client.TmserverClient()
    # tc_b = AgadaClient()
    input = open(input_file, 'r')
    output1 = open(output1_file, 'w')
    output2 = open(output2_file, 'w')
    count = 0
    count1 = 0
    count2 = 0
    for line in input:
        count = count + 1
        line = list(line.strip().split('\t'))
        content = line[0].decode('utf-8')
        dept_name = line[1].decode('utf-8')
        classify_result_b = tc_b.query({'q': content.encode('utf-8')}, service='dept_classify')
        format = '%s==%s==%s==%s'
        try:
            data = classify_result_b.get('data')
            pre_dept_name = data[0].get('dept_name')

            if pre_dept_name != 'unknow':
                pre_dept_name_pro = data[0].get('score')
                if pre_dept_name_pro >= confidence:
                    count1 = count1+1
                    if pre_dept_name == dept_name:
                        count2 = count2+1
                        # buf = format % (content, dept_name, pre_dept_name, pre_dept_name_pro)
                        # output1.write(buf.encode('utf-8'))
                        # output1.write('\n')
                    else:
                        buf = format % (content, dept_name, pre_dept_name, pre_dept_name_pro)
                        output2.write(buf.encode('utf-8'))
                        output2.write('\n')
                else:
                    buf = format % (content, dept_name, 'unknow', 'unknow')
                    output2.write(buf.encode('utf-8'))
                    output2.write('\n')
            else:
                buf = format % (content, dept_name, 'unknow', 'unknow')
                output2.write(buf.encode('utf-8'))
                output2.write('\n')
        except:
            buf = format % (content, dept_name, 'unknow', 'unknow')
            output2.write(buf.encode('utf-8'))
            output2.write('\n')
    result = get_accuracy(output, count, count1, count2, confidence)
    return result


if __name__ == "__main__":
    """
    confidenc>=0 and confidence <1 
    """
    import datetime

    output = open(save_accuracy, 'w')
    starttime = datetime.datetime.now()
    range = [float(i)/10 for i in range(0, 10)]
    for i in range:
        result = dict()
        run_test_new(output, i)
    endtime = datetime.datetime.now()
    print(endtime-starttime).seconds
