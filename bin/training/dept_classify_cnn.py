# coding=utf8
import os
# import tensorflow as tf
# config = tf.ConfigProto()
# config.gpu_options.allow_growth = True
# session = tf.Session(config=config)
import numpy as np
import pandas as pd

from keras.models import Model, save_model, load_model, model_from_json
from keras.layers import Dense, Dropout, Flatten, Input, MaxPooling1D, \
    GlobalMaxPooling1D, Convolution1D, Embedding
from keras.layers.merge import Concatenate
# from mednlp.utils.utils import pprint
import sys

# sys.path.append('/home/zhoulg1/work/mednlp/mednlp/class_dept/scr/textCNN')
from gensim.models import word2vec
from os.path import join, exists, split

import re
import itertools
from collections import Counter
from keras.utils.np_utils import to_categorical
from sklearn.preprocessing import LabelEncoder
import jieba
import pickle
import h5py
import global_conf


os.environ["CUDA_VISIBLE_DEVICES"] = "2"
RELATIVE_PATH = os.path.dirname(__file__) + '/'
cfg_path = RELATIVE_PATH + 'etc/cdss.cfg'
dict_path = RELATIVE_PATH + 'data/dict/'
traindata_path = RELATIVE_PATH + 'data/traindata/'


class SaveLoadData(object):
    """
    读入训练数据，并保存
    """
    def __init__(self, fname):
        self.fpath = os.path.join(traindata_path, fname)

    def is_path_exist(self):
        return True if os.path.exists(self.fpath) else False

    def pkl_save(self, data):
        print '【saving pkl data】=> {}'.format(self.fpath)
        if not self.is_path_exist():
            with open(self.fpath, 'w') as f:
                pickle.dump(data, f)
        else:
            raise ValueError('data path exist')

    def pkl_load(self):
        print '【loading pkl data】=> {}'.format(self.fpath)
        if self.is_path_exist():
            with open(self.fpath, 'r') as f:
                return pickle.load(f)
        else:
            raise ValueError('data path not exist')


def _get_train_data():
    """
    转码unicode
    验证行列读取正确
    输出各个字段，dataframe
    :return:
    """
    print "get train data"
    fname = 'traindata_dept_classify_valid.txt'
    # fname = 'traindata_dept_classify_consult_result.txt'
    cols = ['sen', 'sex', 'age', 'dept']
    fpath = os.path.join(traindata_path, fname)
    with open(fpath, 'r') as f:  # 读取文件比pd快，准。
        texts = f.readlines()
    texts = [text.decode('utf8') for text in texts]
    texts = [text.split('\t') for text in texts if not re.match('\n', text)]  # 解析字段并去掉10万量级的回车行
    df = pd.DataFrame(texts, columns=cols)
    df.sex.replace(u'男', '1', inplace=True)
    df.sex.replace(u'女', '2', inplace=True)
    df['dept'] = df.dept.str.replace('\n', '')
    df.loc[df.dept == u'眼科9', 'dept'] = u'眼科'  # 眼科有一条科室名为眼科9，但其他字段没错，就改了字段名。
    if 0:
        # 整体信息 246619whole 240262unique
        print df.info()
        print df.describe()
        print df.dept.value_counts()
        print df.sen.str.len().describe([0.9, 0.99, 0.999])
    if 0:
        # 分析长短句
        print df.sen.str.len().max(), df.sen.str.len().min()  # 2887,1
        print df.ix[df.sen.str.len().argmax(), 'sen']  # 语句正常
        print df.ix[df.sen.str.len().argmin(), 'sen']
        clen = 6
        print df.ix[df.sen.str.len() < clen].sample(100)
        print df.ix[df.sen.str.len() < clen].describe()
        print df.ix[df.sen.str.len() < clen].dept.value_counts()
    if 0:
        print "--------分析行duplicate------------"
        dup_mask = df.duplicated(keep='first')
        dupdf = df.loc[dup_mask]
        print dupdf.info()
        print dupdf.describe()
        print dupdf.dept.value_counts()
        print "--------print dupdf.head(200)------------"
        print dupdf.head(200)
        print "--------print dupdf.sample(200)------------"
        print dupdf.sample(200)
        print "--------print dupdf.tail(200)------------"
        print dupdf.tail(200)
        print dupdf.sen.str.len().describe([0.9, 0.99, 0.999])
        # 结论：重复性数据为正常数据，去重即可；共8080条,keepfirst后重复4388
    if 0:
        print "--------分析 sen duplicate------------"
        print df.sen.value_counts().head(100)

    if 1:
        # 预处理 V1
        df = df.drop_duplicates()
        df = df.loc[df.sen.str.len() > 3]
        df = df.loc[df.sen != u'问题描述:']  # 去掉132行
        df = df.loc[df.sen != u'请您尽可能详细的描述您的发病时间、主要症状，医生会根据您的描述给予详细的回复。']  # 去掉28行
    if 0:
        print df.info()
        print df.describe()
        print df.dept.value_counts()
        print df.sen.str.len().describe([0.9, 0.99, 0.999])
        """
                                       sen     sex     age        dept
        count                       241882  241882  241882      241882
        unique                      240180     111     297          40
        top     得了老年抑郁症该怎么办啊？       1      25  耳鼻咽喉科
        freq                            13  123359   10575        8887

        count    241910.000000
        mean         67.895564
        std          63.351303
        min           4.000000
        50%          54.000000
        90%         126.000000
        99%         310.000000
        99.9%       636.091000
        max        2887.000000
        """
    return df[['sen', 'dept']]


