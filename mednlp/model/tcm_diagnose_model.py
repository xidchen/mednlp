#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-30 Tuesday
@Desc:	中医诊断模型
"""

import sys
from ailib.model.base_model import BaseModel
from keras.preprocessing.sequence import pad_sequences
from keras.models import model_from_json
from mednlp.text.vector import Char2vector, Dept2Vector
import global_conf


class TCMDiagnoseModel(BaseModel):
    def initialize(self, model_version=0, **kwargs):
        self.model_version = model_version
        self.load_model()
        self.char2vector = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
        disease_to_vector = Dept2Vector(global_conf.tcm_disease_path)
        syndrome_to_vector = Dept2Vector(global_conf.tcm_syndrome_path)
        prescription_to_vector = Dept2Vector(global_conf.tcm_prescription_path)
        self.disease_class_name = disease_to_vector.index2name
        self.disease_name_id = disease_to_vector.name2id
        self.syndrome_class_name = syndrome_to_vector.index2name
        self.syndrome_name_id = syndrome_to_vector.name2id
        self.prescription_class_name = prescription_to_vector.index2name
        self.prescription_name_id = prescription_to_vector.name2id

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        disease_model_path = '{}.d.{}'.format(self.model_path, self.model_version)
        syndrome_model_path = '{}.s.{}'.format(self.model_path, self.model_version)
        prescription_model_path = '{}.p.{}'.format(self.model_path, self.model_version)
        disease_model = model_from_json(open(disease_model_path + '.arch').read())
        disease_model.load_weights(disease_model_path + '.weight', by_name=True)
        syndrome_model = model_from_json(open(syndrome_model_path + '.arch').read())
        syndrome_model.load_weights(syndrome_model_path + '.weight', by_name=True)
        prescription_model = model_from_json(open(prescription_model_path + '.arch').read())
        prescription_model.load_weights(prescription_model_path + '.weight', by_name=True)
        self.disease_model = disease_model
        self.syndrome_model = syndrome_model
        self.prescription_model = prescription_model

    def get_char_dict_vector(self, query, num=10):
        """
        :param query: 输入预测文本
        :param num: 词向量长度
        :return: 词向量
        """
        if not sys.version > '3':
            query = unicode(query).decode('utf-8')
        words = self.char2vector.get_char_vector(query)
        p = 0
        words_list = []
        while len(words[p:p + num]) == num:
            words_list.append(words[p:p + num])
            p += num
        if p != len(words):
            words_list.append(words[p:len(words)])
        return words_list

    def _predict(self, model, query):
        predict_results = model.predict(query)
        return sum(predict_results)

    def _add_entity_info(self, predict_result, class_to_name, name_to_id):
        res = []
        for i, v in enumerate(predict_result):
            res.append({'id': i, 'score': v, 'entity_name': class_to_name[i], 'entity_id': name_to_id[class_to_name[i]]})
        return res

    def _normal(self, result):
        score_sum = sum(map(lambda x: x['score'], result))
        if score_sum != 0:
            for item in result:
                item['score'] = item['score'] / score_sum
        return result

    def _sort(self, predict_result):
        return sorted(predict_result, key=lambda s: s['score'], reverse=True)

    def filter_disease(self, diseases, age, sex):
        if str(sex) == '2' or (0 < age < 5475 or age > 21900):
            for disease in diseases:
                if disease['entity_name'] == '崩漏':
                    disease['score'] = 0
                if disease['entity_name'] == '闭经':
                    disease['score'] = 0
        return diseases

    def predict_syndrome(self, disease_class, query_pad, num=600):
        disease_list = [[disease_class]]
        disease_pad = pad_sequences(disease_list, maxlen=num)
        predict_result = self._predict(self.syndrome_model, [disease_pad, query_pad])
        result = self._add_entity_info(predict_result, self.syndrome_class_name, self.syndrome_name_id)
        result = self._sort(result)
        return result

    def predict_prescription(self, disease_class, syndrome_class, query_pad, num=600):
        disease_list = [[disease_class]]
        disease_pad = pad_sequences(disease_list, maxlen=num)
        syndrome_list = [[syndrome_class]]
        syndrome_pad = pad_sequences(syndrome_list, maxlen=num)
        predict_result = self._predict(self.prescription_model, [disease_pad, syndrome_pad, query_pad])
        result = self._add_entity_info(predict_result, self.prescription_class_name, self.prescription_name_id)
        result = self._sort(result)
        return result

    def predict(self, query, age, sex, rows=3, num=600):
        words_list = self.get_char_dict_vector(query, num=num)
        if not words_list:
            return []
        disease_pad = pad_sequences(words_list, maxlen=num)
        disease_result = self._predict(self.disease_model, disease_pad)
        disease_result = self._add_entity_info(disease_result, self.disease_class_name, self.disease_name_id)
        disease_result = self.filter_disease(disease_result, age, sex)
        disease_result = self._normal(disease_result)
        if disease_result:
            disease_result = self._sort(disease_result)[:rows]
            for dr in disease_result[:rows]:
                syndromes_result = self.predict_syndrome(dr['id'], disease_pad)
                if syndromes_result:
                    syndromes_result = syndromes_result[:5]
                dr['syndromes'] = syndromes_result
                for i, sr in enumerate(syndromes_result):
                    prescription = self.predict_prescription(dr['id'], sr['id'], disease_pad)
                    dr['syndromes'][i]['prescription'] = prescription[:5]
        return disease_result


if __name__ == '__main__':
    model = TCMDiagnoseModel(cfg_path=global_conf.cfg_path, model_section='TCM_DIAGNOSE_MODEL')
    print(model.predict('浮肿,浮肿 消退'))
