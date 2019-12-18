#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
intelligence_service_check_char.py
"""


import os
import sys
from optparse import OptionParser
from keras.layers.embeddings import Embedding
from keras.models import Sequential
from keras.layers import Dense, Bidirectional
import mednlp.dao.data_loader as data_loader
from keras.layers import LSTM
from keras.models import model_from_json
from mednlp.model.AttentionLayer import AttentionLayer
from mednlp.dept.utils.rules import get_file_rows, check_train_path
# from mednlp.model.rules import get_file_rows, check_train_path
from base_trainer import BaseTrainer

embedding_dim = 32
sequence_length = 600
max_nb_words = 8000
classes = 2
batch_size = 128
num_epoches = 50
n_words = max_nb_words


class CharModel(BaseTrainer):
    def __init__(self, file_number=2970812):
        super(CharModel, self).__init__(model_name='model_intelligence_service_check')
        self.file_number = file_number
        self.classes = 2
        self.epoch_num = 5

    def origin_model(self):
        """
        嵌入层+两层lstm
        :return: model
        """
        model = Sequential()
        model.add(Embedding(n_words, 32))
        model.add(Bidirectional(LSTM(64, dropout=0.5, recurrent_dropout=0.2, return_sequences=True)))
        model.add(Bidirectional(LSTM(64, dropout=0.5, recurrent_dropout=0.2)))
        model.add(Dense(classes, activation='softmax'))
        return model

    # def train_model(self, x_train, y_train, x_test, y_test, model):
        # """
        # :param x_train: 训练数据x
        # :param y_train: 训练数据y
        # :param x_test: 测试数据x
        # :param y_test: 测试数据y
        # :param model: 需要训练和编译的模型
        # :return: 训练以后的模型
        # """
        # model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        # model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=batch_size, epochs=num_epoches,
                  # verbose=1)
        # return model

    def train_model(self, model, data_file_path, ratio=0.9):
        """
        :param model: 需要训练和编译的模型
        :param data_file_path: 训练数据存放路径
        :param ratio: 使用多少数据作为训练数据
        :return: 训练以后的模型
        """
        X, Y = data_loader.get_test_data(data_file_path, num=sequence_length, classes=self.classes)
        train_data_num = int(len(X) * ratio)
        x_train, y_train = X[:train_data_num], Y[:train_data_num]
        x_test, y_test = X[train_data_num:], Y[train_data_num:]
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=batch_size, epochs=self.epoch_num,
                  verbose=1, callbacks=[self.model_checkpoint])
        return model

    def train_generator_model(self, train_file, x_test, y_test, model):
        """
        :param train_file: 训练数据路径
        :param x_test: x测试数据
        :param y_test: y测试数据
        :param model: 需要训练的模型
        :return: 训练以后的模型
        """
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, num=600, classes=2),
                            steps_per_epoch=int(self.file_number/batch_size),  epochs=num_epoches, max_q_size=1,
                            validation_data=(x_test, y_test))
        return model

    def load_model(self, model_version):
        """
        加载已经存在的模型,其中version为版本号
        :param model_version: 模型版本
        :return: 返回加载好的数据
        """
        version = model_version
        model_base_path = '/home/caoxg/work/mednlp/bin/training/model_dept_classify'
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        # model = model_from_json(open(model_arch).read())
        model = model_from_json(open(model_arch).read(), {'AttentionLayer': AttentionLayer})
        model.load_weights(model_weight, by_name=True)
        return model

    def save_model(self, model, outpath='.', version=835):
        """
        :param model: 需要保存的模型
        :param outpath: 模型保存路径
        :param model_name: 模型保存名字
        :param version: 模型保存版本
        :return: 无
        """
        model_arch = '%s.%s.arch' % (self.model_name, version)
        model_weight = '%s.%s.weight' % (self.model_name, version)
        model_arch_path = os.path.join(outpath, model_arch)
        model_weight_path = os.path.join(outpath, model_weight)
        # 保存神经网络的结构与训练好的参数
        json_string = model.to_json()
        open(model_arch_path, 'w').write(json_string)
        model.save_weights(model_weight_path)
        return


if __name__ == '__main__':
    command = '\npython %s [-t trainfile -v version -m model]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('--trainfile', dest='train_file', help='the trainfile of train')
    parser.add_option('-v', '--version', dest='version', default='0', help='model version')
    (options, args) = parser.parse_args()
    train_file = options.train_file

    char_model = CharModel()
    model = char_model.origin_model()
    model = char_model.train_model(model, train_file)
    char_model.save_model(model, version=options.version)
