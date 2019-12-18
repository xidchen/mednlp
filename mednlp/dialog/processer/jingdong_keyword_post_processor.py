#!/usr/bin/python
#encoding=utf-8

import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.basic_processor import BasicProcessor

class JingdongKeywordPostProcessor(BasicProcessor):
    """
    处理返回关键字文章的意图
    """

    def get_search_result(self):
        post_search_params = {'rows': '3',
                      'start': '0',
                      'sort': 'help_general',
                      'topic_type': '1',
                      'exclude_type': '2',
                      'highlight': '1',
                      'highlight_scene': '1'
                    }
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        if not q_content and self.input_params.get('input') and self.input_params.get('input').get('q'):
            q_content = self.input_params.get('input').get('q')
            ai_params['q'] = q_content
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'post', [], post_search_params)
        response = ai_search_common.query(search_params, self.input_params, 'post')
        post_obj_list = ai_search_common.get_post_obj(response, self.ai_result, fl_list)
        json_obj_list = []
        if len(post_obj_list) > 0:
            json_obj_list = ai_search_common.get_post_json_obj(response, self.ai_result, fl_list)
        answer = ai_search_common.process_jingong_post(json_obj_list)
        res = {}
        res['code'] = response['code']
        res['message'] = response['message']
        res['answer'] = answer
        res['search_params'] = ai_params
        res['is_end'] = 1
        return res