def _get_test_data():
    """
    转码unicode
    验证行列正确
    输出各个字段，dataframe
    :return:
    """
    print "get test data"
    fname = 'consult_test_20180110_new.txt'
    cols = ['sen', 'dept', 'dept2', 'age', 'sex']  # age sex未研究  dept 39个
    fpath = os.path.join(traindata_path, fname)
    with open(fpath, 'r') as f:
        texts = f.readlines()
    texts = [text.decode('utf8') for text in texts]
    texts = [text.split('\t') for text in texts]
    df = pd.DataFrame(texts, columns=cols)
    if 0:
        print df.info()
        print df.describe()
        print df.dept.value_counts()
        print df.dept2.value_counts()
    return df[['sen', 'dept', 'dept2']]


def gen_label_encoding_dict():
    print "------------  gen_lable_encoding_dict  -------------"
    df = _get_train_data()
    uni_dept = df.dept.unique()
    dept2ind_dict = {d: i for i, d in enumerate(uni_dept)}
    fname = 'LABELs_categorical_dict.pkl'
    fpath = os.path.join(traindata_path, fname)
    with open(fpath, 'w') as f:
        pickle.dump(dept2ind_dict, f)


def load_label_encoding_dict():
    print "------------  load_label_encoding_dict  -------------"
    fname = 'LABELs_categorical_dict.pkl'
    fpath = os.path.join(traindata_path, fname)
    with open(fpath, 'r') as f:
        dept2ind_dict = pickle.load(f)

    assert len(dept2ind_dict) == 40, 'dept2ind_dict wrong'
    return dept2ind_dict


def encoding_labels(labels_list):
    d2i = load_label_encoding_dict()
    # assert set(labels_list) <= set(d2i.keys()), 'label_list out of bound!'
    print "-------- label unique number: {}--------".format(len(set(labels_list)))
    labels_index = [d2i.get(label, 'oob') for label in labels_list]
    if 'oob' in labels_index:
        labels_index = ['40' if label == 'oob' else label for label in labels_index]
        labels_cat = to_categorical(labels_index)[:, 0:40]
    else:
        labels_cat = to_categorical(labels_index)
    return labels_cat


def decoding_labels(labels_cat):
    labels_cat = labels_cat.tolist()
    labels_index = [np.argmax(label) for label in labels_cat]
    d2i = load_label_encoding_dict()
    i2d = {v: k for k, v in d2i.items()}
    labels_list = [i2d[label] for label in labels_index]
    return labels_list


def pad_sentences(sentences, lenth=200, padding_word="</>"):
    if lenth:
        sequence_length = lenth
    else:
        sequence_length = max(len(x) for x in sentences)
    padded_sentences = []
    for i in range(len(sentences)):
        sentence = sentences[i]
        num_padding = sequence_length - len(sentence)
        new_sentence = sentence + [padding_word] * num_padding
        padded_sentences.append(new_sentence)
    return padded_sentences


