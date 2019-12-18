#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor
from mednlp.dialog.configuration import Constant as constant

class KeywordPostProcessor(BasicProcessor):
    """
    处理返回关键字文章的意图
    """

    def get_search_result(self):
        result = {}
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, need_area=False)
        if not q_content and self.input_params.get('input') and self.input_params.get('input').get('q'):
            q_content = self.input_params.get('input').get('q')
            ai_params['q'] = q_content
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'post')
        response = ai_search_common.query(search_params, self.input_params, 'post')
        post_json_list = response.get('data', [])
        result['code'] = response['code']
        result[constant.QUERY_KEY_POST_SEARCH] = post_json_list
        # res['post_search'] = post_json_list
        result['search_params'] = ai_params
        result['is_end'] = 1
        return result
