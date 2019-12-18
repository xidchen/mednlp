#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mmseg.py -- seg for medical word

Author: chenxd
Create on 2018-07-05 Wednesday.
"""

import codecs
import re
import sys
import os
import shutil
import global_conf
from collections import OrderedDict
from optparse import OptionParser
from ailib.storage.db import DBWrapper
from ailib.utils.log import GLLog
from ailib.utils.ioutil import SimpleFileLock
from mednlp.dao.update import FileUpdate
from mednlp.text.dic_filter import filter_doctor_dict, extend_symptom
from mednlp.text.dic_filter import extend_core, extend_area


PUNCTUATIONS = re.compile(r'[\'|",.?!:; ’；：。，《》【】　+“]+')
encoding = 'utf-8'


class MMSeg(object):

    dict_map_430 = {
        'disease': 'disease.dic',
        'symptom': 'symptom.dic',
        'symptom_all': 'symptom_all.dic',
        'symptom_wy': 'symptom_wy.dic',
        'synonym': 'synonym.dic',
        'body_part': 'body_part.dic'
    }
    dict_map_326 = {
        'std_department': 'std_department.dic',
        'hospital_department': 'hospital_department.dic',
        'disease_all': 'disease_all.dic',
        'hospital': 'hospital.dic',
        'doctor': 'doctor.dic',
        'treatment': 'treatment.dic',
        'medicine': 'medicine.dic',
        'area': 'area.dic'
    }
    dict_map_kg = {
        'area': 'area.dic',
        'disease': 'disease.dic',
        'symptom': 'symptom.dic',
        'symptom_wy': 'symptom_wy.dic',
        'synonym': 'synonym.dic',
        'body_part': 'body_part.dic',
        'std_department': 'std_department.dic',
        'treatment': 'treatment.dic',
        'inspection_item': 'inspection_item.dic',
        'examination_item': 'examination_item.dic',
        'examination_result': 'examination_result.dic',
        'physical': 'physical.dic',
        'hospital_department': 'hospital_department.dic',
        'hospital': 'hospital.dic',
        'doctor': 'doctor.dic',
        'medicine': 'medicine.dic'
    }
    dict_other = {
        'core': 'core.dic',
        'hospital_brand': 'hospital_brand.dic',
        'symptom_wy_synonym_extend': 'symptom_wy_synonym_extend.dic',
        'hospital_grade': 'hospital_grade_custom.dic',
        'doctor_level': 'doctor_level_custom.dic',
        'medical_word': 'medical_words_custom.dic',
        'physical': 'physical_custom.dic',
        'crowd': 'crowd_custom.dic',
        'inspection_kg': 'inspection_kg_custom.dic'
    }

    def merge_dicts(*dict_args):
        """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
        """
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result

    dic_base_path = global_conf.dict_mmseg_path
    dict_mmseg = re.split('/', dic_base_path)[-2]
    if  dict_mmseg == 'mmseg_kg':
        dict_map = merge_dicts(dict_other, dict_map_kg)
    else:
        dict_map = merge_dicts(dict_map_430, dict_map_326, dict_other)

    dict_custom_map = {
        'area': 'area_custom.dic',
        'body_part': 'body_part_custom.dic',
        'disease': 'disease_custom.dic',
        'doctor': 'doctor_custom.dic',
        'hospital': 'hospital_custom.dic',
        'medicine': 'medicine_custom.dic',
        'std_department': 'std_department_custom.dic',
        'symptom_wy': 'symptom_custom.dic',
        'treatment': 'treatment_custom.dic'
    }

    dict_default_map = {
        'core': 'core.dic.default',
        'disease': 'disease.dic.default',
        'disease_all': 'disease_all.dic.default',
        'symptom': 'symptom.dic.default',
        'symptom_all': 'symptom_all.dic.default',
        'symptom_wy': 'symptom_wy.dic.default',
        'symptom_synonym_group': 'symptom_synonym_group.dic.default',
        'body_part': 'body_part.dic.default',
        'std_department': 'std_department.dic.default',
        'hospital_department': 'hospital_department.dic.default',
        'hospital': 'hospital.dic.default',
        'hospital_brand': 'hospital_brand.dic.default',
        'doctor': 'doctor.dic.default',
        'treatment': 'treatment.dic.default',
        'medicine': 'medicine.dic.default',
        'area': 'area.dic.default',
        'symptom_wy_synonym_extend': 'symptom_wy_synonym_extend.dic.default',
        'synonym': 'synonym.dic.default'
    }
    dict_default_map_kg = {
        'core': 'core.dic.default',
        'disease': 'disease.dic.default',
        'symptom': 'symptom.dic.default',
        'symptom_wy': 'symptom_wy.dic.default',
        'body_part': 'body_part.dic.default',
        'std_department': 'std_department.dic.default',
        'hospital_department': 'hospital_department.dic.default',
        'hospital': 'hospital.dic.default',
        'hospital_brand': 'hospital_brand.dic.default',
        'doctor': 'doctor.dic.default',
        'treatment': 'treatment.dic.default',
        'medicine': 'medicine.dic.default',
        'area': 'area.dic.default',
        'synonym': 'synonym.dic.default',
        'physical': 'physical.dic.default',
        'inspection_item': 'inspection_item.dic.default',
        'examination_item': 'examination_item.dic.default',
        'examination_result': 'examination_result.dic.default'
    }
    base_path = os.path.join(os.path.dirname(__file__), '../../')

    def __init__(self, dict_type=None, dict_files=None, **kwargs):

        if not dict_type:
            dict_type = []
        if not dict_files:
            dict_files = []
        if self.dict_mmseg == 'mmseg_kg':
            self.dict_default_map = self.dict_default_map_kg

        self.logger = kwargs.pop('logger', GLLog(
            'mmseg', log_dir=global_conf.log_dir).getLogger())
        self.is_uuid = kwargs.pop('is_uuid', True)
        self.uuid_all = kwargs.pop('uuid_all', False)
        self.is_all_word = kwargs.pop('is_all_word', False)
        if kwargs.get('update_dict', False):
            self.update_dict(dict_type)
        self.dict_files = dict_files
        self.dictionary = {}
        # print(dict_type)
        if not dict_files:
            dict_files = self.get_dict_path(dict_type)
        # print('dict_file:'+str(dict_files))
        self.load_dict(dict_files=dict_files)


    def update_dict(self, dict_type=None, verbose=True):

        if not dict_type:
            # dict_type = self.dict_map.keys()
            # To ensure the 'symptom_wy_synonym_extend' comes after 'symptom_wy'
            if self.dict_mmseg == 'mmseg_kg':
                dict_type = (list(self.dict_map_kg.keys())
                             + list(self.dict_other.keys()))
            else:
                dict_type = (list(self.dict_map_430.keys())
                             + list(self.dict_map_326.keys())
                             + list(self.dict_other.keys()))

        db_430 = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB',
                           logger=self.logger)
        db_326 = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB',
                           logger=self.logger)
        db_kg = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB',
                           logger=self.logger)
        if self.dict_mmseg == 'mmseg_kg':
            file_update_326 = FileUpdate(db=db_326, logger=self.logger)
            file_update_430 = FileUpdate(db=db_326, logger=self.logger)
            file_update_kg = FileUpdate(db=db_kg, logger=self.logger)
        else:
            file_update_430 = FileUpdate(db=db_430, logger=self.logger)
            file_update_326 = FileUpdate(db=db_326, logger=self.logger)
            file_update_kg = ''


        for type_str in dict_type:
            # print(type_str)

            if self.dict_mmseg == 'mmseg':
                if type_str in self.dict_map_430:
                    file_update_430.update(self.dict_mmseg, type_str, self.dic_base_path)

            elif type_str == 'doctor':
                    print('------>doctor update<------')
                    file_update_326.update(self.dict_mmseg, type_str,
                                           self.dic_base_path,
                                           dic_filter=filter_doctor_dict)
            elif type_str == 'area':
                file_update_326.update(
                    self.dict_mmseg, type_str, self.dic_base_path,
                    handler=extend_area)
            elif type_str in ['hospital', 'medicine']:
                file_update_326.update(self.dict_mmseg, type_str,
                                       self.dic_base_path)

            elif type_str in self.dict_map_kg:
                # print(type_str, self.dict_mmseg, self.dic_base_path)
                file_update_kg.update(self.dict_mmseg, type_str, self.dic_base_path)

            else:
                extend_core()
                extend_symptom(verbose=False)
                # continue
            if verbose:
                print(str(type_str) + " updated")
        if verbose:
            print("Dict UPDATED TO NEWEST")

    def get_dict_path(self, dict_type=None):
        """
        根据指定的词典类型获取该词典类型的词典文件路径.
        如指定的词典类型词典文件不存在则生成默认词典文件.
        参数:
        dict_type->词典类型列表.
        返回值->词典文件路径列表.
        """
        if not dict_type:
            dict_type = list(self.dict_map.keys())
        dict_path = []
        for type_str in dict_type:
            dict_file = os.path.join(self.dic_base_path,
                                     self.dict_map[type_str])
            # print(dict_file)
            ### 添加自定义词典文件
            if type_str in self.dict_custom_map:
                dict_file_add = os.path.join(self.dic_base_path,
                                             self.dict_custom_map[type_str])
                dict_path.append(dict_file_add)
            if not os.path.exists(dict_file):
                dict_file_default = os.path.join(
                    self.dic_base_path, self.dict_default_map[type_str])
                # cp dict_file_default dict_file
                shutil.copy(dict_file_default, dict_file)

            dict_path.append(dict_file)

        return dict_path

    def load_dict(self, dict_type=None, dict_files=None):

        if not dict_type:
            dict_type = []
        if dict_type and not dict_files:
            dict_files = self.get_dict_path(dict_type)
        # print('load_dict', dict_files)
        for f in dict_files:
            lock = SimpleFileLock(f)
            lock.wait(600)
            if os.path.exists(f):
                for line in codecs.open(f, 'r', encoding):
                    line_split = line.strip().split('\t')
                    if len(line_split) == 2:
                        word, uuid = line_split
                        word = word.strip()
                        if self.is_uuid:
                            if self.uuid_all:
                                self.dictionary.setdefault(word, set()).add(uuid)
                            else:
                                self.dictionary[word] = uuid
                        else:
                            self.dictionary[word] = 1

    def get_punctuation_tokens(self, s):
        return re.split(PUNCTUATIONS, s)

    def is_word(self, token):
        return self.dictionary.get(token)

    def cut(self, sentence, maximum=20):

        words = OrderedDict()
        if sentence is None:
            return words
        for s in self.get_punctuation_tokens(sentence):
            self._cut_forward(s, words, maximum)
            self._cut_backward(s, words, maximum)
        return words

    def _cut_forward(self, sentence, words, maximum):
        str_len = len(sentence)
        i = 0
        while i < str_len + 1:
            chunk_end_index = i + maximum
            if chunk_end_index > str_len:
                chunk_end_index = str_len
            for j in range(chunk_end_index, i - 1, -1):
                chunk = sentence[i: j + 1]
                uuid = self.is_word(chunk)
                if uuid:
                    words[chunk] = uuid
                    chunk_len = j - i
                    if not self.is_all_word:
                        i += chunk_len
                        break
            i += 1

    def _cut_backward(self, sentence, words, maximum):
        str_len = len(sentence)
        i = str_len
        while i > 0:
            chunk_end_index = i - maximum
            if chunk_end_index < 0:
                chunk_end_index = 0
            for j in range(chunk_end_index, i-1, +1):
                chunk = sentence[j: i+1]
                uuid = self.is_word(chunk)
                if uuid:
                    words[chunk] = uuid
                    chunk_len = i - j
                    if not self.is_all_word:
                        i -= chunk_len
                        break
            i -= 1

    def segment(self, sentence, maximum=20):

        tokens = {}
        if sentence is None:
            return tokens
        i = len(sentence)
        while i > 0:
            chunk_start = i - maximum
            if chunk_start < 0:
                chunk_start = 0
            for pos in range(chunk_start, i):
                chunk = sentence[pos: i]
                uuid = self.is_word(chunk)
                if uuid:
                    tokens[chunk] = uuid
                    # tokens[uuid] = chunk
                    i -= i - pos - 1
                    break
            i -= 1
        return tokens

    def paragraph_segment(self, paragraph):

        words = []
        if paragraph is None:
            return words

        for sentence in self.get_punctuation_tokens(paragraph):
            words.append(self.segment(sentence))
        return words


if __name__ == "__main__":
    dict_type_0 = []
    kd = False
    content = '碘[125I]血管紧张素I放射免疫分析药盒，细菌（高倍）十二指肠先天性闭锁、缺如和狭窄'
    command = """
    python %s -s string -d dictionary[medicine,disease]
    """ % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option("-s", "--string", dest="string", help="the cut string")
    parser.add_option("-d", "--dict", dest="dict", help="the dictionary file")
    parser.add_option("-u", "--update", dest="update", action="store_true",
                      default=False, help="update the dictionary file")

    (options, args) = parser.parse_args()
    if options.dict is not None:
        dict_type_0 = options.dict.split(',')
    if options.string is not None:
        content = options.string
    extractor = MMSeg(dict_type_0, uuid_all=False, is_uuid=True,
                      update_dict=options.update, is_all_word=False)
    entities = extractor.cut(content)
    for k, v in entities.items():
        print(k, v)
