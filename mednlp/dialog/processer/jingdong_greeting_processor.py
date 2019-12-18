#!/usr/bin/python
# encoding=utf-8

from mednlp.dialog.processer.basic_processor import BasicProcessor
from mednlp.model.similarity import TfidfSimilarity
import global_conf

class JingdongGreetingProcessor(BasicProcessor):
    """
    寒暄处理的意图
    """

    def get_search_result(self):
        threshold = 0.6
        answer = '很抱歉，我还在学习中，您可以问我，胃不舒服挂什么科'
        query = ''
        if self.input_params.get('input') and self.input_params.get('input').get('q'):
            query = self.input_params.get('input').get('q')
        corpus_greeting_answer = TfidfSimilarity(
                global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
        if corpus_greeting_answer:
            answer = corpus_greeting_answer
        res = {}
        res['answer'] = answer
        res['is_end'] = 1
        res['code'] = 0
        return res
