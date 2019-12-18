#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor


class PostProcessor(BasicProcessor):
    # 处理返回关键字文章的意图
    default_rows = 2

    fl = ['topic_id', 'topic_type',  # 主帖id,类型
          'title', 'title_highlight',  # 主帖标题 + 高亮
          'topic_content_nohtml', 'topic_content_nohtml_highlight',  # 主帖内容
          'topic_nick_name', 'topic_technical_title',  # 主帖昵称  # 主帖医生职称
          'topic_publish_time', 'topic_vote_count', 'topic_view_count',  # 主帖发布时间
          'content', 'content_highlight',  # 回帖内容
          # 'view_count', 'vote_count',                  # 回帖点赞数  # 回帖阅读量
          'nick_name', 'answer_desc',  # 回答者用户昵称
          'help_show_type', 'technical_title_name']  # 回答状态  # 回答者 医生职称

    def initialize(self):
        self.search_params = {
            'start': '0',
            'rows': self.default_rows,
            'highlight': '1',
            'sort': 'help_general',
            'exclude_type': '2',
            'topic_type': '1,3',
            'answered': '1',
            'topic_first': '0',
            'highlight_scene': '1',
            'match_type': '1',
            'question_status': '2,3,6,7,8'
        }

    def process(self, query, **kwargs):
        """
        http://192.168.1.46:2000/post_service?rows=3&start=0&sort=help_general&topic_type=1,3&exclude_type=2&
        highlight=1&highlight_scene=1&q=糖尿病&fl=topic_id,topic_type,title,title_highlight,topic_content_nohtml,
        topic_content_nohtml_highlight,topic_nick_name,topic_technical_title,topic_publish_time,topic_vote_count,
        topic_view_count,content,content_highlight,nick_name,answer_desc,help_show_type,technical_title_name
        :param query:
        :param kwargs:
        :return:
        """
        result = {}
        self.set_rows()
        self.set_params(query)
        # _, q_content = ai_search_common.ai_to_q_params(self.ai_result, need_area=False)
        # if not q_content and self.input_params.get('input') and self.input_params.get('input').get('q'):
        #     q_content = self.input_params.get('input').get('q')
        # 内容搜索利用用户的原始语句进行搜索
        self.search_params['q'] = self.input_params.get('input').get('q')
        self.search_params['fl'] = ','.join(self.fl)
        response = ai_search_common.query(self.search_params, self.input_params, 'post')
        if response.get('data'):
            result[constant.QUERY_KEY_POST_SEARCH] = response['data']
        result['code'] = response['code']
        result['search_params'] = self.search_params
        result['is_end'] = 1
        return result

    def set_rows(self):
        rows = 0
        rows += super(PostProcessor, self).basic_set_rows(4, default_rows=self.default_rows)
        rows += super(PostProcessor, self).basic_set_rows(5, default_rows=self.default_rows)
        self.search_params['rows'] = rows
