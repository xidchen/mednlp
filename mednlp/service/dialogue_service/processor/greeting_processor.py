#!/usr/bin/python
#encoding=utf-8

from basic_processor import BasicProcessor

class GreetingProcessor(BasicProcessor):
    """
    处理寒暄的意图
    """

    def get_search_result(self):

        self.response_data = [{'_text_': '你好，请问有什么可以帮助您？'}]

