#!/usr/bin/python
# -*- coding: utf8 -*-
import os
import re
import sys
import time
import json
import jieba
import codecs
import global_conf
import numpy as np
import pandas as pd
import jieba.posseg as psg
from gensim.models import word2vec
from ailib.storage.db import DBWrapper
from sklearn.metrics import classification_report
from sklearn.cross_validation import train_test_split
reload(sys)
sys.setdefaultencoding( "utf-8" )
from keras import backend as K
K.backend()
from keras.models import model_from_json, Model
from keras.layers.merge import Concatenate
from keras.callbacks import EarlyStopping
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers import Conv1D, MaxPooling1D, Embedding, GlobalMaxPooling1D, Input

### 设置初始化路径
cfg_path = global_conf.cfg_path
dict_path = global_conf.dict_path
training_path = os.path.dirname(__file__) + '/' + 'bin/training/'
train_data_path = os.path.dirname(__file__) + '/' + 'data/traindata/'
entity_dict = os.path.dirname(__file__) + '/' + 'data/dict/entity_dict.txt'


### 装饰器查看 模型运行时间
def print_time(func):
    def warp(*args, **kwargs):
        time_start = time.time()
        fun_result = func(*args, **kwargs)
        time_end = time.time()
        print('The model costs time is %.2f s'%(time_end - time_start))
        return  fun_result
    return warp

### 可以将字典格式的json串，print出中文来，方便查看
def Encode(data):
    return json.dumps(data, encoding='UTF-8', ensure_ascii=False)


def entity_dict_from_sql():
    """
    所有医学相关的实体词和词性
    :return: => 写入到 entity_dict.txt
    """
    sql = """
    SELECT a.entity , a.freq, a.pos
        FROM ai_medical_knowledge.medical_domain_entity a
    """
    db = DBWrapper(cfg_path, 'mysql', 'AIMySQLDB')

    entity_dict = codecs.open(entity_dict, 'w', encoding='utf8')

    rows = db.get_rows(sql)
    medical_dict = {}
    count = 1
    for row in rows:
        words = row['entity'].strip()
        freq = row['freq'].strip()
        pos = row['pos'].strip()
        print words, freq, pos
        entity_dict.write(words + ' ' + freq + ' ' + pos + '\n')
        count += 1

    entity_dict.close()
    db.close()


def get_sample_from_sql():
    """
    input: mysql code
    :return:dataframe
    """
    sql = """
    SELECT id,disease_name,definition,cause,pathogenesis,pathophysiological,clinical_manifestation,
          complication,lab_check,other_check,diagnosis,differential_diagnosis,treatment,prevention,
          prognosis  FROM medical_kg.disease_detail
    """
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB')
    rows = db.get_rows(sql)
    keys_list = ['id', 'disease_name', 'definition', 'cause', 'pathogenesis', 'pathophysiological', 'clinical_manifestation',\
                    'complication', 'lab_check', 'other_check', 'diagnosis', 'differential_diagnosis', 'treatment', 'prevention',\
                    'prognosis']
    len_txt = len(keys_list)

    disease_list = []
    sen_list = []
    label_list = []

    for row in rows:
        for j in range(2, len_txt):
            disease_list.append(row['disease_name'])
            sen = row[keys_list[j]]
            sen_list.append(sen)
            label_list.append(keys_list[j])

    df = pd.DataFrame(disease_list, columns=['disease_name'])
    df['label'] = label_list
    df['sen'] = sen_list

    db.close()
    return df