def load_seg_pad_sens(field='train', num=10000, version='V1', padlen=200, padding_word="<PAD>"):  # 直接切除尾部

    print "--------------   load_seg_pad_sens   ----------------"
    fname = 'SENS_{}_num{}_prep{}_jiebaSeg_pad{}wrd{}.h5'.format(
        field, 'ALL' if num == 0 else num, version, padlen, padding_word)
    fpath = os.path.join(traindata_path, fname)
    if os.path.exists(fpath):
        print 'load exsit seg_pad_sens:【{}】'.format(fpath)
        with h5py.File(fpath, 'r') as f:
            sens = f['sentences'][:]
            return sens.tolist()
    else:
        f = h5py.File(fpath, 'w')
        print 'no exsit seg_pad_sens! do preprocessing....'
        df = eval('_get_{}_data()'.format(field))
        if num:
            df = df.sample(num, random_state=0)
        sens = df.sen.tolist()
        sens = [jieba.lcut(s)[0:padlen] for s in sens]
        sens = pad_sentences(sens, lenth=padlen, padding_word=padding_word)
        arr = np.array(sens, dtype=object)
        string_dt = h5py.special_dtype(vlen=unicode)
        f.create_dataset('sentences', data=arr, dtype=string_dt)
        f.close()
        return sens


def load_seg_pad_sens_MedDict(field='train', num=10000, version='V1', padlen=200, padding_word="<PAD>"):  # 直接切除尾部
    print "--------------   load_seg_pad_sens_MedDict   ----------------"
    fname = 'SENS_{}_num{}_prep{}_jiebaSegDic_pad{}wrd{}.h5'.format(
        field, 'ALL' if num == 0 else num, version, padlen, padding_word)
    fpath = os.path.join(traindata_path, fname)
    if os.path.exists(fpath):
        print 'load exsit segDic_pad_sens:【{}】'.format(fpath)
        with h5py.File(fpath, 'r') as f:
            sens = f['sentences'][:]
            return sens.tolist()
    else:
        f = h5py.File(fpath, 'w')
        print 'no exsit segDic_pad_sens! do preprocessing....'
        df = eval('_get_{}_data()'.format(field))
        if num:
            df = df.sample(num, random_state=0)
        sens = df.sen.tolist()
        jieba.load_userdict(dict_path)
        sens = [jieba.lcut(s)[0:padlen] for s in sens]
        sens = pad_sentences(sens, lenth=padlen, padding_word=padding_word)
        arr = np.array(sens, dtype=object)
        string_dt = h5py.special_dtype(vlen=unicode)
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
        print mm.head(100)
        print mm.sample(100)
        print mm.tail(100)
    # 结论，test数据挺合理，没有杂乱词
    # train 里面，低频词都不是啥好词，错别字多；高频词通用词较多。
    return [vocabulary_w2ind, vocabulary_ind2w]


def load_vocab(fname='VOCABdict_from_trainALL.pkl'):
    print "------------  load_label_encoding_dict  -------------"
    f = SaveLoadData(fname)
    if f.is_path_exist():
        return f.pkl_load()
    else:
        sens = load_seg_pad_sens('train', num=0)
        w2i, i2w = build_vocabulary_dict(sens)
        data = {'w2i': w2i, 'i2w': i2w}
        f.pkl_save(data)
        return data


class Vector(object):
    def __init__(self,
                 num_features=50,
                 min_word_count=1,
                 context=10):
        self.num_features = num_features
        self.min_word_count = min_word_count
        self.context = context
        self.fname = "VECTOR_from_DATAnum{}__{:d}features_{:d}minwords_{:d}context_{:d}padlen". \
            format("ALL", self.num_features, self.min_word_count, self.context, 200)
        # self.fname = 'consult_order_reply_jiebacut_utf8_100dim_5c_5mc_0seed.gs_vec_model'
        self.fpath = join(traindata_path, self.fname)
        self.loaded_model = None

    def train(self):
        print '--------- Training Word2Vec model: {}'.format(self.fname)
        sens = load_seg_pad_sens(num=0)
        model = word2vec.Word2Vec(sens,
                                  size=self.num_features,
                                  min_count=self.min_word_count,
                                  window=self.context,
                                  workers=4,
                                  sample=1e-3)
        model.init_sims(replace=True)
        print 'Saving Word2Vec model: {}'.format(self.fpath)
        model.save(self.fpath)
        self.loaded_model = model
        return self.loaded_model

    def load(self):
        if self.loaded_model:
            return self.loaded_model
        elif exists(self.fpath):
            print 'Loading Word2Vec model: {}'.format(self.fname)
            model = word2vec.Word2Vec.load(self.fpath)
            self.loaded_model = model
            return self.loaded_model
        else:
            self.train()

    def get_weights(self):
        vocab_dict = load_vocab()
        i2w = vocab_dict.get('i2w')
        model = self.load()
        # add unknown words
        weights = {
            key: model[word] if word in model
            else np.random.uniform(-0.25, 0.25, model.vector_size)
            for key, word in i2w.items()
        }

        return weights

    def tes1t1_model(self, testwords=u'高血压，头痛'):
        print "-----test_vector_model-----"
        model = self.load()
        ws = testwords.split(u'，')
        for w in ws:
            lw = []
            lw.append(w)
            data = model.most_similar(positive=lw)
            print u'-------【 {} 】---------'.format(w)
            # pprint(data)


