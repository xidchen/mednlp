#!/usr/bin/python
# encoding=utf-8

from mednlp.dialog.processer.basic_processor import BasicProcessor
from mednlp.model.similarity import TfidfSimilarity
import global_conf
from mednlp.dialog.configuration import Constant as constant


class DefaultGreetingProcessor(BasicProcessor):
    """
    寒暄处理的意图
    """

    def get_search_result(self):
        result = {}
        threshold = 0.6
        # answer = '很抱歉，我还在学习中，您可以问我，胃不舒服挂什么科'
        answer = '您好,请问有什么可以帮您？'
        query = ''
        if self.input_params.get('input') and self.input_params.get('input').get('q'):
            query = self.input_params.get('input').get('q')
        corpus_greeting_answer = TfidfSimilarity(
                global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
        if corpus_greeting_answer:
            answer = corpus_greeting_answer

        result[constant.ANSWER_GENERAL_ANSWER] = answer
        result['is_end'] = 1
        result['code'] = 0
        return result


class DefaultGuideProcessor(BasicProcessor):
    """
    寒暄处理的意图
    """

    def get_search_result(self):
        result = {}
        result[constant.ANSWER_GENERAL_ANSWER] = constant.QUERY_VALUE_GUIDE
        result['is_end'] = 1
        result['code'] = 0
        return result


class DefaultCustomerService(BasicProcessor):
    # 客服意图

    def get_search_result(self):
        result = {}
        result[constant.ANSWER_GENERAL_ANSWER] = constant.QUERY_VALUE_CUSTOMER_SERVICE
        result['is_end'] = 1
        result['code'] = 0
        return result