#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
book_parser.py -- the parser of book

Author: maogy <maogy@guahao.com>
Create on 2017-09-26 Tuesday.
"""


import os
import sys
import codecs
import re
import json
import ujson
from optparse import OptionParser
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class BookParser(object):

    def __init__(self, **kwargs):
        pass

    def parse_chapter(self, book, **kwargs):
        chapters = []
        chapter_mark = u'第[一二三四五六七八九十]+章 '
        chapter = None
        for count, line in enumerate(codecs.open(book, 'r', 'utf-8')):
            line = line.replace('e书联盟电子书下载www.book118.com', '')
            chapter_match = re.search(chapter_mark, line)
            if chapter_match:
                if chapter:
                    chapters.append(chapter)
                chapter = {'content': [line]}
                chapter['title'] = line.replace(' ', '')
            else:
                if not chapter:
                    continue
                chapter['content'].append(line)
        chapters.append(chapter)
        print(len(chapters))
        output_dir = kwargs.get('output')
        for chapter in chapters:
            title = chapter['title'].strip()
            c_path = title
            if output_dir:
                c_path = os.path.join(output_dir, title)
            c_file = open(c_path, 'w+')
            for line in chapter['content']:
                c_file.write(line)
            c_file.close()

    def parse_disease(self, book_chapter, **kwargs):
        sections = []
        section_mark = u'第[一二三四五六七八九十]+节 '
        section = None
        for count, line in enumerate(codecs.open(book_chapter, 'r', 'utf-8')):
            section_match = re.search(section_mark, line)
            if section_match:
                if section:
                    sections.append(section)
                section = {'content': []}
                section['name'] = line.replace(section_match.group(), '').replace(' ', '')
            else:
                if not section:
                    continue
                section['content'].append(line)
        sections.append(section)
        print(len(sections))
        option_mark = [u'[一二三四五六七八九十]+、',
                       u'\([一二三四五六七八九十]+\)']

        maybe_disease = []
        for section in sections:
            print('sec:', section['name'])
            option = None
            list_length = len(maybe_disease)
            for count, line in enumerate(section['content']):
                is_matched = False
                for count, mark in enumerate(option_mark):
                    option_match = re.search(mark, line)
                    if option_match:
                        o_line = line.replace(option_match.group(),
                                              '').replace(' ', '')
                        print('option%s:' % count, o_line)
                        if option:
                            maybe_disease.append(option)
                        option = {'content': []}
                        option['name'] = o_line
                        is_matched = True
                        break
                if not is_matched:
                    if not option:
                        continue
                    option['content'].append(line)
            if option:
                maybe_disease.append(option)
            if len(maybe_disease) == list_length:
                maybe_disease.append(section)
        field_mark = {
            'definition': r'%s\(([^)]+)\)是',
            'cause': u'【病因】',
            'pathogenesis': u'【发病机制】', 'pathophysiological': u'【病理',
            'clinical_manifestation': u'【临床表现】',
            'complication': u'【并发症】', 'lab_check': u'【实验室检查】',
            'other_check': u'【辅助检查】', 'diagnosis': u'【诊断】',
            'differential_diagnosis': u'【鉴别诊断】',
            'treatment': u'【治疗】', 'prevention': u'【预防】',
            'prognosis': u'【预后】'}

        diseases = {}
        for disease in maybe_disease:
            name = disease['name'].strip()
            field_content = []
            last_field = None
            for line in disease['content']:
                is_matched = False
                for field, mark in field_mark.items():
                    match = None
                    if field == 'definition':
                        mark = mark % name
                        match = re.match(mark, line.strip())
                    else:
                        match = re.search(mark, line)
                    if match:
                        if field_content and last_field:
                            disease = diseases.setdefault(name, {})
                            disease[last_field] = ''.join(field_content)
                        last_field = field
                        field_content = []
                        if field == 'definition':
                            field_content.append(line)
                            disease = diseases.setdefault(name, {})
                            disease['disease_name_en'] = match.group(1)
                        is_matched = True
                        break
                if not is_matched:
                    if not last_field:
                        continue
                    line = line.replace('。\n', '||p||')
                    field_content.append(line.strip())
        print('disease num:%s' % len(diseases))
        for name, disease in diseases.items():
            print('===============================')
            print('disease name:', name)
        disease_json = json.dumps(diseases, ensure_ascii=False)
        output_path = 'diseases.json'
        if kwargs.get('output'):
            output_path = kwargs['output']
        f_w = codecs.open(output_path, 'w+', 'utf-8')
        f_w.write(str(disease_json))
        f_w.close()

if __name__ == "__main__":
    command = """
    python %s -s string -d dictionary[symptom]
    """ % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option("-b", "--book", dest="book", help="the book to parse")
    parser.add_option("-t", "--type", dest="type", help="the type of parse")
    parser.add_option("-o", "--output", dest="output",
                      help="the output of parse")
    (options, args) = parser.parse_args()
    func_type = 'parse_chapter'
    if options.type is not None:
        func_type = options.type
    bp = BookParser()
    run_cmd = 'bp.%s' % func_type
    eval(run_cmd)(options.book, output=options.output)

