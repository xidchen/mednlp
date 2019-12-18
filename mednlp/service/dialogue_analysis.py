#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import json
from base_request_handler import BaseRequestHandler
from mednlp.model.medical_robot import DialogueAnalysis
from ailib.utils.exception import ArgumentLostException
from ailib.utils.log import GLLog
import global_conf

dialogue_analysis = DialogueAnalysis()
logger = GLLog('dialogue_analysis_input_output', level='info',
               log_dir=global_conf.log_dir).getLogger()


class DialogueAnalysisService(BaseRequestHandler):
    def initialize(self, runtime=None, **kwargs):
        super(DialogueAnalysisService, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query = self.request.body
        if not query:
            query = self.get_q_argument('', limit=1000)
            if not query:
                raise ArgumentLostException(['q'])

        decoded_query = json.loads(query)
        if not decoded_query.get('source'):
            raise ArgumentLostException(['source'])
        if not decoded_query.get('input'):
            raise ArgumentLostException(['input'])
        mode = decoded_query.get('mode', 'xwyz')

        inputs = decoded_query.get('input')
        if not isinstance(inputs, list):
            raise TypeError('参数 input 应该是list类型 ！！')

        input = {}
        [input.update(i) for i in inputs]
        if not input.get('q'):
            raise ArgumentLostException(['q'])

        decoded_query['input'] = input
        result = {}
        result['data'] = dialogue_analysis.interact(decoded_query, mode=mode)
        self._logging(inputs, result['data'])
        return result

    def _logging(self, in_msg, out_msg):
        log_info = {'in_msg': in_msg,
                    'out_msg': out_msg}
        logger.info(json.dumps(log_info, ensure_ascii=False))


if __name__ == '__main__':
    handlers = [(r'/dialogue_analysis', DialogueAnalysisService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)

