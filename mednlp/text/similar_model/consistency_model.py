#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import global_conf
import logging
from mednlp.text.similar_model.model_predict import ModelPredict, pred_exit_probability
from mednlp.text.neg_filter import filter_negative
from ailib.model.base_model import BaseModel

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)


class ConsistencyModelOld(BaseModel):

    def __init__(self):
        model_dir = '/data/mednlp/models/consistency_model/'
        self.model = ModelPredict(model_dir)
        super(ConsistencyModelOld, self).__init__()

    def predict_probability(self, sentence, disease_name, standrad_case_path):
        standrad_case_dict = json.load(open(standrad_case_path,'r',encoding='utf-8'))
        text_b = standrad_case_dict.get(disease_name)
        sentence = filter_negative(sentence) # 去除否定（正常）的短语
        if text_b:
            pred, prob = self.model.predict_sample_similar(text_a=sentence, text_b=text_b)
            # print(disease_name, prob[0])
            result = pred_exit_probability(sentence, text_b, prob[1])
            return result
        else:
            return 0


class ConsistencyModel(BaseModel):

    def initialize(self, **kwargs):
        model_dir = self.model_path
        model = ModelPredict(model_dir)
        self.model = model

    def predict_probability(self, sentence, disease_name):
        standrad_case_dict = json.load(open(global_conf.standard_case,'r',encoding='utf-8'))
        text_b = standrad_case_dict.get(disease_name)
        sentence = filter_negative(sentence) # 去除否定（正常）的短语
        dict_result = {}
        if text_b:
            pred, prob = self.model.predict_sample_similar(text_a=sentence, text_b=text_b)
            result = pred_exit_probability(sentence, text_b, prob[1])
        else:
            result = 0
        dict_result['consistency_result'] = str(result*100) + '%'
        # print(dict_result)
        return dict_result


if __name__ == '__main__':
    sentence0 = """
    患者于5年前开始反复出现咳嗽、咳痰，呈阵发性咳嗽、咳白色粘痰，易咳出，伴胸闷、气短，乏力，活动后加重，无盗汗、发热、咯血、头痛、晕厥、抽搐、胸痛、
    视物旋转、黑曚、耳鸣、恶心、呕吐、腹痛、腹泻、黑便、尿痛、血尿等症，每次自行给予抗感冒药物治疗，上述症状控制欠佳；2天前受凉后再次出现上述症状，
    伴发热，体温最高达39.1℃，就诊于我院急诊，行血常规未见异常，胸部X线片提示慢性支气管炎，胸主动脉粥样硬化，心电图示：窦性心动过速，偶发房性早搏，
    急诊给予对热处理后以“1.急性支气管炎2.冠心病 不稳定性心绞痛3.高血压”收住，患者自发病以来神志清，精神差，饮食、睡眠差，大小便正常，近期体重无明显增减。
    """
    sentence1 = '患者于半月前无明显诱因出现咳嗽，无发热，偶有气短，无胸闷，无头痛、头晕。'
    sentence = sentence0
    # model = ConsistencyModel()
    # model.predict_probability(sentence, 'gastric_cancer',standrad_case_path)
    # model.predict_probability(sentence, 'bronchiolitis', standrad_case_path)
    # model.predict_probability(sentence, 'lung', standrad_case_path)
    consistency_model = ConsistencyModel(cfg_path=global_conf.cfg_path, model_section='CONSISTENCY_MODEL')
    consistency_model.predict_probability(sentence, '胃癌')
    consistency_model.predict_probability(sentence, '支气管炎')
    consistency_model.predict_probability(sentence, '肺癌')