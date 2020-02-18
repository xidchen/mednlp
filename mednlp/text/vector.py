#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
vector.py -- the service of vectorization

Author: caoxg
Create on 2017-11-22
"""

import codecs
import jieba
import re
import global_conf
import mednlp.text.pinyin as pinyin
from mednlp.dao.data_loader import Key2Value
from mednlp.text.mmseg import MMSeg
from mednlp.utils import utils


def get_sex_to_vector(sex):
    """
    把性别转化为词向量，
    其中女性->1, 男性->2, 未知->0
    :param sex: 性别男或者女
    :return: 返回男女对应的标签
    """
    sex = sex if isinstance(sex, str) else str(sex)
    if sex in ['女', '女性']:
        return '1'
    elif sex in ['男', '男性']:
        return '2'
    sex = str(sex) if str(sex) in ['1', '2'] else '0'
    return sex


def get_age_to_vector_for_lstm(age):
    """
    把年龄拆分成年龄段
    :param age: 用数字表示的年龄
    :return: 返回所对应的年龄段
    """
    if isinstance(age, (int, float)):
        age = float(age)
    else:
        if isinstance(age, str):
            month_label = False
            if re.search('月', age):
                month_label = True
            age = re.search("\d+(\.\d+)?", age)
            if age and month_label:
                age = float(age.group()) / 12
            else:
                age = float(age.group()) if age else 0
        else:
            age = 0
    if 0 < age <= 1:
        return '3'
    elif 1 < age <= 6:
        return '4'
    elif 6 < age <= 15:
        return '5'
    elif 15 < age <= 30:
        return '6'
    elif 30 < age <= 45:
        return '7'
    elif 45 < age <= 60:
        return '8'
    elif 60 < age <= 75:
        return '9'
    elif 75 < age:
        return '10'
    else:
        return '0'


class Char2Vector(object):
    def __init__(self, dept_classify_dict_path=global_conf.dept_classify_char_dict_path):
        self.dept_classify_dict_path = dept_classify_dict_path
        self.medical_word = self.load_medical_dic()
        pinyin.load_pinyin_dic()

    def load_medical_dic(self):
        """装载词典"""
        path = self.dept_classify_dict_path
        medical_word = {}
        for dict_line in open(path, 'r'):
            line_items = str(dict_line).strip().split('\t')
            if len(line_items) != 2:
                continue
            medical_word[line_items[0]] = int(line_items[1])
        return medical_word

    def get_vector(self, content):
        return self.get_char_vector(content)

    def get_char_vector(self, content, is_ignore=True):
        """
        把content按照char词典转化为词向量
        :param is_ignore: 
        :param content: unicode编码的中文文本
        :return: 输出词向量
        """
        words = []
        if content:
            for word in content:
                word = str(word)
                if self.medical_word.get(word):
                    words.append(str(self.medical_word[word]))
                elif not is_ignore:
                    words.append('0')
        return words


class Pinyin2vector(object):
    """
    把语句按照pinyin词典转化为词向量
    """

    def __init__(self,
                 dept_classify_dict_path=global_conf.dept_classify_pinyin_dict_path):
        self.dept_classify_dict_path = dept_classify_dict_path
        self.medical_word = self.load_medical_dic()

    def load_medical_dic(self):
        """装载词典"""
        path = self.dept_classify_dict_path
        medical_word = {}
        for line in open(path, 'r'):
            line = line.strip()
            line_items = line.split('\t')
            if len(line_items) != 2:
                continue
            medical_word[str(line_items[0])] = int(line_items[1])
        return medical_word

    def get_vector(self, content):
        return self.get_pinyin_vector(content)

    def get_pinyin_vector(self, content, is_ignore=True):
        """
        把content按照char词典转化为词向量
        :param is_ignore: 
        :param content: unicode编码的中文文本
        :return: 输出词向量
        """
        words = []
        if content:
            for word in content:
                word = pinyin.get_pinyin(word)
                word = str(word)
                if self.medical_word.get(word):
                    words.append(str(self.medical_word[word]))
                elif not is_ignore:
                    words.append('0')

        return words


class Check2Vector(object):
    """
    把语句按照pinyin词典转化为词向量
    """

    def __init__(self, dept_classify_dict_path=global_conf.dept_classify_check_consult_path):
        self.dept_classify_check_consult_path = dept_classify_dict_path
        self.check_id, self.id_check, self.id_check_code, self.code_check_detail = self.load_medical_dic()

    def load_medical_dic(self):
        """装载词典"""
        path = self.dept_classify_check_consult_path
        check_id = {}
        id_check = {}
        id_check_code = {}
        code_check_detail = {}
        for line in open(path, 'r'):
            line = line.strip()
            line_items = line.split('\t')
            if len(line_items) != 4:
                continue
            check_id[line_items[0]] = int(line_items[1])
            id_check[int(line_items[1])] = line_items[0]
            id_check_code[int(line_items[1])] = line_items[2]
            code_check_detail[line_items[2]] = line_items[3]
        return check_id, id_check, id_check_code, code_check_detail


class BaseVector(object):

    def __init__(self, dict_path):
        self.load_dict(dict_path)

    def load_dict(self, path):
        pass


class Label2Vector(object):

    def __init__(self,
                 disease_classify_dict_path=global_conf.disease_classify_dict_path):
        k2v = Key2Value(disease_classify_dict_path, swap=False)
        self.label_dict = k2v.load_dict()

    def get_vector(self, content):
        """
        标签向量化.
        参数:
        content->需要向量化的标签.
        返回值->该标签的对应的向量.
        """
        return self.label_dict.get(str(content))

    def check_value(self, content):
        """
        检查是否在可向量化范围内.
        参数:
        content->需要检查的内容.
        返回值->在范围内-True,否则-False.
        """
        if content in self.label_dict.keys():
            return True
        if content in self.label_dict.values():
            return True
        return False


class Intent2Vector(BaseVector):

    def __init__(self, dict_path):
        super().__init__(dict_path)
        self.word2idx = {}

    def load_dict(self, file_name=global_conf.dept_classify_char_dict_path):
        with open(file_name, 'r') as f:
            for line_temp in f:
                line_temp = line_temp.strip()
                if not line_temp:
                    continue
                _word, _label = line_temp.split('\t')
                self.word2idx[_word] = _label

    def get_vector(self, text):
        seqs = []
        # text无值, 返回空list
        if not text:
            return []
        for word_temp in text:
            if self.word2idx.get(word_temp):
                seqs.append(int(self.word2idx[word_temp]))
        return seqs

    def get_word_vector(self, single_word, **kwargs):
        result = kwargs.get('default_result', 0)
        if self.word2idx.get(single_word):
            result = str(self.word2idx[single_word])
        return result


class Dept2Vector(BaseVector):

    def __init__(self, dict_path):
        self.index2name = {}
        self.name2id = {}
        self.name2index = {}
        super(Dept2Vector, self).__init__(dict_path)

    def load_dict(self, path):
        """
        获得标签名和id
        参数:
        path->标签向量字典文件路径.
        :return:{d_name, d_id}
        """
        for i, line in enumerate(open(path, 'r')):
            dept_name, dept_name_id = line.strip().split('=')
            self.index2name[i] = dept_name
            self.name2id[dept_name] = dept_name_id
            self.name2index[dept_name] = i
        # return self.dept_name_to_id, self.dept_dict, self.dept_id

    def get_vector(self, content):
        """
        标签向量化.
        参数:
        content->需要向量化的标签.
        返回值->该标签的对应的向量.
        """
        return self.name2index.get(content)

    def get_name_from_index(self, index):
        return self.index2name.get(index)

    def get_id_from_name(self, name):
        return self.name2id.get(name)

    def check_value(self, content):
        """
        检查是否在可向量化范围内.
        参数:
        content->需要检查的内容.
        返回值->在范围内-True,否则-False.
        """
        return content in self.name2index


class Char2vectorbody(BaseVector):
    """
    主要是为了实现把实体比方说身体部位在训练中标记出来，进行转化为词向量
    比方说身体部位   $LBP$头$RBP$
    """

    def __init__(self, dict_path):
        super().__init__(dict_path)
        self.medical_word = {}

    def load_dict(self, path):
        """装载词典"""
        for line in open(path, 'r'):
            line = line.strip()
            line_items = line.split('\t')
            if len(line_items) != 2:
                continue
            self.medical_word[str(line_items[0])] = int(line_items[1])
        return self.medical_word

    def get_vector(self, content):
        return self.get_char_vector(content)

    def get_char_vector(self, content):
        """
        把content按照char词典转化为词向量
        :param content: unicode编码的中文文本
        :return: 输出词向量
        """
        dict_type = ['body_part']
        mmseg = MMSeg(dict_type, uuid_all=False, is_uuid=True, update_dict=False, is_all_word=False)
        words = []
        content = utils.get_char_body_part(mmseg, content)
        for word in content:
            word = str(word)
            if self.medical_word.get(word):
                words.append(str(self.medical_word[word]))
        return words


class Word2vector(BaseVector):
    """
    把语句按照pinyin词典转化为词向量
    """

    def __init__(self, dict_path):
        super().__init__(dict_path)
        self.id2word = {}
        self.medical_word = {}

    def load_dict(self, path):
        """装载词典"""
        for line in open(path, 'r'):
            line = line.strip()
            line_items = line.split('\t')
            if len(line_items) != 2:
                print('+++++', line)
                continue
            self.medical_word[str(line_items[0])] = int(line_items[1])
            self.id2word[int(line_items[1])] = str(line_items[0])
        return self.medical_word

    def get_vector(self, content):
        return self.get_word_vector(content)

    def get_word_vector(self, content, seg_type=''):
        """
        把content按照char词典转化为词向量
        :param seg_type: 
        :param content: unicode编码的中文文本
        :return: 输出词向量

        """
        if seg_type == 'all':
            content = jieba.lcut(content.strip(), cut_all=True)
        else:
            content = jieba.lcut(content.strip())
        words = []
        for word in content:
            word = str(word)
            if self.medical_word.get(word):
                words.append(str(self.medical_word[word]))
        return words


class StandardAsk2Vector:

    def __init__(self, path):
        self.id_name, self.name_code = self.load_dict(path)

    def load_dict(self, path):
        """
        获得标签名和id
        参数:
        path->标签向量字典文件路径.
        :return:{d_name, d_id}
        """
        id_name = {}
        name_code = {}
        f = codecs.open(path, 'r', encoding='utf-8')
        for line in f:
            lines = line.strip().split('==')
            id_name[int(lines[0])] = lines[1]
            name_code[lines[1]] = lines[0]
        return id_name, name_code

    def get_vector(self, content):
        """
        标签向量化.
        参数:
        content->需要向量化的标签.
        返回值->该标签的对应的向量.
        """
        return self.name_code.get(content)

    def check_value(self, content):
        """
        检查是否在可向量化范围内.
        参数:
        content->需要检查的内容.
        返回值->在范围内-True,否则-False.
        """
        if content in self.name_code:
            return True
        return False


def tet():
    line = '我身体不舒服头有点疼'
    char2vector = Char2Vector(
        dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
    vector3 = char2vector.get_char_vector(line)
    print(vector3)
    pinyin2vector = Pinyin2vector(
        dept_classify_dict_path=global_conf.dept_classify_pinyin_dict_path)
    vector6 = pinyin2vector.get_pinyin_vector(line)
    print(vector6)
    word2vector = Word2vector(global_conf.dept_classify_cnn_dict_path)
    vector_cnn = word2vector.get_word_vector(line)
    print(vector_cnn)
    check2vector = Check2Vector(dept_classify_dict_path=global_conf.dept_classify_check_consult_path)
    print(check2vector.id_check)
    print(check2vector.check_id)
    body2vector = Char2vectorbody(global_conf.char_vocab_dict_path)
    for word in body2vector.get_vector('我脑袋有问题,我屁股有点疼'):
        print(word)


if __name__ == '__main__':
    tet()
