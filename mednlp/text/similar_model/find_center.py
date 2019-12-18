#/!usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import numpy as np
import pandas as pd
from mednlp.utils.utils import print_time
from mednlp.text.similar_model.model_predict import pred_exit_probability

class FindCenterSentence(object):

    def __init__(self):
        super(FindCenterSentence, self).__init__()

    def get_center_sentence(self, inputfile):
        '''
        inputdata是list形式
        :param inputdata: 列表
        :return: 中心文本句子
        '''
        data_dict, sentence_index_dict, max_line_num = self.get_data_dict(inputfile)
        df_match = self.full_matrix(data_dict, max_line_num)
        sentence_rows_index = self.find_center_index(df_match)
        center_sentence = sentence_index_dict.get(sentence_rows_index)
        redundant_punctuation = re.findall('[，。；：？！;:]{2,}', center_sentence)
        if redundant_punctuation:
            for pun in redundant_punctuation:
                center_sentence = re.sub(pun, '。', center_sentence)
        return center_sentence

    def find_center_index(self, df):
        df['Col_sum'] = df.apply(lambda x: x.sum(), axis=1) # axis=1按照列求和，生成新的列为前面列的累加和结果
        max_value_rows = df['Col_sum'].idxmax() # 获取和最大的行号
        # df.sort_values("Col_sum", inplace=True)
        df.to_excel('probability_matrix.xlsx')
        return str(max_value_rows)

    def full_matrix(self, data_dict, max_line_num):
        df_match = pd.DataFrame(np.zeros((100, 100)))
        # print(df_match.shape)
        # 将预测的label对应到相似矩阵中
        for key, value in data_dict.items():
            i, j = re.split(',', key)
            df_match.iloc[int(i), int(j)] = float(value)
            df_match.iloc[int(j), int(i)] = float(value)
        return df_match
    @print_time
    def get_data_dict(self, inputfile):
        '''
        预测文本：index, sen_a, sen_b, combine_index, lable, pred_label, probability
        :param inputfile:
        :return: {'combine_index':pred_label}
        '''
        sentence_index_dict = {}
        data_dict = {}
        line_num = []
        wt_data = open('text_list.txt', 'w', encoding='utf-8')
        with open(inputfile, 'r', encoding='utf-8') as f:
            for line in f:
                sp_line = re.split('\t', line)
                sentence_a = sp_line[1]
                sentence_b = sp_line[2]
                label = sp_line[-2]
                probability = sp_line[-1] ## 相似(=1)的概率
                combine = sp_line[3] # 形式如 '12,125'(12和125的句子组合，中间以英文逗号隔开)
                # data_dict[combine] = (float(label) + float(probability))/2
                data_dict[combine] = pred_exit_probability(sentence_a, sentence_b, probability)
                combine_index = combine.split(',')
                rows_index = combine_index[0]
                line_num.extend(combine_index)
                if not sentence_index_dict.get(rows_index):
                    wt_data.write(rows_index + '\t' + sentence_a + '\n')
                    sentence_index_dict[str(rows_index)] = sentence_a
        max_line_num = max(line_num)
        wt_data.close()
        return data_dict, sentence_index_dict, max_line_num

class CenterCase(FindCenterSentence):

    def __init__(self):
        super(CenterCase, self).__init__()

    def standard_case_write(self, disease_list, outputfile, outputfile2=None):
        standrad_case_dict = {}
        for disease in disease_list:
            file_name = disease + '_predict.txt'
            filepath = os.path.join('/data/yinwd_data/silimar_data/predict_set/', file_name)
            center_stentence = self.get_center_sentence(filepath)
            standrad_case_dict[disease] = center_stentence
            if outputfile2:
                self.get_prob_order(disease, outputfile2)
        print(standrad_case_dict)
        with open(outputfile, 'w', encoding='utf-8') as writer:
            writer.write(json.dumps(standrad_case_dict, ensure_ascii=False, indent=2))


    def get_prob_order(self, disease, outputfile2):
        outputdata = open(outputfile2, 'a', encoding='utf-8')

        df = pd.read_excel('probability_matrix.xlsx')
        colsum = df['Col_sum'].tolist()
        new_list = []
        k = 0
        with open('text_list.txt', 'r', encoding='utf-8') as rd:
            for line in rd:
                new_list.append([line.strip('\n'), str(round(colsum[k],4))])
                k += 1

        new_list. sort(key=lambda x: x[1], reverse=True)
        for lines in new_list:
            # print(lines)
            outputdata.write(lines[0] + '\t' + disease + '\t' + lines[1] + '\n')
        outputdata.close()


if __name__ == '__main__':

    # model = FindCenterSentence()

    # filepath = os.path.join('/data/yinwd_data/silimar_data/predict_set/', 'appendicitis_predict.txt')
    # center_stentence = model.get_center_sentence(filepath)
    # print(center_stentence)
    from mednlp.text.similar_model.sql_disease import disease_list
    # outputfile = os.path.join(global_conf.dict_path, 'standrad_case_dict01.json')
    outputfile = 'standrad_case_dict1.json'
    outputfile2 = 'result_standrad.txt'
    model_now = CenterCase()
    model_now.standard_case_write(disease_list[4:], outputfile, outputfile2)