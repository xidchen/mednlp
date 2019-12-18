#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_cnn.py -- the cnn training of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-04-11 星期三.
"""
import global_conf
import os
import sys
from gensim.models import word2vec
import numpy as np
import mednlp.dao.data_loader as data_loader
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical
from keras.layers import Dense, Dropout, Flatten, Input, MaxPooling1D, \
     Convolution1D, Embedding, LSTM, Bidirectional, TimeDistributed, Lambda
from keras.layers.merge import Concatenate, concatenate
from keras.models import Model
from mednlp.text.vector import Word2vector
from keras.models import model_from_json
from keras import backend as K
from mednlp.dept.utils.rules import get_file_rows, check_train_path


RELATIVE_PATH = global_conf.RELATIVE_PATH
cfg_path = RELATIVE_PATH + 'etc/cdss.cfg'
traindata_path = os.path.join(RELATIVE_PATH, 'data/traindata/')
# seg_path = os.path.join(traindata_path, 'dept_classify_traindata_20180904_cnn_seg.txt')
# input_file_path = os.path.join(traindata_path, 'dept_classify_traindata_20180904_cnn_seg.txt')
# input_train_path = os.path.join(traindata_path, 'dept_classify_traindata_20180904_cnn_seg_train.txt')
# input_test_path = os.path.join(traindata_path, 'dept_classify_traindata_20180904_cnn_seg_test.txt')

word2vecotr_div = os.path.join(traindata_path, 'textcnn_duoyu.txt')
word2vec_dict = os.path.join(RELATIVE_PATH, 'data/dict/dept_classify_word2vec_100dim_5c_5mc.gs_vec_model')
embedding_dim = 100
num = 200
classes = 45
sequence_length = 200
dropout_prob = (0.5, 0.5)
batch_size = 512
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


def get_data():
    """
    从文件中读取读取训练数据和测试数据，对于数据的补零方式上，采用前面补零的方式
    :return: 训练数据和测试数据
    """
    train, test = data_loader.load_data_dept_classify(
        path=seg_path, n_words=max_nb_words, valid_portion=0.2,
        sort_by_len=True)
    train_x, train_y = train
    test_x, test_y = test
    x_train = pad_sequences(train_x, padding='post', maxlen=num)
    x_test = pad_sequences(test_x, padding='post', maxlen=num)
    y_train = to_categorical(train_y, num_classes=classes)
    y_test = to_categorical(test_y, num_classes=classes)
    return x_train, y_train, x_test, y_test

# def get_test_data(test_file):
#     x_test,y_test = data_loader.load_file(test_file)
#     x_test =  pad_sequences(x_test, padding='post', maxlen=num)
#     y_test = to_categorical(y_test, num_classes=classes)
#     return x_test, y_test


class CnnModel():
    """
    主要是定义了一些常用的cnn模型架构，用于分类的
    """

    def __init__(self, file_number=4482678):
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
        model_output = Dense(classes, activation="softmax")(z)
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

    def multi_layer_conv_large_model(self):
        """
        模型主要采用紧跟嵌入层并行的多个卷积层和池化层，然后跟全连接层
        :return: 模型
        """
        model_input = Input(shape=(sequence_length,))
        z = Embedding(max_nb_words, embedding_dim, input_length=sequence_length,
                      weights=[self.embedding_matrix], name="embedding")(model_input)
        z = Dropout(dropout_prob[0])(z)
        conv1 = Convolution1D(filters=64, kernel_size=3, strides=1, padding="valid", activation="relu")(z)
        pool1 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv1)
        conv2 = Convolution1D(filters=64, kernel_size=3, strides=1, padding="valid", activation="relu")(pool1)
        pool2 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv2)
        conv3 = Convolution1D(filters=64, kernel_size=3, strides=1, padding="valid", activation="relu")(pool2)
        pool3 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv3)
        z = Flatten()(pool3)
        z = Dense(200, activation="relu")(z)
        z = Dropout(dropout_prob[1])(z)
        model_output = Dense(classes, activation="softmax")(z)
        model = Model(model_input, model_output)
        return model

    def rcnn(self):
        """
        模型主要采用紧跟嵌入层，后面跟上双向的lstm，然后跟上最大池化层，最后的softmax层
        :return: 返回模型
        """
        input_a = Input(shape=(sequence_length,))

        e_result = Embedding(max_nb_words, embedding_dim, weights=[self.embedding_matrix],
                             input_length=sequence_length, name="embedding")(input_a)
        b_result = Bidirectional(LSTM(128, return_sequences=True, dropout=0.5, recurrent_dropout=0.2))(e_result)
        t_result = TimeDistributed(Dense(128, activation='tanh'))(b_result)
        pool_rnn = Lambda(lambda x: K.max(x, axis=1), output_shape=(128,))(t_result)
        output = Dense(classes, input_dim=128, activation='softmax')(pool_rnn)
        rcnn_model = Model(inputs=input_a, outputs=output)
        return rcnn_model

    def lcnn(self):
        """
        模型主要采用紧跟嵌入层，后面跟上双向的lstm，然后跟上并行的卷积层，最后的softmax层
        :return: 返回模型
        """
        input_a = Input(shape=(sequence_length,))

        e_result = Embedding(max_nb_words, embedding_dim, weights=[self.embedding_matrix],
                             input_length=sequence_length, name="embedding")(input_a)
        b_result = Bidirectional(LSTM(128, return_sequences=True, dropout=0.5, recurrent_dropout=0.2))(e_result)
        t_result = TimeDistributed(Dense(1, activation='tanh'))(b_result)
        x1 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(t_result)
        x2 = Convolution1D(filters=64, kernel_size=3, padding='valid', activation='relu')(t_result)
        x3 = Convolution1D(filters=64, kernel_size=5, padding='valid', activation='relu')(t_result)
        x4 = Convolution1D(filters=64, kernel_size=4, padding='valid', activation='relu')(t_result)
        x = concatenate([x1, x2, x3, x4], axis=1)
        x = Dropout(0.25)(x)
        x = Dense(100, activation='relu')(x)
        model_output = Dense(classes, activation='softmax')(x)
        model = Model(input_a, model_output)
        print(model.summary())
        return model

    def lcnnk(self):
        """
        模型主要采用紧跟嵌入层，后面跟上双向的lstm，然后跟上并行的卷积层，最后的softmax层
        :return: 返回模型
        """
        input_a = Input(shape=(sequence_length,))

        e_result = Embedding(max_nb_words, embedding_dim, weights=[self.embedding_matrix],
                             input_length=sequence_length, name="embedding")(input_a)
        b_result = Bidirectional(LSTM(128, return_sequences=True, dropout=0.5, recurrent_dropout=0.2))(e_result)
        t_result = TimeDistributed(Dense(128, activation='tanh'))(b_result)
        x = Convolution1D(filters=64, kernel_size=1, padding='valid', activation='relu')(t_result)
        x1 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(x)
        x2 = Convolution1D(filters=64, kernel_size=3, padding='valid', activation='relu')(x)
        x3 = Convolution1D(filters=64, kernel_size=5, padding='valid', activation='relu')(x)
        x4 = Convolution1D(filters=64, kernel_size=4, padding='valid', activation='relu')(x)
        x = concatenate([x1, x2, x3, x4], axis=1)
        x = Dropout(0.25)(x)
        x = Dense(100, activation='relu')(x)
        model_output = Dense(classes, activation='softmax')(x)
        model = Model(input_a, model_output)
        print(model.summary())
        return model

    def ac_blstm(self):
        """
        模型主要采用紧跟嵌入层，串形卷积层的使用，从原来的n*k的卷积核，改成n*1，1*k的卷积核，然后跟上并行的卷积层，最后的softmax层
        :return: 返回模型
        """
        model_input = Input(shape=(sequence_length,))
        z = Embedding(max_nb_words, embedding_dim, input_length=sequence_length,
                      weights=[self.embedding_matrix], name="embedding")(model_input)
        x = Convolution1D(filters=64, kernel_size=1, padding='valid', activation='relu')(z)
        x1 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(x)
        x2 = Convolution1D(filters=64, kernel_size=3, padding='valid', activation='relu')(x)
        x3 = Convolution1D(filters=64, kernel_size=5, padding='valid', activation='relu')(x)
        x = concatenate([x1, x2, x3], axis=1)
        x = Bidirectional(LSTM(200))(x)
        x = Dropout(0.25)(x)
        x = Dense(100, activation='relu')(x)
        model_output = Dense(classes, activation='softmax')(x)
        model = Model(model_input, model_output)
        return model

    def lstm_cnn_p(self):
        """
        lstm+并行cnn
        :return:
        """
        input_a = Input(shape=(sequence_length,))
        e_result = Embedding(max_nb_words, embedding_dim, input_length=sequence_length,
                             weights=[self.embedding_matrix], name="embedding")(input_a)
        b_result = Bidirectional(LSTM(128, return_sequences=True, dropout=0.5, recurrent_dropout=0.2))(e_result)
        conv_x1 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(b_result)
        conv_x1 = MaxPooling1D(pool_size=2)(conv_x1)
        conv_x1 = Flatten()(conv_x1)

        conv_x2 = Convolution1D(filters=64, kernel_size=3, padding='valid', activation='relu')(b_result)

        conv_x2 = MaxPooling1D(pool_size=2)(conv_x2)
        conv_x2 = Flatten()(conv_x2)

        conv_x3 = Convolution1D(filters=64, kernel_size=5, padding='valid', activation='relu')(b_result)

        conv_x3 = MaxPooling1D(pool_size=2)(conv_x3)
        conv_x3 = Flatten()(conv_x3)

        conv_x4 = Convolution1D(filters=64, kernel_size=4, padding='valid', activation='relu')(b_result)
        conv_x4 = MaxPooling1D(pool_size=2)(conv_x4)
        conv_x4 = Flatten()(conv_x4)

        x = concatenate([conv_x1, conv_x2, conv_x3, conv_x4], axis=1)

        x = Dense(1000, activation='relu')(x)
        x = Dropout(0.25)(x)

        x = Dense(100, activation='relu')(x)
        x = Dropout(0.25)(x)
        model_output = Dense(classes, activation='softmax')(x)
        model = Model(input_a, model_output)
        return model

    def lstm_cnn_s(self):
        """
        训练lstm+串行cnn
        :return: 返回模型
        """
        input_a = Input(shape=(sequence_length,))
        e_result = Embedding(max_nb_words, embedding_dim, input_length=sequence_length,
                             weights=[self.embedding_matrix], name="embedding")(input_a)
        b_result = Bidirectional(LSTM(128, return_sequences=True, dropout=0.5, recurrent_dropout=0.2))(e_result)
        conv_x1 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(b_result)
        conv_x1 = MaxPooling1D(pool_size=2)(conv_x1)
        conv_x2 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(conv_x1)
        conv_x2 = MaxPooling1D(pool_size=2)(conv_x2)
        conv_x3 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(conv_x2)
        conv_x3 = MaxPooling1D(pool_size=2)(conv_x3)
        conv_x4 = Convolution1D(filters=64, kernel_size=2, padding='valid', activation='relu')(conv_x3)
        conv_x4 = MaxPooling1D(pool_size=2)(conv_x4)
        conv_x4 = Flatten()(conv_x4)
        x = Dense(100, activation='relu')(conv_x4)
        x = Dropout(0.25)(x)
        model_output = Dense(classes, activation='softmax')(x)
        model = Model(input_a, model_output)
        return model

    def multi_layer_conv_model(self):
        """
        模型主要采用紧跟嵌入层，并行的卷积层，最后的softmax层
        :return: 返回模型
        """
        model_input = Input(shape=(sequence_length,))
        z = Embedding(max_nb_words, embedding_dim, input_length=sequence_length,
                      weights=[self.embedding_matrix], name="embedding")(model_input)
        z = Dropout(dropout_prob[0])(z)
        conv1 = Convolution1D(filters=64, kernel_size=2, strides=1, padding="valid", activation="relu")(z)
        pool1 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv1)
        conv2 = Convolution1D(filters=64, kernel_size=2, strides=1, padding="valid", activation="relu")(pool1)
        pool2 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv2)
        conv3 = Convolution1D(filters=64, kernel_size=2, strides=1, padding="valid", activation="relu")(pool2)
        pool3 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv3)
        z = Flatten()(pool3)
        z = Dense(200, activation="relu")(z)
        z = Dropout(dropout_prob[1])(z)
        model_output = Dense(classes, activation="softmax")(z)
        model = Model(model_input, model_output)
        return model

    def train_model(self, x_train, y_train, x_test, y_test, model):
        """
        :param x_train: 训练数据x
        :param y_train: 训练数据y
        :param x_test: 测试数据x
        :param y_test: 测试数据y
        :param model: 需要训练和编译的模型
        :return: 训练以后的模型
        """
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=batch_size, epochs=num_epochs,
                  verbose=1)
        return model

    def train_generator_model(self, train_file, x_test, y_test, model):
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, padding='post'),
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
        model.fit_generator(data_loader.generate_arrays_from_file(train_file, batch_size, padding='post'),
                            steps_per_epoch=int(self.file_number / batch_size), epochs=num_epochs, max_q_size=1,
                            validation_data=(x_test, y_test))
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
    if modeltype == 1:
        model = cnn_model.ac_blstm()
    elif modeltype == 2:
        model = cnn_model.lcnn()
    elif modeltype == 3:
        model = cnn_model.origin_model()
    elif modeltype == 4:
        model = cnn_model.rcnn()
    elif modeltype == 5:
        model = cnn_model.lstm_cnn_p()
    elif modeltype == 6:
        model = cnn_model.lstm_cnn_s()
    else:
        model = cnn_model.origin_diff_size_model()
    x_test, y_test = data_loader.get_test_data(input_test_path, padding='post')
    if increase_model == 1:
        print('increate')
        model = cnn_model.train_generate_increate(trainfile, x_test, y_test)
    else:
        model = cnn_model.train_generator_model(trainfile, x_test, y_test, model)
    cnn_model.save_model(model, version=version)
