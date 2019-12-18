#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
find_basis.py -- file aimed at finding the basis of dignosis or operation

Author: yinwd <yinwd@guahao.com>
Create on 2019-04-08.
"""

import re
import json
import numpy as np
from mednlp.text.mmseg import MMSeg
from mednlp.kg.drgs.rule_basis_conf import rule_result_list

class FindingBasis(object):

    def __init__(self):
        self.rule_result_list = rule_result_list
        super(FindingBasis, self).__init__()

    def result_audit_rules(self, txt_json):
        result_rules = []
        for rule_result_set in rule_result_list:
            result_one_rule = self.result_keywords_rule(rule_result_set, txt_json)
            result_rules.append(result_one_rule)
        return result_rules

    def result_keywords_rule(self, rule_result_set, txt_json):
        judge_result = ''
        basis_list = []
        if rule_result_set:
            rule_set, rule_result = rule_result_set[0], rule_result_set[-1]
            match_rule_result = ''
            for key, value in rule_set.items():
                content = ''
                words_list = value.get('key_word')
                content_type = value.get('content_type', '')
                paragraph_type = value.get('paragraph_type', '')
                content_c = txt_json.get(content_type, '')
                if content_c:
                    content = content_c.get(paragraph_type)
                    basis_list.append(self.get_keywords_basis(words_list, content, content_type, paragraph_type))
                if words_list and content:
                    res = self.get_key_words(words_list, content)
                    if res:
                        match_rule_result += key + '+'
                    else:
                        match_rule_result += key + '-'
            judge_result = rule_result.get(match_rule_result)
            if not judge_result:
                judge_result = rule_result.get('other')
        result = {}
        result['judge_result'] = judge_result
        result['basis'] = basis_list
        return result

    def get_key_words(self, words_list, content):
        return re.findall("|".join(words_list), content)

    def get_keywords_basis(self, words_list, content, content_type, paragraph_type):
        basis_dict = {}
        basis_dict['source'] = str(content_type) + '-' + str(paragraph_type)
        basis_cont = ''
        if content:
            sp_content = re.split('[，。,;；]', content)
            for sp_cont in sp_content:
                if self.get_key_words(words_list, sp_cont):
                    basis_cont += sp_cont
        basis_dict['basis'] = basis_cont
        return basis_dict

    def get_value_compare(self, items, value, rule_dict):
        std_value = rule_dict.get(items)
        rule_status = rule_dict.get('status') # 大于还是小于
        if value:
            return None

if __name__ == '__main__':
    text = {'入院记录':{'主诉':'患者3天前来进行化疗'},
            '手术记录单':{'手术名称':'放疗',"手术经过":"左肺行肺叶切除手术"},
            '出院记录': {'住院经过':'化疗'}
            }
    model = FindingBasis()
    res = model.result_keywords_rule(rule_result_list[1], text)
    print(res)





