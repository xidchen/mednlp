#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sentence_vector.py -- the service of sentence_vector

Author: renyx <renyx@guahao.com>
Create on 2019-09-09 Monday
"""
import traceback
import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.utils.exception import ArgumentLostException
from mednlp.model.sentence_vector_model import SentenceVectorModel, logger
import json
from ailib.utils.verify import check_is_exist_params
from ailib.client.zk_register import ZkRegister

control = SentenceVectorModel()
zkRegister = ZkRegister.load_register(cfg_path=global_conf.cfg_path, section='ZookeeperRegister',
                            node_prefix='sentence_vector;1.0;', service_name='sentence_vector',
                            logger=logger)
zkRegister.start()


class SentenceVector(BaseRequestHandler):

    def initialize(self, runtime=None,  **kwargs):
        super(SentenceVector, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        """
        入参:
        {
            "content": {},
            "parameter": {}
        }
        :return:
        """
        result = {'data': {}}
        content = None
        if self.request.body:
            data_json = json.loads(self.request.body, encoding='utf-8')
            content = data_json.get('content', {})
        elif self.get_argument('q'):
            content = self.get_argument('content', {})
        check_is_exist_params(content, ['q', 'source'])
        try:
            data = control.get_vector(content['q'])
            result['data'] = data
        except Exception as err:
            logger.error(traceback.format_exc())
        finally:
            logger.info('入参:%s,返回参数:%s' % (
                json.dumps(['q'], ensure_ascii=False), json.dumps(result, ensure_ascii=False)))
        return result


if __name__ == '__main__':
    handlers = [(r'/sentence_vector', SentenceVector)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
