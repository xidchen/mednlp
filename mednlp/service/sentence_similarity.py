#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sentence_similarity.py -- the service of sentence_similarity

Author: caoxg <caoxg@guahao.com>
Create on 2018-09-29 周六.
"""

import global_conf
from mednlp.utils.utils import unicode_python_2_3
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.sentence_similarity_merge_model  import MergeModel
from mednlp.dept.utils.rules import dept_filter_error
import ast
import json


sentence_model = MergeModel(cfg_path=global_conf.cfg_path, model_section='SENTENCE_SIMILARITY_MODEL')


class SentenceSimilarity(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        result = self._get()
        if result:
            self.write_result(result)
        else:
            self.write_result(result, message='unsuccessful', code=1)

    def get_arguments(self, arguments):
        request_type = 'form'
        for key, val in arguments.items():
            arguments[key] = self.get_argument(key, val)

        query_str = self.request.body
        headers = self.request.headers
        content_type = headers.get('Content-type', None)
        if content_type and 'application/json' in content_type and query_str:
            request_type = 'body_json'
            query = json.loads(query_str, encoding='utf-8')
            for key, val in arguments.items():
                arguments[key] = query.get(key, val)

        return request_type

    def _get(self):
        arguments = {'q': '', 'contents': '[]', 'rows': 1, 'sex': 0, 'age': -1, 'mode': 1}
        self.get_arguments(arguments)
        contents = arguments.get('contents')
        rows = arguments.get('rows')
        sex = arguments.get('sex')
        age = arguments.get('age')
        mode = arguments.get('mode')

        query = self.get_q_argument('', limit=2000)
        query = query if query else arguments.get('q')

        sex = dept_filter_error(sex, 0)
        age = dept_filter_error(age, -1)
        mode = dept_filter_error(mode, 1)
        result = {}
        if not query:
            return result
        try:
            # contents = eval(unicode_python_2_3(contents))
            contents = ast.literal_eval(unicode_python_2_3(contents))
        except:
            return None
        depts = sentence_model.predict(query, sentences=contents, age=age, sex=sex, mode=mode)
        data = result.setdefault('data', {})
        if not depts:
            data['is_similarity'] = 0
            return result
        if float(depts[0][1]) > 0.6:
            data['score'] = float(depts[0][1])
            data['is_similarity'] = 1
            data['index'] = int(depts[0][2])
            data['content'] = depts[0][0]
        else:
            data['is_similarity'] = 0
        return result


if __name__ == '__main__':
    handlers = [(r'/sentence_similarity', SentenceSimilarity, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
