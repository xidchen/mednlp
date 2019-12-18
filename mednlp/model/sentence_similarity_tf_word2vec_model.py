#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentence_similarity_tf_word2vec_model.py -- 融合tfidf和word2vec的语义相似性模型

Author: caoxg <caoxg@guahao.com>
Create on 2018-09-29 星期六.
"""


import jieba
from ailib.model.base_model import BaseModel
import gensim.corpora as corpora
import gensim.models
import global_conf
import numpy as np
from mednlp.text.vector import Word2vector
import math
from mednlp.utils.utils import unicode_python_2_3


class SentenceModel(BaseModel):
    def initialize(self, model_version=1, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.dictionary = corpora.Dictionary.load(global_conf.sentence_dict)
        self.load_model()
        self.word2id()

    def load_model(self):
        """
        :param model_path: 模型路径
        :return: 加载模型
        """
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + str(version) + '.tfidf'
        self.model = gensim.models.TfidfModel.load(model_path)

    def sentence2vec(self, sentence):
        """
        :param sentence: 一句话
        :return: 返回这段话对应的词向量
        """
        vec_bow = self.dictionary.doc2bow((jieba.cut(sentence, cut_all=True)))
        return self.model[vec_bow]

    def word2id(self):
        """
        :return: 返回token到id和id到token的映射
        """
        self.token2id = self.dictionary.token2id
        self.id2token = dict(zip(self.token2id.values(), self.token2id.keys()))

    def word2vec(self, sentence):
        """
        :param sentence: 句子
        :return: 返回token和tfidf之间值得对应关系以字典返回
        """
        vec = self.sentence2vec(sentence)
        word_tfidf = {}
        for id, tfidf in vec:
            word_tfidf[self.id2token.get(id)] = tfidf
        return word_tfidf


class SentenceWordModel(BaseModel):
    def initialize(self, model_version=1, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.word2vec_dict = self.model_path + '_word2vec.' + str(model_version) + '.model.bin'
        self.word2vec_dict_vocab = self.word2vec_dict + '.vocab'
        self.word2vector = Word2vector(global_conf.dept_classify_cnn_dict_path)
        self.id2word = self.word2vector.id2word
        self.max_nb_words = len(self.id2word) + 1
        self.embedding_dim = 100
        self.embedding_matrix = self.get_weights()
        self.word2id = dict(zip(list(self.id2word.values()), list(self.id2word.keys())))

    def get_embedding(self):
        """
        读取预训练的word2vector词向量，保存成字典的形式，其中key为词语，value为词向量
        :return: 保存以后的词语和词向量的对应字典形式
        """
        w2v_model = gensim.models.KeyedVectors.load_word2vec_format(self.word2vec_dict, self.word2vec_dict_vocab, binary=True)
        embeddings_index = {}
        for word in w2v_model.wv.vocab:
            embeddings_index[word] = w2v_model[word]
        return embeddings_index

    def get_weights(self):
        """
        把保存以后的词语和词向量的对应关系结合id和词语的对应关系，得到id和词向量的对应关系，用数组表示，数组的行即使id的数字，对于
        没有词向量的词语，用-0.25-0.25之间的数随机生成
        :return: id和词向量的对应数组
        """
        embeddings_index = self.get_embedding()
        embedding_matrix = np.zeros((self.max_nb_words + 1, self.embedding_dim))
        np.random.seed(1234)
        for i, word in self.id2word.items():
            word = unicode_python_2_3(word)
            if word in embeddings_index and i < embedding_matrix.shape[0]:
                embedding_vector = embeddings_index[word]
                embedding_matrix[i] = embedding_vector
            elif i < embedding_matrix.shape[0]:
                embedding_matrix[i] = np.random.uniform(-0.25, 0.25, self.embedding_dim)
        embedding_matrix = embedding_matrix.astype(np.float16)
        return embedding_matrix

    def sentence2id(self, sentence):
        """
        :param sentence:
        :return:返回按照字典分词的id列表
        """
        sentence = unicode_python_2_3(sentence)
        words = self.word2vector.get_word_vector(sentence, seg_type='all')
        return words


class TfWordModel(BaseModel):
    """
    几个模型的简单融合功能
    """
    def initialize(self, **kwargs):
        """
        对两个模型进行初始化，对置信度指标和准确率之间的关系进行初始化
        :param kwargs: 初始化两个模型参数
        :return: 返回两个模型
        """
        self.sentence_model = SentenceModel(cfg_path=global_conf.cfg_path, model_section='SENTENCE_SIMILARITY_MODEL')
        self.sentence_word_model = SentenceWordModel(cfg_path=global_conf.cfg_path,
                                                     model_section='SENTENCE_SIMILARITY_MODEL')
        self.word2id = self.sentence_word_model.word2id
        self.embedding_matrix = self.sentence_word_model.embedding_matrix
        self.embedding_dim = 100

    def id_tfidf(self, sentence):
        """
        :param sentence: 句子
        :return: 返回以id和tfidf之间的对应关系，以字典形式返回
        """
        id_tfidf = {}
        sentence_tfidf = self.sentence_model.word2vec(sentence)
        for key, value in sentence_tfidf.items():
            id_tfidf[self.word2id.get(str(key))] = value
        return id_tfidf

    def sentence_vector(self, sentence):
        """
        :param sentence: 句子
        :return: 返回句子的加权词向量表示，以list形式返回
        """
        sentence_vector = []
        id_tfidf = self.id_tfidf(sentence)
        sentence2id = self.sentence_word_model.sentence2id(sentence)
        sentecne2tfidf = [(term_id, id_tfidf.get(int(term_id), 15.0)) for term_id in sentence2id]
        length = 1.0 * math.sqrt(sum(val ** 2 for term_id, val in sentecne2tfidf))
        sentecne2tfidf = dict([(term_id, val/length) for term_id, val in sentecne2tfidf])
        for id in sentence2id:
            sentence_vector.append(self.embedding_matrix[int(id)]*sentecne2tfidf.get(id))
        return sentence_vector

    def sentences_vector(self, sentences):
        """
        :param sentences: 句子对
        :return: 返回句子对的加权词向量表示
        """
        sentences_vector = []
        for sentence in sentences:
            sentence_vector = self.sentence_vector(sentence)
            sentences_vector.append(sentence_vector)
        return sentences_vector

    def sentence_norm(self, sentence):
        """
        :param sentence: 句子
        :return: 返回句向量
        """
        senvec = self.sentence_vector(sentence)
        if not senvec:
            return np.array([])
        sentence_vector = np.array(senvec)
        sentence_norm = np.sum(sentence_vector, axis=0)
        return sentence_norm

    def sentences_norm(self, sentences):
        """
        :param sentences:句子对
        :return: 返回句子对的词向量
        """
        sentences_norm = []
        for sentence in sentences:
            sen_norm = self.sentence_norm(sentence)
            sentences_norm.append(sen_norm)
        sentences_norm = np.array(sentences_norm)
        return sentences_norm

    def elu_distance(self, sentence_norm_a, sentence_norm_b):
        """
        :param sentence_norm_a: 句子a
        :param sentence_norm_b: 句子a
        :return: 返回两个句子的欧氏距离相似度
        """
        if not sentence_norm_a.size or not sentence_norm_b.size:
            return 0
        sentence_norm_a = sentence_norm_a.reshape(1, self.embedding_dim)
        sentence_norm_b = sentence_norm_b.reshape(1, self.embedding_dim)
        sim = 0
        if sentence_norm_a.any() and sentence_norm_b.any():
            dist = np.linalg.norm(sentence_norm_a - sentence_norm_b)
            sim = 1.0 / (1.0 + dist)
        return sim

    def cos_distance(self, sentence_norm_a, sentence_norm_b):
        """
        :param sentence_norm_a: 句子a
        :param sentence_norm_b: 句子b
        :return: 返回两个句子的余弦距离相似度
        """
        if not sentence_norm_a.size or not sentence_norm_b.size:
            return 0
        sentence_norm_a = sentence_norm_a.reshape(1, self.embedding_dim)
        sentence_norm_b = sentence_norm_b.reshape(1, self.embedding_dim)
        sim = 0
        if sentence_norm_b.any() and sentence_norm_a.any():
            num = float(np.dot(sentence_norm_a, sentence_norm_b.T))
            denom = np.linalg.norm(sentence_norm_a) * np.linalg.norm(sentence_norm_b)
            cos = num / denom
            sim = 0.5 + 0.5 * cos
        return sim

    def distance(self, sentence, sentences, type='elu'):
        """
        :param sentence:句子
        :param sentences: 句子对
        :param type: 采用何种方式计算相似度
        :return: 返回句子和句子对的相似度
        """
        sentence_vec = self.sentence_norm(sentence)
        sentences_vec = self.sentences_norm(sentences)
        sentences_dist = []
        for vec in sentences_vec:
            if type == 'elu':
                sentence_dist = self.elu_distance(sentence_vec, vec)
            else:
                sentence_dist = self.cos_distance(sentence_vec, vec)
            sentences_dist.append(sentence_dist)
        return sentences_dist

    def predict(self, sentence, **kwargs):
        """
        :param sentence: 句子
        :param sentences: 句子对
        :param type: 采用何种方式计算相似度
        :return: 返回句子和句子对的相似度
        """
        sentences = []
        type = 'cos'
        if kwargs.get('sentences'):
            sentences = kwargs.get('sentences')
        if kwargs.get('type'):
            type = kwargs.get('type')
        result = []
        if not isinstance(sentence, str):
            return []
        if not isinstance(sentences, list):
            return []
        if sentence and sentences:
            dist = self.distance(sentence, sentences, type=type)
        else:
            return []
        for i in range(len(sentences)):
            result.append([unicode_python_2_3(sentences[i]), dist[i], str(i)])
        result.sort(key=lambda item: item[1], reverse=True)
        return result
