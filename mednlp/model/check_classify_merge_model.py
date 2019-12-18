"""
check_classify_merge_model.py -- the mergemodel of check_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-03-08 星期四.
"""

from ailib.model.base_model import BaseModel
from mednlp.model.check_classify_model import CheckClassifyModel
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
        self.char_model_1 = CheckClassifyModel(cfg_path=global_conf.cfg_path, model_version=1, type=1,
                                               model_section='INTELLIGENCE_SERVICE_CHECK_MODEL')
        self.char_model_2 = CheckClassifyModel(cfg_path=global_conf.cfg_path,  model_version=2, type=2,
                                               model_section='INTELLIGENCE_SERVICE_CHECK_MODEL')
        self.char_model_3 = CheckClassifyModel(cfg_path=global_conf.cfg_path,  model_version=3, type=3,
                                               model_section='INTELLIGENCE_SERVICE_CHECK_MODEL')

    def filter_result(self, result, value=0.5):
        """
        :param result: 模型预测结果
        :param value: 阈值
        :return: 返回根据阈值过滤以后的模型预测结果
        """
        if not result:
            return result
        else:
            if result[0][1] > float(value):
                return result[0]
            else:
                if float(value) + 0.1 >= 1:
                    return [result[1][0], 0.99, result[1][2]]
                else:
                    return [result[1][0], float(value) + 0.1, result[1][2]]

    def predict(self, query, sex=0, age=-1,  level=1, dept_set=1):
        """
        融合char和textcnn模型，对预测结果进行简单加权，实现sex、age、level的过滤条件、增加预测准确率，返回最终的结果
        :param query: 查询条件
        :param sex: 性别
        :param age: 年龄
        :param level: 所要求的置信度等级
        :return: 返回融合以后，进行性别、年龄和level水平的过滤条件之后的结果
        """
        result = []
        model1_result = self.char_model_1.predict(query, sex=sex, age=age)
        model2_result = self.char_model_2.predict(query, sex=sex, age=age)
        model3_result = self.char_model_3.predict(query, sex=sex, age=age)
        result.append(self.filter_result(model1_result, value=0.6))
        result.append(self.filter_result(model2_result, value=0.6))
        result.append(self.filter_result(model3_result, value=0.6))
        return result


if __name__ == '__main__':
    merge_model = MergeModel(cfg_path=global_conf.cfg_path, model_section='INTELLIGENCE_SERVICE_CHECK_MODEL')
    line = '你好，你这样的情况一般是痔疮引起的，可以用马应龙痔疮栓塞肛门治疗有可能的'
    pred = merge_model.predict(line)
    print(pred)
