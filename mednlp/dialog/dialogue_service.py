#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dialogue_service.py -- the service of dialogue

Author: maogy <maogy@guahao.com>
Create on 2018-10-02 Tuesday.
"""

import copy
import traceback
import time
import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.dialog.dialogue_control import DialogueControl
import json
from mednlp.dialog.configuration import Constant as constant
import pdb
import traceback
from ailib.utils.exception import AIServiceException
from ailib.utils.verify import check_is_exist_params
from mednlp.dialog.dialogue_constant import stat_logger as logger


dialog_control = DialogueControl()


class DialogueService(BaseRequestHandler):
    # DialogueService 每次请求都会新new1个
    def initialize(self, runtime=None, **kwargs):
        super(DialogueService, self).initialize(runtime, **kwargs)

    def post(self):
        return self.get()

    def get(self):
        start_time = time.time() * 1000
        result = {'data': {}}
        query = self.request.body
        if not query:
            query = self.get_argument('q')
        if not query:
            result[constant.RESULT_CODE] = 1
            result[constant.RESULT_MESSAGE] = 'No query!'
            self.write_result(result, result[constant.RESULT_MESSAGE], result[constant.RESULT_CODE])
            return
        decoded_query = json.loads(query)
        try:
            """
            query是原始的字符串,
            decoded_query是query通过json解析后产生,保证一定有source, input.
            result代表了所有返回的结果
            所有不正常异常通过dialog_control.control抛出,正常异常会包装在result里
            """
            check_is_exist_params(decoded_query, ['source', constant.QUERY_FIELD_INPUT])
            inputs = decoded_query[constant.QUERY_FIELD_INPUT]
            if not isinstance(inputs, list):
                raise TypeError('参数 input 应该是list类型 ！！')
            result = dialog_control.control(copy.deepcopy(decoded_query))
        except AIServiceException as ai_err:
            logger.info('###start###%s###end###' % json.dumps({'input': decoded_query}, ensure_ascii=False))
            logger.error(traceback.format_exc())
            logger.error(ai_err.message)
            self.write_result(result, ai_err.message, ai_err.code)
            return
        except Exception as e:
            logger.info('###start###%s###end###' % json.dumps({'input': decoded_query}, ensure_ascii=False))
            logger.error(traceback.format_exc())
            self.write_result(result, str(e), 1)
            return
        result['qtime'] = time.time() * 1000 - start_time
        logger.info('###start###%s###end###' % json.dumps({'input': decoded_query, 'output': result}, ensure_ascii=False))
        self.write_result(result)


if __name__ == '__main__':
    handlers = [(r'/dialogue_service', DialogueService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
