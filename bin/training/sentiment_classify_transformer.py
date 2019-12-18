#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentiment_classify_transformer.py -- the training of sentiment classifier

Author: caoxg <caoxg@guahao.com>
Create on 2019-10-19 Saturday
"""

import codecs
import numpy
import tensorflow as tf
import keras.backend.tensorflow_backend as ktf
from keras.layers import Dense, Input, Lambda
from keras.models import Model
from keras.optimizers import Adam
from keras.preprocessing.sequence import pad_sequences
from keras_bert import load_trained_model_from_checkpoint, Tokenizer


max_len = 100
data_dir = '/data/caoxg_data/'
model_dir = '/data/caoxg_model/'
config_path = model_dir + 'bert/chinese_L-12_H-768_A-12/bert_config.json'
checkpoint_path = model_dir + 'bert/chinese_L-12_H-768_A-12/bert_model.ckpt'
dict_path = model_dir + 'bert/chinese_L-12_H-768_A-12/vocab.txt'

negative_data = data_dir + 'traindata/neg_60000.txt'
positive_data = data_dir + 'traindata/pos_60000.txt'


def get_session(gpu_fraction=1):
    gpu_options = tf.GPUOptions(
        per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))

ktf.set_session(get_session())


token_dict = {}
for line in codecs.open(dict_path):
    token_dict[line.strip()] = len(token_dict)


dataset = []
for sentence in codecs.open(negative_data):
    dataset.append((sentence, 0))
for sentence in codecs.open(positive_data):
    dataset.append((sentence, 1))


random_order = range(len(dataset))
numpy.random.shuffle(random_order)
train_data = [dataset[j] for i, j in enumerate(random_order) if i % 10 != 0]
valid_data = [dataset[j] for i, j in enumerate(random_order) if i % 10 == 0]


class OurTokenizer(Tokenizer):
    def _tokenize(self, text):
        r = []
        for c in text:
            if c in self._token_dict:
                r.append(c)
            elif self._is_space(c):
                r.append('[unused1]')
            else:
                r.append('[UNK]')
        return r

tokenizer = OurTokenizer(token_dict)


class DataGenerator:

    def __init__(self, data, batch_size=32):
        self.data = data
        self.batch_size = batch_size
        self.steps = len(self.data) // self.batch_size
        if len(self.data) % self.batch_size != 0:
            self.steps += 1

    def __len__(self):
        return self.steps

    def __iter__(self):
        while True:
            index = range(len(self.data))
            numpy.random.shuffle(index)
            x1_list, x2_list, y_list = [], [], []
            for i in index:
                text = self.data[i][0][:max_len]
                x1, x2 = tokenizer.encode(first=text)
                y = self.data[i][1]
                x1_list.append(x1)
                x2_list.append(x2)
                y_list.append([y])
                if len(x1_list) == self.batch_size or i == index[-1]:
                    x1_list = pad_sequences(x1_list, maxlen=max_len,
                                            padding='post', truncating='post')
                    x2_list = pad_sequences(x2_list, maxlen=max_len,
                                            padding='post', truncating='post')
                    y_list = pad_sequences(y_list, maxlen=max_len,
                                           padding='post', truncating='post')
                    yield [x1_list, x2_list], y_list
                    [x1_list, x2_list, y_list] = [], [], []


bert_model = load_trained_model_from_checkpoint(
    config_path, checkpoint_path, seq_len=None)

for l in bert_model.layers:
    l.trainable = True

x1_in = Input(shape=(None,))
x2_in = Input(shape=(None,))

x = bert_model([x1_in, x2_in])
x = Lambda(lambda s: s[:, 0])(x)
p = Dense(1, activation='sigmoid')(x)

model = Model([x1_in, x2_in], p)
model.compile(
    loss='binary_crossentropy',
    optimizer=Adam(1e-5),
    metrics=['accuracy']
)
model.summary()


train_generator = DataGenerator(train_data)
valid_generator = DataGenerator(valid_data)

model.fit_generator(
    train_generator.__iter__(),
    steps_per_epoch=len(train_generator),
    epochs=5,
    validation_data=valid_generator.__iter__(),
    validation_steps=len(valid_generator)
)
