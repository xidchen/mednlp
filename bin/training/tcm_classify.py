# ！/usr/bin/env python
# -*- coding：utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-30 Tuesday
@Desc:	中医诊断训练
"""

import os
import sys
from optparse import OptionParser
# import global_conf
import tensorflow as tf
from keras.layers.embeddings import Embedding
from keras.models import Sequential
from keras.layers import Dense, Bidirectional
import mednlp.dao.data_loader as data_loader
from keras.layers import LSTM
import keras.backend.tensorflow_backend as ktf
from base_trainer import BaseTrainer


def get_session(gpu_fraction=1):
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


ktf.set_session(get_session())


class TCMCharModel(BaseTrainer):
    def __init__(self, file_number=2970861):
        super(TCMCharModel, self).__init__(model_name='tcm_diagnose')
        self.file_number = file_number
        self.classes = 10
        self.epoch_num = 100

    def origin_model(self):
        """
        嵌入层+两层lstm
        :return: model
        """
        model = Sequential()
        model.add(Embedding(6000, 16))
        model.add(Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True)))
        model.add(Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02)))
        model.add(Dense(self.classes, activation='softmax'))
        return model

    def train_model(self, model, data_file_path, ratio=0.9):
        """
        :param model: 需要训练和编译的模型
        :param data_file_path: 训练数据存放路径
        :param ratio: 使用多少数据作为训练数据
        :return: 训练以后的模型
        """
        X, Y = data_loader.get_test_data(data_file_path, num=37, classes=self.classes)
        train_data_num = int(len(X) * ratio)
        x_train, y_train = X[:train_data_num], Y[:train_data_num]
        x_test, y_test = X[train_data_num:], Y[train_data_num:]
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=512, epochs=self.epoch_num,
                  verbose=1, callbacks=[self.model_checkpoint])
        return model

    def save_model(self, model, version=835):
        """
        :param model: 需要保存的模型
        :param version: 模型保存版本
        :return: 无
        """
        model_arch = '%s.%s.arch' % (self.model_name, version)
        model_weight = '%s.%s.weight' % (self.model_name, version)
        model_arch_path = os.path.join('.', model_arch)
        model_weight_path = os.path.join('.', model_weight)

        # 保存神经网络的结构与训练好的参数
        json_string = model.to_json()
        open(model_arch_path, 'w').write(json_string)
        model.save_weights(model_weight_path)
        return


if __name__ == '__main__':
    command = '\npython %s [-t trainfile -v version]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-v', dest='version', help='the version of model')
    parser.add_option('--trainfile', dest='trainfile', help='the trainfile of train')
    (options, args) = parser.parse_args()

    pinyin_model = TCMCharModel()
    model = pinyin_model.origin_model()
    model = pinyin_model.train_model(model, options.trainfile)
    pinyin_model.save_model(model, version=options.version)
