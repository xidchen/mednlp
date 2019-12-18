#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import global_conf
from ailib.client.ai_service_client import AIServiceClient


class ClinicalGuide(object):

    def __init__(self):
        super(ClinicalGuide, self).__init__()
        self.ai_service = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')


    def get_highlight_basis(self, content_input, content_basis):
        '''
        获取诊断依据中能够在输入文本中匹配的文本的高亮位置
        :param content_input:输入文本字典
        :param content_basis:诊断依据
        :return:匹配成功的高亮位置
        '''
        parms = {
            'chief_complaint': content_input,
            'general_info': content_basis,
            'model': '1'
        }
        try:
            structuration_result = self.ai_service.query(parms, service='medical_record', method='get', timeout=1)
            structuration_data = structuration_result.get('data')
            if not structuration_data:
                structuration_data = {}
        except:
            structuration_data = {}
        basis_structuration_data = structuration_data.get('general_info')
        basis_match_cond, basis_high_cond = self.get_candidate(basis_structuration_data)
        input_structuration_data = structuration_data.get('chief_complaint')
        input_match_cond, _ = self.get_candidate(input_structuration_data)
        highlight_word, highlight_position_list = self._get_highlight_list(
                input_match_cond, basis_match_cond, basis_high_cond)
        highlight_position = self._get_highlight(highlight_position_list)

        highlight_words = []
        for posi in highlight_position:
            highlight_words.append(content_basis[posi[0]: posi[1]])

        return highlight_words, highlight_position

    def get_highlight_basis_items(self, content_input, content_basis):
        '''
        获取诊断依据中能够在输入文本中匹配的文本的高亮位置
        :param content_input:输入文本字典
        :param content_basis:诊断依据
        :return:匹配成功的高亮位置
        '''
        content_input['general_info'] = content_basis
        content_input['model'] = '1'

        structuration_result = self.ai_service.query(content_input, service='medical_record', method='get')
        structuration_data = structuration_result.get('data')
        basis_structuration_data = structuration_data.get('general_info')
        basis_match_cond, basis_high_cond = self.get_candidate(basis_structuration_data)
        diagnosis_basis_highlight = []
        diagnosis_highlight_words = []
        for keys in ['chief_complaint', 'medical_history']:
            dict_high = {}
            input_structuration_data = structuration_data.get(keys)
            input_match_cond, _ = self.get_candidate(input_structuration_data)
            highlight_word, highlight_position_list = self._get_highlight_list(
                input_match_cond, basis_match_cond, basis_high_cond)
            highlight_position = self._get_highlight(highlight_position_list)
            dict_high[keys] = highlight_position
            diagnosis_basis_highlight.append(dict_high)
            highlight_words = []
            dict_words = {}
            for posi in highlight_position:
                highlight_words.append(content_basis[posi[0]: posi[1]])
            dict_words[keys] = highlight_words
            diagnosis_highlight_words.append(dict_words)

        return diagnosis_highlight_words, diagnosis_basis_highlight

    def get_candidate(self, structuration_data):
        '''
        获取候选项
        :param structuration_data: 结构化后的字典列表
        :return: 待匹配的候选项，和候选高亮的位置
        '''
        match_candidate = []
        highlight_candidate = []
        if structuration_data:
            for dict_str in structuration_data:
                entity_name = dict_str.get('name')
                position_entity = dict_str.get('position')
                property_ner = dict_str.get('property')
                if property_ner:
                    for pro_dict in property_ner:
                        pro_text = pro_dict.get('text')
                        pro_position = pro_dict.get('position')
                        entity_char = entity_name + '&' + pro_text
                        match_candidate.append(entity_char)
                        entity_char_posi = [position_entity, pro_position]
                        highlight_candidate.append(entity_char_posi)
                else:
                    match_candidate.append(entity_name)
                    highlight_candidate.append([position_entity])

        return match_candidate, highlight_candidate

    def _get_highlight_list(self, input_match_cond, basis_match_cond, basis_high_cond):
        '''
        获取匹配的高亮项和位置
        :param input_match_cond: 输入文本的候选项
        :param basis_match_cond: 诊断依据的候选文本
        :param basis_high_cond: 诊断依据的候选位置列表[[[1,4],[45]],[[12,15],[15,18]]]
        :return: 匹配的高亮文本和位置
        '''
        highlight_word = []
        highlight_position = []

        if basis_match_cond:
            words_input = [x.split('&')[0] for x in input_match_cond]
            words_basis = [x.split('&')[0] for x in basis_match_cond]
            posi_basis = [[x[0]] for x in basis_high_cond]

            input_match_cond.extend(words_input)
            basis_match_cond.extend(words_basis)
            basis_high_cond.extend(posi_basis)

            for index, basis_candidate in enumerate(basis_match_cond):
                if basis_candidate in input_match_cond:
                    highlight_word.append(basis_candidate)
                    highlight_position.append(basis_high_cond[index])


        return highlight_word, highlight_position

    def _get_highlight(self, highlight_position_list):
        new_list = []
        if highlight_position_list:
            for high_posi in highlight_position_list:
                for hp in high_posi:
                    new_list.append(hp)
        new_list.sort()
        # 去重
        highlight_position = []
        for lis in new_list:
            if lis not in highlight_position:
                highlight_position.append(lis)
        # list.sort(cmp=None, key=None, reverse=False)
        # print(highlight_position)
        return highlight_position


class ClinicalGuideDisease(ClinicalGuide):

    def __init__(self):
        super(ClinicalGuideDisease, self).__init__()
        self.ai_base = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService') #, port=6448)

    def get_disease_guide(self, content_input, disease_list, word_print):
        '''
        获取临床指南中的高亮文本和位置
        :param content_input:用户输入文本(string)
        :param disease_list: 预测疾病(string)（disease1, disease2, disease3）
        :param word_print: 打开word开关
        :return: 临床指南的结果
        '''
        content_obtain = self.ai_base.query({'disease': disease_list}, service='knowledge_base')
        content_data = content_obtain.get('data')
        content_higtlight_data = []
        if content_data:
            for data_list in content_data:
                content_basis = data_list.get('diagnosis_basis')
                if content_basis:
                    highlight_words, highlight_position = self.get_highlight_basis(content_input, content_basis)
                    if word_print == '1':
                        data_list['highlight_words'] = highlight_words
                        # print(data_list)
                    data_list['diagnosis_basis_highlight'] = highlight_position

                    content_higtlight_data.append(data_list)
                else:
                    content_higtlight_data.append(data_list)

        return content_higtlight_data


if __name__ == '__main__':

    content_input = '因头晕、头痛、犯困三天入院。高血压三年'
    content_basis = '头痛，头晕，持续时间久。有高血压'
    model = ClinicalGuide()
    result = model.get_highlight_basis(content_input, content_basis)
    print(result)
    # content_input = {'chief_complaint':'皮肤紫癜，可伴腹痛、关节肿痛及血尿',
    #                  'medical_history': '放射性疼痛，僵直，畸形, 局部压痛或叩击痛'}
    content_input = '皮肤紫癜，可伴腹痛、关节肿痛及血尿，放射性疼痛，僵直，畸形, 局部压痛或叩击痛,骨关节结核'
    disease =  '慢性支气管炎,骨关节结核,腹型过敏性紫癜'
    model = ClinicalGuideDisease()
    result = model.get_disease_guide(content_input, disease, word_print=True)
    print(result)
