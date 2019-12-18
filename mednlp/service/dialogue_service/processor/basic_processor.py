#!/usr/bin/python
#encoding=utf-8


class BasicProcessor(object):
    """
    基础意图处理类.
    用来处理不同意图的方法
    """

    def __init__(self):
        """
        构造函数.
        """
        self.ai_result = {}
        self.response_data = {}

    def set_params(self, input_params,intention, conf, entity_dict, fl):
        self.conf = conf
        self.entity_dict = entity_dict
        self.input_params = input_params
        self.ai_result = {}
        self.ai_result['intention'] = intention
        self.ai_result.update(entity_dict)
        self.fl = fl



    def process(self):
        """
        处理对应的数据，返回应有的结果。
        """
        pass

    def build_ai_result(self):
        pass

    def get_search_result(self):
        """
        处理对应的数据，返回应有的结果。
        """
        pass

    def data_output(self, return_type=1):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
	pass

    def checkout_result(self):
        return True

    def get_default_result(self):
        pass

    def get_data(self):
        pass

    def add_docs(self):
        pass

    def change_ai_result(self):
        pass

    def get_intention_result(self):
        self.get_data()
        if self.checkout_result():
            self.get_search_result()
        else:
            self.get_default_result()
        self.add_docs()
        self.change_ai_result()
        return self.data_output()
