#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
structure_property.py -- the property of structure
Author : chenxd
Create on 2019.03.11
"""

import re


class Property(object):

    def __init__(self, candidate_words, content):
        super(Property, self).__init__()
        self.candidate_words = candidate_words
        self.content = content

    ## 实体状态
    def entity_flag_status(self, entity):
        """实体状态"""
        flag = 2
        status_result = []
        entity_index = 0
        sen = self.content
        for x in self.candidate_words:
            if x[2] == entity:
                entity_index = int(x[0])
            else:
                pass
        # min_index = max(0, entity_index-) ## 状态限定词一般出现在 症状前面。限定5个词以内
        status_sen_or = [l for l in self.candidate_words[0: entity_index]]
        for k in status_sen_or:
            if k[1] in ['ve']:
                value = re.sub('[但伴]', '', k[2])
                flag = 0
                position_ls = [x.span() for x in re.finditer(value, sen)]
                position = position_ls[0] if position_ls else []
                status = {'text': value, 'type': 'status', 'value': '无', 'position': position}
                status_result.append(status)
            elif k[1] in ['vp']:
                flag = 1
                position_ls = [x.span() for x in re.finditer((k[2]), sen)]
                position = position_ls[0] if position_ls else []
                status = {'text': k[2], 'type': 'status', 'value': '可能', 'position': position}
                status_result.append(status)
        return flag, status_result

    ## 时间划分
    def get_entity_time(self):
        """实体 时间"""
        time_result = []
        ### 指代性时间
        time_candidate = ''.join([x[2] for x in self.candidate_words])
        if re.findall('入院时|入院后|出院时|出院后|自幼|今晨|近日', time_candidate):
            time = re.findall('入院时|入院后|出院时|出院后|自幼|今晨|近日', time_candidate)[0]
            time_dict = {'text': time, 'type': 'time_happen', 'value': time}
            time_result.append(time_dict)
        for k in self.candidate_words:
            if k[1] == 'nt':
                patt = '[出入]院' + k[2]
                if re.findall(patt, time_candidate):
                    time = re.findall(patt, time_candidate)[0]
                    time_dict = {'text': time, 'type': 'time_happen', 'value': k[2]}
                    time_result.append(time_dict)
                else:
                    time = k[2]
                    if re.findall('^[\d]/[\d]{1, 2}$', time):
                        pass
                    elif re.findall('(周期|余$)', time):
                        time_dict = {'text': time, 'type': 'time_endurance', 'value': time}
                        time_result.append(time_dict)
                    elif re.findall('[昨前去今上][天日月年]', time):
                        time_dict = {'text': time, 'type': 'time_happen', 'value': time}
                        time_result.append(time_dict)
                    elif re.findall('[前今早晚]', time):
                        time_dict = {'text': time, 'type': 'time_happen', 'value': time}
                        time_result.append(time_dict)
                    else:
                        new_time = re.sub('[年月日周天时/.]', '-', time)
                        time_sp = re.split('-', new_time)
                        if len(time_sp) == 2:
                            if len(time_sp[1]) == 0:
                                try:
                                    if int(time_sp[0]) > 1900:
                                        time_dict = {'text': time, 'type': 'time_happen', 'value': time}
                                        time_result.append(time_dict)
                                    else:
                                        time_dict = {'text': time, 'type': 'time_endurance', 'value': time}
                                        time_result.append(time_dict)
                                except:
                                    time_dict = {'text': time, 'type': 'time_endurance', 'value': time}
                                    time_result.append(time_dict)
                            else:
                                if len(time_sp[0]) == 3:
                                    pass
                                else:
                                    time_dict = {'text': time, 'type': 'time_happen', 'value': time}
                                    time_result.append(time_dict)
                        elif len(time_sp) == 3:
                            if len(time_sp[0]) == 0:
                                pass
                            else:
                                time_dict = {'text': time, 'type': 'time_happen', 'value': time}
                                time_result.append(time_dict)
                        elif len(time_sp) == 4:
                            if len(time_sp[-1]) != 0:
                                pass
                            else:
                                time_dict = {'text': time, 'type': 'time_happen', 'value': time}
                                time_result.append(time_dict)
                        else:
                            pass

        if time_result:
            for time_dict in time_result:
                time_entity = time_dict['text']
                if re.findall('[\d]+(秒|分钟|分|小时|时|日|周|天|年|月)', time_entity):
                    num_value = re.findall('[\d]+', time_entity)[0]
                    unit_value = re.findall('(秒|分钟|分|小时|时|日|周|天|年|月)', time_entity)[0]
                    time_dict['value'] = num_value
                    time_dict['unit'] = unit_value
                position_ls = [x.span() for x in re.finditer(time_entity, self.content)]
                time_dict['position'] = position_ls[0] if position_ls else []
        else:
            pass
        return time_result

    ## 部位
    def get_entity_body_part(self):
        """实体  部位"""
        body_part_result = []
        body_part_candidate = ''.join([x[2] for x in self.candidate_words])
        for k in self.candidate_words:
            if k[1] == 'nb':
                pattern = ('[左右上下双单顶底内外两深浅]{0,3}[侧边部区]?'
                           + k[2] + '[左右上下前后双单顶底内外两]?[侧边部区处缘]?')
                if re.findall(pattern, body_part_candidate):
                    value = re.findall(pattern, body_part_candidate)[0]
                    position_ls = [x.span() for x in re.finditer(value, self.content)]
                    for position in position_ls:
                        body_part = {'text': value, 'type': 'body_part',
                                     'value': value, 'position': position}
                        body_part_result.append(body_part)
                else:
                    position_ls = [x.span() for x in re.finditer((k[2]), self.content)]
                    for position in position_ls:
                        body_part = {'text': k[2], 'type': 'body_part',
                                     'value': k[2], 'position': position}
                        body_part_result.append(body_part)

        return body_part_result

    ## 频率
    def get_entity_frequency(self):
        """实体  频率"""
        frequency_result = []
        for k in self.candidate_words:
            if k[1] == 'nps':
                frequency = {'text': k[2], 'type': 'frequency', 'value': k[2]}
                frequency_result.append(frequency)
        fre_candidate = ''.join([x[2] for x in self.candidate_words])

        patt_re1 = ('[\d一二三四五两六七八九十]{1,2}'
                    '(周|星期|日|天|月|个月|年|分钟|小时|个小时|秒)'
                    '[\d一二三四五两六七八九十]{1,2}[回次]')
        patt_re2 = '每?[日天晚]?\d{1,3}(-\d{1,3})?[次支](\/)?[天日周月分]?'
        patt_re3 = '[\d一二两三四五六七八九十]{1,3}[回次]'
        if re.search(patt_re1, fre_candidate):
            search_value = re.search(patt_re1, fre_candidate).group()
            frequency_result.append({'text': search_value,
                                     'type': 'frequency', 'value': search_value})
        elif re.search(patt_re2, fre_candidate):
            search_value = re.search(patt_re2, fre_candidate).group()
            frequency_result.append({'text': search_value,
                                     'type': 'frequency', 'value': search_value})
        elif re.search(patt_re3, fre_candidate):
            search_value = re.search(patt_re3, fre_candidate).group()
            frequency_result.append({'text': search_value,
                                     'type': 'frequency', 'value': search_value})
        else:
            pass
        if frequency_result:
            for frequency_dict in frequency_result:
                entity_frequency = frequency_dict['text']
                position = re.search(entity_frequency, self.content).span()
                frequency_dict['position'] = position
        else:
            pass
        return frequency_result

    ## 大小
    def get_entity_size(self, pos):
        """实体 大小"""
        size_result = []
        if pos == 'ne':
            type_name1, type_name2 = 'value', 'value'
        else:
            type_name1 = 'size'
            type_name2 = 'num'

        # size_candidate = ''.join([x[2] for x in self.candidate_words])

        patt_size = '(?:米粒|蚕豆|针尖|核桃|黄豆|绿豆|拇指|鸡蛋)[大小]{0,2}'
        if re.search(patt_size, self.content):
            size_patt = re.search(patt_size, self.content)
            size_value = size_patt.group()
            size_position = list(size_patt.span())
            size01 = {'text': size_value, 'type': type_name1,
                      'value': size_value, 'position': size_position}
            size_result.append(size01)

        patt_wd = '\d{1,}\.?\d{1,}(度|℃)'
        if re.search(patt_wd, self.content):
            size_patt = re.search(patt_wd, self.content)
            size_text = size_patt.group()
            size_value = re.sub('([度℃])', '', size_text)
            size_unit = re.sub('[\d.]', '', size_text)
            size_position = list(size_patt.span())
            size02 = {'text': size_text, 'type': type_name1, 'value': size_value,
                      'unit': size_unit, 'position': size_position}
            size_result.append(size02)

        for index1, k in enumerate(self.candidate_words):
            if k[2] == 'g':
                k[1]='ni'
            if k[1] in ['ni']:
                size_sen = ''.join([l[2] for l in self.candidate_words[:index1 + 1]])
                size_sen = size_sen.replace('\*', '*').replace('\+', '+').replace('\-', '-')
                ## 由于单位中存在特殊符号/ 导致字典中词不能导入的结巴中，在此处，直接用规则匹配
                if (index1 < len(self.candidate_words) - 2
                        and self.candidate_words[index1 + 2][1] == 'ni'
                        and self.candidate_words[index1 + 1][2] in ['/', '*']):
                    unit = (k[2] + self.candidate_words[index1 + 1][2]
                            + self.candidate_words[index1 + 2][2])
                    patt = '\d{0,}[\*\×\+\.\-\/\d]{0,}\d{1}' + unit
                    if re.search(patt, self.content):
                        match_patt = re.search(patt, self.content)
                        text0 = match_patt.group()
                        value0 = text0.replace(unit, '')
                        position0 = list(match_patt.span())
                        size = {'text': text0, 'type': type_name1,
                                'value': value0, 'unit': unit,
                                'position': position0}
                        size_result.append(size)
                    else:
                        pass

                else:
                    value = re.findall(
                        '\d*?[*×+.\-/]?\d*[*×+.\-/]?\d+' + k[2], self.content)
                    position = re.search(
                        '\d*?[*×+.\-/]?\d*[*×+.\-/]?\d+' + k[2], self.content)
                    if value:
                        size_candidate = value[0]  # + k[2]
                        val = value[0].replace(k[2], '')
                        position = list(position.span())
                        ## 如果单位为 容量和质量 则记为num，否则记为size属性
                        if k[2] in ['μl', 'ml', 'L', 'μg', 'mg', 'g', 'kg',
                                    '克', '毫克', '升', '毫升']:
                            size = {'text': size_candidate, 'type': type_name2,
                                    'value': val, 'unit': k[2], 'position': position}
                            size_result.append(size)
                        else:
                            size = {'text': size_candidate, 'type': type_name1,
                                    'value': val, 'unit': k[2], 'position': position}
                            size_result.append(size)
                    else:
                        pass
        return size_result

    ## 程度
    def get_entity_degree(self):
        """实体 程度"""
        degree_result = []
        for index1, k in enumerate(self.candidate_words):
            if k[1] in ['de']:
                degree = {'text': k[2], 'type': 'degree', 'value': k[2]}
                degree_result.append(degree)
        if degree_result:
            for entity_dict in degree_result:
                en_dict = entity_dict['text']
                position = re.search(en_dict, self.content).span()
                entity_dict['position'] = position
        else:
            pass
        return degree_result

    ## 数量
    def get_entity_num(self):
        """实体  数量"""
        num_result = []
        num = {}
        num_candidate = ''.join([x[2] for x in self.candidate_words])

        if re.search('\d+[个枚]', num_candidate):
            num['text'] = re.search('\d+[个枚]', num_candidate).group()
            num['value'] = re.sub('[个枚]', '', num['text'])
            num['unit'] = re.sub('\d+', '', num['text'])
        elif re.search('数[个|枚]', num_candidate):
            num['text'] = re.search('数[个枚]', num_candidate).group()
            num['value'] = num['text']
        elif re.search('([少大][量许])|(量[适不]?[少中多])', num_candidate):
            num['text'] = re.search('([少大][量许])|(量[适不]?[少中多])',
                                    num_candidate).group()
            num['value'] = num['text']
        if 'text' in num:
            num['type'] = 'num'
            num_result.append(num)
        if num_result:
            for num_dict in num_result:
                en_dict = num_dict['text']
                position = re.search(en_dict, self.content).span()
                num_dict['position'] = position
        else:
            pass

        return num_result

    ## 气味
    def get_entity_smell(self):
        """实体  气味"""
        smell_result = []
        for k in self.candidate_words:
            if k[1] == 'nsm':
                position = re.search((k[2]), self.content).span()
                smell = {'text': k[2], 'type': 'smell',
                         'value': k[2], 'position': position}
                smell_result.append(smell)
        return smell_result

    ## 颜色
    def get_entity_color(self):
        """实体  颜色"""
        color_result = []
        for k in self.candidate_words:
            if k[1] == 'nco':
                position = re.search((k[2]), self.content).span()
                color = {'text': k[2], 'type': 'color',
                         'value': k[2], 'position': position}
                color_result.append(color)
        return color_result

    ## 性质
    def get_entity_nature(self):
        """实体  性质"""
        nature_result = []
        for k in self.candidate_words:
            if k[1] in ['nnt', 'nrs', 'nbd']:
                position = re.search((k[2]), self.content).span()
                nature = {'text': k[2], 'type': 'nature',
                          'value': k[2], 'position': position}
                nature_result.append(nature)
        return nature_result

    ## 诱因
    def get_entity_cause(self):
        """实体  诱因 + 出现|发生|发现|见"""
        cause_result = []
        cause_candidate = ''.join([x[2] for x in self.candidate_words])

        for k in self.candidate_words:
            if k[1] == 'ncf':
                # if re.findall(k[2]+'(?:出现|发生|发现|见|下|开始出现)', (cause_candidate)):
                if re.findall(k[2], cause_candidate):
                    value = re.sub('[时后]$', '', k[2])
                    ## 备注这里只能去除最后的一个后和时，不能去除中间的，否则改变了原文的顺序，位置匹配会报错
                    position = re.search(value, self.content).span()
                    cause = {'text': value, 'type': 'cause',
                             'value': value, 'position': position}
                    cause_result.append(cause)
        return cause_result

    ## 加重
    def get_entity_exacerbation(self):
        """实体 诱因 + 转归  or 变差"""
        change_result = []
        change_candidate = ''.join([x[2] for x in self.candidate_words])
        change_pos = [x[1] for x in self.candidate_words]
        pos_have = True if 'nca' in change_pos else False

        for k in self.candidate_words:
            if pos_have:
                if k[1] == 'nca':
                    if re.findall(
                            '(?:加重|恶化|变差|变坏|扩散|再发|为甚|为著)',
                            change_candidate):
                        text = re.findall(
                            '(?:加重|恶化|变差|变坏|扩散|再发|为甚|为著)',
                            change_candidate)[0]
                        value = re.sub('[时后]', '', k[2])
                        position = re.search(text, self.content).span()
                        change = {'text': text, 'type': 'exacerbation',
                                  'value': value, 'position': position}
                        change_result.append(change)
        return change_result

    ## 减轻
    def get_entity_alleviate(self):
        """实体  诱因 + 转归  or 变好"""
        change_result = []
        change_candidate = ''.join([x[2] for x in self.candidate_words])

        change_pos = [x[1] for x in self.candidate_words]
        pos_have = True if 'ncd' in change_pos else False

        for k in self.candidate_words:
            if pos_have:
                if k[1] == 'ncd':
                    if re.findall(
                            '(?:减轻|缓解|改善|消散|消退|消失|变好|好转)',
                            change_candidate):
                        text = re.findall(
                            '(?:减轻|缓解|改善|消散|消退|消失|变好|好转)',
                            change_candidate)[0]
                        value = re.sub('[时后]', '', k[2])
                        position = re.search(text, self.content).span()
                        change = {'text': text, 'type': 'alleviate',
                                  'value': value, 'position': position}
                        change_result.append(change)
        return change_result

    ## 分型
    def get_entity_period(self):
        period_result = []
        period_sen = ''.join([l[2] for l in self.candidate_words])

        pattern1 = '([A-Za-z]型|([A-Za-z]{0,1}\d{1}[级型期])|([ⅠⅡⅢⅣⅤ][A-Za-z]{0,1}[\d]{0,1}[级期型]))'
        pattern2 = '(?:晚期|早期|极{0,1}很{0,1}高危|ST段抬高型|急性发作期|迁移期)'
        pattern_ls = [pattern1, pattern2]
        for pattern in pattern_ls:
            if re.findall(pattern, period_sen):
                value = re.search(pattern, period_sen).group()
                position = re.search(pattern, self.content)
                position = list(position.span())
                period = {'text': value, 'type': 'period',
                          'value': value, 'position': position}
                period_result.append(period)
            else:
                pass
        return period_result

    ## 药效
    def get_entity_efficacy(self):
        efficacy_result = []
        efficacy_sen = ''.join([l[2] for l in self.candidate_words])

        pattern = ('(抗菌|消炎|抗病毒|解热|抗感染|镇痛|止痛|降血压|降压|止泻|退烧|退热|'
                   '抗炎平喘|止血|消食|明目|安神|祛痰|止咳|补脾|益气|清肺|生津)')
        if re.findall(pattern, efficacy_sen):
            if not re.findall(pattern + '(颗粒|剂|药|胶囊)', efficacy_sen):
                value = re.findall(pattern, efficacy_sen)[0]
                position = re.search(pattern, self.content)
                position = list(position.span())
                efficacy = {'text': value, 'type': 'efficacy',
                            'value': value, 'position': position}
                efficacy_result.append(efficacy)
            else:
                pass
        else:
            pass
        return efficacy_result

    ## 给药方式
    def get_entity_route(self):
        route_result = []
        route_sen = "".join([l[2] for l in self.candidate_words])

        pattern = '(口服|注射|含服|皮下注射|静脉注射|涂抹|肌肉注射|肌注|穴位注射|直肠滴入|吸入|气雾剂吸入)'
        if re.findall(pattern, route_sen):
            value = re.findall(pattern, route_sen)[0]
            position = re.search(pattern, self.content)
            position = list(position.span())
            route = {'text': value, 'type': 'administration_route',
                     'value': value, 'position': position}
            route_result.append(route)
        else:
            pass
        return route_result

    ## 药物剂量
    def get_entity_dosage(self, entity):
        dosage_result = []
        dosage_sen = self._candidate_modify(entity)
        pattern1 = '[每|一|单]次\d{1,3}(ml|g|l|kg|μg|mg|ug|毫升|升|片|粒|微克|克|千克|毫克)'
        pattern2 = ('\d{1,3}(\.\d{1,3})?(ml|g|l|kg|μg|mg|ug|毫升|升|片|袋|粒|微克|克|千克|毫克)'
                   '(\/)?[次日天周月]?(\s+(q\d?d|bid|tid|qid|q\d?h|qn|qod|biw))?')
        if re.findall(pattern1, dosage_sen):
            value = re.search(pattern1, self.content).group()
            position = re.search(pattern1, self.content)
            position = list(position.span())
            dosage = {'text': value, 'type': 'dosage',
                      'value': value, 'position': position}
            dosage_result.append(dosage)
        elif re.findall(pattern2, dosage_sen):
            value = re.search(pattern2, self.content).group()
            position = re.search(pattern2, self.content)
            position = list(position.span())
            dosage = {'text': value, 'type': 'dosage',
                      'value': value, 'position': position}
            dosage_result.append(dosage)
        else:
            pass
        return dosage_result

    ## 治疗效果
    def get_entity_effect(self):
        effect_result = []
        effect_sen = ''.join([l[2] for l in self.candidate_words])

        pattern = ('(病情|症状)?(相对|较前)?[有无略]?'
                   '(成功|失败|稳定|顺利|加重|恶化|减轻|缓解|改善|消散|消退|好转|效果不佳)')
        if re.findall(pattern, effect_sen):
            value = re.search(pattern, self.content).group()
            position = re.search(pattern, self.content)
            position = list(position.span())
            effect = {'text': value, 'type': 'effect',
                      'value': value, 'position': position}
            effect_result.append(effect)
        else:
            pass
        return effect_result

    ## 检查值
    def get_entity_value(self, entity):
        value_sen_or = self._candidate_modify(entity)
        value_sen = re.split('[，。；,]', value_sen_or)[0]
        sen_tr = re.search(entity, self.content)
        if sen_tr:
            position_tr = sen_tr.span()[0]
        else:
            position_tr = 0
        value_result = self._add_value(position_tr, value_sen_or)
        patt_ex = '\d{1,}\.?\d{0,}\%'
        patt_va = '[：:].+?[，。；,）]'
        entity = '#' * len(entity)  ##避免实体中的值影响属性识别
        value_sen_or = entity + value_sen_or[len(entity):]
        patt_num = entity + '\s{0,5}\d{1,}\.?\d{0,}'
        patt_symbol = '[↑↓]'
        if re.search(patt_ex, value_sen):
            value_patt = re.search(patt_ex, value_sen)
            value_text = value_patt.group()
            value_position = [x + position_tr for x in list(value_patt.span())]
            value = {'text': value_text, 'type': 'value',
                     'value': value_text, 'position': value_position}
            value_result.append(value)
        elif re.search(patt_va, value_sen_or):
            value_patt = re.search(patt_va, value_sen_or)
            value_text = value_patt.group()
            value_position = [x + position_tr for x in list(value_patt.span())]
            if re.findall('^[：:]', value_text):
                value_position = [value_position[0] + 1, value_position[1]]
            if re.findall('[，。；,]$', value_text):
                value_position = [value_position[0], value_position[1] - 1]
            value_text = re.sub('^[：:]', '', value_text)
            value_text = re.sub('[，。；,]$', '', value_text)
            value = {'text': value_text, 'type': 'value',
                     'value': value_text, 'position': value_position}
            value_result.append(value)
        elif re.search(patt_num, value_sen_or):
            position_match = re.search('\d+\.?\d*', value_sen_or)
            position = [x + int(position_tr) for x in position_match.span()]
            value_text = position_match.group()
            value = {'text': value_text, 'type': 'value',
                     'value': value_text, 'position': position}
            value_result.append(value)
            symbol = re.search(patt_symbol, value_sen_or)
            if symbol:
                symbol_text = symbol.group()
                symbol_position = [x + int(position_tr) for x in symbol.span()]
                value = {'text': symbol_text, 'type': 'value',
                         'value_status': symbol_text, 'position': symbol_position}
                value_result.append(value)
        else:
            pass
        return value_result

    def _add_value(self, position_tr, value_sen_or):
        value_result = []
        patt1 = '(阴性|阳性|\+|\-)'
        patt2 = '[<>＜＞]\d{1,}\.?\d{0,}'
        match_patt1 = re.search(patt1, value_sen_or)
        match_patt2 = re.search(patt2, value_sen_or)
        for match_patt in [match_patt1, match_patt2]:
            if match_patt:
                text_match = match_patt.group()
                position_match = [x + position_tr for x in match_patt.span()]
                value = {'text': text_match, 'type': 'value',
                         'value': text_match, 'position': position_match}
                value_result.append(value)
        return value_result

    def _candidate_modify(self, entity):
        """
        按照语言习惯，部分属性在实体后面，进行候选属性修正
        :param entity: 实体
        :return: 新的候选属性项
        """
        entity_index = 0
        for x in self.candidate_words:
            if x[2] == entity:
                entity_index = int(x[0])
            else:
                pass
        candidate_sen = ''.join(
            [l[2] for l in self.candidate_words[entity_index:]])
        return candidate_sen

    def get_entity_immediate_family(self):
        """实体  直系家人"""
        immediate_family_result = []
        for k in self.candidate_words:
            if k[1] == 'cr':
                post = re.search((k[2]), self.content).span()
                immediate_family = {'text': k[2], 'type': 'immediate_family',
                                    'value': k[2], 'position': post}
                immediate_family_result.append(immediate_family)
        return immediate_family_result
