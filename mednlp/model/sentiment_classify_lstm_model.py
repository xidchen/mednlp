#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentiment_classify_lstm_model.py -- the lstm model of sentiment classification

Author: chenxd <chenxd@guahao.com>
Create on 2019-04-25 Thursday
"""

import global_conf
from keras.models import model_from_json
from mednlp.text.vector import Char2vector
from ailib.model.base_model import BaseModel
from mednlp.model.utils import normal_probability
from keras.preprocessing.sequence import pad_sequences


class SentimentClassifyLSTM(BaseModel):

    def initialize(self, **kwargs):
        """
        初始化模型,词典
        """
        self.model_version = 8
        self.model = self.load_model()
        self.char2vector = Char2vector(global_conf.char_vocab_dict_path)
        self.sentiment_dict = {0: 'negative', 1: 'positive'}

    def load_model(self):
        """
        加载已经存在的模型,其中version为版本号
        """
        version = self.model_version
        model_base_path = self.model_path + 'sentiment_classify'
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        return model

    def generate_sequence(self, query):
        """
        生成向量化的序列
        """
        seq_len = 100
        words = self.char2vector.get_vector(query)[:seq_len]
        return words

    def predict(self, query, **kwargs):
        """
        预测批量序列对应的情感分类
        每条序列总长度为100
        :param query: list
        :return: result, 格式:
        [{query_id:, positive: score, negative: score}]
        """
        total_len = 100
        words_list = []
        for q in query:
            words = self.generate_sequence(query=q.get('query', ''))
            words_list.append(words)
        sequences = pad_sequences(words_list, maxlen=total_len)
        empty_query = [
            i for i, sequence in enumerate(sequences) if not any(sequence)]
        sentiment_values = self.model.predict(sequences)
        result = []
        for query_id, sentiment_value in enumerate(sentiment_values):
            sentiment = {}
            for i, value in enumerate(sentiment_value):
                if self.sentiment_dict[i] not in sentiment:
                    sentiment[self.sentiment_dict[i]] = 0
                sentiment[self.sentiment_dict[i]] += value
            normal_probability(sentiment)
            sentiments = {'query_id': query_id}
            for name, score in sentiment.items():
                if query_id in empty_query:
                    continue
                sentiments[name] = score
            result.append(sentiments)
        return result


if __name__ == "__main__":
    pass
