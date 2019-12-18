#!/usr/bin/python
#encoding=utf-8

from basic_processor import BasicProcessor

class GuideProcessor(BasicProcessor):
    """
    处理寒暄的意图
    """

    def get_search_result(self):

        self.response_data = [{'_text_':'你好，小微目前仅支持医疗相关问题，请问有什么可以帮您吗'}]

