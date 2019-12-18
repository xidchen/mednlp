#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.generator.search_generator import SearchGenerator
from ailib.utils.exception import AIServiceException
from mednlp.dialog.configuration import Constant as constant


class PostSearchGenerator(SearchGenerator):
    name = 'post_search'
    input_field = ['q', 'match_type']
    exclude_hospital = [
        '80d5876d-47e0-48b2-9def-dafaa032174b000',
        '5b79b94c-dc4d-4133-9d70-9625850b5eb5000',
        'fc689425-f2c1-4be6-b5f9-93a5823f2fdf000',
        '81c73c40-de3d-4e36-8df5-1c3f81fcc922000'
    ]
    # 搜索字段, AI输出字段
    field_trans = {
        'topic_id': 'topic_id',
        'topic_type': 'topic_type',
        'title': 'topic_title',
        'title_highlight': 'topic_title_highlight',
        'topic_content_nohtml': 'topic_content_nohtml',
        'topic_content_nohtml_highlight': 'topic_content_nohtml_highlight',
        'content': 'post_content',
        'content_highlight': 'post_content_highlight',
        'topic_nick_name': 'topic_nick_name',
        'topic_technical_title': 'topic_technical_title',
        'topic_vote_count': 'topic_vote_count',
        'topic_view_count': 'topic_view_count',
        'vote_count': 'post_vote_count',
        'view_count': 'post_view_count',
        'nick_name': 'post_nick_name',
        'help_show_type': 'help_show_type',
        'technical_title_name': 'post_technical_title_name',
        constant.GENERATOR_CARD_FLAG: constant.GENERATOR_CARD_FLAG
    }
    output_field = ['topic_id', 'topic_type', 'topic_title', 'topic_title_highlight',
                    'topic_content_nohtml', 'topic_content_nohtml_highlight', 'post_content',
                    'post_content_highlight', 'topic_nick_name', 'topic_technical_title',
                    'topic_vote_count', 'topic_view_count', 'post_vote_count', 'post_view_count',
                    'post_nick_name', 'help_show_type', 'post_technical_title_name',
                    constant.GENERATOR_CARD_FLAG, constant.GENERATOR_EXTEND_SEARCH_PARAMS,
                    constant.GENERATOR_EXTEND_QUERY_CONTENT]

    def __init__(self, cfg_path, **kwargs):
        super(PostSearchGenerator, self).__init__(cfg_path, **kwargs)

    def generate(self, input_obj, **kwargs):
        result = {}
        param = {
            'start': '0',
            'rows': '50',
            'sort': 'help_general',
            'topic_type': '1,3',
            'highlight': '1',
            'fl': ','.join(self.field_trans.keys()),
            'exclude_hospital': ','.join(self.exclude_hospital),

            # 'exclude_type': '2',
            # 'highlight_scene': '1',
            # 'exclude_post_heat_status': '1',
            # 'digest': '2',
            'block_type': '1',
            'answered': '1',
            'topic_first': '0',
            'question_status': '2,3,6,7,8',
            'lang': '1'
        }
        for field in self.input_field:
            value = input_obj.get(field)
            if not value:
                continue
            param[field] = value
        res = self.sc.query(param, 'post_service', method='get')
        if not res or res['code'] != 0:
            message = 'dept_search error'
            if not res:
                message += ' with no res'
            else:
                message += res.get('message')
            raise AIServiceException(message)
        posts = res.get('data')
        content = result.setdefault('content', [])
        fl = input_obj.get('fl', self.output_field)
        for temp in posts:
            content_item = {}
            for field, value in temp.items():
                if field not in fl and self.field_trans.get(field) not in fl:
                    continue
                if field in self.field_trans:
                    content_item[self.field_trans[field]] = value
                else:
                    content_item[field] = value
            if constant.GENERATOR_CARD_FLAG in fl:
                content_item[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_POST
            content.append(content_item)
        if constant.GENERATOR_EXTEND_SEARCH_PARAMS in fl:
            result[constant.GENERATOR_EXTEND_SEARCH_PARAMS] = {'q': param.get('q', '')}
        if constant.GENERATOR_EXTEND_QUERY_CONTENT in fl and param.get('q'):
            result[constant.GENERATOR_EXTEND_QUERY_CONTENT] = param['q']
        return result


if __name__ == '__main__':
    import global_conf
    import json
    generator = PostSearchGenerator(global_conf.cfg_path)
    input_obj = {
        "q": "头痛",
        # "fl": ["topic_title", "topic_title_highlight", "topic_id",
        #        "card_flag", constant.GENERATOR_EXTEND_SEARCH_PARAMS]
        # "fl": ['topic_title', 'topic_title_highlight', 'topic_id']
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))