def shufdata(x, y, val_ratio=0.2, randst=0):
    np.random.seed(randst)
    shuffle_indices = np.random.permutation(np.arange(len(y)))
    x = np.array(x)
    x = x[shuffle_indices]

    y = y[shuffle_indices]
    train_len = int(len(x) * (1 - val_ratio))
    x_train = x[:train_len]
    y_train = y[:train_len]
    x_test = x[train_len:]
    y_test = y[train_len:]
    return x_train, y_train, x_test, y_test


class Param(object):
    def __init__(self, rd):
        # Model Hyperparameters
        self.sequence_length = 200
        self.embedding_dim = 100
        self.min_word_count = 1
        self.context = 10
        self.filter_sizes = [1]
        self.num_filters = 80  # 80
        self.dropout_prob = (0.5, 0.5)
        # self.hidden_dims = 1000
        self.output_dims = 40
        # Training parameters
        self.val_ratio = 0.2
        self.num_sens = 0
        self.rdstate = rd
        self.batch_size = 256
        self.num_epochs = 4
        # self.num_epochs = 45
        # self.num_epochs = 20
        # self.model_name = 'origin{}'.format(self.rdstate)  # muti_layer_conv  origin  origin1_diff_size_num
        # self.model_name = 'muti_layer_conv{}'.format(self.rdstate)
        self.model_name = 'origin1_diff_size_num{}'.format(self.rdstate)
        # self.model_name = 'muti_layer_conv_large'  # 不建议使用
        self.model_path = os.path.join(traindata_path, self.model_name)
        self.loaded_model = None


