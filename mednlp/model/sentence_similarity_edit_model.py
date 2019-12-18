#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentence_similarity_edit.py
Author: caoxg <caoxg@guahao.com>
Create on 18/12/24 下午2:17.
"""

import numpy as np
from ailib.model.base_model import BaseModel
from mednlp.utils.utils import unicode_python_2_3
import global_conf


class SentenceEditModel(BaseModel):

    def sentence_distance(self, sentence1, sentence2):
        """
        :param sentence1:句子a
        :param sentence2:句子b
        :return:返回句子a和句子b的编辑距离
        """
        len_str1 = len(sentence1)
        len_str2 = len(sentence2)
        if len_str1 == 0 or len_str2 == 0:
            return 0
        taglist = np.zeros((len_str1 + 1, len_str2 + 1))
        for a in range(len_str1+1):
            taglist[a][0] = a
        for a in range(len_str2+1):
            taglist[0][a] = a
        for i in range(1, len_str1 + 1):
            for j in range(1, len_str2 + 1):
                if (sentence1[i - 1] == sentence2[j - 1]):
                    temp = 0
                else:
                    temp = 1
                taglist[i][j] = min(taglist[i - 1][j - 1] + temp, taglist[i][j - 1] + 1, taglist[i - 1][j] + 1)
        return 1 - taglist[len_str1][len_str2] / max(len_str1, len_str2)

    def have_distance(self, sentence1, sentence2):
        """
        :param sentence1: 句子a
        :param sentence2: 句子b
        :return: 返回句子a和句子b的简单共有词距离
        """
        if not sentence1 or not sentence2:
            return 0
        sentence1_str = set(list(sentence1))
        sentence2_str = set(list(sentence2))
        inter = sentence1_str & sentence2_str
        sim = len(inter) / max(len(sentence1_str), len(sentence2_str))
        return sim

    def jaccard_distance(self, sentence1, sentence2):
        """
        :param sentence1: 句子a
        :param sentence2: 句子b
        :return: 返回句子a和句子b的雅克比距离
        """
        if not sentence1 or not sentence2:
            return 0
        sentence1_str = set(list(sentence1))
        sentence2_str = set(list(sentence2))
        inter = sentence1_str & sentence2_str
        un = sentence1_str | sentence2_str
        sim = (len(inter) / len(un))
        return sim

    def sentences_distance(self, sentence, sentences, type=1):
        """
        :param sentence: 句子
        :param sentences: 句子对
        :param type: 采用何种方式计算相似度
        :return: 返回句子和句子对的相似度
        """
        sentences_dis = []
        for line in sentences:
            if type == 1:
                sentences_dis.append(self.sentence_distance(sentence, line))
            elif type == 2:
                sentences_dis.append(self.have_distance(sentence, line))
            else:
                sentences_dis.append(self.jaccard_distance(sentence, line))

        return sentences_dis

    def predict(self, sentence, **kwargs):
        """
        :param sentence: 句子
        :param kwargs: sentences：句子对，type：采用何种方式计算相似度
        :return: 返回句子和句子对的相似度
        """
        """
        :param sentence: 句子
        :param sentences: 句子对
        :param type: 采用何种方式计算相似度
        :return: 返回句子和句子对的相似度
        """
        sentences = []
        type = 1
        if kwargs.get('sentences', []):
            sentences = kwargs.get('sentences')
        if kwargs.get('type'):
            type = kwargs.get('type')
        result = []
        if not isinstance(sentence, str):
            return []
        if not isinstance(sentences, list):
            return []
        if sentence and sentences:
            dist = self.sentences_distance(sentence, sentences, type=type)
        else:
            return []
        for i in range(len(sentences)):
            result.append([unicode_python_2_3(sentences[i]), dist[i], str(i)])
        result.sort(key=lambda item: item[1], reverse=True)
        return result


if __name__ == '__main__':
    sentence_edit_model = SentenceEditModel(cfg_path=global_conf.cfg_path, model_section='SENTENCE_SIMILARITY_MODEL')
    # a = '我脑袋有点疼'
    # b = ['我脑袋有点不舒服', '我脑袋疼', '我脑袋不舒服']
    a = "我拉肚子"
    b = ["你陪我长大，我没有陪你变老"]
    print(sentence_edit_model.predict(a, sentences=b, type=3))
    print(sentence_edit_model.predict(a, sentences=b, type=1))
    print(sentence_edit_model.predict(a, sentences=b, type=2))
    # a = "我拉肚子"
    # b = "你陪我长大，我没有陪你变老"
