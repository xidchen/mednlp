#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease_classify_cnn_model.py -- the cnn model of disease classification

Author: chenxd <chenxd@guahao.com>
Create on 2018-05-07 Monday
"""

import numpy
import codecs
import global_conf
from keras.models import load_model
from ailib.model.base_model import BaseModel
from mednlp.dao.data_loader import Key2Value
from mednlp.dataset.padding import pad_sentences
from mednlp.model.utils import normal_probability


class DiseaseClassifyCNN(BaseModel):

    def initialize(self, **kwargs):
        """
        初始化模型,词典
        """
        self.model_version = 33
        self.model = self.load_model()
        self.w2i = {}
        for row in codecs.open(global_conf.vocab_dict_path):
            r = str(row).strip().split('\t')
            if len(r) == 2:
                self.w2i[r[0]] = int(r[1])
        self.disease_dict = Key2Value(
            path=global_conf.disease_classify_dict_path, swap=True).load_dict()

    def load_model(self):
        """
        加载已经存在的模型,其中version为版本号
        """
        version = self.model_version
        model_base_path = self.model_path + 'disease_classify_cnn'
        model_path = model_base_path + '.' + '%s' + '.model'
        model_name = model_path % version
        model = load_model(model_name)
        return model

    def generate_sequence(self, sens):
        """
        生成向量化的序列
        :param sens: list
        :return: sens: list
        """
        sequence_length = 50
        sens = [s.split(',') for s in sens]
        sens = [[self.w2i[w] for w in s if w in self.w2i] for s in sens]
        sens = pad_sentences(sens, sequence_length, value=0)
        return sens

    def predict(self, medical_record, **kwargs):
        """
        预测批量序列对应的疾病分类
        :param medical_record: list
        :return: result, 格式:
        [{medical_record_id:, diseases:[disease_name:, score:]}]
        """
        sequences = []
        for mr in medical_record:
            sequences.append(mr.get('query', ''))
        sequences = self.generate_sequence(sequences)
        empty_medical_record = [
            i for i, sequence in enumerate(sequences) if not any(sequence)]
        disease_values = self.model.predict(numpy.array(sequences))
        rows = kwargs.get('rows')
        result = []
        for medical_record_id, disease_value in enumerate(disease_values):
            disease = {}
            for i, value in enumerate(disease_value):
                if self.disease_dict.get(i) not in disease:
                    disease[self.disease_dict.get(i)] = 0
                disease[self.disease_dict.get(i)] += value
            normal_probability(disease)
            result_list = [(name, score) for name, score in disease.items()]
            result_list.sort(key=lambda item: item[1], reverse=True)
            if medical_record_id in empty_medical_record:
                result_list = []
            result.append(
                {'medical_record_id': medical_record_id,
                 'diseases': result_list[:rows]})
        return result


if __name__ == "__main__":
    pass