class Cnnd(Param):
    def model_1(self):
        weights_dic = Vector(self.embedding_dim,
                             self.min_word_count, self.context).get_weights()
        weights = np.array([v for v in weights_dic.values()])
        model_input = Input(shape=(self.sequence_length,))
        z = Embedding(len(weights), self.embedding_dim, input_length=self.sequence_length, name="embedding")(
            model_input)
        z = Dropout(self.dropout_prob[0])(z)

        if self.model_name == 'origin{}'.format(self.rdstate):
            conv_blocks = []
            for sz in (2, 20):
                conv = Convolution1D(filters=100,
                                     kernel_size=sz,
                                     padding="valid",
                                     activation="relu",
                                     strides=1)(z)
                conv = MaxPooling1D(pool_size=2)(conv)
                conv = Flatten()(conv)
                conv_blocks.append(conv)
            z = Concatenate()(conv_blocks) if len(conv_blocks) > 1 else conv_blocks[0]

            z = Dropout(self.dropout_prob[1])(z)
            z = Dense(1000, activation="relu")(z)
            z = Dropout(0.5)(z)

            model_output = Dense(40, activation="softmax")(z)

            """
            100,(2,20), 4epoch,top12:0.728,0.806,tran val 0.7377,0.7374
            """

        if self.model_name == 'origin1_diff_size_num{}'.format(self.rdstate):
            conv_blocks = []
            sz1, sz2, sz3, sz4, sz5 = 1, 2, 3, 12, 30
            fn1, fn2, fn3, fn4, fn5 = 120, 100, 80, 50, 10
            # conv size 1
            conv1 = Convolution1D(filters=fn1,
                                  kernel_size=sz1,
                                  padding="valid",
                                  activation="relu",
                                  strides=1)(z)
            conv1 = MaxPooling1D(pool_size=2)(conv1)
            conv1 = Flatten()(conv1)

            conv2 = Convolution1D(filters=fn2,
                                  kernel_size=sz2,
                                  padding="valid",
                                  activation="relu",
                                  strides=1)(z)
            conv2 = MaxPooling1D(pool_size=2)(conv2)
            conv2 = Flatten()(conv2)

            conv3 = Convolution1D(filters=fn3,
                                  kernel_size=sz3,
                                  padding="valid",
                                  activation="relu",
                                  strides=1)(z)
            conv3 = MaxPooling1D(pool_size=2)(conv3)
            conv3 = Flatten()(conv3)

            conv4 = Convolution1D(filters=fn4,
                                  kernel_size=sz4,
                                  padding="valid",
                                  activation="relu",
                                  strides=1)(z)
            conv4 = MaxPooling1D(pool_size=2)(conv4)
            conv4 = Flatten()(conv4)

            conv5 = Convolution1D(filters=fn5,
                                  kernel_size=sz5,
                                  padding="valid",
                                  activation="relu",
                                  strides=1)(z)
            conv5 = MaxPooling1D(pool_size=2)(conv5)
            conv5 = Flatten()(conv5)

            z = Concatenate()([conv1, conv2, conv3, conv4, conv5])

            z = Dropout(self.dropout_prob[1])(z)
            z = Dense(1000, activation="relu")(z)
            z = Dropout(0.5)(z)

            model_output = Dense(40, activation="softmax")(z)
        if self.model_name == 'muti_layer_conv{}'.format(self.rdstate):
            conv1 = Convolution1D(filters=64, kernel_size=3, strides=1,
                                  padding="valid", activation="relu")(z)
            pool1 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv1)

            conv2 = Convolution1D(filters=64, kernel_size=3, strides=1,
                                  padding="valid", activation="relu")(pool1)
            pool2 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv2)

            conv3 = Convolution1D(filters=64, kernel_size=3, strides=1,
                                  padding="valid", activation="relu")(pool2)
            pool3 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv3)

            z = Flatten()(pool3)
            z = Dense(200, activation="relu")(z)
            z = Dropout(self.dropout_prob[1])(z)
            model_output = Dense(self.output_dims, activation="softmax")(z)

        if self.model_name == 'muti_layer_conv_large{}'.format(self.rdstate):
            conv1 = Convolution1D(filters=64, kernel_size=2, strides=1,
                                  padding="valid", activation="relu")(z)
            pool1 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv1)

            conv2 = Convolution1D(filters=64, kernel_size=2, strides=1,
                                  padding="valid", activation="relu")(pool1)
            pool2 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv2)

            conv3 = Convolution1D(filters=64, kernel_size=2, strides=1,
                                  padding="valid", activation="relu")(pool2)
            pool3 = MaxPooling1D(pool_size=2, strides=None, padding='valid')(conv3)

            z = Flatten()(pool3)
            z = Dense(200, activation="relu")(z)
            z = Dropout(self.dropout_prob[1])(z)
            model_output = Dense(self.output_dims, activation="softmax")(z)

        model = Model(model_input, model_output)
        model.compile(loss="categorical_crossentropy",
                      metrics=["categorical_accuracy"],
                      optimizer="adam")
        print "Initializing embedding layer with word2vec weights, shape", weights.shape
        embedding_layer = model.get_layer("embedding")
        embedding_layer.set_weights([weights])
        return model

    def _get_data(self, field='train', num=10000, rdstate=0):
        sens = load_seg_pad_sens(field=field, num=num)  # 该函数缺random_state
        vocab = load_vocab()
        w2i = vocab.get('w2i')
        _pad = w2i['<PAD>']
        sens_int = [[w2i.get(w, _pad) for w in sen] for sen in sens]

        get_field_data = "_get_{}_data()".format(field)
        if field == 'train':
            if num:
                labels = eval(get_field_data).dept.sample(num, random_state=rdstate).tolist()
            else:
                labels = eval(get_field_data).dept.tolist()
            labels_cat = encoding_labels(labels)
            return sens_int, labels_cat

        elif field == 'test':
            data = eval(get_field_data)
            labels_cat = encoding_labels(data.dept.tolist())
            labels2_cat = encoding_labels(data.dept2.tolist())
            print labels2_cat
            return sens_int, labels_cat, labels2_cat

        else:
            raise ValueError('field wrong!')

    def get_tvdata(self):
        x, y = self._get_data(field='train', num=self.num_sens)
        self.x_train, self.y_train, self.x_val, self.y_val = shufdata(x, y, self.val_ratio, self.rdstate)

    def load_model(self, name=None):
        if name:
            path = os.path.join(traindata_path, name)
            if os.path.exists(path):
                print "load exist model: {}".format(name)
            self.loaded_model = load_model(path)
            print self.loaded_model.summary()
            return self.loaded_model

        self.get_tvdata()
        if self.loaded_model:
            print self.loaded_model.summary()
            return self.loaded_model
        elif os.path.exists(self.model_path):
            print "load exist model: {}".format(self.model_name)
            self.loaded_model = load_model(self.model_path)
            print self.loaded_model.summary()

        else:
            print 'training model:{} '.format(self.model_name)
            model = self.model_1()
            print model.summary()
            model.fit(self.x_train, self.y_train,
                      validation_data=(self.x_val, self.y_val),
                      batch_size=self.batch_size,
                      epochs=self.num_epochs,
                      verbose=2)
            print 'saving model:{} '.format(self.model_name)
            model.save(self.model_path)
            self.loaded_model = model

        return self.loaded_model

    def evaluate_top12(self):
        print "------  evaluate  --------"
        model = self.load_model()
        x, y, y2 = self._get_data('test', 0)
        top1 = model.evaluate(x, y)[1]
        top2 = model.evaluate(x, y2)[1] + top1
        return top1, top2

    def sum_model(self, names=[]):
        x, y, y2 = self._get_data('test', 0)

        y_preds = []
        for modelname in names:
            model = self.load_model(modelname)
            y_pred = model.predict(x)
            y_preds.append(y_pred)

        y_pred_sum = reduce(lambda x, y: x + y, y_preds)

        y_pred_avr = y_pred_sum / 3.0

        print y_pred_avr[0:3]

        y_pred_01 = np.zeros(y_pred_avr.shape)
        for line in np.arange(y_pred_avr.shape[0]):
            argm = np.argmax(y_pred_avr[line])
            y_pred_01[line, argm] = 1

        dot1 = np.sum(np.multiply(y, y_pred_01))
        dot2 = np.sum(np.multiply(y2, y_pred_01))
        acc1 = dot1 / y_pred_01.shape[0]
        acc2 = (dot1 + dot2) / y_pred_01.shape[0]

        print '----- sum model  top1 , 2'
        print acc1, acc2
        return acc1, acc2

    def error_analize(self):
        print "------  error_analize  --------"
        model = self.load_model()
        y = self.y_val
        y_pred = model.predict(self.x_val)
        y_pred_01 = np.zeros(y_pred.shape)

        for line in np.arange(y_pred.shape[0]):
            argm = np.argmax(y_pred[line])
            y_pred_01[line, argm] = 1
        accs = []
        recalls = []
        index_int = np.arange(y.shape[1])
        for dept in index_int:
            y_dept = y[:, dept]
            y_pred_dept = y_pred_01[:, dept]
            dot = float(np.dot(y_dept, y_pred_dept))
            print dot
            acc = dot / np.sum(y_pred_dept)
            recall = dot / np.sum(y_dept)
            accs.append(acc)
            recalls.append(recall)
        dept2i = load_label_encoding_dict()
        i2dept = {v: k for k, v in dept2i.items()}
        index = [i2dept[i] for i in index_int]
        df = pd.DataFrame(data={'acc': accs, 'recalls': recalls}, index=index)
        y = decoding_labels(y)
        y_pred_01 = decoding_labels(y_pred_01)
        y_i = np.array([dept2i[d] for d in y])
        y_pred01_i = np.array([dept2i[d] for d in y_pred_01])

        return accs, recalls, df, index, y_i, y_pred01_i


def my_confusion_matrix(y_true, y_pred, index):
    from sklearn.metrics import confusion_matrix

    conf_mat = confusion_matrix(y_true, y_pred, range(len(index)))
    print "confusion_matrix(left labels: y_true, up labels: y_pred):"
    print "labels\t",
    for i in range(len(index)):
        print index[i], "\t",
    print
    for i in range(len(conf_mat)):
        print i, "\t",
        for j in range(len(conf_mat[i])):
            print conf_mat[i][j], '\t',
        print
    print


def my_classification_report(y_true, y_pred, index):
    from sklearn.metrics import classification_report
    print "classification_report(left: labels):"
    print classification_report(y_true, y_pred, target_names=index)


if __name__ == '__main__':
    model = Cnnd(rd=10)
    print model.load_model()

