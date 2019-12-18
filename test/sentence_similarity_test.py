#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
sentence_similarity_test.py --  句子相似性测试程序

Author: caoxg <caoxg@guahao.com>
Create on 2018-08-16 星期三.
"""


import xlrd
import random
import global_conf
from ailib.client.ai_service_client import AIServiceClient
import codecs
import pandas as pd
import sys


# search = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService', port=3000)
# test_file = '/ssddata/testdata/mednlp/sentence_similarity/sentence_similarity_20180926.txt'


def save_test_data():
    """
    从标记的100*10的相似文本，加上其他无关的数据形成 100*100的测试文本
    并把文本保存下来
    :return: 无
    """
    data = xlrd.open_workbook('/home/caoxg/work/mednlp/test/sentence_similarity_20180926.xlsx')
    table = data.sheet_by_index(0)
    file = codecs.open('/home/caoxg/work/mednlp/test/sentence_similarity_20180926.txt', 'w', encoding='utf-8')
    nrows = table.nrows
    target_sentence = []
    test_sentences = []
    for i in range(nrows):
        target_sentence.append(table.row_values(i)[0])
        test_sentences.append(
            [table.row_values(i)[1], table.row_values(i)[2], table.row_values(i)[3], table.row_values(i)[4],
             table.row_values(i)[5], table.row_values(i)[6], table.row_values(i)[7], table.row_values(i)[8],
        table.row_values(i)[9], table.row_values(i)[10]])
    second_file = codecs.open('/home/caoxg/work/mednlp/test/simi.txt', 'r', encoding='utf-8')
    second_test_sentence = {}
    for index, line in enumerate(second_file):
        if len(line.strip()) == 0:
            continue
        second_test_sentence[index] = line

    def random_num():
        b_list = range(0, 120)
        random_int = random.sample(b_list, 90)
        return random_int

    def random_sentence(second_test_sentence):
        random_int = random_num()
        random_sentence = [second_test_sentence.get(num) for num in random_int]
        return random_sentence

    for line in test_sentences:
        t = random_sentence(second_test_sentence)
        line.extend(t)

    for target, test in zip(target_sentence, test_sentences):
        test = [str(word).strip() for word in test]
        output_format = '%s\t%s\n'
        out_line = output_format % (target, '#'.join(test))
        file.write(out_line)


class Test(object):
    def __init__(self, port, test_file = '',mode=1):
        print('please check your port', port)
        self.mode=mode
        self.search = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService', port=port)
        self.querys = []
        self.contents = []
        self.test_file = test_file
        self.get_data()

    def get_data(self):
        """
        读取测试数据
        :return: 返回目标语句和语句列
        """
        target_sentence = []
        test_sentences = []
        file = codecs.open(self.test_file, 'r', encoding='utf-8')
        # file = codecs.open('/ssddata/testdata/mednlp/sentence_similarity/sentence_similarity_20180926.txt', 'r', encoding='utf-8')
        for line in file:
            lines = line.strip().split('\t')
            if len(lines) == 2:
                target_sentence.append(lines[0])
                test_sentence = lines[1].strip().split('#')
                test_sentences.append(test_sentence)
        self.querys = target_sentence
        self.contents = test_sentences

    def get_pred_count(self):
        """
        给出top3和top6以及预测出的结果准确率
        :return: 返回预测出的样本数，top3准确的样本数，top6准确的样本数
        """
        pred_count = 0
        top3_count = 0
        top6_count = 0
        pred_result = []
        for query, content in zip(self.querys, self.contents):
            query = str(query)
            content = str(content)
            if mode==2:
                t = self.search.query({'q': query, 'contents': content,'mode':self.mode}, service='sentence_similarity')
            else:
                t = self.search.query({'q': query, 'contents': content}, service='sentence_similarity')
            if t.get('data'):
                if t.get('data').get('is_similarity') == 1:
                    pred_count = pred_count + 1
                    index = t.get('data').get('index')
                    score = t.get('data').get('score')
                    pred_result.append([index,score])
        return pred_result

    def compute_accuracy(self):
        result = {'confidence': [], 'total_count': [], 'pred_count': [], 'top3_count': [], 'top6_count': [],'cover':[],
                  'top3_accuracy':[],'top6_accuracy':[]}
        confidence = [float(index) / 10 for index in range(10)]
        for level in confidence:
            pred_count = 0
            top3_count = 0
            top6_count = 0
            for line in self.get_pred_count():
                if line[1] > level:
                    pred_count = pred_count + 1
                    if line[0] < 3:
                        top3_count = top3_count + 1
                    if line[0] < 6:
                        top6_count = top6_count + 1
            result['confidence'].append(level)
            result['total_count'].append(100)
            result['pred_count'].append(pred_count)
            result['top3_count'].append(top3_count)
            result['top6_count'].append(top6_count)
            result['cover'].append("%.2f" % (round(float(pred_count)/100,4)*100)+ '%')
            result['top3_accuracy'].append("%.2f" %(round(float(top3_count)/pred_count,4)*100) + '%')
            result['top6_accuracy'].append("%.2f" %(round(float(top6_count)/pred_count,4)*100)+ '%')
        return result

    def save_result(self,save_path = ''):
        if not save_path:
            save_path = 'sentence_similarity_accuracy.csv'
        df = pd.DataFrame(self.compute_accuracy())
        df.to_csv(save_path, index=False, header=True)



if __name__ == '__main__':
    command = '\npython %s [-p port -source_type source_type]' % sys.argv[0]
    from optparse import OptionParser
    parser = OptionParser(usage=command)
    parser.add_option('-p', '--port', dest='port', help='the port of service')
    parser.add_option('--source_type', dest='source_type', help='the test of machine')
    parser.add_option('-m', dest='mode', help='the mode of model')

    (options, args) = parser.parse_args()
    port = 3000
    source_type =1
    mode =1
    if options.port:
        port = options.port
        port = int(port)
    if options.source_type:
        source_type = options.source_type
        source_type = int(source_type)
    if options.mode:
        mode = options.mode
        mode = int(mode)

    if source_type==1:
        test_file = '/data/testdata/mednlp/sentence_similarity/sentence_similarity_20180926.txt'
    else:
        test_file = '/ssddata/testdata/mednlp/sentence_similarity/sentence_similarity_20180926.txt'

    test = Test(port=port, test_file=test_file,mode=mode)
    # test.get_pred_count()
    test.save_result()
