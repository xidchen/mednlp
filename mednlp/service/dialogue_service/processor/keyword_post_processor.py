#!/usr/bin/python
#encoding=utf-8

import ai_search_common
from basic_processor import BasicProcessor

class KeywordPostProcessor(BasicProcessor):
    """
    处理返回关键字文章的意图
    """

    def get_search_result(self):
	ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)  
        search_params, fl_list = ai_search_common.get_search_params(               
                            ai_params, self.input_params, 'post')
        response = ai_search_common.query(search_params, self.input_params, 'post')
	self.response_data = response['data']	
