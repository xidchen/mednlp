#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentiment_classify_lstm.py -- the LSTM training of sentiment classifier

Author: chenxd <chenxd@guahao.com>
Create on 2019-04-30 Tuesday
"""

import os
import sys
import codecs
import global_conf
import tensorflow as tf
import keras.backend.tensorflow_backend as ktf
import mednlp.dao.data_loader as data_loader
from optparse import OptionParser
from keras.callbacks import ModelCheckpoint
from keras.layers import LSTM, Dense, Bidirectional
from keras.layers.embeddings import Embedding
from keras.models import Sequential, model_from_json
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical


def get_session(gpu_fraction=1):
    gpu_options = tf.GPUOptions(
        per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


def generate_train_data(train_file, batch_size, seq_length, classes):
    cnt = 0
    while 1:
        x_train, y_train = [], []
        for row in codecs.open(train_file):
            x, y = data_loader.process_line(row)
            x_train.append(x)
            y_train.append(y)
            cnt += 1
            if cnt == batch_size:
                x_train = pad_sequences(x_train, maxlen=seq_length)
                y_train = to_categorical(y_train, num_classes=classes)
                yield (x_train, y_train)
                x_train, y_train = [], []
                cnt = 0


def train(train_part_file, valid_part_file, seq_length,
          epoch_value, classes, batch_size):
    n_words = 6000
    train_set_length = sum(1 for _ in open(train_part_file))
    valid_x, valid_y = data_loader.load_file(valid_part_file)
    x_valid = pad_sequences(valid_x, maxlen=seq_length)
    y_valid = to_categorical(valid_y, num_classes=classes)
    train_model = Sequential()
    train_model.add(Embedding(n_words, 100))
    train_model.add(Bidirectional(
        LSTM(100, dropout=0.2, recurrent_dropout=0.02, implementation=2,
             return_sequences=True)))
    train_model.add(Bidirectional(
        LSTM(100, dropout=0.2, recurrent_dropout=0.02, implementation=2)))
    train_model.add(Dense(classes, activation='softmax'))
    train_model.compile(optimizer='adam',
                        loss='categorical_crossentropy', metrics=['accuracy'])
    train_model.fit_generator(generate_train_data(train_part_file, batch_size,
                                                  seq_length, classes),
                              steps_per_epoch=train_set_length // batch_size,
                              epochs=epoch_value,
                              callbacks=[checkpoint],
                              validation_data=(x_valid, y_valid))
    return train_model


def train_incremental(train_part_file, valid_part_file, seq_length,
                      epoch_value, base_version, classes, batch_size):
    train_set_length = sum(1 for _ in open(train_part_file))
    valid_x, valid_y = data_loader.load_file(valid_part_file)
    x_valid = pad_sequences(valid_x, maxlen=seq_length)
    y_valid = to_categorical(valid_y, num_classes=classes)
    train_model = load_model(base_version)
    train_model.compile(optimizer='adam',
                        loss='categorical_crossentropy', metrics=['accuracy'])
    train_model.fit_generator(generate_train_data(train_part_file, batch_size,
                                                  seq_length, classes),
                              steps_per_epoch=train_set_length // batch_size,
                              epochs=epoch_value,
                              callbacks=[checkpoint],
                              validation_data=(x_valid, y_valid))
    return train_model


def load_model(model_version):
    """加载已经存在的模型，其中version为版本号"""
    model_base_path = global_conf.training_path + name
    model_path = model_base_path + '.{}.arch'
    model_arch = model_path.format(model_version)
    model_weight_path = model_base_path + '.{}.weight'
    model_weight = model_weight_path.format(model_version)
    train_model = model_from_json(open(model_arch).read())
    train_model.load_weights(model_weight, by_name=True)
    return train_model


def save_model(train_model, output_path, model_name, model_version):
    """保存模型"""
    model_arch = '{}.{}.arch'.format(model_name, model_version)
    model_weight = '{}.{}.weight'.format(model_name, model_version)
    model_arch_path = os.path.join(output_path, model_arch)
    model_weight_path = os.path.join(output_path, model_weight)
    json_string = train_model.to_json()
    open(model_arch_path, 'w').write(json_string)
    train_model.save_weights(model_weight_path)
    return


if __name__ == '__main__':
    ktf.set_session(get_session())
    command = '\n python {} [-d dir -o output -v version]'.format(sys.argv[0])
    parser = OptionParser(usage=command)
    parser.add_option('-t', '--train', dest='train', help='file to be trained')
    parser.add_option('-d', '--dir', dest='directory', help='temporary directory')
    parser.add_option('-v', '--version', dest='version', help='model version')
    parser.add_option('-m', '--model', dest='name', help='model name')
    parser.add_option('-o', '--output', dest='output', help='output directory')
    parser.add_option('-l', '--len', dest='length', help='segmentation length')
    parser.add_option('-e', '--epoch', dest='epoch', help='epoch value')
    parser.add_option('-b', '--base', dest='base', help='base model')
    (options, args) = parser.parse_args()
    version = ''
    name = 'sentiment_classify'
    path = global_conf.training_path
    model = None
    length = 100
    epoch = 5
    categories = 2
    batch = 500
    if options.version:
        version = options.version
    if options.name:
        name = options.name
    if options.output:
        path = options.output
    best_model_name = '{}.best.{}.weight'.format(name, version)
    best_model_path = path + best_model_name
    checkpoint = ModelCheckpoint(best_model_path,
                                 monitor='val_acc', verbose=1, mode='max',
                                 save_best_only=True, save_weights_only=True)
    if options.length:
        length = int(options.length)
    if options.epoch:
        epoch = int(options.epoch)
    if options.directory and not options.base:
        directory = options.directory
        if directory[-1] != '/':
            directory += '/'
        if directory[0] != '/':
            directory = global_conf.RELATIVE_PATH + directory
        train_part = directory + 'temp_train_' + version + '.txt'
        valid_part = directory + 'temp_valid_' + version + '.txt'
        model = train(
            train_part, valid_part, length, epoch, categories, batch)
    if options.base:
        base = options.base
        directory = options.directory
        if directory[-1] != '/':
            directory += '/'
        if directory[0] != '/':
            directory = global_conf.RELATIVE_PATH + directory
        train_part = directory + 'temp_train_' + version + '.txt'
        valid_part = directory + 'temp_valid_' + version + '.txt'
        model = train_incremental(
            train_part, valid_part, length, epoch, base, categories, batch)
    save_model(model, path, name, version)
    print('Model is available!')
