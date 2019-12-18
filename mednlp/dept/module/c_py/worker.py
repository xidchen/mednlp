from mednlp.dept.common.dictionary import *
from keras.preprocessing.sequence import pad_sequences
from mednlp.dept.common.result import DeptResults


class CharPinyinWorker(object):
    def __init__(self):
        """
        初始化模型，加载相关字典文件
        """
        self.pinyin_to_vector = py_helper
        self.char_to_vector = char_helper
        self.dept_helper = dept_helper
        self.dept_dictionary = dept_dictionary

    def pre(self, query):
        char_vector = [self.char_to_vector.get_char_vector(query, is_ignore=False)]
        padding_char_vector = pad_sequences(char_vector, maxlen=100)
        pinyin_vector = [self.pinyin_to_vector.get_pinyin_vector(query, is_ignore=False)]
        padding_pinyin_vector = pad_sequences(pinyin_vector, maxlen=100)
        return padding_char_vector, padding_pinyin_vector

    @staticmethod
    def execute(data, model):
        data_dict = {'input_1:0': data[0], 'input_2:0': data[1]}
        results = model.predict(data_dict)
        return results

    @staticmethod
    def execute1(data, model):
        results = model.predict(*data)
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
