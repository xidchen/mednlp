#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.configuration import Constant as constant, logger
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.model.similarity import TfidfSimilarity
import global_conf
import time
from mednlp.dialog.generator_manager.generator_manager import cgm


class GreetingProcessor(BasicProcessor):
    """
    寒暄处理的意图
    """

    def process(self, query, **kwargs):
        result = {}
        self.set_params(query, **kwargs)
        threshold = 0.6
        # answer = '很抱歉，我还在学习中，您可以问我，胃不舒服挂什么科'
        answer = '你好，请问有什么可以帮助您？'
        query = ''
        if self.input_params.get('input') and self.input_params.get('input').get('q'):
            query = self.input_params.get('input').get('q')
        # corpus_greeting_answer = constant.tf_idf.best_answer(query, threshold)
        corpus_greeting_answer = TfidfSimilarity(
                global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
        if corpus_greeting_answer:
            answer = corpus_greeting_answer
        result[constant.ANSWER_GENERAL_ANSWER] = answer
        result['is_end'] = 1
        result['code'] = 0
        return result


class GuideProcessor(BasicProcessor):
    """
    寒暄处理的意图
    """

    def process(self, query, **kwargs):
        result = {}
        result[constant.ANSWER_GENERAL_ANSWER] = constant.QUERY_VALUE_GUIDE
        result['is_end'] = 1
        result['code'] = 0
        return result


class CustomerServiceProcessor(BasicProcessor):
    # 客服意图

    def process(self, query, **kwargs):
        result = {}
        self.set_params(query)
        param = {
            'q': self.input_params['input']['q'],
            'sort': 'customer_service'
        }
        try:
            res = cgm.get_strategy(constant.general_organization, 'greeting', param)
            if res and res.get('general_answer'):
                result[constant.ANSWER_GENERAL_ANSWER] = res['general_answer']
        except:
            logger.info('content_generation error, params:%s' % json.dumps(param))
        if not result.get(constant.ANSWER_GENERAL_ANSWER):
            result[constant.ANSWER_GENERAL_ANSWER] = constant.QUERY_VALUE_CUSTOMER_SERVICE
        # if self.intention_conf.configuration.mode == constant.VALUE_MODE_XWYZ:
        #     # 门户小微医助调用客服系统
        #
        #     q = self.input_params['input']['q']
        #     user = 'user' + str(time.time() * 1000)
        #     param = {'fromuser': user, 'reqtype': 1, 'ip': '127.0.0.1',
        #              'q': str(q)}
        #     try:
        #         # 获取客服系统回答
        #         kf_res = constant.kf.query(param)
        #         result[constant.ANSWER_GENERAL_ANSWER] = kf_res['text']['content']
        #     except Exception as err:
        #         # 异常处理的客服文案, 需要校对
        #         logger.exception(err)
        #         result[constant.ANSWER_GENERAL_ANSWER] = constant.QUERY_VALUE_CUSTOMER_SERVICE
        #     result['is_end'] = 1
        #     result['code'] = 0
        #     return result
        result['is_end'] = 1
        result['code'] = 0
        return result