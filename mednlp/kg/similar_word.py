#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
语义相似词计算
Author: raogj <raogj@guahao.com>
Create on 2019-11-26 .
"""
import logging
import os

from Levenshtein import ratio, jaro, jaro_winkler, seqratio, setratio

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

RELATIVE_PATH = os.path.dirname('../../')+'/'
dict_path = RELATIVE_PATH + 'data/dict/similar_word_dict/'
print(dict_path)
type_ls = ['disease']


class SimilarWordModel(object):
    def __init__(self):
        self.all_word_dt = self.load_data(dict_path, dict_type_ls=type_ls)
        super(SimilarWordModel, self).__init__()

    @staticmethod
    def load_data(root_path: str, dict_type_ls: list) -> dict:
        all_word_dt = {}
        for dict_name in dict_type_ls:
            file_path = root_path + dict_name + '.txt'
            code_2_name = {}
            for line in open(file_path, 'r', encoding='utf-8'):
                code, name = line.strip().split('\t')
                code_2_name[code] = name
            all_word_dt[dict_name] = code_2_name
        return all_word_dt

    def similar_calculation(self, original_word: str, word_type: str, top_n=10) -> list:
        result_ls = []
        word_dt = self.all_word_dt.get(word_type)
        if not word_dt:
            logging.error("word_type输入有误，请在[disease，examination，symptom，medicine，treatment]中选择！")
        for candidate_word in word_dt.values():
            # ratio, jaro, jaro_winkler, setratio, seqratio
            sim_score = ratio(original_word, candidate_word)
            if sim_score <= 0:
                continue
            result_ls.append({"name": candidate_word, "sim_score": sim_score})
        result_top_n = sorted(result_ls, key=lambda x: (x["sim_score"]), reverse=True)[:top_n]
        return result_top_n


if __name__ == '__main__':
    similar_word_model = SimilarWordModel()
    target = '呼吸道感染'
    print(target)
    result = similar_word_model.similar_calculation(target, word_type='disease')
    print(result)