@print_time
def data_transform_split(fname):
    df_data = get_sample_from_sql()
    ##切分句子，将其按照。和换行符切分为断句，保留句子长度大于5的
    ##写出样本集

    entity_dict = global_conf.entity_dict
    jieba.load_userdict(entity_dict)

    path_traindata = os.path.join(train_data_path, fname)
    output_file = codecs.open(path_traindata, 'w', encoding='utf8')
    path_training = os.path.join(training_path, 'corpus.utf8')
    corpus_data = codecs.open(path_training, 'w', encoding='utf8')
    sen_list = df_data['sen'].tolist()
    disease_list = df_data['disease_name'].tolist()
    label_list = df_data['label'].tolist()
    for index, label in enumerate(label_list):
        if label != 'clinical_manifestation':
            label_list[index] = '0'
        else:
            label_list[index] = '1'

    for index, sen in enumerate(sen_list):
        if sen:##如果句子存在，则利用句号和换行符对句子进行切分
            sen_split = re.split(u'。|\n', sen.decode('utf8'))
            for lit_sen in sen_split:
                if len(lit_sen) > 5:###保留句子长度大于5个字符的
                    lit_sen = lit_sen.strip()
                    lit_sen = re.sub('\t', '', lit_sen)
                    split_sen =" ".join(jieba.lcut(str(lit_sen)))
                    corpus_data.write(split_sen + '\n')
                    output_file.write(disease_list[index] + '\t' + label_list[index] + '\t' + lit_sen + '\n')
                else:
                    pass
        else:
            pass
    corpus_data.close()
    output_file.close()

@print_time
def word2vec_model(inputdata):
    '''
    inputdata:只支持两种，一种是列表，直接进行word2vec；一种是txt(utf8等corpus_data)(分词后的文件)大的文件，用 word2vec.Text8Corpus()函数转化成训练
    eg：sentences = [["cat", "say", "meow"], ["dog", "say", "woof"]],列表套列表的格式
    output: 模型
    参数：
    sentences:可以是一个列表，对于大语料集，建议使用BrownCorpus,Text8Corpus或lineSentence构建。
    size：是指特征向量的维度，默认为100。大的size需要更多的训练数据,但是效果会更好. 推荐值为几十到几百。
    sg： 用于设置训练算法，默认为0，对应CBOW算法；sg=1则采用skip-gram算法。
    window：表示当前词与预测词在一个句子中的最大距离是多少
    alpha: 是学习速率
    seed：用于随机数发生器。与初始化词向量有关。
    min_count: 可以对字典做截断. 词频少于min_count次数的单词会被丢弃掉, 默认值为5
    max_vocab_size: 设置词向量构建期间的RAM限制。如果所有独立单词个数超过这个，则就消除掉其中最不频繁的一个。每一千万个单词需要大约1GB的RAM。设置成None则没有限制。
    sample: 高频词汇的随机降采样的配置阈值，默认为1e-3，范围是(0,1e-5)
    workers：参数控制训练的并行数。
    hs: 如果为1则会采用hierarchica·softmax技巧。如果设置为0（default），则negative sampling会被使用。
    negative: 如果>0,则会采用negativesamp·ing，用于设置多少个noise words
    cbow_mean: 如果为0，则采用上下文词向量的和，如果为1（default）则采用均值。只有使用CBOW的时候才起作用。
    hashfxn： hash函数来初始化权重。默认使用python的hash函数
    iter： 迭代次数，默认为5
    trim_rule： 用于设置词汇表的整理规则，指定那些单词要留下，哪些要被删除。可以设置为None（min_count会被使用）或者一个接受()并返回RU·E_DISCARD,uti·s.RU·E_KEEP或者uti·s.RU·E_DEFAU·T的函数。
    sorted_vocab： 如果为1（default），则在分配word index 的时候会先对单词基于频率降序排序。
    batch_words：每一批的传递给线程的单词的数量，默认为10000
    '''
    path_traindata =os.path.join(global_conf.training_path, 'clinical_word2vec.model')

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    if isinstance(inputdata, list):
        sentences = inputdata
    else:
        sentences = word2vec.Text8Corpus(inputdata)  # 加载语料
    model = word2vec.Word2Vec(sentences, size=100, min_count=2, sg=1, window=5, workers=8)

    model.save(path_traindata)


def word_order_generate(maxlen):
    corpus_path = os.path.join(training_path, 'corpus.utf8')
    text_data = codecs.open(corpus_path, 'r', encoding='utf8').readlines()
    ## 利用keras带的文本 分词器
    text_data = [str(x) for x in text_data]
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(text_data)

    ##将文本转化成向量模式（用每个词的序号代表每个词）
    sequences = tokenizer.texts_to_sequences(text_data)
    word_index = tokenizer.word_index
    print('Found %s unique tokens.' % len(word_index))
    data = pad_sequences(sequences, maxlen=maxlen)
    ### 写出 word_order
    word_order_json = os.path.join(train_data_path, 'word_order_dictionary.json')
    with open(word_order_json, "w") as f:
        json.dump(word_index, f)
    
    return data, word_index


