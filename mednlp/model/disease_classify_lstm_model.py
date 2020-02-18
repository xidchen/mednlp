#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease_classify_lstm_model.py -- the lstm model of disease classification

Author: chenxd <chenxd@guahao.com>
Create on 2018-04-02 Monday
"""

import global_conf
from keras.models import model_from_json
from keras.preprocessing.sequence import pad_sequences
from ailib.model.base_model import BaseModel
from mednlp.dao.data_loader import Key2Value
from mednlp.dataset.padding import pad_sentences
from mednlp.model.utils import normal_probability
from mednlp.text.vector import Char2Vector
from mednlp.text.vector import get_sex_to_vector, get_age_to_vector_for_lstm


class DiseaseClassifyLSTM(BaseModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_version = 144
        self.model_name = 'disease_classify'
        self.model = self.load_model()
        self.char2vector = Char2Vector(global_conf.char_vocab_dict_path)
        self.disease_dict = Key2Value(
            path=global_conf.disease_classify_dict_path, swap=True).load_dict()

    def load_model(self):
        model_base_path = self.model_path + self.model_name
        model_arch = model_base_path + '.{}.arch'.format(self.model_version)
        model_weight = model_base_path + '.{}.weight'.format(self.model_version)
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        return model

    def generate_sequence(self, query, **kwargs):
        """
        生成向量化的序列
        主诉现病史query，检查检验ins，体格检查pe，既往史pmh的序列长度为500，150，100，50
        :param query: str
        :param kwargs: inspection, physical_exam, sex, age, past_history
        :return: words
        """
        seq_len = 500
        sep_len = 2
        ins_len = 150 - sep_len
        pe_len = 100 - sep_len
        sex_and_age_len = 8
        history_len = 50 - sex_and_age_len
        words = self.char2vector.get_vector(query)[:seq_len]
        ins = self.char2vector.get_vector(kwargs.get('inspection'))[:ins_len]
        pe = self.char2vector.get_vector(kwargs.get('physical_exam'))[:pe_len]
        sex = get_sex_to_vector(kwargs.get('sex'))
        age = get_age_to_vector_for_lstm(kwargs.get('age'))
        pmh = self.char2vector.get_vector(kwargs.get('past_history'))
        pmh = pad_sentences([pmh], history_len, value='0',
                            padding='post', truncating='post')[0]
        sep = ['0'] * 2
        words.extend(sep + ins + sep + pe)
        words.extend(sep + [sex] + sep + [age] + sep + pmh)
        return words

    def predict(self, medical_record, **kwargs):
        """
        预测批量序列对应的疾病分类
        每条序列总长度为800
        :param medical_record: list
        :return: result, 格式:
        [{medical_record_id:, diseases:[disease_name:, score:]}]
        """
        total_len = 800
        words_list = []
        for mr in medical_record:
            words = self.generate_sequence(
                query=mr.get('chief_complaint', ''),
                medical_history=mr.get('medical_history', ''),
                inspection=mr.get('inspection', ''),
                physical_exam=mr.get('physical_examination', ''),
                sex=mr.get('sex', ''),
                age=mr.get('age', ''),
                past_history=mr.get('past_medical_history', ''))
            words_list.append(words)
        sequences = pad_sequences(words_list, maxlen=total_len)
        empty_medical_record = [
            i for i, sequence in enumerate(sequences) if not any(sequence)]
        disease_values = self.model.predict(sequences)
        result = []
        for medical_record_id, disease_value in enumerate(disease_values):
            disease = {}
            for i, value in enumerate(disease_value):
                if self.disease_dict[i] not in disease:
                    disease[self.disease_dict[i]] = 0
                disease[self.disease_dict[i]] += value
            normal_probability(disease)
            result_list = [(name, score) for name, score in disease.items()]
            result_list.sort(key=lambda item: item[1], reverse=True)
            if medical_record_id in empty_medical_record:
                result_list = []
            result.append(
                {'medical_record_id': medical_record_id,
                 'diseases': result_list})
        return result


if __name__ == "__main__":
    pass
