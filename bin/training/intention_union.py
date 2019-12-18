#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
char 为主, 加入pinyin 和 char_pos
label 1#2#3,4#4#4,
"""

from keras.layers import Input, Embedding, LSTM, Dense, concatenate, Bidirectional
from keras.models import Model, Sequential
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical
import numpy as np
import keras
import mednlp.dao.data_loader as data_loader
import os
from keras.callbacks import ModelCheckpoint

char_size = 80
pinyin_size = 80
pos_size = 80
classes = 17
# train_file = '/home/renyx/work/model_data/intent_2019/04_09/lstm_union_train_04_09.txt'
# val_file = '/home/renyx/work/model_data/intent_2019/04_09/lstm_union_val_04_09.txt'
train_file = '/home/renyx/work/model_data/intent_2019/08_01/lstm_3_union_train_08_01.txt'
val_file = '/home/renyx/work/model_data/intent_2019/08_01/lstm_3_union_val_08_01.txt'
filepath = '/home/renyx/work/model_bin/intent_19_08_01/intention_union_classify_9.best.weight'


def train(train_file, seg_length, epoch_value):
    char_train, pinyin_train, pos_train, y_train = data_loader.load_data_intention_union(train_file)
    char_val, pinyin_val, pos_val, y_val = data_loader.load_data_intention_union(val_file)

    char_train = pad_sequences(char_train, maxlen=seg_length)
    char_val = pad_sequences(char_val, maxlen=seg_length)

    pinyin_train = pad_sequences(pinyin_train, maxlen=seg_length)
    pinyin_val = pad_sequences(pinyin_val, maxlen=seg_length)

    pos_train = pad_sequences(pos_train, maxlen=seg_length)
    pos_val = pad_sequences(pos_val, maxlen=seg_length)

    y_train = to_categorical(y_train, num_classes=classes)
    y_val = to_categorical(y_val, num_classes=classes)
    char_x = Input((seg_length,), name='char_x')
    pinyin_x = Input((seg_length,), name='pinyin_x')
    pos_x = Input((seg_length,), name='pos_x')

    char_embedding = Embedding(6000, char_size)(char_x)
    pinyin_embedding = Embedding(600, pinyin_size)(pinyin_x)
    pos_embedding = Embedding(6000, pos_size)(pos_x)

    x = concatenate([char_embedding, pinyin_embedding, pos_embedding])
    x = Bidirectional(
        LSTM(char_size + pinyin_size + pos_size, dropout=0.2, recurrent_dropout=0.02, return_sequences=True, implementation=2))(x)
    x = Bidirectional(
        LSTM(char_size + pinyin_size + pos_size, dropout=0.2, recurrent_dropout=0.02, implementation=2))(x)
    output = Dense(classes, activation='softmax')(x)

    model = Model(inputs=[char_x, pinyin_x, pos_x], outputs=[output])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    print(model.summary())
    checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True,
                                 mode='auto', save_weights_only=True)
    model.fit([char_train, pinyin_train, pos_train], y_train, epochs=epoch_value,
              batch_size=128, validation_data=([char_val, pinyin_val, pos_val], y_val), callbacks=[checkpoint])
    # 5 加入了客服数据
    save_model_architecture(model, '/home/renyx/work/model_bin/intent_19_05_22/', 'intention_union', 8)
    # save_model(model, '/home/renyx/work/model_bin/intent_19_04_21/', 'intention_union', 6)


def save_model_architecture(train_model, output_path, model_name, model_version):
    # 存储模型结构
    model_arch = '%s.%s.arch' % (model_name, model_version)
    model_arch_path = os.path.join(output_path, model_arch)
    json_string = train_model.to_json()
    open(model_arch_path, 'w').write(json_string)
    return


def save_model(train_model, output_path, model_name, model_version):
    model_arch = '%s.%s.arch' % (model_name, model_version)
    model_weight = '%s.%s.weight' % (model_name, model_version)
    model_arch_path = os.path.join(output_path, model_arch)
    model_weight_path = os.path.join(output_path, model_weight)
    json_string = train_model.to_json()
    open(model_arch_path, 'w').write(json_string)
    train_model.save_weights(model_weight_path)
    return

if __name__ == '__main__':
    # load_data(train_file)
    train(train_file, 100, 60)