def embedding_matrix_generate(model_path, word_index, maxlen):
    path_model = os.path.join(training_path, model_path)
    w2v_model = word2vec.Word2Vec.load(path_model)

    ### 词向量矩阵
    embedding_matrix = np.random.random((len(word_index)+1, maxlen))
    for word, i in word_index.items():
        try:
            embedding_vector = w2v_model.wv[word.decode('utf8')]
            # print word
        except:
            embedding_vector = None
        if embedding_vector is not None:
            # words not found in embedding index will be all-zeros.
            embedding_matrix[i] = embedding_vector
    return embedding_matrix


def label_vector(label_list):
    labels = to_categorical(np.asarray(label_list))
    return labels


class Model_Train():
    def __init__(self, embedding_matrix, word_index_len,
                    maxlen=100, embedding_dim=100, batch_size=128, n_epochs=10, n_split=0.2):
        self.embedding_matrix = embedding_matrix
        self.word_index_len = word_index_len
        self.maxlen = maxlen
        self.embedding_dim = embedding_dim
        self.batch_size = batch_size
        self.n_epochs = n_epochs
        self.n_split = n_split


    def cnn_model(self):
        embedding_layer = Embedding(self.word_index_len + 1,
                                    self.embedding_dim,
                                    weights=[self.embedding_matrix],
                                    input_length=self.maxlen,
                                    trainable=True)

        sentence_input = Input(shape=(self.maxlen,), dtype='int32',name='sentence_input')
        embedded_sequences = embedding_layer(sentence_input)

        drop1 = Dropout(0.2)(embedded_sequences)
        con1 = Conv1D(128, 3, padding='valid', activation='relu', strides=1)(drop1)
        maxp1 = MaxPooling1D(3)(con1)

        con2 = Conv1D(128, 3, padding='valid', activation='relu', strides=1)(maxp1)
        maxp2 = MaxPooling1D(3)(con2)

        con3 = Conv1D(128, 3, padding='valid', activation='relu', strides=1)(maxp2)
        maxp3 = MaxPooling1D(3)(con3)

        fl = Flatten()(maxp3)
        dense1 = Dense(self.embedding_dim, activation='relu')(fl)
        dense2 = Dense(self.labels.shape[1], activation='softmax')(dense1)

        model = Model(sentence_input, dense2)
        model.summary()
        model.compile(loss='categorical_crossentropy', optimizer='rmsprop',
                metrics=['acc'])
        return model


    def atrous_cnn_model(self):## 膨胀卷积网络
        embedding_layer = Embedding(self.word_index_len + 1,
                                    self.embedding_dim,
                                    weights=[self.embedding_matrix],
                                    input_length=self.maxlen,
                                    trainable=True)

        sentence_input = Input(shape=(self.maxlen,), dtype='int32',name='sentence_input')
        embedded_sequences = embedding_layer(sentence_input)

        drop1 = Dropout(0.2)(embedded_sequences)
        con1 = Conv1D(128, 3, dilation_rate =1, padding='same', activation='relu')(drop1)
        con2 = Conv1D(128, 3, dilation_rate =2, padding='same', activation='relu')(con1)
        con3 = Conv1D(128, 3, dilation_rate =4, padding='same', activation='relu')(con2)
        con4 = Conv1D(128, 3, dilation_rate =8, padding='same', activation='relu')(con3)

        fl = Flatten()(con4)
        dense1 = Dense(self.embedding_dim, activation='relu')(fl)
        dense2 = Dense(self.labels.shape[1], activation='softmax')(dense1)

        model = Model(sentence_input, dense2)
        model.summary()
        model.compile(loss='categorical_crossentropy', optimizer='rmsprop',
                metrics=['acc'])
        return model


    def merge_cnn_model(self):
        embedding_layer = Embedding(self.word_index_len + 1,
                                    self.embedding_dim,
                                    weights=[self.embedding_matrix],
                                    input_length=self.maxlen,
                                    trainable=True)
        sentence_input = Input(shape=(self.maxlen,), dtype='int32',name='sentence_input')
        embedded_sequences = embedding_layer(sentence_input)

        sz1, sz2, sz3, sz4, sz5 = 1, 2, 3, 12, 30
        fn1, fn2, fn3, fn4, fn5 = 120, 100, 80, 50, 10
        # conv size 1
        conv1 = Conv1D(filters=fn1, kernel_size=sz1, padding="valid",
                              activation="relu", strides=1)(embedded_sequences)
        conv1 = MaxPooling1D(pool_size=2)(conv1)
        conv1 = Flatten()(conv1)

        conv2 = Conv1D(filters=fn2, kernel_size=sz2, padding="valid",
                              activation="relu", strides=1)(embedded_sequences)
        conv2 = MaxPooling1D(pool_size=2)(conv2)
        conv2 = Flatten()(conv2)

        conv3 = Conv1D(filters=fn3, kernel_size=sz3, padding="valid",
                              activation="relu", strides=1)(embedded_sequences)
        conv3 = MaxPooling1D(pool_size=2)(conv3)
        conv3 = Flatten()(conv3)

        conv4 = Conv1D(filters=fn4, kernel_size=sz4, padding="valid",
                              activation="relu", strides=1)(embedded_sequences)
        conv4 = MaxPooling1D(pool_size=2)(conv4)
        conv4 = Flatten()(conv4)

        conv5 = Conv1D(filters=fn5, kernel_size=sz5, padding="valid",
                              activation="relu", strides=1)(embedded_sequences)
        conv5 = MaxPooling1D(pool_size=2)(conv5)
        conv5 = Flatten()(conv5)

        z = Concatenate()([conv1, conv2, conv3, conv4, conv5])

        z = Dense(self.embedding_dim, activation="relu")(z)
        z = Dropout(0.5)(z)

        model_output = Dense(2, activation="softmax")(z)

        model = Model(sentence_input, model_output)
        model.summary()
        model.compile(loss='categorical_crossentropy', optimizer='rmsprop',
                metrics=['acc'])

        return model


    def train_model(self, data ,labels ,model_name):
        model = self.merge_cnn_model() ### 目前先用方法三
        stop = EarlyStopping(monitor='val_loss', patience=0, verbose=0, mode='auto')

        x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=self.n_split)
        # print y_test
        model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=self.n_epochs,
                        batch_size=self.batch_size, callbacks=[stop])
        ##保存模型
        #保留模型的配置、框架、权重等
        save_name =  os.path.join(training_path, model_name)
        model.save(save_name)
        ###结果验证
        y_true = np.argmax(y_test, axis=1)
        #print y_true
        y_predseq = model.predict(x_test)
        y_pred = np.argmax(y_predseq, axis=1)
        #print y_pred
        print(classification_report(y_true, y_pred, digits=4))

