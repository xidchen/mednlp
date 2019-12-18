#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pdb
import traceback
import global_conf
from ailib.utils.verify import check_is_exist_params
from ailib.utils.search_util import get_parameter_split
from mednlp.dialog.generator.search_generator import SearchGenerator
from ailib.utils.exception import AIServiceException
from mednlp.dialog.cg_constant import logger, REQUEST_IS_OK
from mednlp.utils.utils import get_search_plat_keys


class RecommendQuestionGenerator(SearchGenerator):
    """
    获取推荐问句列表
    sort:
        query:普通的查询，排序优先级：相关度desc，id asc
    """
    name = 'recommend_question'
    input_field = ['question_id', 'start', 'rows', 'sort', 'organize_code']
    output_field = ['recommend_question_id', 'recommend_question']

    def __init__(self, cfg_path, **kwargs):
        super(RecommendQuestionGenerator, self).__init__(cfg_path, **kwargs)
        self.search_plat_dict = get_search_plat_keys(section_key='SEARCH_PLATFORM_SOLR')
        self.recommend_question_key = self.search_plat_dict['CAT_RECOMMENDED_QUESTION_PRIMARYKEY']
        self.fq_dict = {
            'question_id': 'standard_question_id',
            'organize_code': 'organize_code'
        }

    def generate(self, input_obj, **kwargs):
        result = {}
        query_info = {}
        check_is_exist_params(input_obj, ['sort'])
        sort = input_obj['sort']
        fl = input_obj.get('fl', self.output_field)
        if sort not in ('query', ):
            raise AIServiceException()
        params = {
            'cat': 'ai_recommend_question',
            'primaryKey': self.recommend_question_key,
            'start': int(input_obj.get('start', 0)),
            'rows': int(input_obj.get('rows', 1)),
            'fl': 'id,question,recommend_question_id',
            'filter': ['status:1'],
            'sort': {'score': 'desc', 'id': 'asc'},
            'query': '*:*'
        }
        for param_temp, solr_param_temp in self.fq_dict.items():
            param_value = input_obj.get(param_temp, '-1')
            if param_value != '-1':
                params['filter'].append('%s:%s' % (solr_param_temp, get_parameter_split(param_value)))
        if 'query' == sort:
            check_is_exist_params(input_obj, ['question_id'])
        params_dumps = json.dumps(params, ensure_ascii=False)
        logger.info('ai_recommend_question search参数:%s' % params_dumps)
        res = None
        try:
            res = self.plat_sc.query(params_dumps, 'search/1.0', method='post', timeout=0.3)
        except Exception as err:
            logger.exception(traceback.format_exc())
        if res and res.get('code') == REQUEST_IS_OK:
            query_info['content'] = res.get('data', [])
        elif res:
            logger.exception('ai_recommend_question search异常, 结果:%s' % json.dumps(res, ensure_ascii=False))
        field_trans = {
            'question': 'recommend_question'
        }
        if query_info.get('content'):
            content = result.setdefault('content', [])
            for temp in query_info['content']:
                content_item = {}
                for field, value in temp.items():
                    if field not in fl and field_trans.get(field) not in fl:
                        continue
                    if field in field_trans:
                        content_item[field_trans[field]] = value
                    else:
                        content_item[field] = value
                content.append(content_item)
        logger.info('%s,返回结果:%s\n' % (self.name, json.dumps(result, ensure_ascii=False)))
        return result


if __name__ == '__main__':
    generator = RecommendQuestionGenerator(global_conf.cfg_path)
    input_obj = {
        'sort': 'query',
        'question_id': '34,115',
        'fl': ['recommend_question_id', 'recommend_question'],
        'rows': 3
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True, ensure_ascii=False))

