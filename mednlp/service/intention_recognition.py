#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify.py -- the service of dept_classify

Author: renyx <renyx@guahao.com>
Create on 2018-09-07 Friday
"""

import copy
import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.utils.log import GLLog
from ailib.utils.exception import ArgumentLostException
from mednlp.model.intention import IntentionStrategy
import json

logger = GLLog('intention_recognition_input_output', level='info',
               log_dir=global_conf.log_dir).getLogger()

# 规则
intention = IntentionStrategy(logger=logger)


class IntentionRecognition(BaseRequestHandler):

    def initialize(self, runtime=None,  **kwargs):
        super(IntentionRecognition, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        result = {'data': {}}
        query = None
        intention_set = '-1'
        accompany_intention_set = '-1'
        mode = 'xwyz'
        debug = 0
        if self.request.body:
            data_json = json.loads(self.request.body)
            query = data_json.get('q')
            intention_set = data_json.get('intention_set', '-1')
            accompany_intention_set = data_json.get('accompany_intention_set', '-1')
            mode = data_json.get('mode', 'xwyz')
            debug = data_json.get('debug', 0)
        elif self.get_q_argument('', limit=2000):
            query = self.get_q_argument('', limit=2000)
            intention_set = self.get_argument('intention_set', '-1')
            if '-1' != intention_set:
                intention_set = json.loads(intention_set)
            accompany_intention_set = self.get_argument('accompany_intention_set', '-1')
            if '-1' != accompany_intention_set:
                accompany_intention_set = json.loads(accompany_intention_set)
            mode = self.get_argument('mode', 'xwyz')
            debug = self.get_argument('debug', 0)
        if not query:
            raise ArgumentLostException(['q'])
        params_dict = {}
        if '-1' != intention_set:
            params_dict['intention_set'] = intention_set
        if '-1' != accompany_intention_set:
            params_dict['accompany_intention_set'] = accompany_intention_set
        if debug:
            params_dict['debug'] = 1
        input_params = copy.deepcopy(params_dict)
        input_params['query'] = query
        input_params['mode'] = mode
        logger.info('入参:%s' % json.dumps(input_params, ensure_ascii=False))
        intent_result = intention.get_intention_and_entities(query, mode=mode, **params_dict)
        result['data'] = intent_result
        logger.info('返回参数:%s' % json.dumps(result, ensure_ascii=False))
        return result

if __name__ == '__main__':
    handlers = [(r'/intention_recognition', IntentionRecognition)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
