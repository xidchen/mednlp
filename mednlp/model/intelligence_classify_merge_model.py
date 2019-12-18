#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
intelligence_classify_merge_model.py

Author: caoxg <caoxg@guahao.com>
Create on 2018-03-08 星期四.
"""

from ailib.model.base_model import BaseModel
from mednlp.model.intelligence_classify_model import InterlligenceClassifyModel
from mednlp.model.intelligence_classify_cnn_model import InterlligenceClassifyCNN
from mednlp.model.intelligence_classify_pinyin_model import InterlligenceClassifyPhonetic
import codecs
import global_conf


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
        self.char_model = InterlligenceClassifyModel(cfg_path=global_conf.cfg_path,
                                                     model_section='INTELLIGENCE_CLASSIFY_MODEL')
        # self.cnn_model = InterlligenceClassifyCNN(cfg_path=global_conf.cfg_path,
                                                  # model_section='INTELLIGENCE_CLASSIFY_TEXTCNN_MODEL')
        self.pinyin_model = InterlligenceClassifyPhonetic(cfg_path=global_conf.cfg_path,
                                                          model_section='INTELLIGENCE_CLASSIFY_PINYIN_MODEL')
        self.standard_ask = self.load_standard_ask()

    def load_standard_ask(self):
        '导入标准问句'
        standard_ask = {}
        with codecs.open(global_conf.standard_ask, 'r', 'utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('==')
                if len(items) == 2:
                    _id, question = items
                    standard_ask[question] = _id
        return standard_ask

    def model_merge(self, model1_result, model2_result, per=(0.5, 0.5)):
        """
        主要是对两种模型的预测结果进行加权，其中per是权重，并对预测结果按照预测概率排序
        :param model1_result: 模型1预测结果 类型为嵌套列表 其中子列表形如[预测科室，预测概率，预测科室id]
        :param model2_result: 模型2预测结果 类型为嵌套列表 其中子列表形如[预测科室，预测概率，预测科室id]
        :param per 模型结果的融合比例
        :return: 返回简单融合模型结果 类型为嵌套列表 其中子列表形如[预测科室，预测概率，预测科室id]
        """
        dept_name = {}
        for i in model2_result:
            dept_name[i[0]] = i[1]
        for line in model1_result:
            if line[0] in dept_name:
                line[1] = line[1]*per[0] + dept_name[line[0]]*per[1]
        model1_result.sort(key=lambda line: line[1], reverse=True)
        return model1_result

    def predict(self, query, sex=0, age=-1, level=1, dept_set=1):
        """
        融合char和textcnn模型，对预测结果进行简单加权，实现sex、age、level的过滤条件、增加预测准确率，返回最终的结果
        :param query: 查询条件
        :param sex: 性别
        :param age: 年龄
        :param level: 所要求的置信度等级
        :return: 返回融合以后，进行性别、年龄和level水平的过滤条件之后的结果
        """
        if query in self.standard_ask:
            return [[query, 1.0, self.standard_ask[query]]]
        # model2_result = self.cnn_model.predict(query, sex=sex, age=age)
        model1_result = self.char_model.predict(query, sex=sex, age=age)
        model3_result = self.pinyin_model.predict(query, sex=sex, age=age)
        result_union = self.model_merge(model3_result, model1_result, per=(0.4, 0.6))
        return result_union
        # result = self.model_merge(model2_result, result_union, per=(0.3, 0.7))
        # return result


if __name__ == '__main__':
    merge_model = MergeModel(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_TEXTCNN_MODEL')
    line = '绑卡后，我可以解绑或者更换其他银行卡吗'
    pred = merge_model.predict(line)
    print(pred[0])
