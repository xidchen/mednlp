#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
synonym.py -- module of synonym

Author: maogy <maogy@guahao.com>
Create on 2017-09-07 Thursday.
"""

import sys
import os
import datetime
import shutil
import codecs
import copy
import optparse
import global_conf
import ailib.utils.ioutil as io_util
import mednlp.dao.loader as loader
from ailib.storage.db import DBWrapper
from ailib.utils.ioutil import SimpleFileLock
from ailib.utils.log import GLLog
from mednlp.dao.update import FileUpdate


class Synonym(object):
    """
    同义词映射类.
    """

    # dict_map = {
    #     'symptom': 'symptom_synonym.dic',
    #     'synonym': 'synonym.dic',
    #     'wy_symptom': 'wy_symptom_synonym.dic',
    #     'wy_symptom_name': 'wy_symptom_name_synonym.dic'
    # }
    # dict_default_map = {
    #     'symptom': 'symptom_synonym.dic.default',
    #     'synonym': 'synonym.dic.default',
    #     'wy_symptom': 'wy_symptom_synonym.dic.default',
    #     'wy_symptom_name': 'wy_symptom_name_synonym.dic.default'
    # }
    dict_map = {
        'symptom': 'symptom.dic',
        'synonym': 'synonym.dic',
        'wy_symptom': 'wy_symptom.dic',
        'wy_symptom_name': 'wy_symptom_name.dic'
    }
    dict_default_map = {
        'symptom': 'symptom.dic.default',
        'synonym': 'synonym.dic.default',
        'wy_symptom': 'wy_symptom.dic.default',
        'wy_symptom_name': 'wy_symptom_name.dic.default'
    }

    # dict_map = {
    #     'synonym': 'synonym.dic',
    #     'wy_symptom_name': 'wy_symptom_name_synonym.dic'
    # }
    # dict_default_map = {
    #     'synonym': 'synonym.dic.default',
    #     'wy_symptom_name': 'wy_symptom_name_synonym.dic.default'
    # }
    base_path = os.path.join(os.path.dirname(__file__), '../../')
    dic_base_path = os.path.join(base_path, './data/dict/synonym/')
    
    def __init__(self, dict_type=[], dict_files=[], **kwargs):
        """
        初始化方法.
        参数:
        dict_type->需要加载的词典类型数组,默认为[],表示加载全部词典.
        可选值:symptom-全体症状,含错误,synonym-哈工大同义词词林,
        wy_symptom-自有同义词,包括症状身体部位和医学词,但是词以ID表示,
        wy_symptom_name:同wy_symptom,但是词以名称表示.
        dict_files->加载的词典文件,优先级高于dict_type.
        update_dict->是否更新词典,默认为False,不更新.
        is_uuid->是否开启返回uuid,默认True,返回uuid.
        uuid_all->是否返回全部重名的uuid,默认False,只返回一个uuid.
        """
        self.logger = kwargs.pop('logger', GLLog('mmseg').getLogger())
        if kwargs.get('update_dict', False):
            self.update_dict(dict_type)
        self.dict_files = dict_files
        self.group_dict = {}
        self.synonym_group_dict = {}
        if not dict_files:
            dict_files = self.get_dict_path(dict_type)
        self.load_dict(dict_files=dict_files)
        self.seg = kwargs.get('seg')

    def update_dict(self, dict_type=[]):
        """
        更新词典.
        参数:
        dict_type->需要更新的词典类型列表.
        """
        db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB', logger=self.logger)
        file_update = FileUpdate(db=db, logger=self.logger)
        if not dict_type:
            dict_type = self.dict_map.keys()
        for type_str in dict_type:
            file_update.update('synonym', type_str, self.dic_base_path)
            # self.__update_one_dict(db, type_str, self.dic_base_path)

    def __update_one_dict(self, db, type_str, out_dir):
        dic_path = os.path.join(out_dir, self.dict_map[type_str])
        lock = SimpleFileLock(dic_path)
        try:
            lock.lock(600)
            today = datetime.date.today().strftime('%Y-%m-%d')
            tmp_dict_file = os.path.join(
                out_dir, '%s.%s' % (self.dict_map[type_str], today))
            out_file = open(tmp_dict_file, 'w')
            synonym_dict = loader.load_synonym_data(db, type_str)
            for group_id, synonym_set in synonym_dict.items():
                out_file.write('%s\t%s\n' % (group_id, '|||'.join(synonym_set)))
            out_file.close()
            dict_file = os.path.join(out_dir, self.dict_map[type_str])
            io_util.file_replace(tmp_dict_file, dict_file)
        finally:
            lock.unlock()

    def get_dict_path(self, dict_type=[]):
        """
        根据指定的词典类型获取该词典类型的词典文件路径.
        如指定的词典类型词典文件不存在则生成默认词典文件.
        参数:
        dict_type->词典类型列表.
        返回值->词典文件路径列表.
        """
        if not dict_type:
            dict_type = self.dict_map.keys()
        dict_path = []
        for type_str in dict_type:
            dict_file = os.path.join(self.dic_base_path,
                                     self.dict_map[type_str])
            if not os.path.exists(dict_file):
                dict_file_default =\
                    os.path.join(self.dic_base_path,
                                 self.dict_default_map[type_str])
                shutil.copy(dict_file_default, dict_file)
            dict_path.append(dict_file)
        return dict_path

    def load_dict(self, dict_type=[], dict_files=[]):
        """
        加载词典文件.
        参数:
        dict_files->词典文件路径列表.文件每行格式:group_id \t synonym1|||synonym2
        """
        if dict_type and not dict_files:
            dict_files = self.get_dict_path(dict_type)
        for f in dict_files:
            lock = SimpleFileLock(f)
            lock.wait(600)
            for line in codecs.open(f, 'r', encoding='utf-8'):
                line_split = line.strip().split('\t')
                if len(line_split) == 2:
                    group_id, synonym_id = line_split
                    synonym_set = self.group_dict.setdefault(group_id, set())
                    synonym_set.add(synonym_id)
                    group_set = self.synonym_group_dict.setdefault(
                            synonym_id, set())
                    group_set.add(group_id)
                    # synonym_set = synonym_str.split('|||')
                    # self.group_dict[group_id] = synonym_set
                    # for synonym_id in synonym_set:
                    #     group_set = self.synonym_group_dict.setdefault(
                    #         synonym_id, set())
                    #     group_set.add(group_id)

    def get_synonym(self, word_id):
        """
        获取同义词.
        """
        group_set = self.synonym_group_dict.get(word_id)
        if not group_set:
            return None
        synonym_set = set()
        for group_id in group_set:
            synonym = self.group_dict.get(group_id)
            synonym_set.update(synonym)
        return synonym_set

    def synonym_extend(self, content=None, words=['']):
        """
        根据同义词扩展内容.
        参数:
        content->需要扩展的词或短语,考虑性能和实际意义,限制最大长度为10,超出不处理.
        """
        if len(content) > 10:
            return content
        combinations = self._build_word_combinations(words)
        extend_synonym = set()
        for comb in combinations:
            # print '|'.join(comb)
            extend_group = self._extend_synonym(content, comb)
            if extend_group:
                extend_synonym.update(extend_group)
        return extend_synonym

    def _extend_synonym(self, content, combination):
        """
        """
        synonym_set_list = []
        for word in combination:
            synonym_set = self.get_synonym(word)
            # print synonym_set
            if synonym_set:
                synonym_set_list.append({word: synonym_set})
        if not synonym_set_list:
            return None
        extend_synonym = set()
        s_len = len(synonym_set_list)
        if s_len == 1:
            synonym_set = synonym_set_list[0]
            word = list(synonym_set.keys())[0]
            s_set = synonym_set[word]
            for s in s_set:
                content_r = copy.deepcopy(content)
                content_r = content_r.replace(word, s)
                extend_synonym.add(content_r)
        if s_len == 2:
            synonym_set = synonym_set_list[0]
            synonym_set2 = synonym_set_list[1]
            word = list(synonym_set.keys())[0]
            word2 = list(synonym_set2.keys())[0]
            s_set = synonym_set[word]
            s_set2 = synonym_set2[word2]
            for s in s_set:
                for s2 in s_set2:
                    content_r = copy.deepcopy(content)
                    content_r = content_r.replace(word, s)
                    content_r = content_r.replace(word2, s2)
                    extend_synonym.add(content_r)
        if s_len == 3:
            synonym_set = synonym_set_list[0]
            synonym_set2 = synonym_set_list[1]
            synonym_set3 = synonym_set_list[2]
            word = list(synonym_set.keys())[0]
            word2 = list(synonym_set2.keys())[0]
            word3 = list(synonym_set3.keys())[0]
            s_set = synonym_set[word]
            s_set2 = synonym_set2[word2]
            s_set3 = synonym_set3[word3]
            for s in s_set:
                for s2 in s_set2:
                    for s3 in s_set3:
                        content_r = copy.deepcopy(content)
                        content_r = content_r.replace(word, s)
                        content_r = content_r.replace(word2, s2)
                        content_r = content_r.replace(word3, s3)
                        extend_synonym.add(content_r)
        return extend_synonym

    def _build_word_combinations(self, words):
        """
        最多考虑三个词的重组.
        """
        w_len = len(words)
        w_combinations = []
        for w1 in words:
            w_combinations.append([w1])
        if w_len > 1:
            for i in range(w_len):
                for j in range(i+1, w_len):
                    w_combinations.append([list(words)[i], list(words)[j]])
        if w_len > 2:
            for i in range(w_len):
                for j in range(i+1, w_len):
                    for k in range(j+1, w_len):
                        w_combinations.append([list(words)[i], list(words)[j], list(words)[k]])
        return w_combinations


if __name__ == '__main__':
    dict_type0 = ['wy_symptom_name']
    content0 = 'F45272432BC7E65DE040A8C00F017153'
    command = """
    python %s -s string -d dictionary[symptom]
    """ % sys.argv[0]
    parser = optparse.OptionParser(usage=command)
    parser.add_option('-s', '--string', dest='string', help='the cut string')
    parser.add_option('-d', '--dict', dest='dict',
                      help='the dictionary file')
    parser.add_option('-u', '--update', dest='update', action='store_true',
                      default=False, help='update the dictionary file')
    (options, args) = parser.parse_args()

    if options.dict is not None:
        dict_type0 = options.dict.split(',')
    if options.string is not None:
        content0 = options.string
    synonym0 = Synonym(dict_type0, update_dict=options.update)
    synonym_set0 = synonym0.get_synonym(content0)
