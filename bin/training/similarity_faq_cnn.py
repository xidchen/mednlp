# ！/usr/bin/env python
# -*- coding：utf-8 -*-
# @Time :2019/4/3 11:02
# @Auther:caoxg@<caoxg@guahao.com>
# @File:intelligence_service_cnn.py

import global_conf
import os
import sys
from gensim.models import word2vec
import numpy as np
import mednlp.dao.data_loader as data_loader
from keras.layers import Dense, Dropout, Flatten, Input, MaxPooling1D, \
     Convolution1D, Embedding
from keras.layers.merge import Concatenate
from keras.models import Model
from mednlp.text.vector import Word2vector
from keras.models import model_from_json
from mednlp.dept.utils.rules import get_file_rows, check_train_path
from base_trainer import BaseTrainer


RELATIVE_PATH = global_conf.RELATIVE_PATH
cfg_path = RELATIVE_PATH + 'etc/cdss.cfg'
traindata_path = os.path.join(RELATIVE_PATH, 'data/traindata/')

word2vecotr_div = os.path.join(traindata_path, 'textcnn_duoyu.txt')
word2vec_dict = os.path.join(RELATIVE_PATH, 'data/dict/dept_classify_word2vec_100dim_5c_5mc.gs_vec_model')
embedding_dim = 100
num = 200
classes = 363
sequence_length = 37
dropout_prob = (0.5, 0.5)
batch_size = 64
num_epochs = 45
word2vector = Word2vector(global_conf.dept_classify_cnn_dict_path)
id2word = word2vector.id2word
max_nb_words = len(id2word)+1
print('max_nb_words', max_nb_words)


def get_embedding():
    """
    读取预训练的word2vector词向量，保存成字典的形式，其中key为词语，value为词向量
    :return: 保存以后的词语和词向量的对应字典形式
    """
    w2v_model = word2vec.Word2Vec.load(word2vec_dict)
    embeddings_index = {}
    for word in w2v_model.wv.vocab:
        embeddings_index[word] = w2v_model[word]
    return embeddings_index


def get_weights():
    """
    把保存以后的词语和词向量的对应关系结合id和词语的对应关系，得到id和词向量的对应关系，用数组表示，数组的行即使id的数字，对于
    没有词向量的词语，用-0.25-0.25之间的数随机生成
    :return: id和词向量的对应数组
    """
    embeddings_index = get_embedding()
    nb_words = max_nb_words
    embedding_matrix = np.zeros((nb_words, embedding_dim))

    for i, word in id2word.items():
        if word in embeddings_index:
            embedding_vector = embeddings_index[word]
            # print(embedding_vector)
            embedding_matrix[i] = embedding_vector
        else:
            embedding_matrix[i] = np.random.uniform(-0.25, 0.25, embedding_dim)
    return embedding_matrix


