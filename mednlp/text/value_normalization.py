#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import jieba
import global_conf
import jieba.posseg as psg


class ValueNormalization(object):

    char_dict = global_conf.symptom_char_dict
    # char_dict = global_conf.dict_path + 'char_dict2.dic'
    jieba.load_userdict(char_dict)

    inspection_dict = open(global_conf.inspection_dict, 'r', encoding='utf-8')

    def __init__(self):
        super(ValueNormalization, self).__init__()
        self.valuedict = json.load(self.inspection_dict)
        jieba.initialize()

    def get_temperature(self, sentence):
        '''
        提取温度值
        :return: 温度和标准化文本描述
        '''
        temp_dict = {}
        patt_wd = u'\d{1,}\.?\d{1,}(摄氏度|度|℃)'
        if re.search(patt_wd, sentence):
            size_patt = re.search(patt_wd, sentence)
            size_text = size_patt.group()
            loc = list(size_patt.span())
            property_res = self.temperature_norm(size_text)
            temp_dict = {'entity_name': size_text, 'type': 'value', 'type_all': ['value'] , 'loc': loc}
            if property_res:
                temp_dict['property'] = property_res
        else:
            pass
        return temp_dict

    def get_word(self, sentence):
        word_dict = {}
        patt_wd = '阴性|阳性'
        if re.search(patt_wd, sentence):
            size_patt = re.search(patt_wd, sentence)
            size_text = size_patt.group()
            loc = list(size_patt.span())
            word_dict = {'entity_name': size_text, 'type': 'value', 'type_all': ['value'], 'loc': loc}
        return word_dict

    def get_value(self, preword, sentence):
        '''
        提取除了温度以外其他体征和检查检验的值,数值+单位模式
        :param preword: 前一个待取值的实体
        :return: 值和属性
        '''
        value_dict = {}
        candadite_words = [[x.word, x.flag] for x in psg.cut(sentence, HMM=True)]
        # print(candadite_words)
        for index1, k in enumerate(candadite_words):
            if k[0] in ['g','次', '个']:
                k[1] = 'niu'
            if k[1] in ['niu']:
                ## 由于单位中存在特殊符号/ 导致字典中词不能导入的结巴中，在此处，直接用规则匹配
                if index1 < len(candadite_words) - 2 and candadite_words[index1 + 2][1] == 'niu' and \
                        candadite_words[index1 + 1][0] in ['/', '*']:
                    unit = k[0] + candadite_words[index1 + 1][0] + candadite_words[index1 + 2][0]
                    # print(unit)
                else:
                    unit = k[0]
                patt = '\d{0,}\.?\d{1,}' + unit

                value_match = re.search(patt, sentence)
                if value_match:
                    text = value_match.group()
                    values = text.replace(unit, '')
                    property_res = self._value_norm(values, preword)
                    loc = list(value_match.span())
                    value_dict = {'entity_name': text, 'type': 'value', 'type_all': ['value'], 'loc': loc}
                    if property_res:
                        value_dict['property'] = property_res
                else:
                    pass
        return value_dict

    def get_value_num(self, preword, sentence):
        '''
        提取除了温度以外其他体征和检查检验的值，纯数值没有单位的
        :param preword: 前一个待取值的实体
        :return: 值和属性
        '''
        value_dict = {}
        # sentence = sentence[:8]
        # print(sentence)
        patt = '\d{1,}\.\d{1,}'

        value_match = re.search(patt, sentence)
        if value_match:
            values = value_match.group()
            # values = re.sub('[:：\s]', '', text)
            property_res = self._value_norm(values, preword)
            loc = list(value_match.span())
            value_dict = {'entity_name': values, 'type': 'value', 'type_all': ['value'], 'loc': loc}
            if property_res:
                value_dict['property'] = property_res
        else:
            pass
        return value_dict

    def temperature_norm(self, temperature):
        temp_value = re.sub(u'(摄氏度|度|℃)', '', temperature)
        property_tp = {}
        if temperature < '36':
            tem_ty = '低温'
        elif temperature <= '37':
            tem_ty = '正常'
        elif temperature <= '38':
            tem_ty = '低热'
        elif temperature <= '39':
            tem_ty = '中度发热'
        elif temperature <= '41':
            tem_ty = '高度发热'
        elif temperature > '41':
            tem_ty = '超高热'
        else:
            tem_ty = ''
        if tem_ty:
            property_tp['value'] = temp_value
            property_tp['value_status'] = tem_ty
        return property_tp

    def _value_norm(self, value, preword):
        value_range = self.valuedict.get(preword, '')
        values = float(value)
        property_tp = {}
        if value_range:
            if values < float(value_range[0]):
                type_value = '下降'
            elif values <= float(value_range[1]):
                type_value = '正常'
            elif values > float(value_range[1]):
                type_value = '上升'
            else:
                type_value = ''
            if type_value:
                property_tp['value'] = value
                property_tp['value_status'] = type_value
        return property_tp


