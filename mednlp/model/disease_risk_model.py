#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease_risk_model.py -- the model of disease risk classification

Author: chenxd
Create on 2020-02-18 Tuesday
"""

import global_conf
from keras.models import model_from_json
from keras.preprocessing.sequence import pad_sequences
from ailib.model.base_model import BaseModel
from mednlp.dao.data_loader import Key2Value
from mednlp.text.vector import Char2Vector


class DiseaseRiskModel(BaseModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_version = 0
        self.model_name = 'disease_risk'
        self.seq_len = 650
        self.model = self.load_model()
        self.c2v = Char2Vector(global_conf.char_vocab_dict_path)
        self.label_dict = Key2Value(
            path=global_conf.disease_risk_dict_path, swap=True).load_dict()

    def load_model(self):
        model_base_path = self.model_path + self.model_name
        model_arch = model_base_path + '.{}.arch'.format(self.model_version)
        model_weight = model_base_path + '.{}.weight'.format(self.model_version)
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        return model

    def generate_sequence(self, query):
        return self.c2v.get_vector(''.join(query))

    def predict(self, query, **kwargs):
        sequences = pad_sequences([self.generate_sequence(query)],
                                  maxlen=self.seq_len)
        prediction = self.model.predict(sequences)[0]
        result, result_dict = [], {}
        for i, score in enumerate(prediction):
            if self.label_dict[i] not in result_dict:
                result_dict[self.label_dict[i]] = 0
            result_dict[self.label_dict[i]] += score
        result_list = [(name, score) for name, score in result_dict.items()]
        result_list.sort(key=lambda item: item[1], reverse=True)
        for r in result_list:
            result.append({'disease': r[0], 'score': r[1]})
        return result


if __name__ == '__main__':
    pass
