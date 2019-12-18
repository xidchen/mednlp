#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
disease_classify_cnn.py -- the CNN training of disease classifier

Author: chenxd <chenxd@guahao.com>
Create on 2018-05-04 Friday
"""

import os
import sys
import h5py
import codecs
import pickle
import itertools
import global_conf
import numpy as np
import pandas as pd
from collections import Counter
from optparse import OptionParser
from gensim.models import word2vec
from keras.layers import Dense, Dropout, Flatten, Input
from keras.layers import MaxPooling1D, Conv1D, Embedding
from keras.layers.merge import Concatenate
from keras.models import Model, load_model
from keras.utils.np_utils import to_categorical
from mednlp.dao.data_loader import Key2Value
from mednlp.dataset.padding import pad_sentences
from mednlp.text.synonym import Synonym


TOTAL_DISEASE = 589
dict_path = global_conf.dict_path
training_path = global_conf.training_path
train_data_path = global_conf.train_data_path
k2v = Key2Value(path=global_conf.disease_classify_dict_path)


class SaveLoadData(object):
    """
    读入训练数据，并保存
    """
    def __init__(self, f):
        self.path = f

    def is_path_exist(self):
        return True if os.path.exists(self.path) else False

    def save(self, data):
        print('【saving data】=> {}'.format(self.path))
        if not self.is_path_exist():
            with open(self.path, 'w') as f:
                f.write(data)
        else:
            raise ValueError('data path exist')

    def pkl_load(self):
        print('【loading pkl data】=> {}'.format(self.path))
        if self.is_path_exist():
            with open(self.path, 'r') as f:
                return pickle.load(f)
        else:
            raise ValueError('data path not exist')


def _get_train_data(model_version):
    print('Loading training data')
    fname = 'mr_generated_{}.txt'.format(model_version)
    cols = ['sen', 'sex', 'age', 'label']
    fpath = os.path.join(train_data_path, fname)
    with open(fpath, 'r') as f:
        texts = f.readlines()
    print('Training data is loaded')
    texts = [str(text).strip().split('\t') for text in texts]
    df = pd.DataFrame(texts, columns=cols)
    print('Training data is ready')
    return df[['sen', 'label']]


def encoding_labels(labels_list):
    d2i = k2v.load_dict()
    print("------ label unique number: {} ------".format(len(set(labels_list))))
    labels_index = [d2i[label] for label in labels_list]
    print('Label index is done')
    labels_cat = to_categorical(labels_index)
    print('Categorization is done')
    return labels_cat


def load_seg_pad_sens(field='train', num=10000, model_version=0,
                      padlen=50, padding_word="<PAD>"):
    print("--------------   load_seg_pad_sens   ----------------")
    fname = 'SENS_{}_num{}_seg_pad{}wrd{}.h5'.format(
        field, 'ALL' if num == 0 else num, padlen, padding_word)
    fpath = os.path.join(training_path, fname)
    f = h5py.File(fpath, 'w')
    df = eval('_get_{}_data({})'.format(field, model_version))
    if num:
        df = df.sample(num, random_state=0)
    sens = df.sen.tolist()
    sens = [str(s).strip().split('，') for s in sens]
    sens = pad_sentences(sens, padlen, value=padding_word)
    arr = np.array(sens, dtype=object)
    string_dt = h5py.special_dtype(vlen=str)
    f.create_dataset('sentences', data=arr, dtype=string_dt)
    f.close()
    return sens


def build_vocabulary_dict(sentences, verbose=False):
    word_counts = Counter(itertools.chain(*sentences))
    most_common_list = word_counts.most_common()
    vocabulary_ind2w_list = [x[0] for x in most_common_list]
    vocabulary_ind2w = {x: i for x, i in enumerate(vocabulary_ind2w_list)}
    vocabulary_w2ind = {x: i for i, x in enumerate(vocabulary_ind2w_list)}
    if verbose:
        mm = pd.Series(most_common_list)
        print(mm.head(100))
        print(mm.sample(100))
        print(mm.tail(100))
    return [vocabulary_w2ind, vocabulary_ind2w]


def load_vocab():
    f = SaveLoadData(global_conf.vocab_dict_path)
    if f.is_path_exist():
        d = codecs.open(f.path)
        vocab, d_1, d_2 = {}, {}, {}
        for row in d:
            r = str(row).strip().split('\t')
            if len(r) == 2:
                d_1[r[0]] = int(r[1])
                d_2[int(r[1])] = r[0]
        vocab['w2i'], vocab['i2w'] = d_1, d_2
    else:
        sens = load_seg_pad_sens('train', num=0, model_version=version)
        w2i, i2w = build_vocabulary_dict(sens, verbose=True)
        vocab = {'w2i': w2i, 'i2w': i2w}
        f.save(vocab)
    return vocab


class Vector(object):
    def __init__(self, num_features=50, min_word_count=1,
                 context=10, model_version=0):
        self.num_features = num_features
        self.min_word_count = min_word_count
        self.context = context
        self.version = model_version
        self.model_name = 'disease_word2vec.model'
        self.model_path = os.path.join(training_path, self.model_name)
        self.loaded_model = None
        self.synonym = Synonym(dict_type=['wy_symptom_name'])

    def load(self):
        if self.loaded_model:
            return self.loaded_model
        elif os.path.exists(self.model_name):
            print('Loading Word2Vec model: {}'.format(self.model_name))
            return pickle.load(codecs.open(self.model_name, 'rb'))
        elif os.path.exists(self.model_path):
            print('Loading Word2Vec model: {}'.format(self.model_name))
            return word2vec.Word2Vec.load(self.model_path)
        else:
            self.train()

    def train(self):
        print('Training Word2Vec model: {}'.format(self.model_name))
        sens = load_seg_pad_sens(num=0, model_version=self.version)
        w2v_model = word2vec.Word2Vec(sens,
                                      size=self.num_features,
                                      min_count=self.min_word_count,
                                      window=self.context,
                                      workers=4,
                                      sample=1e-3)
        w2v_model.init_sims(replace=True)
        print('Saving Word2Vec model: {}'.format(self.model_path))
        w2v_model.save(self.model_path)
        self.loaded_model = w2v_model
        return self.loaded_model

    def get_weights(self):
        print('Loading vocab dictionary')
        vocab_dict = load_vocab()
        w2i, i2w = vocab_dict.get('w2i'), vocab_dict.get('i2w')
        w2v_model = self.load()
        vector_size = len(list(w2v_model.values())[0])
        weights = {}
        for key, word in i2w.items():
            if key in weights:
                continue
            else:
                synonyms = self.synonym.get_synonym(word)
                # 如果该词没有同义词
                if not synonyms:
                    if word in w2v_model:
                        weights[key] = w2v_model[word]
                    else:
                        weights[key] = np.random.uniform(
                            -0.25, 0.25, vector_size)
                # 如果该词有同义词
                else:
                    # 把同义词的对应的key放入keys
                    keys = set()
                    keys.add(key)
                    for synonym in synonyms:
                        if str(synonym) in w2i:
                            keys.add(w2i[str(synonym)])
                    synonym_in_w2v = False
                    # 如果有同义词在w2v中，遍历keys，把key和向量放入weights
                    for synonym in synonyms:
                        if synonym in w2v_model:
                            synonym_in_w2v = True
                            weight = w2v_model[synonym]
                            for k in keys:
                                weights[k] = weight
                            break
                    # 如果没有一个同义词在w2v中，则随机生成向量放入weights
                    if not synonym_in_w2v:
                        weight = np.random.uniform(
                            -0.25, 0.25, vector_size)
                        for k in keys:
                            weights[k] = weight
        return weights


def shufdata(x, y, val_ratio=0.2):
    np.random.seed(0)
    shuffle_indices = np.random.permutation(np.arange(len(y)))
    x = np.array(x)
    x, y = x[shuffle_indices], y[shuffle_indices]
    train_len = int(len(x) * (1 - val_ratio))
    x_train, y_train = x[:train_len], y[:train_len]
    x_test, y_test = x[train_len:], y[train_len:]
    return x_train, y_train, x_test, y_test


class Param(object):
    def __init__(self, model_version):
        # Model Hyperparameters
        self.sequence_length = 50
        self.embedding_dim = 100
        self.min_word_count = 1
        self.context = 10
        self.filter_sizes = [1]
        self.num_filters = 80
        self.dropout_prob = (0.5, 0.5)
        # self.hidden_dims = 1000
        self.output_dims = TOTAL_DISEASE
        # Training parameters
        self.val_ratio = 0.1
        self.num_sens = 0
        self.version = model_version
        self.batch_size = 256
        self.num_epochs = 10
        self.model_name = 'disease_classify_cnn.{}.model'.format(self.version)
        self.model_path = os.path.join(training_path, self.model_name)
        self.loaded_model = None
        self.x_train, self.y_train, self.x_val, self.y_val = [], [], [], []


class Cnnd(Param):
    def model_1(self):
        global model_output
        weights_dic = Vector(self.embedding_dim,
                             self.min_word_count,
                             self.context,
                             self.version).get_weights()
        weights = np.array([v for v in weights_dic.values()])
        model_input = Input(shape=(self.sequence_length,))
        z = Embedding(len(weights), self.embedding_dim,
                      input_length=self.sequence_length,
                      name="embedding")(model_input)
        z = Dropout(self.dropout_prob[0])(z)

        if self.model_name == 'origin{}'.format(self.version):
            conv_blocks = []
            for sz in (2, 20):
                conv = Conv1D(filters=100, kernel_size=sz, activation="relu")(z)
                conv = Flatten()(MaxPooling1D()(conv))
                conv_blocks.append(conv)
            z = Concatenate()(conv_blocks) if len(
                conv_blocks) > 1 else conv_blocks[0]
            z = Dropout(self.dropout_prob[1])(z)
            z = Dense(1000, activation="relu")(z)
            z = Dropout(0.5)(z)
            model_output = Dense(self.output_dims, activation="softmax")(z)

        if self.model_name == 'disease_classify_cnn.{}.model'.format(
                self.version):
            sz1, sz2, sz3, sz4, sz5 = 1, 2, 3, 12, 30
            fn1, fn2, fn3, fn4, fn5 = 120, 100, 80, 50, 10
            conv1 = Conv1D(filters=fn1, kernel_size=sz1, activation="relu")(z)
            conv1 = Flatten()(MaxPooling1D()(conv1))
            conv2 = Conv1D(filters=fn2, kernel_size=sz2, activation="relu")(z)
            conv2 = Flatten()(MaxPooling1D()(conv2))
            conv3 = Conv1D(filters=fn3, kernel_size=sz3, activation="relu")(z)
            conv3 = Flatten()(MaxPooling1D()(conv3))
            conv4 = Conv1D(filters=fn4, kernel_size=sz4, activation="relu")(z)
            conv4 = Flatten()(MaxPooling1D()(conv4))
            conv5 = Conv1D(filters=fn5, kernel_size=sz5, activation="relu")(z)
            conv5 = Flatten()(MaxPooling1D()(conv5))
            z = Concatenate()([conv1, conv2, conv3, conv4, conv5])
            z = Dropout(self.dropout_prob[1])(z)
            z = Dense(self.output_dims, activation="relu")(z)
            z = Dropout(0.5)(z)
            model_output = Dense(self.output_dims, activation="softmax")(z)

        if self.model_name == 'multi_layer_conv{}'.format(self.version):
            conv1 = Conv1D(filters=64, kernel_size=3, activation="relu")(z)
            pool1 = MaxPooling1D()(conv1)
            conv2 = Conv1D(filters=64, kernel_size=3, activation="relu")(pool1)
            pool2 = MaxPooling1D()(conv2)
            conv3 = Conv1D(filters=64, kernel_size=3, activation="relu")(pool2)
            pool3 = MaxPooling1D()(conv3)
            z = Flatten()(pool3)
            z = Dense(200, activation="relu")(z)
            z = Dropout(self.dropout_prob[1])(z)
            model_output = Dense(self.output_dims, activation="softmax")(z)

        if self.model_name == 'multi_layer_conv_large{}'.format(self.version):
            conv1 = Conv1D(filters=64, kernel_size=2, activation="relu")(z)
            pool1 = MaxPooling1D()(conv1)
            conv2 = Conv1D(filters=64, kernel_size=2, activation="relu")(pool1)
            pool2 = MaxPooling1D()(conv2)
            conv3 = Conv1D(filters=64, kernel_size=2, activation="relu")(pool2)
            pool3 = MaxPooling1D()(conv3)
            z = Flatten()(pool3)
            z = Dense(200, activation="relu")(z)
            z = Dropout(self.dropout_prob[1])(z)
            model_output = Dense(self.output_dims, activation="softmax")(z)

        cnn_model = Model(model_input, model_output)
        cnn_model.compile(loss="categorical_crossentropy",
                          metrics=["categorical_accuracy"],
                          optimizer="adam")
        print("Initializing embedding layer with word2vec: ", weights.shape)
        embedding_layer = cnn_model.get_layer("embedding")
        embedding_layer.set_weights([weights])
        return cnn_model

    def _get_data(self, field='train', num=0):
        sens = load_seg_pad_sens(field=field, num=num,
                                 model_version=self.version, padlen=50)
        vocab = load_vocab()
        w2i = vocab['w2i']
        _pad = w2i['<PAD>']
        sens_int = [[w2i.get(w, _pad) for w in sen] for sen in sens]
        get_field_data = "_get_{}_data({})".format(field, self.version)
        if field == 'train':
            if num:
                labels = eval(get_field_data).label.sample(num).tolist()
            else:
                labels = eval(get_field_data).label.tolist()
            labels_cat = encoding_labels(labels)
            return sens_int, labels_cat
        elif field == 'test':
            data = eval(get_field_data)
            labels_cat = encoding_labels(data.label.tolist())
            return sens_int, labels_cat
        else:
            raise ValueError('field wrong!')

    def get_tvdata(self):
        x, y = self._get_data(num=self.num_sens)
        self.x_train, self.y_train, self.x_val, self.y_val = shufdata(
            x, y, self.val_ratio)

    def load_model(self, name=None):
        if name:
            path = os.path.join(training_path, name)
            if os.path.exists(path):
                print("Loading existing model: {}".format(name))
            self.loaded_model = load_model(path)
            return self.loaded_model
        self.get_tvdata()
        if self.loaded_model:
            return self.loaded_model
        elif os.path.exists(self.model_path):
            print("Loading existing model: {}".format(self.model_name))
            self.loaded_model = load_model(self.model_path)
        else:
            print('Training model:{} '.format(self.model_name))
            cnn_model = self.model_1()
            cnn_model.fit(self.x_train, self.y_train,
                          validation_data=(self.x_val, self.y_val),
                          batch_size=self.batch_size,
                          epochs=self.num_epochs,
                          verbose=1)
            print('Saving model:{} '.format(self.model_name))
            cnn_model.save(self.model_path)
            self.loaded_model = cnn_model
        return self.loaded_model

    def predict(self):
        print("------ predict ------")
        return self.load_model(name=self.model_name)


def my_confusion_matrix(y_true, y_pred, index):
    from sklearn.metrics import confusion_matrix
    conf_mat = confusion_matrix(y_true, y_pred, range(len(index)))
    print("confusion_matrix(left labels: y_true, up labels: y_pred):")
    print("labels\t")
    for i in range(len(index)):
        print(index[i], "\t")
    for i in range(len(conf_mat)):
        print(i, "\t")
        for j in range(len(conf_mat[i])):
            print(conf_mat[i][j], '\t')


def my_classification_report(y_true, y_pred, index):
    from sklearn.metrics import classification_report
    print("classification_report(left: labels):")
    print(classification_report(y_true, y_pred, target_names=index))


if __name__ == '__main__':
    command = '\n python %s [-v version]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-v', '--version', dest='version', help='model version')
    (options, args) = parser.parse_args()
    version = 0
    if options.version:
        version = options.version
    model = Cnnd(model_version=version)
    print(model.load_model())
