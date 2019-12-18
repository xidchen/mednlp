import codecs
import jieba
import mednlp.text.pinyin as pinyin
from collections import defaultdict


class BaseVector(object):

    def __init__(self, dict_path):
        self.load_dict(dict_path)

    def load_dict(self, path):
        raise NotImplementedError


class Char2vector(object):
    def __init__(self, dept_classify_dict_path):
        self.dept_classify_dict_path = dept_classify_dict_path
        self.medical_word = self.load_medical_dic()

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
        :param content: unicode编码的中文文本
        :param is_ignore:
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

    def __init__(self, dept_classify_dict_path):
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
        :param content: unicode编码的中文文本
        :param is_ignore:
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


class Word2vector(BaseVector):
    """
    把语句按照pinyin词典转化为词向量
    """

    def __init__(self, path):
        self.medical_word = {}
        self.id2word = {}
        super(Word2vector, self).__init__(path)

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


class InternetDept2Vector(BaseVector):
    def __init__(self, dict_path):
        self.standard2internet = {}
        self.internet2id = {}
        super(InternetDept2Vector, self).__init__(dict_path)

    def load_dict(self, path):
        file_stream = codecs.open(path, 'r', encoding='utf-8')
        for line in file_stream:
            standard_name, internet_name, dept_id = line.strip().split('=')
            self.standard2internet[standard_name] = internet_name
            self.internet2id[internet_name] = dept_id
        file_stream.close()

    def get_internet_from_standard(self, standard):
        return self.standard2internet.get(standard)

    def get_id_from_internet(self, internet):
        return self.internet2id.get(internet)


class SubDept2Vector(BaseVector):
    def __init__(self, dict_path, chief_dept_name):
        self.parent_name = chief_dept_name
        self.dept2child = {}
        self.child2id = {}
        self.child2dept = {}
        super(SubDept2Vector, self).__init__(dict_path)

    def load_dict(self, path):
        file_stream = codecs.open(path, 'r', encoding='utf-8')
        for line in file_stream:
            dept_name, child_name, child_dept_id = line.strip().split('=')
            self.dept2child[dept_name] = child_name
            self.child2id[child_name] = child_dept_id
            self.child2dept[child_name] = dept_name
        file_stream.close()

    def get_child_from_dept(self, dept_name):
        return self.dept2child.get(dept_name)

    def get_id_from_child(self, child_name):
        return self.child2id.get(child_name)

    def get_dept_from_child(self, child_name):
        return self.child2dept.get(child_name)


class Probability2Vector(BaseVector):
    def __init__(self, dict_path):
        self.id2accuracy = {}
        super(Probability2Vector, self).__init__(dict_path)

    def load_dict(self, path):
        file_stream = codecs.open(path, 'r', encoding='utf-8')
        for line in file_stream:
            prob_id, accuracy = line.strip().split('\t')
            self.id2accuracy[prob_id] = accuracy
        file_stream.close()

    @staticmethod
    def _get_id(probability):
        assert 0 <= probability <= 1
        prob = probability * 100
        prob = int(prob) // 2 * 2
        return str(prob)

    def get_accuracy_from_probability(self, probability):
        prob_id = self._get_id(probability)
        return self.id2accuracy.get(prob_id)


class Disease2Vector(BaseVector):
    def __init__(self, dict_path):
        self.disease2dept = {}
        self.dept2id = {}
        super(Disease2Vector, self).__init__(dict_path)

    def load_dict(self, path):
        """
        加载疾病-科室、科室-科室id对应关系的文件
        :return: 无
        """
        file_stream = codecs.open(path, 'r', encoding='utf-8')
        for line in file_stream:
            disease, dept, dept_id = line.strip().split('=')
            self.disease2dept[disease] = dept
            self.dept2id[dept] = dept_id
        file_stream.close()

    def get_dept_from_disease(self, disease):
        return self.disease2dept.get(disease)

    def get_id_from_dept(self, dept):
        return self.dept2id.get(dept)


class Medicine2Dept(object):
    def __init__(self, dict_path):
        self.disease2dept = defaultdict(dict)
        self.load_dict(dict_path)

    def load_dict(self, path):
        """
        加载疾病-科室、科室-科室id对应关系的文件
        :return: 无
        """
        file_stream = codecs.open(path, 'r', encoding='utf-8')
        for i, line in enumerate(file_stream):
            disease, dept, percentage = line.strip().split('\t')
            dept2score = self.disease2dept[disease]
            dept2score[dept] = float(percentage)
        file_stream.close()

    def get_dept_score_by_medicine(self, medicine):
        return self.disease2dept.get(medicine)
