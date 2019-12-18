#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sentence_similarity_model.py -- 语句相似性模型

Author: caoxg <caoxg@guahao.com>
Create on 2018-09-29 星期六.
"""

from ailib.model.base_model import BaseModel
from gensim import corpora,models,similarities
import global_conf
from mednlp.utils.utils import Seg,Sentence


class  SentenceModel(BaseModel):
    def initialize(self, model_version=0, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.load_dict()
        self.load_model()
        self.seg = Seg()

    def load_dict(self,dict_path = global_conf.sentence_dict):
        """
        :param dict_path: 词典路径
        :return: 加载词典
        """
        self.dictionary = corpora.Dictionary.load(dict_path)

    def load_model(self):
        """
        :param model_path: 模型路径
        :return: 加载模型
        """
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path  + '.' + str(version) + '.tfidf'
        self.model = models.TfidfModel.load(model_path)


    def sentence2vec(self,sentence):
        """
        :param sentence: 一句话
        :return: 返回这段话对应的词向量
        """
        sentence = Sentence(sentence,self.seg)
        vec_bow = self.dictionary.doc2bow((sentence.get_cuted_sentence()))
        return self.model[vec_bow]


    def sentences2vec(self,sentences):
        """
        :param sentences: 句子组
        :return: 返回句子组的词向量
        """
        sentences_vec = []
        for sentence in sentences:
            sentence_vec = self.sentence2vec(sentence)
            sentences_vec.append(sentence_vec)
        return sentences_vec

    def predict(self,sentence,sentences):
        """
        计算一个句子句子组的相关性
        :param sentence: 一个句子
        :param sentences: 一个句子组
        :return: 一个句子和句子组中每个句子的相关性
        """
        result = []
        sentence_tfidf = self.sentence2vec(sentence)
        sentences.append(sentence)
        corpus_tfidf = self.sentences2vec(sentences)
        if sentence_tfidf and corpus_tfidf:
            index = similarities.MatrixSimilarity(corpus_tfidf)
            sims = index[sentence_tfidf]
        else:
            return []
        for i in range(len(sentences)-1):
            result.append([sentences[i],str(sims[i]),str(i)])
        result.sort(key=lambda item: item[1], reverse=True)
        return result

