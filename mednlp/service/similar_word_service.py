#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
similar_word_service.py -- 用户输入词与标准词库的相似性计算，并返回相似度排名前n个标准词
Author : raogj
Create on 2019.11.26
"""

import json
import ujson
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from tornado import web, ioloop, httpserver
from tornado.options import define, options

from mednlp.kg.similar_word import SimilarWordModel

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

similar_word_model = SimilarWordModel()

# 多线程执行
EXECUTOR = ThreadPoolExecutor(max_workers=10)
define("port", default=9101, help="run on the given port", type=int)

LABEL_FORMAT = """<label STYLE="font-size: small; font-family:'sans-serif'; 
                white-space: pre-wrap; wrap=on"><b>%s</b></label>"""


class Htmllize(object):
    @staticmethod
    def html_text(s):
        html = LABEL_FORMAT % s
        html += '<br>'
        return html

    @staticmethod
    def json_string(dic):
        return ujson.dumps(dic, ensure_ascii=False)


htmlize = Htmllize()


class SimilarWord(web.RequestHandler):

    def initialize(self, **kwargs):
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')

    @web.asynchronous
    def asynchronous_get(self, default=None, **kwargs):
        """异步请求，子类在get方法中调用此方法，然后实现_get(self)方法
        """
        def callback(future):
            ex = future.exception()
            if ex is None:
                self.write_result(future.result())
            else:
                message = str(ex).replace('\n', '<br>' + ' ' * 8)
                message = message.replace('"', '&quot;')
                if isinstance(ex, Exception):
                    code = 1
                    message = 'not correct argument!'
                    self.write_result(default, message, code=code)
                else:
                    self.write_result(default, message, code=1)
            self.finish()

        return_future = EXECUTOR.submit(self.nomalization_get, **kwargs)
        return_future.add_done_callback(
            lambda future: ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))

    def nomalization_get(self, **kwargs):
        return self._get(**kwargs)

    # write result to reaponse
    def write_result(self, result, message='successful', code=0):
        if result is None:
            result = {'totalCount': 0, 'data': []}
        if isinstance(result, dict):
            result['code'] = code
            result['message'] = message
        buf = htmlize.json_string(result)
        self.write(buf)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        query_str = self.request.body
        if query_str:
            query = json.loads(query_str, encoding='utf-8')
            q = query.get('q')
            source = query.get('source')
            word_type = query.get('word_type')
            top_n = query.get('top_n', 10)
        else:
            q = self.get_argument('q')
            source = self.get_argument('source')
            word_type = self.get_argument('word_type')
            top_n = self.get_argument('top_n', 10)
        if not source:
            logging.error('lost source')
        if not q:
            logging.error('lost q')
        if not word_type:
            logging.error('lost word_typ')
        if top_n:
            if type(top_n) is str:
                if not top_n.isdigit():
                    logging.error('top_n should be a number')
                top_n = int(top_n)
        result = {}
        similar_result = similar_word_model.similar_calculation(q, word_type, top_n=top_n)
        result['data'] = similar_result
        return result


def run(handlers):
    options.parse_command_line()
    app = web.Application(handlers=handlers)
    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    handlers = [(r'/similar_word', SimilarWord)]
    run(handlers)
