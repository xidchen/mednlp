# -*- coding: utf-8 -*-
# @Author: yinwd
# @Date:   2018-11-26 14:11:08

import re
import pandas as pd
from mednlp.utils.data_prepare import AiServiceResult

model_service = AiServiceResult(port=2138, service_name='entity_extract', service_q='q')

def get_type_word(sentence, type_need):
    word_list = []
    reslut_list = model_service.web_result(sentence)
    for dict in reslut_list:
        tp = dict['type']
        word = dict['entity_name']
        if tp == type_need:
            word_list.append(word)
    result = ",".join(word_list)
    return result

def get_num(real_label, pred_label):
    glod_num, pred_num, acc_num = 0, 0, 0
    for index, list_l in enumerate(pred_label):
        words_re = []
        words = []
        if list_l:
            words = re.split(',', list_l)
            pred_num += len(words)
        if real_label[index]:
            words_re = re.split(',', real_label[index])
            glod_num += len(words_re)
        if words:
            for word in words:
                if word in words_re:
                    acc_num += 1
    print('glod_num: %d, pred_num: %d, acc_num: %d'%(glod_num, pred_num, acc_num))
    return glod_num, pred_num, acc_num

def prf(glod_num, pred_num, acc_num):
    '''
    :param glod_num:the number of real values
    :param pred_num: the number of predictive values
    :param acc_num: the number of correct values
    :return:precision,recall,F
    '''
    p = 1
    r = 1
    f = 1
    if pred_num != 0:
        p = acc_num/pred_num
    if glod_num != 0:
        r = acc_num/glod_num
    if p != 0 or r != 0:
        f = 2 * p * r / (p + r)

    print('Statistics Result: P: %.2f%%, R: %.2f%%, F: %.2f%%'%(p*100, r*100, f*100))

def merge_pred(pred_list1, pred_list2):
    '''
    :param pred_list1:模型预测的结果
    :param pred_list2: 实体识别的结果
    :return: 汇总的结果(用模型补充实体识别的结果)
    '''
    pred_mixture = []
    for index, words in enumerate(pred_list1):
        sp_words1 = re.split(',', words)
        sp_words2 = re.split(',', pred_list2[index])
        add_list = pred_list2[index]
        for j in sp_words1:
            if not re.findall(j, add_list):
                add_list += ("," + j)
                add_list = re.sub(',$', '', add_list)
                add_list = re.sub('^,', '', add_list)
                # print(pred_mixture[index])
        pred_mixture.append(add_list)
    return pred_mixture

def result_statitics(result_file, brat=False):
    sentence_list = []
    real_label = []
    pred_label = []
    # 先拆分出句子
    with open(result_file, 'r', encoding='utf-8') as result_list:
        sentence = []
        word_re = []
        word_pr = []
        for line in result_list:
            if line != '\n':
                char, pos, real, pred = re.split('\t', line.strip())
                sentence.append(char)
                word_re.append(real)
                word_pr.append(pred)
            else:
                sentence_list.append(sentence)
                real_label.append(word_re)
                pred_label.append(word_pr)
                sentence = []
                word_re = []
                word_pr = []

        data_df = pd.DataFrame(["".join(x) for x in (sentence_list)], columns=['content'])
        content_list = data_df.content.tolist()
        if brat:
            new_pred_entity = [get_type_word(x, 'hospital') for x in content_list]
        new_real_label = []
        new_pred_label = []
        ## 字的组合（按照标签）
        for index, label_list in enumerate(real_label):
            word_list = []
            word = ''
            for j, lb in enumerate(label_list):
                if lb != 'O':
                    word += sentence_list[index][j]
                    if j == len(label_list)-1:
                        word_list.append(word)
                else:
                    word_list.append(word)
                    word = ''
            new_real_label.append(','.join([x for x in word_list if x]))

        for index1, label_list1 in enumerate(pred_label):
            # print(label_list1)
            word_list1 = []
            word1 = ''
            for j1, l1 in enumerate(label_list1):
                if l1 != 'O':
                    word1 += sentence_list[index1][j1]
                else:
                    word_list1.append(word1)
                    word1 = ''
            new_pred_label.append(','.join([x for x in word_list1 if x]))
        data_df['real_label'] = new_real_label
        data_df['pred_label'] = new_pred_label
        # crf模型预测结果
        glod_num, pred_num, acc_num = get_num(new_real_label, new_pred_label)
        prf(glod_num, pred_num, acc_num)

        if brat:
            data_df['pred_label_en'] = new_pred_entity
            # 实体识别模型结果
            glod_num1, pred_num1, acc_num1 = get_num(new_real_label, new_pred_entity)
            prf(glod_num1, pred_num1, acc_num1)

            pred_mixture = merge_pred(new_pred_label, new_pred_entity)
            data_df['pred_label_mix'] = pred_mixture

            # 融合模型的预测结果
            glod_num2, pred_num2, acc_num2 = get_num(new_real_label, pred_mixture)
            prf(glod_num2, pred_num2, acc_num2)

        data_df.to_excel('/home/yinwd/work/mednlp/mednlp/text/crf_model/data/result_pred.xlsx')

if __name__ == '__main__':
    # result_file = '/home/yinwd/work/mednlp/mednlp/text/crf_model/data/output.txt'
    # result_statitics(result_file)
    result_file2 = '/home/yinwd/work/mednlp/mednlp/text/crf_model/data/pred_brat_output.txt'
    result_statitics(result_file2)