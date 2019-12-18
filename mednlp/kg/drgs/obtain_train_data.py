# !/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import os
import random
import logging
from ailib.utils.exception import AIServiceException, ArgumentLostException
from mednlp.kg.get_sql_data import get_data
from mednlp.text.neg_filter import filter_negative, remove_redundant_punctuation

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

class SimilarDataTranslate(object):

    def __init__(self):
        super(SimilarDataTranslate, self).__init__()

    def merge_data_label(self, content_list, output_file, data_dir):
        '''
        获取句子组合
        :param content_list:[sen1+'\t'+label ,...]
        :param output_file: 输出组合后的样本
        :return:
        '''
        output_path = os.path.join(data_dir, output_file)
        output_data = open(output_path, 'w', encoding='utf-8')
        if not content_list:
            raise ArgumentLostException('lost content_list')
        k = 0
        len_sen = []
        for index, content in enumerate(content_list):
            sentence, lable_name = self.split_content('\t', content)
            for j, content_next in enumerate(content_list[index+1:]):
                sentence_next, lable_name_next = self.split_content('\t', content_next)
                if lable_name == lable_name_next:
                    label = '1'
                else:
                    label = '0'
                sentence_final = str(sentence) + '\t' + str(sentence_next) + '\t' + str(index) + ',' + str(j+index+1)
                len_sen.extend([len(sentence), len(sentence_next)])
                k += 1
                if k % 100 == 0:
                    print('Having writing %d sentence'%k)
                output_data.write(str(k) + '\t' + sentence_final + '\t' + label + '\n')
        output_data.close()
        len_sen.sort()
        max_len = len_sen[int(len(len_sen)*0.9)]
        print('MAX_LENGTH', max_len)

    def split_content(self, tag, content):
        if not isinstance(content, str):
            raise AIServiceException(content)
        sp_cont = re.split(tag, content)
        sentence = sp_cont[0]
        label = sp_cont[-1]
        return sentence, label


class SQLDataProcess(object):

    def __init__(self):
        super(SQLDataProcess, self).__init__()

    def combin_data_column(self, data_list, column_list, label):
        '''
        data类型为[{'column1':'value1'},{]]
        :param data: 数组
        :param column_list: 数组,需要合并的列名
        :return: 合并后的数组
        '''
        content_label_list = []
        for data_dict in data_list:
            content = ''
            label_name = data_dict.get(label, '')
            try:
                for index, column in enumerate(column_list):
                    if index < len(column_list)-1 :
                        content += self.deal_abnormal(data_dict.get(column, '')) + '。'
                    else:
                        content += self.deal_abnormal(data_dict.get(column, ''))
            except AIServiceException as e:
                print('文本格式存在非字符串的形式')
            content = content.replace('\t', '').replace('\n', '')
            content = filter_negative(content)
            content_label_list.append(content + '\t' + label_name)
        return content_label_list

    def deal_abnormal(self, sentence):
        if re.search('可靠主诉:', sentence):
            sentence = re.split('可靠主诉:', sentence)[-1]
        sentence = re.sub('患者自发病以来.*', '', sentence)
        sentence = re.sub('患者自入院以来.*', '', sentence)
        sentence = re.sub('自患病以来.*', '', sentence)
        sentence = re.sub('自发病以来.*', '', sentence)
        sentence = re.sub('\s{1,}', ' ', sentence)
        sentence = filter_negative(sentence)
        return sentence

class SQLDataCombine(SQLDataProcess):

    def __init__(self):
        super(SQLDataCombine, self).__init__()

    def data_combine(self, sqllist, column_list, label):
        data_list = []
        for sql_code in sqllist:
            result_data = get_data(sql_code)
            data_list.extend(self.combin_data_column(result_data, column_list, label))
        return data_list



def shuffle_data(inputfile, rows_num, ouputfile):

    id_rows = [x for x in range(1, rows_num+1)]
    random.shuffle(id_rows)
    data_all = open(inputfile, 'r', encoding='utf-8').readlines()
    print(len(data_all), len(id_rows))
    outputdata = open(ouputfile, 'w', encoding='utf-8')
    k = 0
    for index in id_rows:
        k += 1
        if k %1000 ==0:
            logging.info('Having write %d sample'%k)
        outputdata.write(data_all[index-1])

    outputdata.close()

def data_divide(data_dir, inputfile, set_type, rows_num):
    train_data = open(os.path.join(data_dir, 'train.tsv'), 'w', encoding='utf-8')
    dev_data = open(os.path.join(data_dir, 'dev.tsv'), 'w', encoding='utf-8')
    test_data = open(os.path.join(data_dir, 'test.tsv'), 'w', encoding='utf-8')

    if 'dev' in set_type and 'test' in set_type:
        traindata_num  = int(rows_num*0.6)
        devdata_num = int(rows_num*0.8)
    else:
        traindata_num = int(rows_num*0.8)
        devdata_num = rows_num
    sum_train, sum_dev, sum_test = 0, 0, 0

    with open(inputfile, 'r', encoding='utf-8') as f:
        k = 0
        for line in f:
            k += 1
            lable_num = int(re.split('\t', line)[-1])
            if k <= traindata_num:
                sum_train += lable_num
                train_data.write(line)
            elif k <= devdata_num:
                sum_dev += lable_num
                dev_data.write(line)
            else:
                sum_test += lable_num
                test_data.write(line)
    logging.info('The number of positive sample in  train set is %d'%(sum_train))
    logging.info('The number of positive sample in  dev set is %d' % (sum_dev))
    logging.info('The number of positive sample in  test set is %d' % (sum_test))
    train_data.close()
    dev_data.close()
    test_data.close()


def data_summarization(data_dir, sum_data_file):
    content_list = []
    list_file_name = os.listdir(data_dir)
    for i in range(len(list_file_name)):
        logging.info('--->准备写入%s<---'%list_file_name[i])
        path = os.path.join(data_dir, list_file_name[i])
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as rf:
                for line in rf:
                    if line not in content_list:
                        line = line.strip('\n')
                        content_list.append(line)
    logging.info('--》样本数据量为%d条《--'%len(content_list))
    with open(sum_data_file, 'w', encoding='utf-8') as dw:
        for lines in content_list:
            dw.write(lines + '\n')
    # return len(content_list)

def get_data_from_sql(data_dir):
    from mednlp.text.similar_model.sql_disease import sql_list
    lens = int(len(sql_list) / 2)
    for i in range(lens):
        sql_list_need = sql_list[(i * 2):(i * 2 + 2)]
        column_list = ['chief_complaint', 'medical_history']
        label = 'disease_name'
        model_data = SQLDataCombine()
        #
        data_list = model_data.data_combine(sql_list_need, column_list, label)
        print(len(data_list), data_list[0:10])

        data_write_model = SimilarDataTranslate()
        filename = 'train_data_' + str(i) + '.txt'
        data_write_model.merge_data_label(data_list, filename, data_dir)

if __name__ == '__main__':
    # 获取训练数据
    data_dir_train = '/data/yinwd_data/silimar_data/train_data/'
    # get_data_from_sql(data_dir_train)
    # 汇总数据
    data_dir = '/data/yinwd_data/silimar_data/'
    input_file = os.path.join(data_dir, 'consistency_data.txt')
    # data_summarization(data_dir_train, input_file)
    # shuffle data
    output_file = os.path.join(data_dir, 'consistency_shuffle_data.txt')
    shuffle_data(input_file, 149678, output_file)
    # divide data
    data_divide(data_dir, output_file, ['train', 'dev', 'test'], 149678)
