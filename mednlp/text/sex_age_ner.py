#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import jieba


class AgeSexTrans(object):

    CN_NUM = {
        '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0,
        '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2,
    }

    CN_UNIT = {
        '十': 10, '拾': 10, '百': 100, '佰': 100, '千': 1000, '仟': 1000, '万': 10000,
        '萬': 10000, '亿': 100000000, '億': 100000000, '兆': 1000000000000,
        }

    age_range = {
        '小儿':[0, 3],
        '儿童':[3, 8],
        '少年':[8, 16],
        '青年': [16, 30],
        '壮年':[30, 45],
        '中年':[45, 60],
        '老年':[60, 120],
        '成年':[18, 60]
    }

    def __init__(self):
        super(AgeSexTrans,self).__init__()

    def chinese_to_arabic(self, cn):
        '''
        将中文数字转化为阿拉伯数字
        :param cn:
        :return:
        '''
        unit = 0  # current
        ldig = []  # digest
        for cndig in reversed(cn):
            if cndig in self.CN_UNIT:
                unit = self.CN_UNIT.get(cndig)
                if unit == 10000 or unit == 100000000:
                    ldig.append(unit)
                    unit = 1
            else:
                dig = self.CN_NUM.get(cndig)
                if unit:
                    dig *= unit
                    unit = 0
                ldig.append(dig)
        if unit == 10:
            ldig.append(10)
        val, tmp = 0, 0
        for x in reversed(ldig):
            if x == 10000 or x == 100000000:
                val += tmp * x
                tmp = 0
            else:
                tmp += x
        val += tmp
        return val

    def obtain_sex(self, sentence):
        sex_list = []
        if sentence:
            # 性别：男
            patt1 = '性别.{0,2}[男女]'
            # 男女+特定字
            patt2 = '[男女][性孩人童娃子的]'

            pattern = [patt1, patt2]
            for patt in pattern:
                if re.findall(patt, sentence):
                    # print(re.findall(patt, sentence))
                    sex_match = re.finditer(patt, sentence)
                    for words in sex_match:
                        dict = {}
                        word = words.group()
                        position = words.span()
                        if patt == patt1:
                            sex_word = word[-1]
                            sex_pt = [position[-1]-1, position[-1]]
                        else:
                            sex_word = word
                            sex_pt = list(position)
                        dict['name'] = sex_word
                        dict['position'] = sex_pt
                        if re.findall('男', sex_word):
                            dict['sex'] = '男'
                        else:
                            dict['sex'] = '女'
                        sex_list.append(dict)
        return sex_list


    def obtain_age(self, sentence, ner=True):
        age_list = []
        patt0 = '年龄.{0,2}\d{1,2}[\s|，|，|。]'
        patt1 = '年龄.{0,2}\d{1,3}个?[天月周]'
        patt2 = '[\d一二三四五六七八九十几百零]{1,5}周?岁'
        patt3 = '(中年|老年|青年|儿童|婴儿|婴幼儿|幼儿|少年|宝宝|小儿|中老年|青壮年|壮年|女童|\
                男童|小孩|老男人|老女人|男孩|女孩|女娃|小娃娃|成人|成年|男生|女生)'
        if ner:
            pattern = [patt0, patt1, patt2]
        else:
            pattern = [patt0, patt1, patt2, patt3]
        for patt in pattern:
            if re.findall(patt, sentence):
                # print(re.findall(patt, sentence))
                age_match = re.finditer(patt, sentence)
                for words in age_match:
                    dict = {}
                    word = words.group()
                    position = words.span()
                    if patt == patt0:
                        num_age = re.search('\d+', word)
                        age_word = num_age.group()
                        age_pt = [x+position[0] for x in num_age.span()]
                        dict['age'] = age_word
                        dict['position'] = age_pt
                    elif patt == patt1:
                        if not re.findall(patt1+'岁', sentence):
                            num_age = re.search('\d.*', word)
                            age_word = num_age.group()
                            age_type = self.age_range.get('小儿')
                            age_pt = [x+position[0] for x in num_age.span()]
                            dict['age'] = age_word
                            dict['type'] = age_type
                            dict['position'] = age_pt
                    else:
                        age_word = word
                        age_pt = list(position)
                        if re.findall('周?岁', sentence):
                            new_word = re.sub('[周岁]', '', age_word)
                        #     if re.findall('\D', new_word): #15岁
                        #         new_word = self.chinese_to_arabic(new_word)
                        # dict['name'] = age_word
                            dict['age'] = new_word
                            dict['position'] = age_pt
                    if dict:
                        age_list.append(dict)
        return age_list

    def age_section(self, ageword):
        if re.findall('壮', ageword):
            agerange = self.age_range.get('壮年')
        elif re.findall('老', ageword):
            agerange = self.age_range.get('老年')
        elif re.findall('[婴宝]', ageword):
            agerange = self.age_range.get('小儿')
        elif re.findall('[小幼]儿', ageword):
            agerange = self.age_range.get('小儿')
        elif re.findall('[童娃孩]', ageword):
            agerange = self.age_range.get('儿童')
        elif re.findall('成|大人', ageword):
            agerange = self.age_range.get('成年')
        else:
            agerange = self.age_range.get(ageword, '')

        return ageword, agerange

if __name__ == '__main__':
    sentence = '性别：女，年龄：24 可惜是个女的，不然就可以,来个22岁男的,成人,年龄：12天大，一百零五岁，二十五周岁'
    model = AgeSexTrans()
    result1 = model.obtain_sex(sentence)
    result2 = model.obtain_age(sentence)
    print('result1',result1)
    print('result2:',result2)
    for i in ['老男人','小孩','婴幼儿','青壮年','青年','成人']:
        print('age_range', model.age_section(i))
