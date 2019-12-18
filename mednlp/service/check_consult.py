#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-07-08 星期日.
"""

import global_conf
import os
import sys
import time
from base_request_handler import BaseRequestHandler
from mednlp.model.check_consult_model import CheckConsultModel, id_consult,get_contents,get_result

check_consult_model = CheckConsultModel(cfg_path=global_conf.cfg_path, model_section='CHECK_CLASSIFY_MODEL')


class CheckConsult(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.write_result(self._get())

    def _get(self):
        query = self.get_q_argument('', limit=2000)
        consult = self.get_argument('consult', '')
        rows = int(self.get_argument('rows', 1))
        sex = int(self.get_argument('sex', 0))
        age = int(self.get_argument('age', -1))
        fl = self.get_argument('fl', '')
        result = {}
        if not query and not consult:
            return result
        consults = id_consult(consult)
        consult = get_contents(consults)
        consult_query = get_result(consult)
        if not query and not consult_query:
            return result
        if query:
            depts = check_consult_model.predict(query)
        else:
            depts = check_consult_model.predict(consult_query)
        data = result.setdefault('data', {})
        if not depts:
            data['check_code'] = ['unknow']
            return result
        check_codes = []
        code_details = []
        scores = []
        for check_code, score, code_detail in depts:
            if check_code != '0' and score >= 0.3:
                check_codes.append(check_code)
                scores.append(score)
                code_details.append(code_detail)
        if not check_codes:
            check_codes.append(depts[0][0])
            scores.append(depts[0][1])
            code_details.append(depts[0][2])
        data['check_code'] = check_codes
        data['score'] = scores
        if query:
            data['content'] = query
        else:
            data['content'] = consult
        if fl == 'code_detail':
            data['code_details'] = code_details
        return result

if __name__ == '__main__':
    handlers = [(r'/check_consult', CheckConsult, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
