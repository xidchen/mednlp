#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor

class JingdongOtherProcessor(BasicProcessor):
    """
    other处理的意图
    """

    def get_search_result(self):
        res = {}
        res['answer'] = {'text': '很抱歉，我还在学习中。您可以问我，胃不舒服挂什么科'}
        res['is_end'] = 1
        res['code'] = 0
        return res
