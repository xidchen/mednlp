from mednlp.dept.utils.vectors import Disease2Vector, InternetDept2Vector, SubDept2Vector, Probability2Vector, \
    Pinyin2vector, Char2vector, Dept2Vector, Word2vector, Medicine2Dept
from mednlp.dept.utils.misc import DeptDictionary
import global_conf

__all__ = [
    'disease_helper', 'py_helper', 'char_helper', 'dept_helper',
    'word_helper', 'internet_dept_helper',
    'sub_pediatrics_helper', 'sub_chinese_medicine_helper', 'sub_tumor_helper',
    'accuracy_helper', 'accuracy_helper1', 'medicine_helper', 'dept_dictionary'
]

disease_helper = Disease2Vector(dict_path=global_conf.dept_disease_dept_id_path)

py_helper = Pinyin2vector(dept_classify_dict_path=global_conf.dept_classify_pinyin_dict_path)
char_helper = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
dept_helper = Dept2Vector(global_conf.dept_classify_dept_path)
internet_dept_helper = InternetDept2Vector(dict_path=global_conf.standard_transform_internet_dept_path)
word_helper = Word2vector(global_conf.dept_classify_cnn_dict_path)

sub_pediatrics_helper = SubDept2Vector(global_conf.children_sub_deptment, '儿科')
sub_chinese_medicine_helper = SubDept2Vector(global_conf.chinese_medicine_sub_deptment, '中医科')
sub_tumor_helper = SubDept2Vector(global_conf.tumour_sub_deptment, '肿瘤科')

medicine_helper = Medicine2Dept(global_conf.medicine_dept_score_path)
dept_dictionary = DeptDictionary(dept_helper, sub_pediatrics_helper,
                                 sub_chinese_medicine_helper, sub_tumor_helper)

accuracy_helper = Probability2Vector(global_conf.accuracy_path)
accuracy_helper1 = Probability2Vector(global_conf.accuracy_second_path)