class CnnModel(BaseTrainer):
    """
    主要是定义了一些常用的cnn模型架构，用于分类的
    """

    def __init__(self, file_number=4482678):
        super(CnnModel, self).__init__(model_name='similarity_faq_cnn')
        self.classes = 365
        self.epoch_num = 100
        self.embedding_matrix = get_weights()
        self.file_number = file_number

    def origin_model(self):
        """
        模型主要采用紧跟嵌入层并行的多个卷积层和池化层（其中改变的主要是卷积核的大小，然后跟全连接层。
        :return: 返回模型
        """
        model_input = Input(shape=(sequence_length,))
        z = Embedding(max_nb_words, embedding_dim, input_length=sequence_length, weights=[self.embedding_matrix],
                      name="embedding")(model_input)
        z = Dropout(dropout_prob[0])(z)
        conv_blocks = []
        for sz in (2, 20):
            conv = Convolution1D(filters=100, kernel_size=sz, padding="valid", activation="relu", strides=1)(z)
            conv = MaxPooling1D(pool_size=2)(conv)
            conv = Flatten()(conv)
            conv_blocks.append(conv)
        z = Concatenate()(conv_blocks) if len(conv_blocks) > 1 else conv_blocks[0]
        z = Dropout(dropout_prob[1])(z)
        z = Dense(1000, activation="relu")(z)
        z = Dropout(0.5)(z)
        model_output = Dense(classes, activation="softmax")(z)
        model = Model(model_input, model_output)
        return model

    def origin_diff_size_model(self):
        """
        模型主要采用紧跟嵌入层并行的多个卷积层和池化层（其中改变卷积核的大小和卷积核的多少），然后跟全连接层
        :return: 返回模型
        """
        model_input = Input(shape=(sequence_length,))
        z = Embedding(max_nb_words, embedding_dim, input_length=sequence_length, weights=[self.embedding_matrix],
                      name="embedding")(model_input)
        z = Dropout(dropout_prob[0])(z)
        conv_blocks = []
        sz1, sz2, sz3, sz4, sz5 = 1, 2, 3, 12, 30
        fn1, fn2, fn3, fn4, fn5 = 120, 100, 80, 50, 10
        conv1 = Convolution1D(filters=fn1, kernel_size=sz1, padding="valid", activation="relu", strides=1)(z)
        conv1 = MaxPooling1D(pool_size=2)(conv1)
        conv1 = Flatten()(conv1)
        conv2 = Convolution1D(filters=fn2, kernel_size=sz2, padding="valid", activation="relu", strides=1)(z)
        conv2 = MaxPooling1D(pool_size=2)(conv2)
        conv2 = Flatten()(conv2)
        conv3 = Convolution1D(filters=fn3, kernel_size=sz3, padding="valid", activation="relu", strides=1)(z)
        conv3 = MaxPooling1D(pool_size=2)(conv3)
        conv3 = Flatten()(conv3)
        conv4 = Convolution1D(filters=fn4, kernel_size=sz4, padding="valid", activation="relu", strides=1)(z)
        conv4 = MaxPooling1D(pool_size=2)(conv4)
        conv4 = Flatten()(conv4)
        conv5 = Convolution1D(filters=fn5, kernel_size=sz5, padding="valid", activation="relu", strides=1)(z)
        conv5 = MaxPooling1D(pool_size=2)(conv5)
        conv5 = Flatten()(conv5)
        z = Concatenate()([conv1, conv2, conv3, conv4, conv5])
        z = Dropout(dropout_prob[1])(z)
        z = Dense(1000, activation="relu")(z)
        z = Dropout(0.5)(z)
        model_output = Dense(self.classes, activation="softmax")(z)
        model = Model(model_input, model_output)
        return model

    def origin_diff_size_model_s(self):
        """
        模型主要采用紧跟嵌入层串行的多个卷积层和池化层（其中改变卷积核的大小和卷积核的多少），然后跟全连接层
        :return: 返回模型
        """
        model_input = Input(shape=(sequence_length,))
        z = Embedding(max_nb_words, embedding_dim, input_length=sequence_length,
                      weights=[self.embedding_matrix], name="embedding")(model_input)
        z = Dropout(dropout_prob[0])(z)
        conv_blocks = []
        sz1, sz2, sz3 = 3, 4, 5
        # fn1, fn2, fn3, fn4, fn5 = 120, 100, 80, 50, 10
        fn1, fn2, fn3 = 40, 40, 40
        conv1 = Convolution1D(filters=fn1, kernel_size=sz1, padding="valid", activation="relu", strides=1)(z)
        conv1 = MaxPooling1D(pool_size=2)(conv1)
        conv1 = Flatten()(conv1)
        conv2 = Convolution1D(filters=fn2, kernel_size=sz2, padding="valid", activation="relu", strides=1)(z)
        conv2 = MaxPooling1D(pool_size=2)(conv2)
        conv2 = Flatten()(conv2)
        conv3 = Convolution1D(filters=fn3, kernel_size=sz3, padding="valid", activation="relu", strides=1)(z)
        conv3 = MaxPooling1D(pool_size=2)(conv3)
        conv3 = Flatten()(conv3)
        z = Concatenate()([conv1, conv2, conv3])
        z = Dropout(dropout_prob[1])(z)
        z = Dense(1000, activation="relu")(z)
        z = Dropout(0.5)(z)
        model_output = Dense(classes, activation="softmax")(z)
        model = Model(model_input, model_output)
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
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, padding='post', num=37, classes=self.classes),
                            steps_per_epoch=int(self.file_number/batch_size),  epochs=num_epochs, max_q_size=1,
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
        model = model_from_json(open(model_arch).read())
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

    def train_generate_increate(self, train_file, x_test, y_test):
        """
        :param train_file: 训练数据文件路径
        :param x_test: 测试数据x
        :param y_test: 测试数据y
        :return: 返回训练后的模型
        """
        model = self.load_model(2025)
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, padding='post', num=37,
                                                                  classes=363), steps_per_epoch=int(self.file_number / batch_size),
                            epochs=num_epochs, max_q_size=1, validation_data=(x_test, y_test))
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
    from optparse import OptionParser
    parser = OptionParser(usage=command)
    parser.add_option('-v', dest='version',
                      help='the version of model')
    parser.add_option('-m', dest='model',
                      help='the name of model')
    parser.add_option('-o', dest='output',
                      help='the dir input')
    parser.add_option('-n', dest='num', help='seg word of num')
    parser.add_option('--cl', dest='classes', help='the classes of model')

    parser.add_option('--trainfile', dest='trainfile',
                      help='the trainfile of train')
    parser.add_option('--testfile', dest='testfile',
                      help='the testfile of train')
    parser.add_option('--modeltype', dest='modeltype',
                      help='the type of model')

    parser.add_option('--increase_model', dest='increase_model',
                      help='the increate of model')
    parser.add_option('--increase_version', dest='increase_version',
                      help='the increate_version of model')
    (options, args) = parser.parse_args()
    version = 0
    trainfile = ''
    input_test_path = ''
    modeltype = 7
    increase_model = 0

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
    cnn_model = CnnModel(file_number=file_number)
    model = cnn_model.origin_diff_size_model()
    x_test, y_test = data_loader.get_test_data(input_test_path, padding='post', num=37, classes=365)
    if increase_model == 1:
        print('increate')
        model = cnn_model.train_generate_increate(trainfile, x_test, y_test)
    else:
        model = cnn_model.train_generator_model(trainfile, x_test, y_test, model)
        # model = cnn_model.train_model(model, trainfile)
    cnn_model.save_model(model, version=version)
