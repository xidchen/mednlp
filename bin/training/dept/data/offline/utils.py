import os
import global_conf
import pypinyin
from mednlp.utils.utils import unicode_python_2_3

mode_dict = {'full': pypinyin.NORMAL, 'first': pypinyin.FIRST_LETTER}


def load_pinyin_dic(dicfiles=None):
    """
    加载自定义词典.
    参数:
    dicfiles->字典文件列表.
    """
    dict_files = dicfiles or [os.path.join(global_conf.dict_path, 'gl_pinyin_custom.dic')]
    pinyin_dict = {}
    for dicfile in dict_files:
        for line in open(dicfile):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = unicode_python_2_3(line)
            (word, pinyin) = line.split(u'|')
            pinyin = pinyin.split(u',')
            pinyin_dict[word] = [[py] for py in pinyin]
    pypinyin.load_phrases_dict(pinyin_dict, style=pypinyin.NORMAL)


def get_pinyin(content, mode='full', errors='ignore', separator=u''):
    """
    生成拼音.
    参数:
    content->unicode类型的字符串.
    mode->可选值:full-全拼,first-拼音首字母
    返回值:
    unicode类型的字符串.
    """
    unicode_content = unicode_python_2_3(content)
    return pypinyin.slug(unicode_content, separator=separator, style=mode_dict[mode],
                         errors=errors)


class Dept2Vector(object):
    def __init__(self, dict_path):
        self.index_dept_mapping = {}
        self.dept_id_mapping = {}
        self.dept_index_mapping = {}
        self.load_dict(dict_path)

    def load_dict(self, path):
        """
        获得标签名和id
        参数:
        path->标签向量字典文件路径.
        :return:{d_name, d_id}
        """

        for i, line in enumerate(open(path, 'r')):
            dept_name, dept_name_id = line.strip().split('=')
            self.index_dept_mapping[i] = dept_name
            self.dept_id_mapping[dept_name] = dept_name_id
            self.dept_index_mapping[dept_name] = i

    def get_vector(self, content, reverse=False):
        """
        标签向量化.
        参数:
        content->需要向量化的标签.
        返回值->该标签的对应的向量.
        """
        mapping = self.dept_index_mapping if not reverse else self.index_dept_mapping
        data = mapping.get(content)
        return data

    def check_value(self, content):
        """
        检查是否在可向量化范围内.
        参数:
        content->需要检查的内容.
        返回值->在范围内-True,否则-False.
        """
        if content in self.dept_index_mapping:
            return True
        return False


class Char2vector(object):
    def __init__(self, dept_classify_dict_path):
        self.dept_classify_dict_path = dept_classify_dict_path
        self.word_num_mapping = {}
        self.num_word_mapping = {}
        self.load_medical_dic()

    def load_medical_dic(self):
        """装载词典"""
        path = self.dept_classify_dict_path
        for dict_line in open(path, 'r'):
            line_items = str(dict_line).strip().split('\t')
            if len(line_items) != 2:
                continue

            self.word_num_mapping[line_items[0]] = int(line_items[1])
            self.num_word_mapping[int(line_items[1])] = line_items[0]

    def get_vector(self, content, reverse=False):
        return self.get_char_vector(content, reverse=reverse)

    def get_char_vector(self, content, is_ignore=True, reverse=False):
        """
        把content按照char词典转化为词向量
        :param content: unicode编码的中文文本
        :param is_ignore: 不忽略的用0填补
        :param reverse: 反向字典
        :return: 输出词向量
        """

        words = []
        if content is None:
            return words
        mapping = self.word_num_mapping if not reverse else self.num_word_mapping
        for word in content:
            word = str(word) if not reverse else int(word)
            item = mapping.get(word)
            if item:
                words.append(str(item))
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
        self.word_num_mapping = {}
        self.num_word_mapping = {}
        self.load_medical_dic()

    def load_medical_dic(self):
        """装载词典"""
        path = self.dept_classify_dict_path
        for line in open(path, 'r'):
            line = line.strip()
            line_items = line.split('\t')
            if len(line_items) != 2:
                continue
            self.word_num_mapping[str(line_items[0])] = int(line_items[1])
            self.num_word_mapping[int(line_items[1])] = str(line_items[0])

    def get_vector(self, content, reverse=False):
        return self.get_pinyin_vector(content, reverse=reverse)

    def get_pinyin_vector(self, content, is_ignore=True, reverse=False):
        """
        把content按照char词典转化为词向量
        :param content: unicode编码的中文文本
        :param is_ignore: 不忽略的用0填补
        :param reverse: 反向字典
        :return: 输出词向量
        """
        words = []
        if content is None:
            return words
        mapping = self.word_num_mapping if not reverse else self.num_word_mapping
        for word in content:
            word = str(get_pinyin(word)) if not reverse else int(word)
            if mapping.get(word):
                words.append(str(mapping[word]))
            elif not is_ignore:
                words.append('0')
        return words
