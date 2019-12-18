#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
data_prepare.py # 数据预处理

Author: yinwd <yinwd@guahao.com>
Create on 2018-11-29 星期四.
"""

import re
import jieba
import requests
from urllib import parse
import jieba.posseg as psg
from requests.auth import HTTPDigestAuth

class AiServiceResult(object):
    '''
    通过网页获取192.168.4.30相应ai服务的结果
    :param
    inputdata:输入
    port: 服务的端口号
    service_name: 服务的名称
    service_q： 服务的q（前置名称，一般为q）
    '''
    def __init__(self, port, service_name, service_q):
        self.port = port
        self.service_name = service_name
        self.service_q = service_q

    def get_web_data(self, url):
        r = requests.get(url)
        if r.status_code == 200:
            return r.content
        else:
            return u'请求失败'

    def web_result(self, input_data):
        url = 'http://172.27.249.130:' + str(self.port)+ '/' + self.service_name + '?'
        dict ={self.service_q: input_data}
        url = url + parse.urlencode(dict) ## 注意urlencode需要的格式是{q: contence}字典格式
        output_data = self.get_web_data(url)
        output_dict = eval(output_data)  ##返回字典格式
        reslut_list = output_dict.get('data')
        return reslut_list

class AiServiceUrl(AiServiceResult):
    '''
    可以自由配置ip
    '''
    def __init__(self,  port, service_name, service_q, ip):
        super(AiServiceUrl, self).__init__(port, service_name, service_q)
        self.ip = ip

    def web_result_url(self, input_data):
        url = 'http://' + self.ip + ':' + str(self.port)+ '/' + self.service_name + '?'
        dict ={self.service_q: input_data}
        url = url + parse.urlencode(dict) ## 注意urlencode需要的格式是{q: contence}字典格式
        print(url)
        output_data = self.get_web_data(url)
        output_dict = eval(output_data)  ##返回字典格式
        reslut_list = output_dict.get('data')
        return reslut_list

class CRFDataPrepare(AiServiceResult):

    def __init__(self, port, service_name, service_q):
        # self.port = port
        # self.service_name = service_name
        # self.service_q = service_q
        super(CRFDataPrepare, self).__init__(port, service_name, service_q)

    ### 利用实体识别模型为切词器
    def words_segment(self, content):
        data_list = self.web_result(content)
        words_pos_list = []
        if data_list:
            for dict in data_list:
                words = dict['entity_name']
                pos = dict['type']
                words_pos_list.append([pos, words])
        return words_pos_list

    def jieba_tagging(self, input_data, output_psg_file):
        '''
        :param input_data: 文本句子列表
        :param output_path_file: 输出文本
        :return: 我 n 2列展示的文本，第1列为char，第2列为jieba分词的词性
        '''
        output_data = open(output_psg_file, 'w', encoding='utf-8')
        for index, sentence in enumerate(input_data):
            print('----->index%d' % (index))
            sentence = re.sub('\s|%|/|\+|#|&', '', sentence)  ## 中间有空格或者换行影响后面模型，因此都去掉。
            sentence = re.sub(';', '；', sentence)
            jieba_split = psg.cut(sentence.strip())
            if jieba_split:
                for words in jieba_split:
                    word = words.word
                    flag = words.flag
                    for char in word:
                        output_data.write(char + "\t" + flag + "\n")

            output_data.write("\n")
        output_data.close()

    def entity_tagging(self, input_data, output_ner_file, typelist):
        '''
        :param input_data: 文本句子列表
        :param output_ner_file: 实体识别标注结果文件
        :param typelist: 需要的实体类别列表eg: ['symptom', 'disease'. 'hospital']
        :return: 我 O 2列展示的文本，第1列为char，第2列为预设标签
        '''

        output_data = open(output_ner_file, 'w', encoding='utf-8')
        for index, sentence in enumerate(input_data):
            print('----->index%d' % (index))
            sentence = re.sub('\s|%|/|\+|#|&', '', sentence)  ## 中间有空格或者换行影响后面模型，因此都去掉
            sentence = re.sub(';', '；', sentence.strip())  # 在服务调用的时候如果是英文分号，分号后的内容会被切除掉，因此先处理掉
            words_pos_list = self.words_segment(sentence)
            if words_pos_list:
                for words_pos in words_pos_list:
                    flag = words_pos[0]
                    word = words_pos[1]
                    if 'symptom' in typelist: # 在几类实体列别中，症状是由单字成为实体的，选用BMESO标注体系，其余采用BIO标注体系
                        if flag in typelist:
                            if len(word) == 1:
                                output_data.write(word[0] + "\tS-" + flag + "\n")
                            else:
                                output_data.write(word[0] + "\tB-" + flag + "\n")
                                for w in word[1:len(word) - 1]:
                                    output_data.write(w + "\tM-" + flag + "\n")
                                output_data.write(word[len(word) - 1] + "\tE-" + flag + "\n")
                        else:
                            for w in word:
                                output_data.write(w + "\tO\n")
                    else:
                        if flag in typelist:
                            output_data.write(word[0] + "\tB-" + flag + "\n")
                            for w in word[1:len(word)]:
                                output_data.write(w + "\tI-" + flag + "\n")
                        else:
                            for w in word:
                                output_data.write(w + "\tO\n")
            output_data.write("\n")
        # input_data.close()
        output_data.close()

    ## 训练样本或者测试样本生成：
    def data_make(self, jieba_file, ner_file, output_file):
        '''
        :param jieba_file: jieba分词附带的词性特征文件， jieba_tagging生成的文件
        :param ner_file: 实体识别标注的文件，entity_tagging生成的文件
        :param output_file:  返回 添加jieba分词词性的以实体识别结果为标签的文件
        :return: 生成汇总文件
        '''
        jieba_data = open(jieba_file, 'r', encoding='utf-8').readlines()
        ner_data = open(ner_file, 'r', encoding='utf-8').readlines()
        output_data = open(output_file, 'a+', encoding='utf-8')
        assert len(jieba_data) == len(ner_data), 'Length mismatch'

        for ind, char_ in enumerate(jieba_data):
            if char_:
                tag2 = ner_data[ind].split('\t')[-1]
                output_data.write(char_.strip() + '\t' + tag2)
            else:
                output_data.write('\n')

        output_data.close()

    def main_function(self, path_file, set_type, n, m, typelist, finderror=False):
        '''
        :param path_file: 语料文本路径
        :param set_type: 可选 train,validation,test 等
        :param n: 语料切片 start
        :param m: 语料切片 end
        :param typelist: 实体列表 ['symptom', 'disease'. 'hospital']
        :param finderror ，合并文本时，长度不同会报错，利用find_error查找错误在哪，然后令finderror=True重新运行该模型，
        :return: 融合文件
        '''
        # 开启并行分词模式，参数为并发执行的进程数
        jieba.enable_parallel(8)
        ner_file = '../data/' + set_type + '_ner_tagging.txt'
        jieba_file = '../data/' + set_type + '_jieba_tagging.txt'
        n, m = int(n), int(m)
        input_data = open(path_file, 'r', encoding='utf-8').readlines()

        assert len(input_data) >= m, 'Length Over, Please choose a little m'

        input_data = input_data[n: m]
        if not finderror: ## 当有问题经过 find_error查找错误后，可以修改文件，修改后，改为finderror=True，在运行该函数，进行合并
            self.entity_tagging(input_data, ner_file, typelist)
            self.jieba_tagging(input_data, jieba_file)
        output_file = '../data/' + set_type + '_crf_data.txt'
        self.data_make(jieba_file, ner_file, output_file)
        jieba.disable_parallel()

    def find_error(self, set_type):
        '''
        :param set_type: 可选 train,validation,test 等
        :return: 返回未匹配的地方
        '''
        path_jieba = '../data/' + set_type + '_jieba_tagging.txt'
        path_ner = '../data/' + set_type + '_ner_tagging.txt'
        jieba_data = open(path_jieba, 'r', encoding='utf-8').readlines()
        ner_data = open(path_ner, 'r', encoding='utf-8').readlines()
        for index, words in enumerate(jieba_data):
            if words:
                if ner_data[index]:
                    char = re.split('\t', words)[0]
                    char2 = re.split('\t', ner_data[index])[0]
                    if char != char2:
                        print(index, char)
                        print(index - 1, jieba_data[index - 1])
                        break

if __name__ == '__main__':
    sentence = '我想去浙二呼吸内科挂个号'
    entity_model = AiServiceResult(port=3000, service_name= 'dept_classify', service_q='q')
    result = entity_model.web_result(sentence)
    print(result)
    mdoeltest = CRFDataPrepare(port=3000, service_name= 'entity_extract', service_q='q')
    print(mdoeltest.words_segment(sentence))