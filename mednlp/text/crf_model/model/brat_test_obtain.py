# -*- coding: utf-8 -*-
# @Author: yinwd
# @Date:   2018-11-26 15:18:20

import re
import codecs
import numpy as np
from mednlp.utils.data_prepare import AiServiceResult


## 实体识别
model_service = AiServiceResult(port=2138, service_name='entity_extract', service_q='q')

### 利用实体识别模型为切词器
def words_segment(sentence):
    data_list = model_service.web_result(sentence)
    words_pos_list = []
    if data_list:
        for dict in data_list:
            words = dict['entity_name']
            pos = dict['type']
            words_pos_list.append([pos, words])
    return words_pos_list


## 获取测试集 的标注结果 改为crf标注形式
def get_data_brat(n_list, type_need):
    filepath = '/home/yinwd/work/mednlp/mednlp/text/crf_model/data/'
    data_write = codecs.open(filepath + 'test_ner_tagging.txt', 'w', encoding='utf-8')
    content_brat = open(filepath + 'brat_content.txt', 'w', encoding='utf-8')
    for n in n_list:
        data_path = '/home/yinwd/work/brat-v1.3_Crunchy_Frog/data/brat_entity_label/data{}/'.format(n)
        if n == 2700:
            n_low = 2600
            n_up = 2737
        else:
            n_low = n-200
            n_up = n
        for m in range(n_low, n_up):
            result_list = []
            print('----------data{}----------'.format(m))
            ## brat标注的结果
            brat_ont_path = data_path + 'data{}.ann'.format(m)
            ## brat标注的原文本
            brat_text_path = data_path + 'data{}.txt'.format(m)
            brat_data_list = codecs.open(brat_ont_path, 'r', encoding='utf8').readlines()
            brat_text_sentence = codecs.open(brat_text_path, 'r', encoding='utf8').readlines()
            sentence = brat_text_sentence[0].strip()
            content_brat.write(sentence + '\n')
            brat_result_position = []

            if brat_data_list :
                for bratdata in brat_data_list:
                    data_split = re.split('\t', bratdata.strip())
                    types, start, end = re.split('\s', data_split[1])
                    if types == type_need:
                        brat_result_position.append([start, end])


            for indw, w in enumerate(sentence):
                if brat_result_position:
                    startlist = [int(x[0]) for x in brat_result_position]
                    endlist = [int(x[1]) for x in brat_result_position]
                    I_label = []
                    for j, i in enumerate(startlist):
                        I_label.extend([x for x in range(startlist[j]+1, endlist[j])])

                    if indw in startlist:
                        data_write.write(w + '\t' + 'B-' + type_need + '\n')
                    elif indw in I_label:
                        data_write.write(w + '\t' + 'I-' + type_need + '\n')
                    else:
                        data_write.write(w + '\t' + 'O' + '\n')
                else:
                    data_write.write(w + '\t' + 'O' + '\n')
            data_write.write('\n')
            #         brat_dict[types] = data_split[2]
            #         result_list.append(brat_dict)
            # result_dict = json.dumps([m, sentence, result_list], ensure_ascii=False)
            # print result_dict
            # data_write.write(result_dict + '\n')
    data_write.close()
    content_brat.close()

if __name__ == '__main__':
    # n_list = np.arange(200,2800,200).tolist()
    # n_list.append(2700)
    # type_need = 'hospital'
    # get_data_brat(n_list, type_need)
    # input_data = open('../data/test_brat_hospital.txt', 'r', encoding='utf-8').readlines()
    # output_path_file = '../data/test_brat_crf.txt'
    # typelist = ['hospital']
    # entity_tagging(input_data, output_path_file, typelist)

    from mednlp.utils.data_prepare import CRFDataPrepare
    model_ser = CRFDataPrepare(port=2148, service_name='entity_extract', service_q='q')
    input_data = open('../data/brat_content.txt', 'r', encoding='utf-8').readlines()
    outputfile = '../data/brat_jieba_tagging.txt'
    max_output_file = '../data/test_brat_crf.txt'
    # model_ser.jieba_tagging(input_data, outputfile)
    model_ser.data_make(outputfile, '../data/brat_ner_tagging.txt', max_output_file)
    # model_ser.find_error('brat')
