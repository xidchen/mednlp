from keras.preprocessing.sequence import pad_sequences
from mednlp.dept.common.dictionary import *

from mednlp.dept.common.result import DeptResults


class CNNWorker(object):
    def __init__(self):
        self.word_helper = word_helper
        self.dept_helper = dept_helper
        self.dept_dictionary = dept_dictionary

        self.num = 200

    def pre(self, query):
        words = self.word_helper.get_word_vector(query)
        words_list = [words[:self.num]]  # TODO: words可能为空
        data = pad_sequences(words_list, padding='post', maxlen=self.num)
        return data

    @staticmethod
    def execute(query, model):
        results = model.predict(query)
        return results

    def post(self, results):
        dept_prob_list = results.sum(axis=0)

        dept_results = DeptResults()
        for i, prob in enumerate(dept_prob_list):
            dept_name = self.dept_helper.get_name_from_index(i)
            dept = self.dept_dictionary.get_department_by_name(dept_name)
            dept.probability = prob
            dept_results.append(dept)
        dept_results.normalize_score()
        dept_results.sort()
        return dept_results
