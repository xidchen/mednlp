#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentence_similarity_merge_model.py -- 使用融合模型计算语句相似性模型

Author: caoxg <caoxg@guahao.com>
Create on 2018-10-12 星期五.
"""

from ailib.model.base_model import BaseModel
from mednlp.model.sentence_similarity_tf_word2vec_model import TfWordModel
from mednlp.model.sentence_similarity_entity_model import SentenceEntityModel
import global_conf
import numpy as np
from mednlp.model.sentence_similarity_edit_model import SentenceEditModel


class MergeModel(BaseModel):
    """
    几个模型的简单融合功能
    """
    def initialize(self, **kwargs):
        """
        对两个模型进行初始化，对置信度指标和准确率之间的关系进行初始化
        :param kwargs: 初始化两个模型参数
        :return: 返回两个模型
        """
        self.sentence_model = TfWordModel(cfg_path=global_conf.cfg_path, model_section='SENTENCE_SIMILARITY_MODEL')
        self.sentence_entity_model = SentenceEntityModel(cfg_path=global_conf.cfg_path,
                                                         model_section='SENTENCE_SIMILARITY_MODEL')
        self.sentence_edit_model = SentenceEditModel(cfg_path=global_conf.cfg_path,
                                                     model_section='SENTENCE_SIMILARITY_MODEL')

    def model_merge(self, model1_result, model2_result, per=(0.5, 0.5)):
        """
        主要是对两种模型的预测结果进行加权，其中per是权重，并对预测结果按照预测概率排序
        :param model1_result: 模型1预测结果 类型为嵌套列表 其中子列表形如[句子，预测概率，句子id]
        :param model2_result: 模型2预测结果 类型为嵌套列表 其中子列表形如[句子，预测概率，句子id]
        :param per 模型结果的融合比例
        :return: 返回简单融合模型结果 类型为嵌套列表 其中子列表形如[句子，预测概率，句子id]
        """
        dept_name = {}
        for i in model2_result:
            dept_name[i[0]] = i[1]
        for line in model1_result:
            if line[0] in dept_name:
                line[1] = line[1]*per[0] + dept_name[line[0]]*per[1]
        model1_result.sort(key=lambda line: line[1], reverse=True)
        return model1_result

    def predict(self, sentence, **kwargs):

        """
        这里是tfidf+word2vector模型预测结果+实体识别关于年龄和性别的过滤结果
        :param sentence: 预测句子
        :param sentences: 候选预测句子对
        :return: 返回模型预测结果
        """
        sentences = []
        type = 3
        age = -1
        sex = 0
        mode = 1
        if kwargs.get('sentences', []):
            sentences = kwargs.get('sentences')
        if kwargs.get('type'):
            type = kwargs.get('type')
        if kwargs.get('age'):
            age = kwargs.get('age')
        if kwargs.get('sex'):
            sex = kwargs.get('sex')
        if kwargs.get('mode'):
            mode = kwargs.get('mode')
            mode = int(mode)
        result1 = self.sentence_model.predict(sentence, sentences=sentences)
        result2 = self.sentence_edit_model.predict(sentence, sentences=sentences, type=type)
        result = self.model_merge(result1, result2)
        nums = [int(line[2]) for line in result if float(line[1]) >= 0.6]
        nums = nums[:min(3, len(nums))]
        pred_sentences = [sentences[index] for index in nums]
        pred_label, center_label = self.sentence_entity_model.predict(pred_sentences, age=age, sex=sex, q=sentence,
                                                                      mode=mode)
        label = np.sum(np.array(pred_label))
        if label == 0.75:
            return []
        pred_label_dict = dict(zip(nums, pred_label))
        for line in result:
            if int(line[2]) in nums:
                line[1] = line[1]*pred_label_dict.get(int(line[2]))
        if mode == 2:
            center_label_dict = dict(zip(nums, center_label))
            for line in result:
                if int(line[2]) in nums:
                    line[1] = line[1] * center_label_dict.get(int(line[2]))
                    if line[1] >= 1:
                        line[1] = 0.95
        result.sort(key=lambda line: line[1], reverse=True)
        return result
