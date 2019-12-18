#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import pdb
import traceback
import global_conf
from ailib.utils.verify import check_is_exist_params
from ailib.utils.search_util import get_parameter_split
from mednlp.dialog.generator.search_generator import SearchGenerator
from ailib.utils.exception import AIServiceException
from mednlp.dialog.cg_constant import logger, REQUEST_IS_OK
from mednlp.utils.utils import get_search_plat_keys


class QuestionAnswerGenerator(SearchGenerator):
    """
    获取标准问句/相似问句的回答
    sort:
        query:普通的查询，排序优先级：相关度desc，有特定场景的靠前，id asc
    """
    name = 'question_answer'
    input_field = ['question_id', 'start', 'rows', 'sort', 'scene']
    output_field = ['answer', 'standard_question_id']

    def __init__(self, cfg_path, **kwargs):
        super(QuestionAnswerGenerator, self).__init__(cfg_path, **kwargs)
        self.search_plat_dict = get_search_plat_keys(section_key='SEARCH_PLATFORM_SOLR')
        self.qa_key = self.search_plat_dict['CAT_QUESTION_ANSWER_PRIMARYKEY']
        self.fq_dict = {

        }

    def generate(self, input_obj, **kwargs):
        result = {}
        query_info = {}
        check_is_exist_params(input_obj, ['sort'])
        sort = input_obj['sort']
        fl = input_obj.get('fl', self.output_field)
        if sort not in ('query',):
            raise AIServiceException()
        params = {
            'cat': 'ai_question_answer',
            'primaryKey': self.qa_key,
            'start': int(input_obj.get('start', 0)),
            'rows': int(input_obj.get('rows', 1)),
            'fl': 'id,question_id,answer,scene_id,unlimit',
            'filter': ['status:1'],
            'sort': {'score': 'desc', 'id': 'asc'},
            'query': '*:*'
        }
        for param_temp, solr_param_temp in self.fq_dict.items():
            # scene用了默认值-1
            param_value = input_obj.get(param_temp, '-2')
            if param_value != '-2':
                params['filter'].append('%s:%s' % (solr_param_temp, get_parameter_split(param_value)))
        if input_obj.get('scene'):
            # 不限场景时scene=-1,solr查询做转义
            scene = '%s,-1' % str(input_obj['scene'])
            scene = list(set(scene.split(',')))
            for index, scene_temp in enumerate(scene):
                if str(scene_temp) == '-1':
                    scene[index] = '\"-1\"'
            params['filter'].append('scene_id:(%s)' % ' OR '.join(scene))
        if sort in ('query',):
            check_is_exist_params(input_obj, ['question_id'])
            # 获取标准问句和相似问句匹配上的回答,增加平行答案的筛选
            question_id_str = ' OR '.join(input_obj['question_id'].split(','))
            params['filter'].append(
                'question_id:(%s) OR similar_question_id:(%s)' % (question_id_str, question_id_str))
        if 'query' == sort:
            # 不限场景置底，平行答案随机， 利用RandomSortField进行随机排序
            cur_time = 'random_%s' % int(time.time())
            params['sort'] = {'unlimit': 'desc', cur_time: 'desc'}
        params_dumps = json.dumps(params, ensure_ascii=False)
        logger.info('ai_question_answer search参数:%s' % params_dumps)
        res = None
        try:
            res = self.plat_sc.query(params_dumps, 'search/1.0', method='post', timeout=0.3)
        except Exception as err:
            logger.exception(traceback.format_exc())
        if res and res.get('code') == REQUEST_IS_OK:
            query_info['content'] = res.get('data', [])
        elif res:
            logger.exception('ai_question_answer search异常, 结果:%s' % json.dumps(res, ensure_ascii=False))
        field_trans = {
            'question_id': 'standard_question_id'
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
    generator = QuestionAnswerGenerator(global_conf.cfg_path)
    input_obj = {
        'question_id': '43241', # 36,-1 # 47,2  43241
        'sort': 'query',
        'start': 0,
        'rows': 4,
        'scene': '21,22',
        'fl': ['answer', 'standard_question_id']
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True, ensure_ascii=False))

