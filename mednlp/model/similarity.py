#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
similarity.py -- some class of similarity

Author: maogy <maogy@guahao.com>
Create on 2018-08-27 Monday.
"""


import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from mednlp.utils.utils import pretty_print, strip_all_punctuations
from mednlp.dao.ai_service_dao import greeting_service


class TfidfSimilarity(object):
    def __init__(self, corpus_path):
        with open(corpus_path) as f:
            self.corpus = [strip_all_punctuations(s.strip()) for s in f.readlines()]
        self.tokenizer = jieba.cut
        self.vectorizer = CountVectorizer(tokenizer=self.tokenizer)
        self.transformer = TfidfTransformer()
        self.tfidf = self.transformer.fit_transform(self.vectorizer.fit_transform(self.corpus))
        self.word = self.vectorizer.get_feature_names()
        self.weight = self.tfidf.toarray()

    def jieba_cutall(self, q):
        return jieba.cut(q, cut_all=True)

    def verbose_corpus(self, n=10):
        for i in range(n):
            print(u"\n")
            print(self.corpus[i])
            for j in range(len(self.word)):
                if self.weight[i][j] > 0.00:
                    print(self.word[j], self.weight[i][j])

    def verbose_q(self, q):
        q_tfidf_weight = self.transformer.transform(
            self.vectorizer.transform([strip_all_punctuations(q.strip())])).toarray()
        q_tokens = "|".join(self.tokenizer(q.strip())).split("|")
        print(q_tokens)
        print(q_tfidf_weight)
        print(self.word)
        for w, t in zip(q_tfidf_weight[0], self.word):
            if w > 0.0:
                print(t, w)

    def cosine(self, q, match_corpus=[], threshold=0.4, verbose=False):
        """
        计算余弦相似，加了一点规则
        :param q: 问句
        :param match_corpus: 搜索得到的相似自己
        :param verbose: 是否打印一些中间过程，用于调试
        :return: 相似问句或者None
        """

        q_tfidf_weight = self.transformer.transform(
            self.vectorizer.transform([strip_all_punctuations(q.strip())])).toarray()

        if match_corpus:
            match_corpus_strip = [strip_all_punctuations(s.strip()) for s in match_corpus]
            corpus_tfidf_weight = self.transformer.transform(
                self.vectorizer.transform(match_corpus_strip)).toarray()
            sim_vec = np.dot(corpus_tfidf_weight, np.transpose(q_tfidf_weight))
            sim_arg = np.argmax(sim_vec)
            best_q = match_corpus[sim_arg]
            best_score = np.max(sim_vec)
        else:
            sim_vec = np.dot(self.weight, np.transpose(q_tfidf_weight))
            sim_arg = np.argmax(sim_vec)
            best_q = self.corpus[sim_arg]
            best_score = np.max(sim_vec)

        if verbose:
            print("best_score:", best_score)
            self.verbose_q(q)
            print(best_q)
            self.verbose_q(best_q)

        # 词数小于4的，所有词都必须在相似问句中出现
        q_tokens = "|".join(self.tokenizer(q.strip())).split("|")
        best_q_tokens = "|".join(self.tokenizer(best_q.strip())).split("|")
        if len(q_tokens) < 4:
            if not set(q_tokens).issubset(set(best_q_tokens)):
                best_score = 0
        if len(best_q_tokens) > 2*len(q_tokens):
            best_score = 0

        if best_score > threshold:
            return best_q, sim_arg
        else:
            return None, None

    def get_search_results(self, q):
        answers, err_msg = greeting_service(q)
        if err_msg:  # 无返回数据也会报错
            pretty_print(err_msg)
            return [], []
        return [strip_all_punctuations(s.get('ask')) for s in answers], [s.get('answer') for s in answers]

    def best_answer(self, q, threshold):
        search_ask, search_answer = self.get_search_results(q)
        if search_ask:
            best_q, sim_arg = self.cosine(q, search_ask, threshold)
            if best_q:
                return search_answer[sim_arg]
