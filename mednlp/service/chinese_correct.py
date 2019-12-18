#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: huhy
Create on 2018-08-17 Friday.
"""

import os
import global_conf
from base_request_handler import BaseRequestHandler
from ailib.utils.exception import ArgumentLostException
from mednlp.model.pinyin2chn_nmt_model import pinyin2chnNMT
from pypinyin import lazy_pinyin
import json
from mednlp.utils.utils import unicode_python_2_3
os.environ['CUDA_VISIBLE_DEVICES'] = ''
pinyin2chn_nmt = pinyin2chnNMT(cfg_path=global_conf.cfg_path,
                               model_section='PINYIN2CHN_MODEL',
                               src_vocab_file=global_conf.chinese_correct_src_vocab_file,
                               tgt_vocab_file=global_conf.chinese_correct_tgt_vocab_file,
                               name_file=global_conf.chinese_correct_special_name_file)


class ChineseCorrection(BaseRequestHandler):
    def initialize(self, runtime=None,  **kwargs):
        super(ChineseCorrection, self).initialize(runtime, **kwargs)

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        data = {}
        if self.request.body:
            data_json = json.loads(self.request.body)
            query = data_json.get('q')
            source = data_json.get('source', '')
        else:
            query = self.get_q_argument('', limit=60)
            source = int(self.get_argument('source', ''))

        if not query:
            raise ArgumentLostException(['q'])
        if not source:
            raise ArgumentLostException(['source'])
        if query != '':
            query = ''.join(query.split(' '))
            query_pinyin = ' '.join([x for x in lazy_pinyin(unicode_python_2_3(query))])
            query = [query_pinyin, query]
            has_error, corrected_query = pinyin2chn_nmt.predict(query)
            data["has_error"] = has_error
            data["correct"] = corrected_query
            return {"code": 0, "message": "successful", "data": data}
        else:
            return {"code": 2, "message": "unsuccessful", "data": None}


if __name__ == '__main__':
    handlers = [(r'/chinese_correct', ChineseCorrection)]
    import ailib.service.base_service \
        as base_service
    base_service.run(handlers)