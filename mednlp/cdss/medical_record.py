#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
medical_record.py -- process for medical record

Author: chenxd
Create on 2017-09-07 Thursday.
"""

import sys
import re
import global_conf
from optparse import OptionParser
from mednlp.text.mmseg import MMSeg
from mednlp.text.synonym import Synonym
from mednlp.text.medseg import MedSeg
from mednlp.text.symptom_parser import SymptomParser


class MedicalRecordParser(object):
    """
    病历解析类.
    """

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', True)
        self.chief_complaint_parser = ChiefComplaintParser(debug=self.debug)
        self.past_medical_history_parser = PastMedicalHistory()
        self.age_seg = [28, 365*15, 365*30, 365*45, 365*60, 365*500]

    def parse(self, medical_record):
        """
        解析病历.
        参数:
        medical_record->病历,结构:{chief_complaint,}
        返回值->病历解析后的结果,结构:{chief_complaint,}
        """
        result = {'symptom_all': set()}
        symptom_parse_field = ['chief_complaint', 'inspection', 'physical_examination']
        for field in symptom_parse_field:
            content = medical_record.get(field)
            if content:
                result[field] = self.chief_complaint_parser.parse(content)
                symptom_all = result[field].get('symptom_all')
                if symptom_all:
                    result['symptom_all'].update(symptom_all)
        result['sex'] = medical_record.get('sex')
        result['age'] = medical_record.get('age')
        if result['age'] and result['age'] != '-1':
            start_pos = 0
            for count, end_pos in enumerate(self.age_seg):
                age_int = int(result['age'])
                if start_pos < age_int < end_pos:
                    result['age_seg'] = count + 1
                    break
                start_pos = end_pos
        disease_history_field = ['past_medical_history']
        disease_history_field.extend(symptom_parse_field)
        past_medical_history = {}
        for field in disease_history_field:
            content = medical_record.get(field)
            if not content:
                continue
            past_medical_history.update(
                self.past_medical_history_parser.parse(content))
        result['past_medical_history'] = past_medical_history
        duration = self.parse_duration(
            medical_record['chief_complaint'])
        if duration > 0:
            result['duration'] = duration
        return result

    def parse_duration(self, content):
        """
        解析症状持续时间.
        参数:
        content->需要解析的内容.
        返回值->天数,未早到则返回-1
        """
        units = {'天': 1, '日': 1, '周': 7, '月': 30, '年': 365}
        for unit, base in units.items():
            m = re.match('\D*(\d+)(%s)' % unit, str(content))
            if not m:
                continue
            return int(m.group(1)) * base
        return -1


class PastMedicalHistory(object):
    """
    既往史解析类。
    """

    def __init__(self, **kwargs):
        if 'extractor' in kwargs:
            self.extractor = kwargs.get('extractor')
        else:
            self.extractor = MMSeg(dict_type=['disease'])

    def parse(self, content):
        """
        实体抽取方法.
        参数:
        content->需要抽取的用户主诉或者现病史.
        返回值->抽取的症状实体列表,格式:{disease_name: disease_id}.
        """
        diseases = self.extractor.cut(content)
        new_diseases = {}
        for d_name, d_id in diseases.items():
            new_diseases[str(d_id)] = str(d_name)
        return new_diseases


class ChiefComplaintParser(object):
    """
    用户主诉实体抽取类.
    """

    negative_mark = [u'无', u'未见', u'未现', u'没有', u'无明显']

    def __init__(self, extractor=None, **kwargs):
        self.debug = kwargs.get('debug', False)
        if extractor:
            self.extractor = extractor
        else:
            # 可以考虑是否开启完全切分模式
            self.extractor = MMSeg(dict_type=['symptom_wy'])
            self.bp_extractor = MMSeg(dict_type=['body_part'])
            self.d_extractor = MMSeg(dict_type=['disease'])
            self.ins_extractor = MMSeg(dict_type=['examination'])
            self.pe_extractor = MMSeg(dict_type=['physical'])
            self.symptom_parser = SymptomParser()
        self.multi_seg = MMSeg(dict_type=['synonym'], is_all_word=True)
        self.seg = MedSeg(global_conf)
        self.synonym = Synonym(dict_type=['wy_symptom_name'])

    def parse(self, chief_complaint):
        """
        实体抽取方法.
        参数:
        chief_complaint->需要抽取的用户主诉或者现病史.
        返回值->抽取的症状实体列表,格式:{symptom_name:symptom_id}.
        """
        return self._parse_with_negative(chief_complaint)

    def _parse_with_negative(self, chief_complaint):
        """
        实体抽取方法.
        参数:
        chief_complaint->需要抽取的用户主诉或者现病史.
        返回值->抽取的症状.结构:{'symptoms':,'symptom_synonym':,\
        'symptom_all':,'symptom_negative'}
        symptoms->原始症状名称和id,结构:{symptom_name: symptom_id}
        symptom_synonym->症状同义词组,结构:[symptom_synonym_group]
        symptom_all->包含同义词组的症状集合,结构:set(symptom_id)
        symptom_negative->否定的症状.
        """
        sent_list = self.seg.sentence(chief_complaint, no_mark=True)
        sent_filtered = []
        symptom_negative = set()
        self.bp_symptoms = {}
        for sent in sent_list:
            sent = sent.strip()
            f_sent = self._filter_negative(sent, symptom_negative)
            if not f_sent:
                continue
            bp_symptom = self.symptom_parser.parse(f_sent)
            if bp_symptom:
                for body_part, symptom_dict in bp_symptom.items():
                    s_dict = self.bp_symptoms.setdefault(body_part, {})
                    s_dict.update(symptom_dict)
            sent_filtered.append(f_sent)
        self.bp_symptom_set = set()
        for s_dict in self.bp_symptoms.values():
            self.bp_symptom_set.update(s_dict.values())

        sent_join = '  '.join(sent_filtered)
        cc_parsed = self._parse_by_dict(sent_join)
        symptom_negative_id = set()
        for s_name in symptom_negative:
            s_id = self._check_symptom(s_name)
            symptom_negative_id.add(s_id)
        cc_parsed['symptom_negative'] = symptom_negative_id
        cc_parsed['symptom_all'].update(symptom_negative)
        return cc_parsed

    def _filter_negative(self, sentence, symptom_negative):
        """
        过滤否定模式.
        """
        phrase_list = self.seg.phrase(sentence, no_mark=True)
        filter_pos = 0
        filtered_phrase = []
        for count, phrase in enumerate(phrase_list):
            if not phrase:
                continue
            if count < filter_pos:
                symptom_negative.add(phrase)
                continue
            is_negative_match, mark = self._is_negative_match(phrase)
            if not is_negative_match:
                filtered_phrase.append(phrase)
                continue
            t_phrase = phrase[len(mark):]
            if t_phrase:
                symptoms = self.extractor.cut(t_phrase)
                symptom_negative.update(symptoms.keys())
            # symptom_negative.add(phrase[len(mark):])
            filter_pos = count
            if count + 1 < len(phrase_list):
                filter_pos += self._find_filter_pos(
                    phrase_list[count + 1:], mark)
        return '  '.join(filtered_phrase)

    def _find_filter_pos(self, phrase_list, mark):
        """
        确定过滤模式作用偏移量.
        """
        for count, phrase in enumerate(phrase_list):
            if not self._check_symptom(phrase):
                return count + 1
            if self._check_symptom(mark + phrase):
                return count + 1
        return len(phrase_list) + 1

    def _is_negative_match(self, phrase):
        """
        检查是否否定模式.
        """
        for mark in self.negative_mark:
            index = phrase.find(mark)
            if 0 == index:
                if self._check_symptom(phrase):
                    continue
                test_symptom = phrase[len(mark):]
                if self._check_symptom(test_symptom, multi=True):
                    return True, mark
        return False, None

    def _check_symptom(self, test_symptom, multi=False):
        """
        检查是否症状.
        参数:
        test_symptom->需要检测的疑似症状.
        multi->是否支持多症状并列,False不支持,True支持,可空,默认为False.
        """
        symptoms = self.extractor.cut(test_symptom)
        if not symptoms:
            return False
        for s_names, s_id in symptoms.items():
            if s_names == test_symptom:
                return s_id
        if multi:
            if ''.join(symptoms.keys()) == test_symptom:
                return symptoms.values()
        return False

    def _parse_by_dict(self, chief_complaint):
        """
        基于词典的实体抽取方法.
        参数:
        chief_complaint->需要抽取的用户主诉或者现病史.
        返回值->抽取的症状.结构:{'symptoms':,'symptom_synonym':,'symptom_all':}
        symptoms->原始症状名称和id,结构:{symptom_name: symptom_id}
        symptom_synonym->症状同义词组,结构:[symptom_synonym_group]
        symptom_all->包含同义词组的症状集合,结构:set(symptom_id)
        """
        symptoms = self.extractor.cut(chief_complaint)
        new_symptoms = {}
        for s_name, s_id in symptoms.items():
            if len(s_name) > 0:
                new_symptoms[str(s_name)] = str(s_id)
        diseases = self.d_extractor.cut(chief_complaint)
        new_diseases = {}
        for d_name, d_id in diseases.items():
            if len(d_name) > 0:
                new_diseases[str(d_name)] = str(d_id)
        body_parts = self.bp_extractor.cut(chief_complaint)
        new_body_parts = {}
        for bp_name, bp_id in body_parts.items():
            if len(bp_name) > 0:
                new_body_parts[str(bp_name)] = str(bp_id)
        inspections = self.ins_extractor.cut(chief_complaint)
        new_inspections = {}
        for ins_name, ins_id in inspections.items():
            if len(ins_name) > 0:
                new_inspections[str(ins_name)] = str(ins_id)
        physical_examinations = self.pe_extractor.cut(chief_complaint)
        new_physical_examinations = {}
        for pe_name, pe_id in physical_examinations.items():
            if len(pe_name) > 0:
                new_physical_examinations[str(pe_name)] = str(pe_id)
        cc_parsed = {'symptoms': new_symptoms,
                     'diseases': new_diseases,
                     'body_parts': new_body_parts,
                     'ins': new_inspections,
                     'pe': new_physical_examinations}
        symptom_synonym_list = []
        symptom_all = set()
        for symptom_name, symptom in new_symptoms.items():
            symptom_all.add(symptom)
            # 屏蔽症状组
            symptom_synonym = {symptom}
            sub_symptom = self.multi_seg.cut(symptom_name)
            if sub_symptom:
                extend_symptom = self.synonym.synonym_extend(
                    symptom_name, list(sub_symptom.keys()))
                if extend_symptom:
                    extend_symptom_id = set()
                    for e_symptom in extend_symptom:
                        mm_symptom = self.extractor.cut(e_symptom)
                        if (mm_symptom and len(mm_symptom) == 1 and
                                e_symptom == list(mm_symptom.keys())[0]):
                            extend_symptom_id.add(list(mm_symptom.values())[0])
                    symptom_synonym.update(extend_symptom_id)
            if symptom_synonym:
                self.bp_symptom_set = self.bp_symptom_set - symptom_synonym
                symptom_synonym_list.append(symptom_synonym)
                symptom_all.update(symptom_synonym)
        for s_id in self.bp_symptom_set:
            symptom_synonym_list.append({s_id})
            symptom_all.add(s_id)
        cc_parsed['symptom_synonym'] = symptom_synonym_list
        cc_parsed['symptom_all'] = symptom_all
        return cc_parsed


if __name__ == '__main__':
    content0 = '3年前无诱因反复头晕，多次测血脂高于正常，要求休息。'
    command = """
    python %s -s string -d dictionary[disease|treatment|symptom|doctor|hospital|department]
    """ % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-s', '--string', dest='string', help='the cut string')
    parser.add_option('-t', '--type', dest='type', help='medical record type')
    parser.add_option('-g', '--debug', action='store_true', dest='debug',
                      default=False, help='是否开启调试模式')
    (options, args) = parser.parse_args()
    run_type = 'ChiefComplaintParser'
    if options.type is not None:
        run_type = options.type
    if options.string is not None:
        content0 = options.string
    runner = eval(run_type)(debug=options.debug)
    result0 = runner.parse(content0)
    if isinstance(result0, dict):
        for k, v in result0.items():
            print(k, v)
