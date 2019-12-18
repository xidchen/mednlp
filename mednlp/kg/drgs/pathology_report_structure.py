#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from mednlp.kg.segment_words import words_segment
from mednlp.kg.structure_property import Property
from mednlp.kg.structure_new import SplitSentence, dict_entity, uuid_model


class PropertyAdd(Property):

        def __init__(self, candidate_words, content):
            super(PropertyAdd, self).__init__(candidate_words, content)

        # 组织学分型
        def get_histology_classification(self):
            patt = '(小细胞肺癌|小细胞癌|非小细胞肺癌|腺癌|鳞癌|大细胞癌|鳞状细胞癌|浸润前病变)'
            property_type = 'histology_classification'
            histology_result = self.get_entity_property(patt, property_type)
            return histology_result

        # 分化程度
        def get_cancer_differentiation(self):
            """实体 分化程度"""
            differentiated_degree_result = []
            for k in self.candidate_words:
                if k[1] == 'dd':
                    post = re.search((k[2]), self.content).span()
                    differentiation = {'text': k[2], 'type': 'cancer_differentiation',
                                       'value': k[2], 'position': post}
                    differentiated_degree_result.append(differentiation)
            return differentiated_degree_result

        # 侵及状态
        def get_invasion_status(self):
            patt = '(侵及|侵犯|累及|浸润)'
            property_type = 'invasion_status'
            invasion_result = self.get_entity_property(patt, property_type)
            return invasion_result

        # 部位分开、所在部位、侵及部位、转移部位
        def get_body_part_type(self):
            body_part_result = []
            body_part_candidate = ''.join([x[2] for x in self.candidate_words])
            patt1 = '(?:侵及|侵犯|累及|浸润)'
            patt2 = '远处转移'
            for k in self.candidate_words:
                if k[1] == 'nb':
                    if re.search(patt1, body_part_candidate):
                        type_value = 'invasion_body_part'
                    elif re.search(patt2, body_part_candidate):
                        type_value = 'transfer_body_part'
                    else:
                        type_value = 'body_part'
                    position_ls = [x.span() for x in re.finditer((k[2]), self.content)]
                    for position in position_ls:
                        body_part = {'text': k[2], 'type': type_value,
                                     'value': k[2], 'position': position}
                        body_part_result.append(body_part)
            return body_part_result

        def get_orientation(self, entity):
            orientation_result = []
            if entity == '淋巴结转移':
                patt = '(同侧|对侧)'
                property_type = 'orientation'
                orientation_result = self.get_entity_property(patt, property_type)
            return orientation_result


        def get_entity_property(self, patt, property_type):
            list_result = []
            candidate_sentence = ''.join([x[2] for x in self.candidate_words])
            match_patt = re.finditer(patt, candidate_sentence)  # 在句子中的位置
            if match_patt:
                for mp in match_patt:
                    mp_value = mp.group()
                    mp_position = list(mp.span())
                    mp_dict = {'text': mp_value, 'type': property_type,
                               'value': mp_value, 'position': mp_position}
                    list_result.append(mp_dict)
            return list_result

        def get_tumour_size(self):
            patt = '\d{0,}\.?\d{0,}[cdm]?m?\*?\d{0,}\.?\d{1,}[cdm]m'
            property_type = 'size'
            size_result = self.get_entity_property(patt, property_type)
            return size_result


class PathologyStructure(PropertyAdd):

    def __init__(self, candidate_words, content):
        super(PathologyStructure, self).__init__(candidate_words, content)

    def pathological_entity_property(self, pos, entity):
        char_dict = {}
        if pos == 'ns':
            char_dict['body_result'] = self.get_body_part_type()
            char_dict['invasion_status_result'] = self.get_invasion_status()
            char_dict['size _result'] = self.get_tumour_size()
            char_dict['orientation_result'] = self.get_orientation(entity)
            _, char_dict['status_result'] = self.entity_flag_status(entity)
        elif pos == 'nd':
            char_dict['body_result'] = self.get_body_part_type()
            char_dict['histology_classification'] = self.get_histology_classification()
            char_dict['cancer_differentiation'] = self.get_cancer_differentiation()

        return char_dict


class EntityCharRelation(SplitSentence):

    def __init__(self):
        super(EntityCharRelation, self).__init__()

    def entity_dict(self, segment_sen, sentence, pos, sen_position):
        """
        segment_sen: 分词后的句子
        sentence: 原始没做变化的句子
        pos: 词性，实体或者属性的类（这里指实体的类）
        sen_position: 句子的位置，为了准确计算句子中词的位置。
        """
        entity_type = dict_entity[pos]

        entity_dict_list = []
        index_entity = [index for index, x in enumerate(segment_sen) if x[1] == pos]
        entity = [(x[0]) for index, x in enumerate(segment_sen)]
        if index_entity:
            sen_re = sentence
            for index in index_entity:
                property_original = []
                entity_name = entity[index]
                candidate_words = [[j, segment_sen[j][1], segment_sen[j][0]]
                                   for j in range(0, len(segment_sen))]

                ## 如果属性存在在添加进属性列表
                char_dict = PathologyStructure(
                    candidate_words, sentence).pathological_entity_property(
                    pos, entity_name)
                for char_result in list(char_dict.keys()):
                    if char_dict.get(char_result):
                        property_original.extend(char_dict.get(char_result))

                word_position = [0, 0]
                if sen_re:
                    word_match = re.search(re.escape(entity[index]), sen_re)
                    if word_match:
                        word_position = word_match.span()
                        # 避免有重复的实体
                        sen_re = (sen_re[:word_position[0]]
                                  + '#' * len(entity[index])
                                  + sen_re[word_position[1]:])

                entity_dict = dict()
                entity_dict['text'] = entity[index]
                entity_dict['type'] = entity_type
                entity_dict['name'] = entity[index]
                entity_dict['uuid'] = uuid_model.obtain_uuid(entity[index])
                if sen_position:
                    # 由于python显示的列表中，前闭后开，##不需要了 -----因此为了实际距离，后面-1
                    position = [sen_position[0] + word_position[0],
                                sen_position[0] + word_position[1]]
                    property_list = []
                    for prop in property_original:
                        if 'position' in prop and len(prop['position']) > 0:
                            prop['position'] = [prop['position'][0] + sen_position[0],
                                                prop['position'][1] + sen_position[0]]
                            property_list.append(prop)
                        else:
                            property_list.append(prop)
                else:
                    position = []
                    property_list = property_original
                entity_dict['position'] = position
                property_list = sorted(property_list, key=lambda x: x['position'])
                entity_dict['property'] = property_list
                entity_dict_list.append(entity_dict)
        return entity_dict_list

    # 结构化框架
    def structured_result(self, sentence, _, pos_list):
        """
        sentence: 字符串
        pos_list: 词性列表，需要对那些类实体进行结构化，就在列表中填入实体对应的词性。
        """
        result = []
        sen_list = self.sentence_tran_comma(sentence)
        for sen in sen_list:
            sen_position_list = [x.span() for x in
                                 re.finditer(re.escape(sen), sentence)]
            sen_position = sen_position_list[0] if sen_position_list else []
            segment_sentence = words_segment(sen)

            for pos in pos_list:
                entity_dict_list = self.entity_dict(
                    segment_sentence, sen, pos, sen_position)
                result.extend(entity_dict_list)

        result = sorted(result, key=lambda x: x['position'])
        return result


if __name__ == '__main__':
    sentence1 = """盆腔内未见明显肿大淋巴结."""
    model = EntityCharRelation()
    res = model.structured_result(sentence1, 'pathology_report', ['ns', 'nd'])
    print(res)
