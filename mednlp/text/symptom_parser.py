#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
symptom_parser.py -- the parser of symptom

Author: maogy <maogy@guahao.com>
Create on 2017-12-27 Wednesday.
"""

import sys
from optparse import OptionParser
from mednlp.text.mmseg import MMSeg
from mednlp.text.synonym import Synonym
from mednlp.utils.utils import unicode_python_2_3

class SymptomParser(object):
    """
    症状解析器.
    """

    def __init__(self, **kwargs):
        self.checker = SymptomCheck()
        # self.extractor = MMSeg(dict_type=['symptom'])
        self.bp_extractor = MMSeg(dict_type=['body_part'])
        self.extender = SymptomExtend(checker=self.checker)

    def parse(self, content):
        """
        解析.
        参数:
        content->需要解析的内容.
        返回值->解析得到的症状,结构:{body_part:{symptom_name: symptom_id}}
        """
        content = unicode_python_2_3(content)
        bps = self.bp_extractor.cut(content)
        if not bps:
            return None
        bp_symptom = {}
        for body_part in bps.keys():
            segs = content.split(body_part)[1:]
            for seg in segs:
                if not seg:
                    continue
                symptoms = self._find_symptom(body_part, seg)
                if symptoms:
                    symptom_found = bp_symptom.setdefault(body_part, {})
                    symptom_found.update(symptoms)
        return bp_symptom

    def _find_symptom(self, body_part, block):
        """
        从语块中寻找症状.
        参数:
        body_part->身体部位名词.
        block->尝试的语句块.
        返回值->症状字典,结构:{symptom_name: symptom_id}
        """
        block = block[:5]
        symptoms = {}
        for w_len in range(5, 0, -1):
            pos = 0
            while pos + w_len < len(block) + 1:
                test_word = block[pos: pos + w_len]
                test_symptom = body_part + test_word
                symptom_id = self.checker.check(test_symptom)
                if symptom_id:
                    symptoms[test_symptom] = symptom_id
                    e_symptom = self.extender.extend(test_symptom)
                    if e_symptom:
                        symptoms.update(e_symptom)
                pos += 1
        # print '@@@@@', ','.join(symptoms.keys())
        return symptoms


class SymptomExtend(object):
    """
    症状同义词扩展器.
    """

    def __init__(self, **kwargs):
        """
        初始化函数.
        参数:
        extractor->切词器,可选,默认symptom词库,开启小词切分.
        extender->同义词扩展器,可选,默认wy_symptom_name词库.
        """
        self.extractor = kwargs.pop('extractor', MMSeg(dict_type=['symptom'],
                                                       is_all_word=True))
        self.extender = kwargs.pop('extender',
                                   Synonym(dict_type=['wy_symptom_name']))
        self.checker = kwargs.pop('checker', SymptomCheck())

    def extend(self, symptom):
        """
        症状同义词扩展.
        参数:
        symptom->症状名称.
        """
        sub_symptom = self.extractor.cut(unicode_python_2_3(symptom))
        if sub_symptom:
            extend_symptom = self.extender.synonym_extend(symptom,
                                                          sub_symptom.keys())
            if extend_symptom:
                extend_symptom = {}
                for e_symptom in extend_symptom:
                    symptom_id = self.checker.check(e_symptom)
                    if symptom_id:
                        extend_symptom[e_symptom] = symptom_id
                return extend_symptom
        return None
        

class SymptomCheck(object):
    """
    症状检查器.
    """

    def __init__(self, **kwargs):
        """
        初始化函数.
        参数:
        extractor->症状实体抽取器,可选,默认symptom词库.
        """
        self.extractor = kwargs.pop('extractor', MMSeg(dict_type=['symptom']))

    def check(self, word):
        """
        检查是否症状.
        参数:
        word->待检查的词.
        返回值->是症状返回症状ID,否则返回False
        """
        test_symptom = unicode_python_2_3(word)
        symptoms = self.extractor.cut(test_symptom)
        if not symptoms:
            return False
        for s_names, s_id in symptoms.items():
            if s_names == test_symptom:
                return s_id
        return False


if __name__ == "__main__":
    content = '    3年前无诱因反复头晕，多次测血脂高于正常，要求休息。'
    command = """
    python %s -s string
    """ %sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option("-s", "--string", dest="string", help="the cut string")
    (options, args) = parser.parse_args()
    if options.string is not None:
        content = options.string
    parser = SymptomParser()
    print(parser.parse(content))
