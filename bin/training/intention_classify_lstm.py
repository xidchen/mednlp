#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease_classify_lstm.py -- the LSTM training of disease classifier

Author: chenxd <chenxd@guahao.com>
Create on 2018-04-02 Monday
"""

import os
import sys
import global_conf
import mednlp.dao.data_loader as data_loader
import tensorflow as tf
import keras.backend.tensorflow_backend as ktf
from optparse import OptionParser
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical
from keras.layers.embeddings import Embedding
from keras.models import Sequential, model_from_json
from keras.layers import LSTM, Dense, Bidirectional


def get_session(gpu_fraction=0.4):
    gpu_options = tf.GPUOptions(
        per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


def train(train_file, seg_length, epoch_value):
    n_words = 6000
    classes = 17
    train_set, test_set = data_loader.load_data_intention_classify(
        path=train_file, n_words=n_words, valid_portion=0.1, sort_by_len=True)
    train_x, train_y = train_set
    test_x, test_y = test_set
    x_train = pad_sequences(train_x, maxlen=seg_length)
    x_test = pad_sequences(test_x, maxlen=seg_length)
    y_train = to_categorical(train_y, num_classes=classes)
    y_test = to_categorical(test_y, num_classes=classes)
    print('x_train shape:', x_train.shape)
    print('x_test shape:', x_test.shape)
    print('y_train shape:', y_train.shape)
    print('y_test shape:', y_test.shape)
    train_model = Sequential()
    train_model.add(Embedding(n_words, 80))
    train_model.add(Bidirectional(
        LSTM(128, dropout=0.2, recurrent_dropout=0.02,
             return_sequences=True, implementation=2)))
    train_model.add(Bidirectional(
        LSTM(128, dropout=0.2, recurrent_dropout=0.02, implementation=2)))
    train_model.add(Dense(classes, activation='softmax'))
    train_model.compile(optimizer='adam',
                        loss='categorical_crossentropy', metrics=['accuracy'])
    train_model.fit(x_train, y_train, epochs=epoch_value,
                    batch_size=128, validation_data=(x_test, y_test))
    return train_model


def train_incremental(train_file, seg_length, epoch_value, base_version):
    n_words = 6000
    classes = 17
    train_set, test_set, _ = data_loader.load_data_intention_classify(
        path=train_file, n_words=n_words, valid_portion=0.1, sort_by_len=True)
    train_x, train_y = train_set
    test_x, test_y = test_set
    x_train = pad_sequences(train_x, maxlen=seg_length)
    x_test = pad_sequences(test_x, maxlen=seg_length)
    y_train = to_categorical(train_y, num_classes=classes)
    y_test = to_categorical(test_y, num_classes=classes)
    print('x_train shape:', x_train.shape)
    print('x_test shape:', x_test.shape)
    print('y_train shape:', y_train.shape)
    print('y_test shape:', y_test.shape)
    train_model = load_model(base_version)
    train_model.compile(optimizer='adam',
                        loss='categorical_crossentropy', metrics=['accuracy'])
    train_model.fit(x_train, y_train, epochs=epoch_value,
                    batch_size=128, validation_data=(x_test, y_test))
    return train_model


def load_model(model_version):
    """加载已经存在的模型,其中version为版本号"""
    model_base_path = global_conf.training_path + 'intention_classify'
    model_path = model_base_path + '.' + '%s' + '.arch'
    model_arch = model_path % model_version
    model_weight_path = model_base_path + '.' + '%s' + '.weight'
    model_weight = model_weight_path % model_version
    train_model = model_from_json(open(model_arch).read())
    train_model.load_weights(model_weight, by_name=True)
    return train_model


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
    ktf.set_session(get_session())
    command = '\npython %s [-t train -v version -m model]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-t', '--train', dest='train', help='the file to be trained', metavar='FILE')
    parser.add_option('-v', '--version', dest='version', help='the model version')
    parser.add_option('-m', '--model', dest='name', help='the model name')
    parser.add_option('-o', '--output', dest='output', help='the output directory')
    parser.add_option('-l', '--len', dest='length', help='the segmentation length')
    parser.add_option('-e', '--epoch', dest='epoch', help='the epoch value')
    parser.add_option('-b', '--base', dest='base', help='the base model')
    (options, args) = parser.parse_args()
    version = 0
    name = 'intention_classify'
    path = '.'
    length = 100
    epoch = 70
    if options.version:
        version = options.version
    if options.name:
        name = options.name
    if options.output:
        path = options.output
    if options.length:
        length = int(options.length)
    if options.epoch:
        epoch = int(options.epoch)
    if not options.base:
        model = train(options.train, length, epoch)
    else:
        base = options.base
        model = train_incremental(options.train, length, epoch, base)
    save_model(model, path, name, version)
    print('Model is available!')
