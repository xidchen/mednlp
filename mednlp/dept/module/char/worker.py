from keras.preprocessing.sequence import pad_sequences
from mednlp.dept.common.dictionary import *
from mednlp.dept.common.result import DeptResults


class CharWorker(object):
    def __init__(self):
        self.char_to_vector = char_helper
        self.dept_helper = dept_helper
        self.dept_dictionary = dept_dictionary
        self.num = 300

    def pre(self, query):
        words = self.char_to_vector.get_char_vector(query)
        p = 0
        words_list = []
        while len(words[p:p + self.num]) == self.num:
            words_list.append(words[p:p + self.num])
            p += self.num
        if p != len(words):
            words_list.append(words[p:len(words)])

        data = pad_sequences(words_list, maxlen=self.num)
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
