#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import chardet
import string
import json
import traceback
from ailib.utils.verify import check_is_exist_params
from mednlp.dialog.generator.ai_generator import AIGenerator
from ailib.utils.exception import AIServiceException
from mednlp.dialog.generator.post_search_generator import PostSearchGenerator
from mednlp.dialog.cg_constant import logger
from mednlp.dialog.cg_util import batch_query_search_plat, query_search_plat, filter_q
from mednlp.dialog.configuration import Constant as constant
from mednlp.utils.utils import get_search_plat_keys
from ailib.utils.search_util import get_parameter_split


class SentenceSimilarGenerator(AIGenerator):
    name = 'sentence_similar'
    input_field = ['q', 'start', 'match_type', 'rows', 'sort', 'organization_code', 'category']
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
        'technical_title_name': 'post_technical_title_name'
    }
    output_field = ['topic_id', 'topic_type', 'topic_title', 'topic_title_highlight',
                    'topic_content_nohtml', 'topic_content_nohtml_highlight', 'post_content',
                    'post_content_highlight', 'topic_nick_name', 'topic_technical_title',
                    'topic_vote_count', 'topic_view_count', 'post_vote_count', 'post_view_count',
                    'post_nick_name', 'help_show_type', 'post_technical_title_name',
                    constant.GENERATOR_CARD_FLAG, constant.GENERATOR_EXTEND_SEARCH_PARAMS,
                    'standard_question_id', 'standard_question']

    fq_dict = {
        'category': 'category_id'
    }

    def __init__(self, cfg_path, **kwargs):
        super(SentenceSimilarGenerator, self).__init__(cfg_path, **kwargs)
        self.post_generator = PostSearchGenerator(cfg_path, **kwargs)
        self.search_plat_dict = get_search_plat_keys(section_key='SEARCH_PLATFORM_SOLR')
        self.qa_question_key = self.search_plat_dict['CAT_AI_QUESTION_PRIMARYKEY']
        self.regex = r'[’!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~。？！]+'

    def generate(self, input_obj, **kwargs):
        result = {}
        data = {}
        params = {}
        fl = input_obj.get('fl', self.output_field)
        for field in self.input_field:
            value = input_obj.get(field)
            if not value:
                continue
            params[field] = value
        sort = input_obj.get('sort', 'post')
        if sort == 'post':
            data = self.post_sentence_similar(input_obj, params)
        elif sort == 'question':
            check_is_exist_params(input_obj, ['organization_code', 'q'])
            data = self.question_sentence_similar(input_obj, params)
        for temp in data.get('content', []):
            content_item = {}
            for field, value in temp.items():
                if field not in fl and self.field_trans.get(field) not in fl:
                    continue
                if field in self.field_trans:
                    content_item[self.field_trans[field]] = value
                else:
                    content_item[field] = value
            result.setdefault('content', []).append(content_item)
        for temp in (constant.GENERATOR_EXTEND_SEARCH_PARAMS, constant.GENERATOR_EXTEND_QUERY_CONTENT):
            if temp in fl and data.get(temp):
                result[temp] = data[temp]
        return result

    def query_sentence_similar(self, params):
        """
        :param params: 参数
        :return:
            result: {}
        """
        result = {}
        res = None
        try:
            logger.info('generator: sentence_similar,调用sentence_similarity接口，参数:%s' % json.dumps(
                params, ensure_ascii=False))
            res = self.ac.query(params, 'sentence_similarity', method='post')
        except Exception as err:
            logger.exception(traceback.format_exc())
            raise AIServiceException('sentence_similarity error')
        if not res or res['code'] != 0:
            message = 'sentence_similarity error'
            if not res:
                message += ' with no res'
            elif 'message' in res:
                message += res.get('message')
            raise AIServiceException(message)
        similar_content = res.get('data', {})
        if similar_content:
            result = similar_content
        return result

    def get_standard_question(self, fq=None):
        # 根据标准问句id, 查询标准问句
        result = {}
        params = {
            'cat': 'ai_qa_question',
            'primaryKey': self.qa_question_key,
            'start': 0,
            'rows': 10,
            'fl': 'id,question_str',
            'filter': ['is_deleted:0', 'status:0', 'is_standard:1'],
            'query': '*:*'
        }
        if fq:
            params['filter'].extend(fq)
        query_result = query_search_plat(json.dumps(params, ensure_ascii=False), self.plat_sc)
        if query_result.get('content'):
            question = query_result['content'][0]
            if question.get('id') and question.get('question_str'):
                result['standard_question_id'] = question['id']
                result['standard_question'] = question['question_str']
        return result

    def question_sentence_similar(self, input_obj, input_dict):
        """
        句子相似度
        1.得到候选问句,默认最多取200条
        2.调用相似问句
        3.若相似问句匹配,则获取对应的标准问句
        :param input_obj:
        :param input_dict:
        :return:
        """
        result = {}
        organization = input_dict['organization_code']
        q = input_dict['q']

        question_params = {
            'cat': 'ai_qa_question',
            'primaryKey': self.qa_question_key,
            'start': input_obj.get('start', 0),
            'rows': 99,
            'fl': 'id,question_str,standard_id,is_standard,is_similar',
            'filter': ['organize_code:%s' % organization, 'is_deleted:0', 'status:0'],
            'query': 'question:%s' % filter_q(q)
        }
        for param_temp, solr_param_temp in self.fq_dict.items():
            param_value = input_obj.get(param_temp, '-1')
            if param_value != '-1':
                question_params['filter'].append('%s:%s' % (solr_param_temp, get_parameter_split(param_value)))
        plat_result = batch_query_search_plat(question_params, self.plat_sc, max_rows=190)
        if not plat_result.get('content'):
            return result
        question_candidate_dict = {}    # 问句 和 对应的标准问句id字典
        for temp in plat_result['content']:
            if not temp.get('question_str'):
                continue
            if temp.get('is_standard') and int(temp['is_standard']) == 1 and temp.get('id'):
                question_candidate_dict[temp['question_str']] = temp['id']
            elif temp.get('is_similar') and int(temp['is_similar']) == 1 and temp.get('standard_id'):
                question_candidate_dict[temp['question_str']] = temp['standard_id']
        if not (q and question_candidate_dict):
            return result
        elif question_candidate_dict.get(q):
            # 完全匹配问句
            standard_question_content = self.get_standard_question(fq=['organize_code:%s' % organization,
                                                                       'id:%s' % question_candidate_dict[q]])
            if standard_question_content:
                result['content'] = [standard_question_content]
                return result
        similar_params = {
            'q': q,
            'source': 'ai_self',
            'contents': json.dumps(list(question_candidate_dict.keys()), ensure_ascii=False)
        }
        similar_data = self.query_sentence_similar(similar_params)
        if similar_data and similar_data.get('is_similarity') == 1 and similar_data.get('content')\
                and question_candidate_dict.get(similar_data['content']):
            standard_question_content = self.get_standard_question(
                fq=['organize_code:%s' % organization, 'id:%s' % question_candidate_dict[similar_data['content']]])
            if standard_question_content:
                result['content'] = [standard_question_content]
        return result

    def post_sentence_similar(self, input_obj, post_input_obj):
        """
        帖子的相似问句处理
        1.获取候选post
        2.调用相似问句,将最相似的post置顶
        :param input_obj: 原入参{}
        :param post_input_obj:  根据input_field提取后的{}
        :return:
        """
        result = {}
        rows = 3
        if post_input_obj.get('rows'):
            rows = int(post_input_obj.pop('rows'))
        post_result = self.post_generator.generate(post_input_obj)
        if post_result and post_result.get('content'):
            # 对content进行处理
            post_content = post_result['content']
            title_list = [temp['topic_title'] for temp in post_content if temp.get('topic_title')]
            if title_list:
                params = {
                    'contents': json.dumps(title_list, ensure_ascii=False),
                    'source': 'ai_self'
                }
                if input_obj.get('q'):
                    params['q'] = input_obj['q']
                similar_content = self.query_sentence_similar(params)
                if similar_content.get('content'):
                    similar_index = 0
                    for i in range(len(post_content)):
                        if similar_content['content'] == post_content[i].get('topic_title'):
                            similar_index = i
                            break
                    ai_post = post_content.pop(similar_index)
                    post_content.insert(0, ai_post)
            target_type = 1
            if post_content[0].get('topic_type') == 3:
                target_type = 3
            post_content = [temp for temp in post_content if temp.get('topic_type') == target_type][:rows]
            post_result['content'] = post_content
        if post_result:
            result = post_result
        return result


if __name__ == '__main__':
    import global_conf
    import json
    generator = SentenceSimilarGenerator(global_conf.cfg_path)
    input_obj = {
        "q": "头痛",
        "fl": ['topic_title', 'topic_title_highlight', 'topic_id', 'topic_type',
               'card_flag', constant.GENERATOR_EXTEND_SEARCH_PARAMS, 'query_content'],
        # 'match_type': 4,
        'rows': 3
    }
    input_obj = {
        "q": "提前转正？",
        "sort": "question",
        "rows": 1,
        "organization_code": "430201445ff1467d8bb2181782238191",
        "fl": ["standard_question_id", "standard_question"]
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True, ensure_ascii=False))