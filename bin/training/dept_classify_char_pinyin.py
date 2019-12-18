#!/usr/bin/env python
# increase_model -*- coding: utf-8 -*-

"""
@Author: chaipf
@Email: chaipf@guahao.com
@Date: 2019-05-16
@Desc: the LSTM training of dept classifier
"""
import os
import sys
# from keras.models import Sequential
from keras.models import Model
from keras.layers import Input, Bidirectional, LSTM, Dense
from keras.layers.embeddings import Embedding
from keras.layers import concatenate
from keras.models import load_model
from keras.utils.np_utils import to_categorical
from keras.preprocessing.sequence import pad_sequences
from keras.callbacks import ModelCheckpoint, Callback
# from keras.models import model_from_json
import tensorflow as tf
import keras.backend.tensorflow_backend as ktf
import mednlp.dao.data_loader as data_loader
from optparse import OptionParser


def get_session(gpu_fraction=1):
    gpu_options = tf.GPUOptions(
        per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


save_file_name = '/data/home/fangcheng/data/resource/dept/model-e{epoch:03d}-l{loss:.3f}.h5'
checkpoint = ModelCheckpoint(filepath=save_file_name, monitor='val_categorical_accuracy', mode='auto',
                             save_best_only='True')


class BatchSaver(Callback):
    def __init__(self, output_path, batch_per_save=5000):
        super(BatchSaver, self).__init__()
        self.output_path = output_path
        self.save_ellipse = batch_per_save

    def on_batch_end(self, batch, logs=None):
        if batch % self.save_ellipse == 0 and batch > 0:
            self.model.save(self.output_path)
            print('model has saved: {}'.format(self.output_path))


class CharPinyinMergeModel(object):
    def __init__(self):
        self.class_num = 45
        self.char_num = 8000
        self.pinyin_num = 500
        self.seq_num = 100

    def make_model(self, model_index=0):
        if model_index == 1:
            char_input = Input(shape=(100,))
            pinyin_input = Input(shape=(100,))
            char_embedding = Embedding(self.char_num, 32)(char_input)
            char_lstm1 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True))(
                char_embedding)
            char_lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(char_lstm1)

            pinyin_embedding = Embedding(self.pinyin_num, 16)(pinyin_input)
            pinyin_lstm1 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True))(
                pinyin_embedding)
            pinyin_lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(pinyin_lstm1)

            merge_lstm = concatenate([char_lstm2, pinyin_lstm2])
            out = Dense(self.class_num, activation='softmax')(merge_lstm)
            model = Model(input=[char_input, pinyin_input], outputs=out)
        else:
            char_input = Input(shape=(100,))
            pinyin_input = Input(shape=(100,))
            char_embedding = Embedding(self.char_num, 32)(char_input)
            pinyin_embedding = Embedding(self.pinyin_num, 16)(pinyin_input)
            embedding = concatenate([char_embedding, pinyin_embedding])

            lstm1 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True))(embedding)
            lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(lstm1)
            out = Dense(self.class_num, activation='softmax')(lstm2)
            model = Model(input=[char_input, pinyin_input], outputs=out)
        return model

    def make_train_input(self, char_file_name, pinyin_file_name):
        char_train_set, char_valid_set = data_loader.load_data_dept_classify(path=char_file_name, valid_portion=0.01)
        print('train file line num is: {}'.format((len(char_train_set[0]))))
        char_train_x, char_train_y = char_train_set
        char_valid_x, char_valid_y = char_valid_set
        char_x_train = pad_sequences(char_train_x, maxlen=self.seq_num)
        char_x_valid = pad_sequences(char_valid_x, maxlen=self.seq_num)
        char_y_train = to_categorical(char_train_y, num_classes=self.class_num)
        char_y_valid = to_categorical(char_valid_y, num_classes=self.class_num)

        pinyin_train_set, pinyin_valid_set = data_loader.load_data_dept_classify(path=pinyin_file_name,
                                                                                 valid_portion=0.01)
        pinyin_train_x, pinyin_train_y = pinyin_train_set
        pinyin_valid_x, pinyin_valid_y = pinyin_valid_set
        assert (len(char_train_y) == len(pinyin_train_y))
        assert (len(char_valid_y) == len(pinyin_valid_y))
        pinyin_x_train = pad_sequences(pinyin_train_x, maxlen=self.seq_num)
        pinyin_x_valid = pad_sequences(pinyin_valid_x, maxlen=self.seq_num)

        return ([char_x_train, pinyin_x_train], char_y_train), ([char_x_valid, pinyin_x_valid], char_y_valid)

    def train(self, char_file_name, pinyin_file_name, model_type):
        (train_x, train_y), (valid_x, valid_y) = self.make_train_input(char_file_name, pinyin_file_name)
        model = self.make_model(model_type)
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit(train_x, train_y, batch_size=512, epochs=20, validation_data=(valid_x, valid_y),
                  callbacks=[checkpoint])
        return model

    def increate_train(self, increase_model, char_file_name, pinyin_file_name):
        (train_x, train_y), (valid_x, valid_y) = self.make_train_input(char_file_name, pinyin_file_name)
        model = load_model(increase_model)
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit(train_x, train_y, batch_size=512, epochs=20, validation_data=(valid_x, valid_y),
                  callbacks=[checkpoint])
        return model

    def save_model(self, model, output_path):
        arch_path = os.path.join(output_path, 'dept.arch')
        weight_path = os.path.join(output_path, 'dept.weight')
        # arch_name = "dept_classify.{}.arch".format(version)
        # weight_name = "dept_classify.{}.weight".format(version)
        json_string = model.to_json()
        open(arch_path, 'w').write(json_string)
        model.save_weights(weight_path)


