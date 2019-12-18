#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify.py -- the service of dept_classify

Author: renyx <renyx@guahao.com>
Create on 2018-09-07 Friday
"""
import sys
import numpy as np
import global_conf
from ailib.utils.log import GLLog
from mednlp.text.vector import Intent2Vector
from base_request_handler import BaseRequestHandler
from mednlp.model.intention_model import IntentionModel


logger = GLLog('intention_service_input_output', level='info', log_dir=global_conf.log_dir).getLogger()
intention_model = IntentionModel(cfg_path=global_conf.cfg_path, model_section='INTENTION_CLASSIFY_MODEL')


class IntentionService(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.write_result(self._get())

    def _get(self):
        result = {'data': []}
        query = self.get_q_argument('', limit=2000)
        include_type = self.get_argument('include_type', '-1')
        exclude_type = self.get_argument('exclude_type', '-1')
        if not sys.version > '3':
            if not isinstance(query, unicode):
                query = unicode(query)
        intent_result = intention_model.predict(query, logger=logger)
        if '-1' == intent_result:
            result['data'].append({'intent': -1})
        else:
            intent_temp = intent_result.reshape(1, -1).squeeze()
            # include操作
            if '-1' != include_type:
                include_types_temp = [int(temp) for temp in include_type.split(',')]
                include_temp = np.array([-999] * len(intent_temp))
                for index, value_temp in enumerate(intent_temp):
                    if index in include_types_temp:
                        include_temp[index] = value_temp
                intent_temp = include_temp
            # exclude_type 操作
            if '-1' != exclude_type:
                exclude_types_temp = [int(temp) for temp in exclude_type.split(',')]
                for index, value_temp in enumerate(intent_temp):
                    if index in exclude_types_temp:
                        intent_temp[index] = -999
            result['data'].append({'intent': int(np.argmax(intent_temp))})
            logger.info('max index:%s;max_value:%s' % (np.argmax(intent_temp), np.max(intent_temp)))
        return result

if __name__ == '__main__':
    handlers = [(r'/intention_service', IntentionService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)