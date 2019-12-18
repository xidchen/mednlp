#/!usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import logging
from mednlp.text.similar_model.model_predict import ModelPredict
from mednlp.text.neg_filter import filter_negative


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

model_dir = '/data/mednlp/models/consistency_model/'
PD_Model = ModelPredict(model_dir)

class ConsistencyModel(object):

    def __init__(self):
        super(ConsistencyModel, self).__init__()

    def predict_probability(self, sentence, disease_name, standrad_case_path):
        standrad_case_dict = json.load(open(standrad_case_path,'r',encoding='utf-8'))
        text_b = standrad_case_dict.get(disease_name)
        sentence = filter_negative(sentence) # 去除否定（正常）的短语
        if text_b:
            pred, prob = PD_Model.predict_sample_similar(text_a=sentence, text_b=text_b)
            print(prob[0])
            return prob[0]
        else:
            return 0


if __name__ == '__main__':
    sentence = '患日10余次。'
    standrad_case_path = 'standrad_case_set.txt'
    model = ConsistencyModel()
    model.predict_probability(sentence, 'appendicitis',standrad_case_path)
    model.predict_probability(sentence, 'bronchiolitis', standrad_case_path)
    model.predict_probability(sentence, 'lung', standrad_case_path)
    model.predict_probability(sentence, 'AURI', standrad_case_path)
    model.predict_probability(sentence, 'hypertension', standrad_case_path)
    model.predict_probability(sentence, 'CHD', standrad_case_path)
    model.predict_probability(sentence, 'CG', standrad_case_path)