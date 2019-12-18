# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/4/3 11:07
# @Auther:caoxg@<caoxg@guahao.com>
# @File:intelligence_service.py

from optparse import OptionParser
import os
import sys
from keras.layers.embeddings import Embedding
from keras.models import Sequential
from keras.layers import Dense, Bidirectional
import mednlp.dao.data_loader as data_loader
from keras.layers import LSTM
from keras.models import model_from_json
import tensorflow as tf
import keras.backend.tensorflow_backend as ktf
import global_conf
from mednlp.model.AttentionLayer import AttentionLayer
from mednlp.dept.utils.rules import get_file_rows, check_train_path
from base_trainer import BaseTrainer


def get_session(gpu_fraction=1):
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


ktf.set_session(get_session())
embedding_dim = 16
sequence_length = 37
max_nb_words = 500
classes = 363
batch_size = 512
num_epoches = 30
n_words = max_nb_words
base_path = global_conf.train_data_path


class PinyinModel(BaseTrainer):
    def __init__(self, file_number=2970861):
        super(PinyinModel, self).__init__(model_name='similarity_faq_pinyin')
        self.file_number = file_number
        self.classes = 401
        self.epoch_num = 30

    def origin_model(self):
        """
        嵌入层+两层lstm
        :return: model
        """
        model = Sequential()
        model.add(Embedding(n_words, embedding_dim))
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
        model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=batch_size, epochs=self.epoch_num,
                  verbose=1, callbacks=[self.model_checkpoint])
        return model

    def train_generator_model(self, train_file, x_test, y_test, model):
        """
        :param train_file: 训练数据路径
        :param x_test: x测试数据
        :param y_test: y测试数据
        :param model: 训练以后的模型
        :return: model
        """
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, num=37, classes=363),
                            steps_per_epoch=int(self.file_number/batch_size),  epochs=num_epoches, max_q_size=1,
                            validation_data=(x_test, y_test))
        return model

    def train_generate_increate(self, train_file, x_test, y_test):
        """
        :param train_file: 训练数据路径
        :param x_test: x测试数据
        :param y_test: y测试数据
        :return: model
        """
        model = self.load_model(2039)
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, num=37, classes=363),
                            steps_per_epoch=int(self.file_number / batch_size), epochs=10, max_q_size=1,
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

    def train_model_increase(self, x_train, y_train, x_test, y_test):
        """
        :param x_train: 训练数据x
        :param y_train: 训练数据y
        :param x_test: 测试数据x
        :param y_test: 测试数据y
        :return: 返回已经增量训练后的模型
        """
        model = self.load_model(820)
        model.compile(optimizer='adam', loss='categorical_crossentropy',
                      metrics=['categorical_accuracy'])
        model.fit(x_train, y_train, epochs=20, batch_size=batch_size, validation_data=(x_test, y_test), verbose=1)
        return model

    def save_model(self, model, outpath='.', model_name='model_dept_classify', version=835):
        """
        :param model: 需要保存的模型
        :param outpath: 模型保存路径
        :param model_name: 模型保存名字
        :param version: 模型保存版本
        :return: 无
        """
        model_arch = '%s.%s.arch' % (model_name, version)
        model_weight = '%s.%s.weight' % (model_name, version)
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
    parser.add_option('-v', dest='version',
                      help='the version of model')
    parser.add_option('-m',  dest='model',
                      help='the name of model')
    parser.add_option('-o',  dest='output',
                      help='the dir input')
    parser.add_option('-n', dest='num', help='seg word of num')
    parser.add_option('--cl', dest='classes', help='the classes of model')

    parser.add_option('--trainfile', dest='trainfile',
                      help='the trainfile of train')
    parser.add_option('--testfile',  dest='testfile',
                      help='the testfile of train')
    parser.add_option('--modeltype', dest='modeltype',
                      help='the type of model')

    parser.add_option('--increase_model', dest='increase_model',
                      help='the increate of model')
    parser.add_option('--increase_version', dest='increase_version',
                      help='the increate_version of model')

    (options, args) = parser.parse_args()
    version = 0
    num = 10
    classes = 363
    modeltype = 0
    increase_model = 0
    model_name = 'model_dept_classify'
    trainfile = ''
    input_test_path = ''
    if options.trainfile:
        trainfile = options.trainfile
        trainfile = check_train_path(trainfile)
    print(trainfile)
    if options.testfile:
        input_test_path = options.testfile
        input_test_path = check_train_path(input_test_path)
    print(input_test_path)
    if options.modeltype:
        modeltype = options.modeltype
        modeltype = int(modeltype)
    if options.increase_model:
        increase_model = int(options.increase_model)
    if options.increase_version:
        increase_version = options.increase_version

    if options.version:
        version = options.version
    if options.model:
        model_name = options.model
    if options.output:
        outpath = options.output
    if options.num:
        num = int(options.num)
    file_number = get_file_rows(trainfile)
    print(file_number)
    pinyin_model = PinyinModel(file_number=file_number)
    model = pinyin_model.origin_model()
    # x_test, y_test = data_loader.get_test_data(input_test_path, num=37, classes=363)

    if increase_model == 1:
        print('increate')
        model = pinyin_model.train_generate_increate(trainfile, x_test, y_test)
    else:
        model = pinyin_model.train_model(model, trainfile)
    pinyin_model.save_model(model, version=version)
