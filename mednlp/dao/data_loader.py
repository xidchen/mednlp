#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
data_loader.py -- some data_loader

Author: maogy <maogy@guahao.com>
Create on 2017-05-27 星期六.
"""

from __future__ import print_function
import os
import numpy
import tensorflow as tf
import codecs
from keras.utils.np_utils import to_categorical
from keras.preprocessing.sequence import pad_sequences


class Key2Value(object):

    def __init__(self, path, swap=False, v_is_int=True):
        self.path = path
        self.swap = swap
        self.v_is_int = v_is_int
        self.load_dict()

    def load_dict(self):
        """
        获得标签名和id
        参数:
        path->标签向量字典文件路径.
        :return:{d_name, d_id} or {d_id, d_name}
        """
        d = {}
        for line in codecs.open(self.path):
            key, value = line.strip().split('\t')
            if self.v_is_int:
                if not self.swap:
                    d[key] = int(value)
                else:
                    d[int(value)] = key
            else:
                if not self.swap:
                    d[key] = value
                else:
                    d[value] = key
        return d


def prepare_data(seqs, labels, maxlen=None):
    """Create the matrices from the datasets.
    This pad each sequence to the same length: the length of the
    longest sequence or maxlen.
    if maxlen is set, we will cut all sequence to this maximum
    length.
    This swap the axis!
    """
    # x: a list of sentences
    lengths = [len(s) for s in seqs]

    if maxlen is not None:
        new_seqs = []
        new_labels = []
        new_lengths = []
        for l, s, y in zip(lengths, seqs, labels):
            if l < maxlen:
                new_seqs.append(s)
                new_labels.append(y)
                new_lengths.append(l)
        lengths = new_lengths
        labels = new_labels
        seqs = new_seqs

        if len(lengths) < 1:
            return None, None, None

    n_samples = len(seqs)
    maxlen = numpy.max(lengths)

    x = numpy.zeros((maxlen, n_samples)).astype('int64')
    x_mask = numpy.zeros((maxlen, n_samples)).astype(tf.float32)
    for idx, s in enumerate(seqs):
        x[:lengths[idx], idx] = s
        x_mask[:lengths[idx], idx] = 1.

    return x, x_mask, labels


def get_dataset_file(dataset, default_dataset, origin):
    """
    Look for it as if it was a full path, if not, try local file,
    if not try in the data directory.
    Download dataset if it is not present
    """
    data_dir, data_file = os.path.split(dataset)
    if data_file == default_dataset and not os.path.isfile(dataset):
        from six.moves import urllib
        print('Downloading data from %s' % origin)
        urllib.request.urlretrieve(origin, dataset)

    return dataset


def load_file(path):
    x_list, y_list = [], []
    for line in codecs.open(path, 'r', encoding='utf-8'):
        line = line.strip()
        y_str, x_list_str = line.split(' ')
        x_list.append([int(x) for x in x_list_str.split(',')])
        y_list.append(int(y_str))
    return x_list, y_list


def load_data_intention_union(path):
    char_list, pinyin_list, pos_list = [], [], []
    y_list = []
    with open(path, encoding='utf-8', mode='r') as f:
        for line in f:
            line = line.strip()
            y_str, x_list_str = line.split(' ')
            y_list.append(int(y_str))
            x_list_split = x_list_str.split(',')
            char_list.append([int(temp.split('#')[0]) for temp in x_list_split])
            pinyin_list.append([int(temp.split('#')[1]) for temp in x_list_split])
            pos_list.append([int(temp.split('#')[2]) for temp in x_list_split])
    return char_list, pinyin_list, pos_list, y_list


def load_data_disease_classify(path, n_words=100000, valid_portion=0.1,
                               maxlen=None, sort_by_len=True):
    return load_data(path, n_words, valid_portion, maxlen, sort_by_len)


def load_data_intention_classify(path, n_words=100000, valid_portion=0.1,
                                 maxlen=None, sort_by_len=True):
    return load_data(path, n_words, valid_portion, maxlen, sort_by_len)


def load_data_dept_classify(path, n_words=100000, valid_portion=0.1,
                            maxlen=None, sort_by_len=True):
    return load_data(path, n_words, valid_portion, maxlen, sort_by_len)


def load_data(path, n_words=100000, valid_portion=0.1,
              maxlen=None, sort_by_len=True):
    """
    Loads the dataset
    :type path: String
    :param path: The path to the dataset (here IMDB)
    :type n_words: int
    :param n_words: The number of word to keep in the vocabulary.
        All extra words are set to unknow (1).
    :type valid_portion: float
    :param valid_portion: The proportion of the full train set used for
        the validation set.
    :type maxlen: None or positive int
    :param maxlen: the max sequence length we use in the train/valid set.
    :type sort_by_len: bool
    :name sort_by_len: Sort by the sequence length for the train,
        valid and test set. This allow faster execution as it cause
        less padding per minibatch. Another mechanism must be used to
        shuffle the train set at each epoch.
    """
    train_set = load_file(path)
    if maxlen:
        new_train_set_x = []
        new_train_set_y = []
        for x, y in zip(train_set[0], train_set[1]):
            if len(x) < maxlen:
                new_train_set_x.append(x)
                new_train_set_y.append(y)
        train_set = (new_train_set_x, new_train_set_y)
    # split training set into validation set
    train_set_x, train_set_y = train_set
    n_samples = len(train_set_x)
    numpy.random.seed(0)
    sidx = numpy.random.permutation(n_samples)
    n_train = int(numpy.round(n_samples * (1. - valid_portion)))
    valid_set_x = [train_set_x[s] for s in sidx[n_train:]]
    valid_set_y = [train_set_y[s] for s in sidx[n_train:]]
    train_set_x = [train_set_x[s] for s in sidx[:n_train]]
    train_set_y = [train_set_y[s] for s in sidx[:n_train]]

    train_set = (train_set_x, train_set_y)
    valid_set = (valid_set_x, valid_set_y)

    def remove_unk(set_x):
        return [[1 if w >= n_words else w for w in sen] for sen in set_x]

    train_set_x, train_set_y = train_set
    valid_set_x, valid_set_y = valid_set

    train_set_x = remove_unk(train_set_x)
    valid_set_x = remove_unk(valid_set_x)

    def len_argsort(seq):
        return sorted(range(len(seq)), key=lambda set_x: len(seq[set_x]))

    if sort_by_len:
        sorted_index = len_argsort(valid_set_x)
        valid_set_x = [valid_set_x[i] for i in sorted_index]
        valid_set_y = [valid_set_y[i] for i in sorted_index]

        sorted_index = len_argsort(train_set_x)
        train_set_x = [train_set_x[i] for i in sorted_index]
        train_set_y = [train_set_y[i] for i in sorted_index]

    train = (train_set_x, train_set_y)
    valid = (valid_set_x, valid_set_y)

    return train, valid


def generate_disease_dept_name(disease_id_dept_file):
    """
    生成disease id和department name
    :param
    disease_id_dept_file: 文件路径
    返回值: disease_id_dept: dict 格式：{disease_id: dept_name}
    """
    disease_id_dept = dict()
    with open(disease_id_dept_file, 'r') as f:
        for row in f:
            row = row.strip().split(',,')
            disease_id_dept[row[1]] = row[2].split('|')
    return disease_id_dept


def process_line(line):
    """
    :param line: 对于固定的一行数据
    :return: 返回分割以后的数据，其中x：list y：list
    """
    y_str, x_str = line.strip().split(' ')
    x_list = [int(x) for x in x_str.split(',')]
    y_list = [int(y_str)]
    x = numpy.array(x_list)
    y = numpy.array(y_list)
    return x, y


def generate_arrays_from_file(path, batch_size, num=200, classes=45, padding='pre'):
    """

    :param path: 训练数据路径
    :param batch_size:每次读取文件行数
    :return: 返回x和y的训练数据 其中x已经padding 而y已经to_catego
    """
    while 1:
        f = codecs.open(path, 'r', encoding='utf-8')
        cnt = 0
        X = []
        Y = []
        for line in f:
            x, y = process_line(line)
            X.append(x)
            Y.append(y)
            cnt += 1
            if cnt == batch_size:
                cnt = 0
                X = numpy.array(X)
                Y = numpy.array(Y)
                X = pad_sequences(X, padding=padding, maxlen=num)
                Y = to_categorical(Y, num_classes=classes)
                yield (numpy.array(X), numpy.array(Y))
                X = []
                Y = []
    f.close()


def get_test_data(test_file, num=200, classes=45, padding='pre'):
    """
    :param test_file: 测试数据文件
    :param num: 字符长度
    :param classes: 多少类
    :param padding: padding的方式
    :return: 返回训练数据
    """
    print('test', num, classes)
    x_test, y_test = load_file(test_file)
    x_test = pad_sequences(x_test, padding=padding, maxlen=num)
    y_test = to_categorical(y_test, num_classes=classes)
    return x_test, y_test

if __name__ == '__main__':
    load_data_intention_union('/home/renyx/work/model_data/intent_2019/04_09/lstm_union_train_04_09.txt')
