#!/usr/bin/python
#encoding=utf-8

from basic_processor import BasicProcessor
from mednlp.model.similarity import TfidfSimilarity

class CorpusGreetingProcessor(BasicProcessor):
    """
    处理寒暄的意图
    """

    def get_search_result(self):
	threshold = 0.6
        corpus_greeting_answer = TfidfSimilarity(
                global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
        self.response_data = []
	if corpus_greeting_answer:
	    data_dict = {'_text_': corpus_greeting_answer}
	    self.response_data.append(data_dict)

