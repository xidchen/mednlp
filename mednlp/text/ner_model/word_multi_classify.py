#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
named_entity_recognition.py -- medical entities recognition from content via deep learning model
Author : raogj(raogj@guahao.com)
Create on 2019.07.23
"""

from ailib.model.base_model import BaseModel
from keras.models import model_from_json
from mednlp.text.vector import Char2vector
from mednlp.dao.data_loader import Key2Value
from keras.preprocessing.sequence import pad_sequences
import global_conf
import numpy as np
import time
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


class WordMultiClassify(BaseModel):

    def initialize(self, model_version=1, classify_len=20, **kwargs):
        self.model_version = model_version
        self.classify_max_len = classify_len
        self.multi_classification_model = self.load_model()
        self.char2vector = Char2vector(global_conf.named_entity_recognition_char_dict_path)
        self.type_dict = Key2Value(path=global_conf.named_entity_recognition_type_dict_path, swap=True).load_dict()

    def predict(self, words):
        """
        获取词的多分类结果
        :param words: 待分类的词列表
        :return: 分类标签向量
        """
        word_vec = pad_sequences([np.array(self.char2vector.get_char_vector(word)) for word in words],
                                 maxlen=self.classify_max_len, padding='pre')
        prob = self.multi_classification_model.predict(word_vec)
        label_vec = [np.argmax(p) for p in prob]
        return label_vec

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        return model

def main():
    context = ['请问', '杭州第一人民医院']
    word_multi_classify = WordMultiClassify(cfg_path=global_conf.cfg_path,
                                            model_section='NAMED_ENTITY_RECOGNITION_MODEL_TO_MULTI_CLASSIFY')
    t0 = time.time()
    for i in range(1):
        results = word_multi_classify.predict(context)
    t1 = time.time()
    print(results)
    print(t1-t0)


if __name__ == '__main__':
    main()
