#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
hop_service.py

Author: fangcheng
Create on 2018-08-17 Friday.
"""
import sys
import json

sys.path.append('/data/home/fangcheng/project/develop/mednlp')
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.dept.pet.human_or_pet import HumanPetWorker
from ailib.utils.exception import AIServiceException
from ailib.service.base_service import run

worker = HumanPetWorker()
temp_result = worker.execute('我的狗死了')
print(temp_result)


class HumanOrPet(BaseRequestHandler):
    def initialize(self, runtime=None, **kwargs):
        super(HumanOrPet, self).initialize(runtime, **kwargs)

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def input(self):
        query = self.get_q_argument('', limit=2000)
        if len(query) == 0:
            param = json.loads(self.request.body)
            query = param.get('q')
        return query

    def _get(self):
        exception = AIServiceException()

        query = self.input()
        if len(query) <= 0:
            exception.message = "参数q不可为空"
            raise exception

        data = worker.execute(query)
        result = {'data': data}
        return result


if __name__ == '__main__':
    handlers = [(r'/human_or_pet', HumanOrPet)]
    run(handlers)
