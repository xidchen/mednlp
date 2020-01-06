#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
structure.py -- the core function of structure_service.py
Author: chenxd
Create on 2018.07.25
"""

import re
from collections import OrderedDict
from mednlp.text.mmseg import MMSeg
from mednlp.utils.utils import Encode
from mednlp.kg.structure_mmseg import EntityExtract
from mednlp.kg.structure_property import Property
from mednlp.kg.structure_optimize import MedicalHistoryStructure


segment_model = EntityExtract()
history_model = MedicalHistoryStructure()
dict_entity = {
        'ns': 'symptom',
        'nd': 'disease',
        'nm': 'medicine',
        'tr': 'treatment',
        'np': 'physical',
        'ei': 'examination_item',
		'er': 'examination_result',
        'ii': 'inspection_item'
    }
list_entity = list(dict_entity.keys())


class SplitSentence(object):

    def __init__(self):
        super(SplitSentence, self).__init__()

    ## 按照实体切分后重新组合句子
    def sentence_tran_pos(self, sentence):
        """
        sentence：输入的句子
        """
        # sentence = str
        sen_ner = set(
            [s[0] for s in segment_model.result_seg(sentence)
             if s[1] in list(dict_entity)])
        patt = '|'.join(sen_ner)
        ## 按照实体切分,在重新合并句子
        sen_pos = [x.span()[1] for x in re.finditer(patt, sentence)]
        # ner_sen = [x.group() for x in re.finditer(patt, sentence)]
        ## 初次句子生成
        sen_now = []
        for i in range(len(sen_pos)):
            if i == 0:
                sen_now.append(sentence[0:sen_pos[i]])
            else:
                sen_now.append(sentence[sen_pos[i - 1]:sen_pos[i]])
        sen_now.append(sentence[sen_pos[-1]:])
        ##句子转换
        ##按照实体切割后，重新组合句子
        new_sen_now = []

        for index, s in enumerate(sen_now):
            new_sen_now.append(s)
            s_sp = re.split('([，。])', s)
            for l_id, l_sen in enumerate(s_sp): # 每个句子都是以实体词结尾，因此切分后len(s_sp)必为奇数
                if l_sen and l_id % 2 == 0:
                        new_sen_now.append(l_sen + s_sp[l_id+1])
        ##有顿号和及的情况
        result_dh = []
        for ind, s in enumerate(new_sen_now):
            result_dh.append(s)
            if len(s) > 0:
                if re.findall('^[、|及]', s):
                    result_dh[ind - 1] += s
                    result_dh[ind] = ''
        result = []
        for s in result_dh:
            if len(s) > 0:
                result.append(s)

        return result

    ## 按照标点符号切分后重新组合句子
    def sentence_tran_comma(self, sentence):
        """
        sentence: 输入的句子
        逻辑: 按照，|。|；切分后的句子，如果下一个句子没有实体，则并入前面一个句子
        """
        sen_seg = segment_model.result_seg(sentence) ## 该步骤耗费了约1/2的时间

        pos_entity = [x[0] for x in sen_seg if x[1] in
                      list_entity + ['cr']]  ## 症状/疾病/检查/药物/治疗/体征/人
        patt = '|'.join(pos_entity)

        new_list = []
        pun_index = [i for i, w in enumerate(sen_seg) if w[0] in ['，', '。', '；', ',']]
        if not pun_index:
            new_list.append(sen_seg)
        for index, i  in enumerate(pun_index):
            if index == 0:
                new_list.append(sen_seg[0:i+1])
            else:
                pre_i = pun_index[index-1]
                new_list.append(sen_seg[pre_i+1:i+1])

        if pun_index and sen_seg[pun_index[-1]+1:]:
            new_list.append(sen_seg[pun_index[-1]+1:])
        new_sen_pos_list = []
        if new_list:
            for index, sen_pos in enumerate(new_list):
                words = ''.join([x[0] for x in sen_pos])
                if index == 0:
                    new_sen_pos_list.append(sen_pos)
                elif not re.findall(patt, words) and index > 0:
                    if not re.findall('[。；]', ''.join([x[0] for x in new_sen_pos_list[-1]])):
                        new_sen_pos_list[-1] += sen_pos
                    else:
                        new_sen_pos_list.append(sen_pos)
                else:
                    new_sen_pos_list.append(sen_pos)
        # print('重组后的句子', new_sen_pos_list)
        ## 有些第一个句子,语义未截断（没有句号和分号） 没有实体但里面有属性，因此添加到后面一个短句里面
        sen_pos_list_new = new_sen_pos_list
        if len(new_sen_pos_list) > 1:
            if not re.findall(patt + '|。|；', ''.join([x[0] for x in new_sen_pos_list[0]])):
                new_sen_pos_list[1] = (new_sen_pos_list[0]) + (new_sen_pos_list[1])
                sen_pos_list_new = new_sen_pos_list[1:]
        # print(sen_pos_list_new)
        return sen_pos_list_new

    def sentence_position(self, sentence):
        comma_find = re.finditer('[，。；,]', sentence)
        sen_split = re.split('[，。；,]', sentence)
        comma_num = [0]
        for comma_i in comma_find:
            position = comma_i.span()
            comma_num.extend(position)
        comma_num.append(len(sentence))
        assert len(sen_split) == len(comma_num)/2
        sen_split_position = [comma_num[2*x: 2*(x+1)] for x in range(len(sen_split))]
        new_sen_position = []
        for s_p in sen_split_position:
            if s_p[0] == s_p[1]:
                new_sen_position.append(s_p)
            else:
                new_sen_position.append([s_p[0], s_p[1]+1])
        return new_sen_position


class EntityProperty(Property):

    def __init__(self, candidate_words, content):
        super(EntityProperty, self).__init__(candidate_words, content)

    # @print_time
    def entity_property(self, pos, entity, index):
        char_dict = {'time_result': self.get_entity_time(),
                     'frequency_result': self.get_entity_frequency()}
        if pos == 'ns':
            char_dict['body_result'] = self.get_entity_body_part()
            char_dict['cause_result'] = self.get_entity_cause()
            char_dict['change_result_add'] = self.get_entity_exacerbation()
            char_dict['change_result_reduce'] = self.get_entity_alleviate()
            char_dict['nature_result'] = self.get_entity_nature()
            _, char_dict['status_result'] = self.entity_flag_status(entity[index])
            char_dict['size_result'] = self.get_entity_size(pos)
            char_dict['num_result'] = self.get_entity_num()
            char_dict['degree_result'] = self.get_entity_degree()
            char_dict['smell_result'] = self.get_entity_smell()
            char_dict['color_result'] = self.get_entity_color()
        elif pos == 'nd':
            char_dict['body_result'] = self.get_entity_body_part()
            char_dict['cause_result'] = self.get_entity_cause()
            char_dict['change_result_add'] = self.get_entity_exacerbation()
            char_dict['change_result_reduce'] = self.get_entity_alleviate()
            char_dict['nature_result'] = self.get_entity_nature()
            _, char_dict['status_result'] = self.entity_flag_status(entity[index])
            char_dict['period_result'] = self.get_entity_period()
            char_dict['immediate_family'] = self.get_entity_immediate_family()
        elif pos == 'ii':
            char_dict['size_result'] = self.get_entity_size(pos)
            char_dict['num_result'] = self.get_entity_num()
            if not(char_dict.get('size_result') and char_dict.get('num_result')):
                char_dict['value_result'] = self.get_entity_value(entity[index])
        elif pos in ['np', 'ei', 'er']:
            char_dict['body_result'] = self.get_entity_body_part()
            char_dict['size_result'] = self.get_entity_size(pos)
            char_dict['num_result'] = self.get_entity_num()
            _, char_dict['status_result'] = self.entity_flag_status(entity[index])
        elif pos == 'nm':
            char_dict['effect_result'] = self.get_entity_effect()
            char_dict['efficacy_result'] = self.get_entity_efficacy()
            char_dict['route_result'] = self.get_entity_route()
            char_dict['dosage_result'] = self.get_entity_dosage(entity[index])
        elif pos == 'tr':
            char_dict['effect_result'] = self.get_entity_effect()
            _, char_dict['status_result'] = self.entity_flag_status(entity[index])

        return char_dict


class EntityCharRelation(SplitSentence):

    def __init__(self):
        super(EntityCharRelation, self).__init__()
        self.body_extractor = MMSeg(
            ['body_part'], uuid_all=False, is_uuid=False, update_dict=False,
            is_all_word=False)  ## is_all_word=False(最大匹配)

    ## 受结巴自带字典的影响部分词分词后的词性仍按照结巴的，而不是添加的领域词典。目前发现无  有时会有这种情况
    def tran_pos_jieba(self, candidate_words):
        new_candidate_words = []
        for can_one in candidate_words:
            if can_one[2] == '无':
                can_one[1] = 've'
                new_candidate_words.append(can_one)
            elif can_one[2] in ['姐', '哥', '弟', '父', '母', '爸', '妈']:
                can_one[1] = 'cr'
                new_candidate_words.append(can_one)
            else:
                new_candidate_words.append(can_one)
        return new_candidate_words

    ## 不同实体的属性不同
    def structure_character(self, seg_sen, sen_original, pos, sen_position, is_entity_extract):
        """
        seg_sen: 分词后的句子
        sen_original: 原始没做变化的句子
        # sen: 经过处理的句子（特殊符号转义）
        pos: 词性，实体或者属性的类（这里指实体的类）
        sen_position: 句子的位置，为了准确计算句子中词的位置。
        """
        entity_type = dict_entity[pos]
        entity_dict_list = []
        index_entity = [index for index, x in enumerate(seg_sen) if x[1] == pos]
        entity = [(x[0]) for index, x in enumerate(seg_sen)]
        entity_id_list = [(x[-1]) for index, x in enumerate(seg_sen)]
        if index_entity:
            sen_re = sen_original
            for index in index_entity:
                property_list_original = []
                candidate_words = [[j, seg_sen[j][1], seg_sen[j][0]] for j in range(0, len(seg_sen))]
                candidate_words = self.tran_pos_jieba(candidate_words)

                ## 如果属性存在在添加进属性列表
                char_dict = EntityProperty(candidate_words, sen_original).entity_property(pos, entity, index)
                for char_result in list(char_dict.keys()):
                    if char_dict.get(char_result):
                        property_list_original.extend(char_dict.get(char_result))

                word_position = [0, 0]
                if sen_re:
                    word_match = re.search(re.escape(entity[index]), sen_re)
                    if word_match:
                        word_position = word_match.span()
                        # 避免有重复的实体
                        sen_re = (sen_re[:word_position[0]]
                                  + '#' * len(entity[index]) + sen_re[word_position[1]:])

                entity_dict = OrderedDict()
                # entity_dict['content'] = sen_original
                entity_dict['text'] = entity[index]
                entity_dict['type'] = entity_type
                entity_dict['name'] = entity[index]
                entity_dict['uuid'] = entity_id_list[index]
                if sen_position:
                    ## 由于python显示的列表中，前闭后开，###不需要了 -----因此为了实际距离，后面-1
                    position = [sen_position[0] + word_position[0], sen_position[0] + word_position[1]]
                    property_list = []
                    for prop in property_list_original:
                        if 'position' in prop and len(prop['position']) > 0:
                            prop['position'] = [prop['position'][0] + sen_position[0],
                                                prop['position'][1] + sen_position[0]]
                            property_list.append(prop)
                        else:
                            property_list.append(prop)
                else:
                    position = []
                    property_list = property_list_original

                entity_dict['position'] = position
                property_list = self._extract_nature(pos, property_list, sen_original, sen_position)
                ## 只有 症状、疾病需要对实体提取部位 ## 先不提取 np 体征中的部位
                if is_entity_extract:
                    property_list = self._extract_body_part(
                        pos, index, entity, property_list, sen_original, sen_position, position)

                property_list = sorted(property_list, key=lambda x: x['position'])
                entity_dict['property'] = self._body_part_remove(property_list)
                entity_dict_list.append(entity_dict)
        return entity_dict_list

    def _extract_nature(self, pos, property_list, sen_original, sen_position):
        ## 疾病和症状实体中 提取 常见的性质
        if pos in ['ns', 'nd']:
            patt1 = ('(?:发作|急|亚急|慢|萎缩|刺激|原发|继发|室上|粥样硬化|老年退行|'
                     '再生障碍|社区获得|腔隙|恶|药物|顽固|干|湿|精神|大叶|痉挛|迁移|良|'
                     '分泌|先天|间质|病毒|浅表|异物|开放|酒精|放射|应激|真菌|缺血|特发|'
                     '进行|特异|风湿|后天|溶血|刀割|针刺)[性样]')
            patt2 = '(?:持续|间歇|多发|间断|阵发|反复|一过)性'
            if re.findall(patt1, sen_original):
                nature_list = re.findall(patt1, sen_original)
                for nature_match in nature_list:
                    nature_position = re.search(nature_match, sen_original).span()
                    position_na = [sen_position[0] + nature_position[0],
                                   sen_position[0] + nature_position[1]]
                    body_part = {'text': nature_match, 'type': 'nature',
                                 'value': nature_match, 'position': position_na}
                    property_list.append(body_part)
            if re.search(patt2, sen_original):
                frequency_match = re.search(patt2, sen_original)
                frequency_value = frequency_match.group()
                frequency_position = frequency_match.span()
                position_freq = [sen_position[0] + frequency_position[0],
                                 sen_position[0] + frequency_position[1]]
                body_part = {'text': frequency_value, 'type': 'frequency',
                             'value': frequency_value, 'position': position_freq}
                property_list.append(body_part)
        return property_list

    def _extract_body_part(self, pos, index, entity, property_list, sen_original, sen_position, position):
        if pos in ['ns', 'nd'] and entity[index] not in ['恶心']:
            entities = self.body_extractor.cut((entity[index]))
            for k, v in entities.items():
                patt = ('[左右上下前后双单顶底内外两深浅]{1,3}[侧边区]?'
                        + k + '[左右上下前后双单顶底内外两]?[侧边部区处缘]?')
                if re.search(patt, sen_original) and not re.findall(('[早晚]上' + k), sen_original):
                    value = re.search(patt, sen_original).group()
                    position_value = re.search(patt, sen_original).span()
                    if sen_position:
                        position_value = [sen_position[0] + position_value[0],
                                          sen_position[0] + position_value[1]]
                        body_part = {'text': value, 'type': 'body_part',
                                     'value': value, 'position': position_value}
                        property_list.append(body_part)
                else:
                    position_list = [x.span() for x in re.finditer(k, entity[index])]
                    for position_1 in position_list:
                        position_2 = [position[0] + position_1[0], position[0] + position_1[1]]
                        body_part = {'text': k, 'type': 'body_part',
                                     'value': k, 'position': position_2}
                        property_list.append(body_part)
        return property_list

    def _body_part_remove(self, property_list):
        property_list_new = []
        if property_list:
            for prop_dict in property_list:
                if (prop_dict not in property_list_new
                        and prop_dict['text'] not in
                        ['血', '尿', '便', '皮', '肌']):  ## 去除不是部位的词
                    property_list_new.append(prop_dict)

            property_list_new = sorted(
                property_list_new, key=lambda x: x['position'], reverse=False)

            for index, prop_dict in enumerate(property_list_new):
                if index > 0:
                    ## 去掉腰骶部 和 腰 、腰骶、骶部 的重叠，只保留 最大匹配 腰骶部
                    if (prop_dict['position'][0] == property_list_new[index - 1]['position'][0]
                            and prop_dict['position'][1] >= property_list_new[index - 1]['position'][1]):
                        property_list_new.pop(index - 1)
                    elif ((prop_dict['position'][0] > property_list_new[index - 1]['position'][0])
                          and (prop_dict['position'][1] <= property_list_new[index - 1]['position'][1])):
                        property_list_new.pop(index)
        return property_list_new


class StructuredModel(EntityCharRelation):

    def __init__(self):
        super(StructuredModel, self).__init__()

    ### 在实体和属性匹配中，选择属性距离实体最近的，最为准确的属性
    def entity_nearest_property(self, entity_dict_list):
        if entity_dict_list:
            property_list = []
            for entity_dict in entity_dict_list:
                property_list.extend(entity_dict['property'])
            character_statistics = {}
            for prop in property_list:
                prop = str(prop)
                if character_statistics.get(prop):
                    character_statistics[prop] += 1
                else:
                    character_statistics[prop] = 1
            need_drop_property = []
            for char_key in character_statistics:
                if (character_statistics[char_key] > 1 and eval(char_key)
                ['type'] in ['nature', 'color', 'size', 'num', 'period']):
                    need_drop_property.append(eval(char_key))
            drop_property_list = []
            for ndp in need_drop_property:
                try:
                    candidate_entity = [x['position'][0] for x
                                        in entity_dict_list if ndp in x['property']]
                    ndp_position = ndp['position'][-1]
                    relative_position = [abs(ndp_position - x) for x in candidate_entity]
                    min_relative_position = relative_position.index(min(relative_position))
                    drop_property = [[x['text'], x['position'], ndp]
                                     for x in entity_dict_list if ndp in x['property']]
                    drop_property.pop(min_relative_position)  ## 移除距离最近的
                    drop_property_list.extend(drop_property)
                except (RuntimeError or ValueError):
                    continue

            if drop_property_list:
                for drop_property in drop_property_list:
                    for entity_dict in entity_dict_list:
                        if (entity_dict['text'] == drop_property[0]
                                and entity_dict['position'] == drop_property[1]):
                            entity_dict_property = entity_dict['property']
                            entity_dict_property.remove(drop_property[2])  ## 去除属性中 距离实体较远的错误匹配
        return entity_dict_list

    ## 在体征文本中，症状转为体征
    def content_type_optimize(self, result_list):
        new_result_list = []
        if result_list:
            for result in result_list:
                word_type = result.get('type')
                if word_type == 'symptom':
                    result['type'] = 'physical'
                    new_result_list.append(result)
                else:
                    new_result_list.append(result)
        else:
            new_result_list = result_list
        return new_result_list

    ## 结构化框架
    def structured_method(self, sentence, content_type, pos_list, is_entity_extract=True):
        """
        sentence: 字符串
        pos_list: 词性列表，需要对那些类实体进行结构化，就在列表中填入实体对应的词性。
        """
        section_result = []
        tran_comma_result = self.sentence_tran_comma(sentence)
        for seg_sen in tran_comma_result:
            sen_original = ''.join([x[0] for x in seg_sen])
            sen = re.escape(sen_original)
            sen_position_list = [x.span() for x in re.finditer(sen, sentence)]
            sen_position = []
            if sen_position_list:
                sen_position = sen_position_list[0]

            for pos in pos_list:
                entity_dict_list = self.structure_character(
                    seg_sen, sen_original, pos, sen_position, is_entity_extract)
                entity_dict_list = self.entity_nearest_property(entity_dict_list)
                section_result.extend(entity_dict_list)

            sentence_match = re.search(sen, sentence)
            if sentence:
                sen_position = sentence_match.span()
                # 避免有重复的句子
                sentence = (sentence[:sen_position[0]]
                            + '#' * len(sentence_match.group())
                            + sentence[sen_position[1]:])
        if content_type == 'physical_examination':
            section_result = self.content_type_optimize(section_result)
        section_result = sorted(section_result, key=lambda x: x['position'])
        return section_result


if __name__ == '__main__':
    sentence0 = """抗P-ANCA抗体弱阳性"""
    sentence1 = """遂再次分别于2016年10月30日、11月25日、12月16日、2017年1月、2017年2月
    入住我科给予TAC（多西他赛+多柔比星+环磷酰胺）联合化疗6周期"""
    sentence2 = """心前区疼痛，鼻活组织检查，鼻骨CT平扫，肺中叶钙化灶"""
    model1 = StructuredModel()
    sym_doc_tree0 = model1.structured_method(sentence0, 'disease', list_entity)
    print('=======================================')
    print(Encode(sym_doc_tree0))
