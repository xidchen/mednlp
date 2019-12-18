#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
medseg.py -- the seg for medical

Author: chenxd
Create on 2018-09-18 Monday.
"""


class MedSeg(object):

    sentence_mark = {u'。', u'！', u'？', u'......', u'!', u'?', u',', u'，', u'等'}
    custom_mark = {'患者', '病后'}
    phrase_mark = {u'；', u'、', u'：', u';', u':', u'及'}

    def __init__(self, cfg_path, **kwargs):
        pass

    def _load_dict(self):
        pass

    def sentence(self, content, **kwargs):

        content = str(content)
        for mark in self.custom_mark:
            content = content.replace(mark, '。')
        no_mark = kwargs.get('no_mark', False)
        content = self._check_unicode(content)
        sent = []
        sent_list = []
        for char in content:
            if char in self.sentence_mark:
                if not no_mark:
                    sent.append(char)
                sent_list.append(''.join(sent))
                sent = []
                continue
            sent.append(char)
        sent_list.append(''.join(sent))
        return sent_list

    def phrase(self, content, **kwargs):

        no_mark = kwargs.get('no_mark', False)
        content = self._check_unicode(content)
        phrase = []
        phrase_list = []
        for char in content:
            if char in self.phrase_mark or char in self.sentence_mark:
                if not no_mark:
                    phrase.append(char)
                phrase_list.append(''.join(phrase))
                phrase = []
                continue
            phrase.append(char)
        phrase_list.append(''.join(phrase))
        return phrase_list


    def _check_unicode(self, content):
        if not isinstance(content, str):
            content = str(content)
        return content
