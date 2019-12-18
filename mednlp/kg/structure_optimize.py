#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: chenxd
Create on 2019.01.11
"""

import re
import global_conf
from mednlp.text.mmseg import MMSeg


class StructureOptimization(object):
    dic_base_path = global_conf.dict_mmseg_path
    dict_mmseg = re.split('/', dic_base_path)[-2]
    if dict_mmseg == 'mmseg_kg':
        dict_list = ['disease', 'symptom_wy', 'inspection_item',
                     'examination_item', 'examination_result',
                     'physical', 'medicine', 'treatment']
    else:
        dict_list = ['disease', 'disease_all',
                     'symptom_wy', 'symptom_wy_synonym_extend',
                     'inspection_item',
                     'examination_item', 'examination_result',
                     'physical', 'medicine', 'treatment']

    def __init__(self):
        super(StructureOptimization, self).__init__()
        self.extractor = MMSeg(self.dict_list, uuid_all=False, is_uuid=True,
                               update_dict=False, is_all_word=False )

    def obtain_uuid(self, word):
        result = self.extractor.cut(word)
        uuid = result.get(word, '')
        return uuid


class MedicalHistoryStructure(object):

    def __init__(self):
        super(MedicalHistoryStructure, self).__init__()

    def past_patt_match(self, text, patt, sen_position):
        entity_dict = {}
        res_match = re.findall(patt, text)
        ## findall可以将两边括号的内容分别匹配出来放进一个集合中，而finditer只能匹配出所有
        iter_match = re.finditer(patt, text)
        if not sen_position:
            sen_position = [0, 0]
        k = 0
        for res_iter in iter_match:
            it_words = res_iter.group()
            it_position = res_iter.span()
            position = [sen_position[0] + it_position[0],
                        sen_position[0] + it_position[1]]
            res = res_match[k]
            k += 1
            if len(res) == 2:
                status = res[0]
                words_entity = res[1]
                entity_match_pos = re.search(words_entity, it_words).span()
                entity_position = [position[0] + entity_match_pos[0],
                                   position[0] + entity_match_pos[1]]
                status_position = [position[0],
                                   position[0] + entity_match_pos[0]]
                entity_dict['text'] = words_entity
                entity_dict['type'] = 'disease'
                entity_dict['name'] = words_entity
                entity_dict['position'] = entity_position
                entity_dict['property'] = [
                    {'text': status, 'type': 'status',
                     'value': '无', 'position': status_position}]
        return entity_dict

    def allergen_match(self, text, patt, sen_position):
        entity_dict_ls = []
        if not sen_position:
            sen_position = [0, 0]
        res_match = re.finditer(patt, text)
        if res_match:
            for res in res_match:
                entity_dict = {}
                words_match = res.group()
                pos_match = res.span()
                res_pos = [sen_position[0] + pos_match[0],
                           sen_position[0] + pos_match[1]]
                word_deal = re.sub('[有对过敏药物\"\'“‘”]', '', words_match)
                # print(word_deal, words_match)
                entity_mt =  re.search('(药物)?过敏', words_match)
                entity_mt_w = entity_mt.group()
                entity_mt_p = entity_mt.span()
                words_sp = word_deal.split('、')
                entity_dict['text'] = entity_mt_w
                entity_dict['type'] = 'disease'
                entity_dict['name'] = entity_mt_w
                entity_dict['position'] = [entity_mt_p[0] + res_pos[0],
                                           entity_mt_p[1] + res_pos[0]]
                property_ls = []
                for word in words_sp:
                    word_pos_match = re.search(word, words_match)
                    if word_pos_match:
                        word_pos = word_pos_match.span()
                        property_position = [res_pos[0] + word_pos[0],
                                             res_pos[0] + word_pos[1]]
                        pro_dict = {'text': word, 'type': 'allergen',
                                    'value': word, 'position': property_position}
                        property_ls.append(pro_dict)
                entity_dict['property'] = property_ls
                entity_dict_ls.append(entity_dict)
        return entity_dict_ls


if __name__ == '__main__':
    model = StructureOptimization()
    print(model.obtain_uuid('戒酒'))