def train():
    # ktf.set_session(get_session())
    command = '\npython %s [--input_pinyin trainfile]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('--input_char', dest='input_char', help='the version of model')
    parser.add_option('--input_pinyin', dest='input_pinyin', help='the version of model')
    parser.add_option('--increase_model', dest='increase_model', help='the version of model')
    parser.add_option('--model_type', dest='model_type', help='the version of model')

    (options, args) = parser.parse_args()
    if options.input_char:
        input_char_file = options.input_char
    else:
        input_char_file = '/data/home/fangcheng/data/mednlp/dept/mini_chai/char.txt'

    if options.input_pinyin:
        input_pinyin_file = options.input_pinyin
    else:
        input_pinyin_file = '/data/home/fangcheng/data/mednlp/dept/mini_chai/pinyin.txt'

    if options.model_type:
        model_type = options.model_type
    else:
        model_type = 0

    cp = CharPinyinMergeModel()
    ([char_x_train, pinyin_x_train], char_y_train), ([char_x_valid, pinyin_x_valid], char_y_valid) \
        = cp.make_train_input(input_char_file, input_pinyin_file)

    return ([char_x_train, pinyin_x_train], char_y_train), ([char_x_valid, pinyin_x_valid], char_y_valid)


if __name__ == '__main__':
    # ktf.set_session(get_session())
    command = '\npython %s [--input_pinyin trainfile]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('--input_char', dest='input_char', help='the version of model')
    parser.add_option('--input_pinyin', dest='input_pinyin', help='the version of model')
    parser.add_option('--increase_model', dest='increase_model', help='the version of model')
    parser.add_option('--model_type', dest='model_type', help='the version of model')

    (options, args) = parser.parse_args()
    if options.input_char:
        input_char_file = options.input_char
    else:
        input_char_file = '/data/home/fangcheng/data/mednlp/dept/mini_chai/char.txt'

    if options.input_pinyin:
        input_pinyin_file = options.input_pinyin
    else:
        input_pinyin_file = '/data/home/fangcheng/data/mednlp/dept/mini_chai/pinyin.txt'

    cp = CharPinyinMergeModel()
    if options.model_type:
        model_type = options.model_type
    else:
        model_type = 0

    if options.increase_model:
        model = cp.increate_train(options.increase_model, input_char_file, input_pinyin_file)
    else:
        model = cp.train(input_char_file, input_pinyin_file, model_type)
    output_path = '/data/home/fangcheng/data/resource/dept'
    cp.save_model(model, output_path)
