#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_merge_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-03-08 星期四.
"""

from ailib.model.base_model import BaseModel
from mednlp.dept.utils.accuracy import Score2Accuracy
from mednlp.utils.utils import dept_classify_normal
from mednlp.model.dept_classify_model import DeptClassifyModel
from mednlp.model.dept_classify_cnn_model import DeptClassifyCNN
from mednlp.model.dept_classify_char_pinyin_model import DeptClassifyCharPinyin
from mednlp.model.dept_classify_pinyin_model import DeptClassifyPhonetic
from mednlp.dept.utils.rules import dept_classify_filter_age, dept_classify_filter_sex
from mednlp.dept.utils.rules import get_internet_dept
from mednlp.dept.utils.rules import get_origin_dept
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
        self.cnn_model = DeptClassifyCNN(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_TEXTCNN_MODEL')
        self.char_pinyin_model = DeptClassifyCharPinyin(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_CHAR_PINYIN_MODEL')
        self.score2accuracy = Score2Accuracy()

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

    def add_accuracy(self, result):
        """
        主要是预测后的结果增加预测准确率字段
        :param result:嵌套列表，每个list包含，预测科室，预测概率，预测科室id
        :return: 增加预测准确性以后的嵌套列表，每个list依次为，预测科室、预测科室概率、预测科室id、预测准确性
        """
        add_accuracy_result = [[line[0], line[1], line[2], self.score2accuracy.get_accuracy(line[1])]
                               for line in result]
        return add_accuracy_result

    def add_accuracy2(self, results):
        for dept in results:
            dept.accuracy = self.score2accuracy.get_accuracy(dept.probability)

    def predict(self, query, sex=0, age=-1, level=1, dept_set=1):
        """
        融合char和textcnn模型，对预测结果进行简单加权，实现sex、age、level的过滤条件、增加预测准确率，返回最终的结果
        :param query: 查询条件
        :param sex: 性别
        :param age: 年龄
        :param level: 所要求的置信度等级
        :return: 返回融合以后，进行性别、年龄和level水平的过滤条件之后的结果
        """
        model2_result = self.cnn_model.predict(query, sex=sex, age=age)
        char_pinyin_result = self.char_pinyin_model.predict(query, sex=sex, age=age)
        result = self.model_merge(model2_result, char_pinyin_result, per=(0.4, 0.6))
        if len(result) == 45 and result[0][1] > 0 and result[19][1] > 0 and float(result[0][1]) /\
                float(result[19][1]) < 2:
            return []
        if dept_set == 3:
            result = get_internet_dept(result)
        if dept_set == 1:
            result = get_origin_dept(result, sex)
        filter_sex_result = dept_classify_filter_sex(result, sex=sex)
        filter_age_result = dept_classify_filter_age(filter_sex_result, age=age)
        filter_normal_result = dept_classify_normal(filter_age_result)
        filter_normal_result.sort(key=lambda item: item[1], reverse=True)
        add_accuracy_result = filter_normal_result
        return add_accuracy_result


class MedicalRecordModel(BaseModel):
    """
    几个模型的简单融合功能
    """
    def initialize(self, **kwargs):
        """
        对两个模型进行初始化，对置信度指标和准确率之间的关系进行初始化
        :param kwargs: 初始化两个模型参数
        :return: 返回两个模型
        """
        self.char_model = DeptClassifyModel(model_version=102, cfg_path=global_conf.cfg_path,
                                            model_section='DEPT_CLASSIFY_MODEL')
        self.pinyin_model = DeptClassifyPhonetic(model_version=102, cfg_path=global_conf.cfg_path,
                                                 model_section='DEPT_CLASSIFY_PINYIN_MODEL')

        self.score2accuracy = Score2Accuracy()

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

    def add_accuracy(self, result):
        """
        主要是预测后的结果增加预测准确率字段
        :param result:嵌套列表，每个list包含，预测科室，预测概率，预测科室id
        :return: 增加预测准确性以后的嵌套列表，每个list依次为，预测科室、预测科室概率、预测科室id、预测准确性
        """
        add_accuracy_result = [[line[0], line[1], line[2], self.score2accuracy.get_accuracy(line[1]).encode('utf-8')]
                               for line in result]
        return add_accuracy_result

    def predict(self, query, sex=0, age=-1,  level=1, dept_set=1):
        """
        融合char和textcnn模型，对预测结果进行简单加权，实现sex、age、leve的过滤条件、增加预测准确率，返回最终的结果
        :param query: 查询条件
        :param sex: 性别
        :param age: 年龄
        :param level: 所要求的置信度等级
        :return: 返回融合以后，进行性别、年龄和level水平的过滤条件之后的结果
        """
        model1_result = self.char_model.predict(query, sex=sex, age=age, num=300)
        model3_result = self.pinyin_model.predict(query, sex=sex, age=age, num=300)
        result_union = self.model_merge(model3_result, model1_result, per=(0.4, 0.6))
        result = result_union
        if len(result) == 45 and result[0][1] > 0 and result[19][1] > 0 and float(result[0][1]) /\
                float(result[19][1]) < 2:
            return []
        if dept_set == 3:
            result = get_internet_dept(result)
        if dept_set == 1:
            result = get_origin_dept(result, sex)
        filter_sex_result = dept_classify_filter_sex(result, sex=sex)
        filter_age_result = dept_classify_filter_age(filter_sex_result, age=age)
        filter_normal_result = dept_classify_normal(filter_age_result)
        filter_normal_result.sort(key=lambda item: item[1], reverse=True)
        # add_accuracy_result = self.add_accuracy(filter_normal_result)
        # if level == 2 and add_accuracy_result[0][1] < 0.2:
        #     return []
        # if level == 3 and add_accuracy_result[0][1] < 0.4:
        #     return []
        return filter_normal_result
