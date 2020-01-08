#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
structure_mmseg.py
Author: chenxd
Create on 2019.07.01
"""

import re
import jieba
import string
import global_conf
from collections import OrderedDict
from mednlp.text.mmseg import MMSeg
from mednlp.text.entity_extract import EntityExtractBasic


type_trans = {
    'symptom_wy': 'ns',
    'disease': 'nd',
    'medicine': 'nm',
    'treatment': 'tr',
    'physical': 'np',
    'body_part': 'nb',
    'examination_item': 'ei',
    'examination_result': 'er',
    'inspection_item': 'ii'
}


# 里面是提炼出的时间正则模式
def time_re_pattern():

    # p1：绝对时间点
    p1_1 = '\d+年\d+月\d+日'
    p1_2 = '\d+年\d+月'
    p1_3 = '\d+月\d+日'
    p1_4 = '([1|2]\d{3}[\-\.\/])?\d{1,2}[\-\.\/]\d{1,2}'
    p1_5 = '[1|2]\d{3}[\-|\.|\/]((1{0,1}[012])|(0{0,1}[1-9]))'
    p1_6 = '([01][0-9]|2[0-3]):[0-5][0-9]'

    # p2:相对时间
    p2_1 = '昨天|今天|明天|昨日|今日|明日|上周|本周|这周|下周|上个星期|这个星期|下个星期|上月|本月|下月|上个月|这个月|下个月|去年|今年|明年'
    p2_2 = '现在|目前|早上|晚上'

    # p3:时间段
    p3_1 = '\d+[\-|\~\/]\d+[小时|时|日|天|周|星期|月|年]{1,2}'
    p3_2 = '近?第?前?[半|一|二|三|四|五|六|七|八|九|十|百|千|万|两]{1,2}余?[小时|时|日|天|周|月|年]{1,2}前?(余前)?余?后?(左右)?'
    p3_3 = '近?第?前?\d+个?余?多?[小时|日|天|周|星期|月|年]{1,2}前?(余前)?余?后?(左右)?期?'

    p_list = [p1_1, p1_2, p1_3, p1_4, p1_5, p1_6, p2_1, p2_2, p3_1, p3_2, p3_3]

    return p_list


# 这个函数是利用时间正则模式time_re_pattern提取文本中时间实体
def time_find(sentence):
    t_dict = {}
    for p in time_re_pattern():
        for t in re.compile(p).finditer(sentence):
            words = t.group()
            if t.span() in t_dict:
                t_dict[(t.span()[0] + 1, t.span()[1] + 1)] = t.group()
            else:
                t_dict[t.span()] = t.group()
            sentence = re.sub(words, 'Ю' * (len(t.group()) - 1) + 'Я', sentence, count=1)
    sentence = re.sub('Ю+Я', 'Ю', sentence)
    t_dict = sorted(t_dict.items(), key=lambda x: x[0], reverse=False)
    return t_dict, sentence


class EntityExtract(EntityExtractBasic):
    """
    医学实体抽取器（按照优先级）
    用于抽取文本中的医学实体以及ID
    """
    def __init__(self):
        super(EntityExtract, self).__init__()
        # 中英文标点
        en_punctuation = set(string.punctuation)
        cn_punctuation = {',', '?', '、', '。', '“', '”', '《', '》', '！',
                          '，', '：', '；', '？', '（', '）', '【', '】'}
        self.punctuation = en_punctuation | cn_punctuation
        # 默认辞典的优先级
        self.default_dict_order = ['symptom_wy', 'disease', 'body_part',
                                   'treatment', 'medicine', 'inspection_item',
                                   'examination_item', 'examination_result',
                                   'physical']
        # 初始化优先级，如果用户未指定，则使用默认优先级

        # 对于优先级中的每一个辞典，依次构造 extractor
        self.extractors = {}
        for dict_type in self.default_dict_order:
            extractor = MMSeg([dict_type], uuid_all=True, is_uuid=True,
                              update_dict=False, is_all_word=True)
            self.extractors[str(dict_type)] = extractor
        # 加载 jieba
        char_dict = global_conf.symptom_char_dict
        jieba.load_userdict(char_dict)
        jieba.initialize()
        self.char_word_dict = {}
        with open(char_dict, 'r', encoding='utf-8') as f:
            for lines in f:
                sp_line = re.split(' ', lines.strip('\n'))
                if sp_line:
                    self.char_word_dict[sp_line[0]] = sp_line[-1]

    def jieba_pos(self, sentence, medical_entities):
        """
        照句子顺序抽取实体
        Parameters:
            sentence-> 原句子
            filter_medical_entities-> 经过过滤以后的实体
            loc_on->是否开启loc字段，方便调试，默认为False
            verbose->是否打印详细信息, default=False
            返回值 -> seq_medical_entities() 按照语句顺序抽取的实体
        """
        order_medical_entities = OrderedDict(
            sorted(medical_entities.items(), key=lambda x: (x[1]['loc'][0])))

        order_keys = list(order_medical_entities.keys())
        current_sentence = sentence

        for key in order_keys:
            if order_medical_entities[key].get('entity_text'):
                e = order_medical_entities[key].get('entity_text')
            else:
                e = order_medical_entities[key]['entity_name']
            split_by_e = current_sentence.split(e, 1)
            if len(split_by_e) >= 2:
                unknown_word = split_by_e[0]
                current_sentence = split_by_e[1]
            else:
                unknown_word = ''
                current_sentence = split_by_e[0]

            if unknown_word == '':
                continue
            tokens = jieba.tokenize(unknown_word)
            for token in tokens:
                order_medical_entity = {
                    'entity_name': token[0],
                    'type': self.char_word_dict.get(token[0], 'normal')}
                if token[0] in self.punctuation:
                    order_medical_entity['type'] = 'punctuation'

                base = len(sentence) - len(current_sentence) - len(e) - len(unknown_word)
                beg_index = base + token[1]
                end_index = base + token[2] - 1
                order_medical_entity['loc'] = (beg_index, end_index)
                key = '{0}\t{1}\t{2}'.format(
                    str(order_medical_entity['entity_name']),
                    str(beg_index), str(end_index))
                order_medical_entities[key] = order_medical_entity

        # handle the last split exception
        if current_sentence != '':
            unknown_word = current_sentence
            tokens = jieba.tokenize(unknown_word)
            for token in tokens:
                order_medical_entity = {
                    'entity_name': token[0],
                    'type': self.char_word_dict.get(token[0], 'normal')}
                if token[0] in self.punctuation:
                    order_medical_entity['type'] = 'punctuation'

                base = len(sentence) - len(current_sentence)
                beg_index = base + token[1]
                end_index = base + token[2] - 1
                order_medical_entity['loc'] = (beg_index, end_index)
                key = '{0}\t{1}\t{2}'.format(
                    str(order_medical_entity['entity_name']),
                    str(beg_index), str(end_index))
                order_medical_entities[key] = order_medical_entity

        order_medical_entities = OrderedDict(
            sorted(order_medical_entities.items(),
                   key=lambda x: (x[1]['loc'][0])))
        seq_medical_entities = order_medical_entities

        return seq_medical_entities

    def add_time(self, seq_medical_entities, time_list):
        for word_flag in seq_medical_entities:
            if word_flag.get('entity_name') == 'Ю':
                word_flag['entity_name'] = time_list[0][1]
                word_flag['type'] = 'nt'
                time_list.pop(0)
        return seq_medical_entities

    def segment_word(self, seq_medical_entities):
        result_list = []
        for medical_dict in seq_medical_entities:
            entity_type = medical_dict.get('type')
            if type_trans.get(entity_type):
                entity_type = type_trans.get(entity_type)
            result_list.append([medical_dict.get('entity_name'),
                                entity_type, medical_dict.get('entity_id', '')])
        return result_list

    # @print_time
    def result_seg(self, sentence):
        time_dict, content = time_find(sentence)
        medical_entities = self.extract(content)
        medical_entities = self.filter(medical_entities)
        medical_entities = self.jieba_pos(content, medical_entities)
        res = self.dict_tran_list(medical_entities)
        res = self.add_time(res, time_dict)
        res = self.segment_word(res)
        return res


if __name__ == '__main__':
    sentence0 = """三天前的晚上腹痛。呕吐3次，约500ml咖啡色胃内溶物，
    腹痛运动后加重，休息后减轻。2018年7月18日查体：P:72次/分钟，BP:102/60mmHg，
    体温：37.5，神清语明，口唇无发绀，颈静脉无充盈，肝脾肋下未触及，双下肢无浮肿。"""
    split_model = EntityExtract()
    print(split_model.result_seg(sentence0))
