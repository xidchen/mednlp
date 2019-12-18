#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
intelligence_service_check.py

Author: caoxg <caoxg@guahao.com>
Create on 2017-06-19 星期一.
"""

import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.check_classify_merge_model import MergeModel


mergemodel = MergeModel(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_MODEL')


class IntelligenceServiceCheck(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.write_result(self._get())

    def _get(self):
        query = self.get_q_argument('', limit=5000)
        result = {}
        depts = mergemodel.predict(query)
        rows = self.get_argument('rows', 3)
        rows = int(rows)
        # data = result.setdefault('data', [])
        data = result.setdefault('data', {})
        if not depts:
            data.append({'label': 'unknow'})
            result['totalCount'] = 1
            return result
        result['content'] = query
        for i, line in enumerate(depts[0:rows]):
            temp_result = {}
            if line:
                temp_result['check_desc'] = line[0]
                temp_result['score'] = line[1]
                temp_result['check_label'] = line[2]
            if i == 0:
                data["主动问诊"] = temp_result
            elif i == 1:
                data["疾病分析细致"] = temp_result
            else:
                data["有温度"] = temp_result
            # data.append(temp_result)
        result['totalCount'] = rows
        return result


if __name__ == '__main__':
    handlers = [(r'/intelligence_service_check', IntelligenceServiceCheck, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
