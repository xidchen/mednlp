#!usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: yinwd
# @Date:   2018-11-26 14:11:08
import CRFPP
import global_conf
import jieba.posseg as psg
from ailib.model.base_model import BaseModel


class NerCrfModel(BaseModel):
    def initialize(self, model_version=0, **kwargs):
        """初始化对模型,词典
            ,和部门列表进行初始化"""
        self.model_version = model_version
        self.load_model()

    def load_model(self):
        """
        :param model_path: 模型路径
        :return: 加载模型
        """
        version = self.model_version
        model_path = self.model_path# + '.' + str(version)
        self.tagger = CRFPP.Tagger("-m " + model_path)

    def crf_segmenter(self, sentence):
        tagger = self.tagger
        for words in psg.cut(sentence):
            word = words.word
            flag = words.flag
            for w in word:
                tagger.add(w+'\t'+flag)
        tagger.parse()
        size = tagger.size()
        xsize = tagger.xsize()
        result_label = []
        result_char = []
        for i in range(0, size):
            for j in range(0, xsize-1):# 多一列特征，因此减一
                char = tagger.x(i, j)
                tag = tagger.y2(i)
                result_char.append(char)
                result_label.append(tag)
        # print(result_char,result_label )
        return result_char, result_label

    def print_result(self, result_char, result_label):
        word_list = []
        words = ''
        for ind, tag in enumerate(result_label):
            char = result_char[ind]
            if  tag != 'O':
                words += char
                if ind == len(result_label) - 1:
                    word_list.append(words)
            else:
                if words:
                    word_list.append(words)
                words = ''

        return word_list

    def ner_result(self, sentence):
        result_char, result_label = self.crf_segmenter(sentence)
        result_or = self.print_result(result_char, result_label)
        result_dict = []
        for result in result_or:
            data = {}
            data['type'] = 'hotpital'
            data['name'] = result
            result_dict.append(data)
        return result_dict

if __name__ == '__main__':
    sentence = '我想去北大附属医院拍个CT,上海瑞金医院在哪，301医院逛一圈，川大附医，河南省人民医院，华西，清华大学附属医院，红房子,\
               南阳市中心医院'
    ner_model = NerCrfModel(cfg_path=global_conf.cfg_path, model_section='CRF_MODEL')
    result =ner_model.ner_result(sentence)
    print(result)