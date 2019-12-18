import numpy as np
from keras.utils.np_utils import to_categorical
from keras.preprocessing.sequence import pad_sequences

import global_conf
from bin.training.dept.data.offline.utils import Char2vector, Dept2Vector, Pinyin2vector
from bin.training.dept.train.config import DeptConfig


class DeptLawyer(object):
    def __init__(self, char_path=None, pinyin_path=None, dept_path=None):
        self.char_path = char_path or global_conf.dept_classify_char_dict_path
        self.pinyin_path = pinyin_path or global_conf.dept_classify_pinyin_dict_path
        self.dept_path = dept_path or global_conf.dept_classify_dept_path
        self.char_law = None
        self.pinyin_law = None
        self.dept_law = None
        self.sex_law = {'男': 1, '女': -1}

    def get_char(self, char, reverse=False):
        if self.char_law is None:
            self.char_law = Char2vector(self.char_path)
        vector = self.char_law.get_vector(content=char, reverse=reverse)
        return vector

    def get_pinyin(self, pinyin, reverse=False):
        if self.pinyin_law is None:
            self.pinyin_law = Pinyin2vector(self.pinyin_path)
        vector = self.pinyin_law.get_vector(content=pinyin, reverse=reverse)
        return vector

    def get_dept(self, dept, reverse=False):
        if self.dept_law is None:
            self.dept_law = Dept2Vector(self.dept_path)
        vector = self.dept_law.get_vector(content=dept, reverse=reverse)
        return vector

    def get_sex(self, sex_str):
        return self.sex_law.get(sex_str, None)

    @staticmethod
    def get_age(age_str):
        try:
            age = int(age_str)
        except ValueError:
            age = None
        return age


class DeptPreProcessor(object):
    def __init__(self):
        self.lawyer = DeptLawyer()
        self.config = DeptConfig()

        self.temp = {}
        self.splits = None

    @staticmethod
    def _truncate(vector, length=100):
        return vector[-length:]

    def could_split(self, raw_line):
        raw_line = raw_line.replace('\n', '')
        self.splits = raw_line.split('\t')
        return len(self.splits) == 4

    def could_find_dept(self):
        dept = self.splits[3]
        self.temp['dept'] = self.lawyer.get_dept(dept.strip())
        return self.temp['dept'] is not None

    def could_vectorize(self):
        data, sex, age, dept = self.splits
        self.temp['char'] = self.lawyer.get_char(data)
        if len(self.temp['char']) == 0:
            return False

        self.temp['pinyin'] = self.lawyer.get_pinyin(data)
        if len(self.temp['pinyin']) == 0:
            return False

        self.temp['sex'] = self.lawyer.get_sex(sex)
        if self.temp['sex'] is None:
            return False

        self.temp['age'] = self.lawyer.get_age(age)
        return True

    def raw2pre(self):
        self.temp['char'] = self._truncate(self.temp['char'])
        self.temp['pinyin'] = self._truncate(self.temp['pinyin'])

        return self.temp

    def pre2train(self, char, pinyin, dept):
        # assert len(char) == len(pinyin) == len(dept)
        # data_length = len(char)
        # index = list(range(data_length))
        # index.sort(key=lambda x: len(char[x]))

        char_data = pad_sequences(np.array(char), padding='pre', maxlen=self.config.CHAR_NUM)
        pinyin_data = pad_sequences(np.array(pinyin), padding='pre', maxlen=self.config.PINYIN_NUM)
        dept_data = to_categorical(np.array(dept), num_classes=self.config.CLASSES)

        # char_data = char_data[index]
        # pinyin_data = pinyin_data[index]
        # dept_data = dept_data[index]
        return char_data, pinyin_data, dept_data

    def check(self, char, pinyin, dept):
        char_raw = self.lawyer.get_char(char, reverse=True)
        pinyin_raw = self.lawyer.get_pinyin(pinyin, reverse=True)
        dept_raw = self.lawyer.get_dept(dept, reverse=True)
        return char_raw, pinyin_raw, dept_raw

    def pre2test(self):
        pass
