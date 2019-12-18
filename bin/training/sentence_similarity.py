#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sentence_similarity.py -- 句子相似性训练模型

Author: caoxg <caoxg@guahao.com>
Create on 2018-08-16 星期三.
"""

from gensim import corpora,models
from collections import defaultdict
import global_conf
import codecs
import jieba
from mednlp.text.sentence_seg import SentenceSeg


# sentenceseg = SentenceSeg(seg_type='max_num_word', dict_file_name=['entity_dict.txt'])
sentenceseg = SentenceSeg(seg_type='max_num_word')



class SentenceSimilarity():

    def set_sentence(self,sentences):
        """
        :param sentences: 句子列表
        :return: 返回已经拆分过的句子列表
        """
        self.sentences = []
        for i in range(0,len(sentences)):
            self.sentences.append(sentences[i])

    def get_cuted_sentences(self):
        """
        :return: 返回已经分割好的句子列表
        """
        cuted_sentences = []
        for sentence in self.sentences:
            cuted_sentences.append(sentenceseg.cut_line(sentence))

        return cuted_sentences

    def simple_model(self,min_frequency=1):
        """
        :param min_frequency:单词的最小出现次数
        :return: 返回语料和辞掉
        """
        self.texts = self.get_cuted_sentences()
        frequency = defaultdict(int)
        for text in self.texts:
            for token in text:
                frequency[token] +=1
        self.texts = [[token for token in text if frequency[token] >= min_frequency] for text in self.texts]
        self.dictionary = corpora.Dictionary(self.texts)
        self.corpus_simple = [self.dictionary.doc2bow(text) for text in self.texts]

    def TfidfModel(self):
        """
        tfidf model
        :return: 定义tfidf模型
        """
        self.simple_model()
        #转换模型
        self.model = models.TfidfModel(self.corpus_simple,normalize=False)

    def save_dictionary(self,version=0):
        """
        :param version: 保存词典版本
        :return:无
        """
        save_path = global_conf.training_path + 'sentence_similarity/version_' + str(version) + '/'
        self.dictionary.save(save_path + 'sentence_similarity.' + str(version) + '.dic')

    def save_model(self,version=0):
        """
        :param version: 保存模型版本
        :return: 无
        """
        save_path = global_conf.training_path + 'sentence_similarity/version_' + str(version) + '/'
        self.model.save(save_path + 'sentence_similarity.'+str(version)+'.tfidf' )

    def LsiModel(self):
        """
        训练lsimoodel
        :return: 无
        """
        self.simple_model()
        self.model = models.LsiModel(self.corpus_simple)

    def LdaModel(self):
        """
        训练lda模型
        :return: 无
        """
        self.simple_model()

        self.model = models.LdaModel(self.corpus_simple)


class ReadData(object):

    def __init__(self, filepath):
        self.filepath = filepath

    def read_lines(self):
        """
        读取训练数据
        :return: 返回list形式的训练数据
        """
        self.sentences = []
        file = codecs.open(self.filepath, 'r', encoding='utf-8')
        for line in file:
            line = line.strip()
            if line:
                self.sentences.append(line)
        file.close()
        return self.sentences

    def get_data(self):
        """
        :return:返回训练数据
        """
        self.read_lines()
        return self.sentences


if __name__ == '__main__':
    train_file = '/home/caoxg/work/mednlp/data/traindata/topic_title_rrr_title_target.txt'
    # train_file = '/home/caoxg/work/mednlp/data/traindata/hanxuan_corpus.txt'
    train_data = ReadData(train_file)
    train_sentences =train_data.get_data()
    ss = SentenceSimilarity()
    ss.set_sentence(train_sentences)
    ss.TfidfModel()
    ss.save_dictionary(4)
    ss.save_model(4)