class ValueNormalization2(ValueNormalization):

    def __init__(self):
        super(ValueNormalization2, self).__init__()

    def get_temperature_new(self, sentence):
        '''
        提取温度值
        :return: 温度和标准化文本描述
        '''
        temp_dict = {}
        patt_wd = '((体温|T|温度).{0,2}\d{1,}\.?\d{1,}(?:摄氏度|度|℃|°))'
        size_patt = re.search(patt_wd, sentence)
        if size_patt:
            size_text = size_patt.group()
            value_text = re.search(u'\d{1,}\.?\d{1,}(摄氏度|度|℃|°)', size_text).group()
            entity_text = re.search('(体温|T|温度)', size_text).group()
            loc = list(size_patt.span())
            property_res = self.temperature_norm(value_text)
            temp_dict = {'entity_text': size_text, 'entity_name':entity_text, 'type': 'physical',
                         'type_all': ['physical'] , 'loc': loc}
            if property_res:
                temp_dict['property'] = property_res
        else:
            pass
        return temp_dict

    def get_value_new(self, preword, prewordtype,sentence):
        '''
        提取除了温度以外其他体征和检查检验的值,数值+单位模式
        :param preword: 前一个待取值的实体
        :param prewordtype: 前一个待取值的实体的类型
        :return: 值和属性
        '''
        value_dict = {}
        candadite_words = [[x.word, x.flag] for x in psg.cut(sentence, HMM=True)]
        # print(candadite_words)
        for index1, k in enumerate(candadite_words):
            if k[0] in ['g','次', '个']:
                k[1] = 'niu'
            if k[1] in ['niu']:
                ## 由于单位中存在特殊符号/ 导致字典中词不能导入的结巴中，在此处，直接用规则匹配
                if index1 < len(candadite_words) - 2 and candadite_words[index1 + 2][1] == 'niu' and \
                        candadite_words[index1 + 1][0] in ['/', '*']:
                    unit = k[0] + candadite_words[index1 + 1][0] + candadite_words[index1 + 2][0]
                    # print(unit)
                else:
                    unit = k[0]
                patt = preword + '[:： ]?' +'\d{0,}\.?\d{1,}' + unit

                value_match = re.search(patt, sentence)
                if value_match:
                    text = value_match.group()
                    # values = text.replace(unit, '')
                    values = re.sub('[:：\s]', '', text.replace(preword, '').replace(unit, ''))
                    property_res = self._value_norm(values, preword)
                    loc = list(value_match.span())
                    value_dict = {'entity_text': text,'entity_name': preword, 'type': prewordtype,
                                  'type_all': [prewordtype], 'loc': loc}
                    if property_res:
                        value_dict['property'] = property_res
                else:
                    pass
        return value_dict

    def get_value_num_new(self, preword, prewordtype, sentence):
        '''
        提取除了温度以外其他体征和检查检验的值，纯数值没有单位的
        :param preword: 前一个待取值的实体
        :return: 值和属性
        '''
        value_dict = {}
        # sentence = sentence[:8]
        # print(sentence)
        patt = preword + '[:： ]?' + '\d{0,}\.?\d{1,}'

        value_match = re.search(patt, sentence)
        if value_match:
            text = value_match.group()
            values = re.sub('[:：\s]', '', text.replace(preword, ''))
            # values = re.sub('[:：\s]', '', text)
            property_res = self._value_norm(values, preword)
            loc = list(value_match.span())
            value_dict = {'entity_text': text, 'entity_name': preword, 'type': prewordtype,
                          'type_all': [prewordtype], 'loc': loc}
            if property_res:
                value_dict['property'] = property_res
        else:
            pass
        return value_dict


if __name__ == '__main__':
    # valuedict = {'高血压': ['80', '120'], '淋巴细胞':['0.2', '0.4']}
    sentence = '白细胞：37mol/l，红细胞 48，脉搏:72次/分,验血,温度39.5°,中性粒细胞百分比79'
    model = ValueNormalization2()
    a = model.get_temperature_new(sentence)
    b = model.get_value_new('白细胞', 'examination', sentence)
    d = model.get_value_num_new('红细胞', 'examination',sentence)
    print(a,'\n', d,'\n', b)