@print_time
def main(train_data_name, w2v_mdoel_name, iterations):
    '''
    train_data_name：训练模型的样本名称
    w2v_mdoel_name：word2vec模型的名称
    iterations：模型的迭代轮数
    '''
    inputfile_path = os.path.join(train_data_path, train_data_name)
    ##当 inputfile_path存在时直接调用，当不存在时利用函数生成，而后在调用
    if not os.path.exists(inputfile_path):
        data_transform_split(train_data_name)

    inputfile = codecs.open(inputfile_path, 'r', encoding='utf8').readlines()
    label_list = []
    for file in inputfile:
        label = re.split('\t', file)[1]
        label_list.append(label)

    labels = label_vector(label_list)
    # print labels

    data, word_index = word_order_generate(100)
    word_index_len = len(word_index)

    w2v_mdoel_path = os.path.join(training_path, w2v_mdoel_name)
    if not os.path.exists(w2v_mdoel_path):
        corpus_path = os.path.join(training_path, corpus.utf8)
        word2vec_model(corpus_path)

    embedding_matrix = embedding_matrix_generate(w2v_mdoel_name, word_index, 100)

    model = Model_Train(embedding_matrix, word_index_len,
                    maxlen=100, embedding_dim=100, batch_size=128, n_epochs=10, n_split=0.2)

    model_name = 'clinical_classify_model_{}.h5'.format(iterations)
    model.train_model(data, labels, model_name)


if __name__ == '__main__':
    main('train_data_clinical.utf8', "clinical_word2vec.model", 3)


