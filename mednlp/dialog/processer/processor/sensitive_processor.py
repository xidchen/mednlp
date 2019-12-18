#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.configuration import Constant as constant


class SensitiveProcessor(BasicProcessor):

    def process(self, query, **kwargs):
        result = {'is_end': 1,
                  constant.ANSWER_GENERAL_ANSWER: '很抱歉，小微没有理解您的意思，您可以按引导咨询医疗相关问题~'}
        return result

    def process_2(self, environment):
        result = {'is_end': 1,
                  'answer': [{'text': '很抱歉，小微没有理解您的意思，您可以按引导咨询医疗相关问题~'}]}
        return result
