#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
the generator of greeting

Author: renyx <renyx@guahao.com>
Create on 2019-02-26 TuesDay.
"""
import time
import global_conf
from ailib.client.http_client import HttpClient
from ailib.utils.exception import AIServiceException
from mednlp.dialog.generator.ai_generator import AIGenerator
from mednlp.model.similarity import TfidfSimilarity
import configparser
from ailib.client.ai_service_client import AIServiceClient
from mednlp.dialog.configuration import Constant as constant, content_generation_logger as logger
import json
import jieba
from mednlp.utils.utils import get_search_plat_keys

user_dict = global_conf.dict_path + './question_cut_word.dict'
stop_dict = global_conf.dict_path + './question_stop.dict'
jieba.load_userdict(user_dict)
stop_words = [line.strip() for line in open(stop_dict, 'r', encoding='utf-8').readlines()]


class GreetingGenerator(AIGenerator):
    name = 'greeting_search'
    input_field = ['q', 'sort', 'customer_service_category', 'organization_code']
    output_field = ['general_answer', 'match_type', 'question', 'question_type', 'standard_question_id',
                    constant.GENERATOR_CARD_FLAG]

    def __init__(self, cfg_path, **kwargs):
        super(GreetingGenerator, self).__init__(cfg_path, **kwargs)
        self.plat_sc = AIServiceClient(cfg_path, 'SEARCH_PLATFORM_SOLR')
        self.kf = HttpClient(global_conf.cfg_path, 'WangXunKeFuService')
        self.search_plat_dict = get_search_plat_keys(section_key='SEARCH_PLATFORM_SOLR')
        self.ai_question_sentence_key = self.search_plat_dict['CAT_QUESTION_SENTENCE_PRIMARYKEY']
        self.ai_recommended_question_key = self.search_plat_dict['CAT_RECOMMENDED_QUESTION_PRIMARYKEY']

    def generate(self, input_obj, **kwargs):
        result = {}
        for temp in ['q', 'sort']:
            if not input_obj.get(temp):
                message = 'no parameter: %s' % temp
                raise AIServiceException(message)
        query = input_obj['q']
        sort = input_obj['sort']
        fl = input_obj.get('fl', self.output_field)
        # 默认不匹配语料库数据
        query_info = {'match_type': 2}
        logger.info('greeting_generator, 入参:%s\n' % json.dumps(input_obj))
        if sort == 'guide':
            query_info['general_answer'] = '你好，小微目前仅支持医疗相关问题，请问有什么可以帮您吗？'
        elif sort == 'greeting':
            threshold = 0.6
            answer_temp = '你好，请问有什么可以帮助您？'
            corpus_greeting_answer = TfidfSimilarity(
                global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
            if corpus_greeting_answer:
                answer_temp = corpus_greeting_answer
                query_info['match_type'] = 1
            query_info['general_answer'] = answer_temp
        elif sort == 'customer_service':
            # 相似问句有结果则返回、无结果仍走网讯
            similar_result = self.get_similar_answer(query, input_obj)
            if similar_result.get('general_answer'):
                query_info['general_answer'] = similar_result['general_answer']
                logger.info('greeting_generator, get similarity_faq result')
                if similar_result.get('standard_question_id'):
                    query_info['standard_question_id'] = similar_result['standard_question_id']
                if similar_result.get('content'):
                    query_info['content'] = similar_result['content']
                    query_info[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_QUESTION
            # 若无相似问句, 去solr里获取
            if not query_info.get('general_answer'):
                question_result = self.get_question(query, input_obj)
                if question_result.get('slot'):
                    result['slot'] = question_result['slot']
                    result['general_answer'] = question_result['general_answer']
                    return result
                if question_result.get('content'):
                    # 只有1个问句,则给出答案
                    if len(question_result['content']) == 1:
                        logger.info('相似问句只有1个,直接给出对应回复')
                        similar_result = self.get_similar_answer(
                            question_result['content'][0]['question'], input_obj)
                        if similar_result.get('general_answer'):
                            query_info['general_answer'] = similar_result['general_answer']
                            if similar_result.get('standard_question_id'):
                                query_info['standard_question_id'] = similar_result['standard_question_id']
                            if similar_result.get('content'):
                                query_info['content'] = similar_result['content']
                                query_info[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_QUESTION
                    else:
                        query_info['content'] = question_result['content']
                        query_info[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_QUESTION
            if (not query_info.get('general_answer')) and (not query_info.get('content')):
                query_info['general_answer'] = '''对不起，微医君没能查到匹配的内容，建议您可以点击“呼叫人工”获取人工客服的帮助，若非人工客服服务时间点击“我要留言”反馈您的问题，客服看到后会给您回复。 感谢您的理解与支持！'''
                logger.info('generator:greeting, customerService兜底问句\n')
            query_info['match_type'] = 1
        if query_info.get('content'):
            field_trans = {}
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

        for field, value in query_info.items():
            if field not in fl or field not in ['match_type', 'general_answer',
                                                constant.GENERATOR_CARD_FLAG, 'standard_question_id']:
                continue
            result[field] = value
        logger.info('generator:greeting,返回结果:%s\n' % json.dumps(result))
        return result

    def get_similar_answer(self, query, input_obj):
        # 走相似问句
        result = {}
        similar_params = {
            'source': 'content_generation',
            'q': query,
            'rows': 1,
            'fl': 'similarity_ask,answer,score,ask_id',
            'level': 1
        }
        similar_res = self.ac.query(similar_params, 'similarity_faq')
        logger.info('greeting_generator, similarity_faq params:%s, 结果:%s' % (
            json.dumps(similar_params), json.dumps(similar_res)))
        if similar_res and similar_res.get('code') == 0 and similar_res.get('data'):
            data = similar_res['data']
            result['general_answer'] = data[0].get('answer')
            ask_id = data[0].get('ask_id')
            if ask_id is not None:
                result['standard_question_id'] = ask_id
            if ask_id is not None and input_obj.get('organization_code'):
                recommended_params = {
                    'cat': 'ai_recommend_question',
                    'primaryKey': self.ai_recommended_question_key,
                    'start': 0,
                    'rows': 12,
                    'fl': 'score,id,question',
                    'filter': ['status:1', 'standard_question_id:%s' % ask_id],
                    'sort': {'score': 'desc', 'id': 'asc'},
                    'query': '*:*'
                }
                recommended_params['filter'].append('organize_code:%s' % input_obj['organization_code'])
                res = self.plat_sc.query(json.dumps(recommended_params), 'search/1.0', method='post', timeout=0.3)
                logger.info('greeting_generator, get recommend_question, recommended_params:%s,res:%s' % (
                    json.dumps(recommended_params), json.dumps(res)))
                if res and res['code'] == 200 and res.get('data'):
                    content = [{'question': temp['question'], 'question_type': constant.question_type.get(
                        'config_recommend')} for temp in res.get('data') if temp.get('question')]
                    if content:
                        result['content'] = content
                        return result
        return result

    def get_question(self, query, input_obj):
        # 获取槽位和相似问句
        """
        1.从标准句的keyword构建slot
        2.句子根据标准句的score排序
        3.获取标准句的相似句
        """
        result = {}
        cut_words = jieba.cut(query)
        query_word = list(set([cut_temp for cut_temp in cut_words if len(
            cut_temp) > 1 and cut_temp not in stop_words]))
        if not query_word:
            return result
        max_rows = 12
        question_params = {
            'cat': 'ai_question_sentence',
            'primaryKey': self.ai_question_sentence_key,
            'start': 0,
            'rows': max_rows,
            'fl': 'score,id,question,is_standard,keyword,is_similar,standard_id',
            'filter': ['status:0', '-question_str:%s' % query, 'is_standard:1'],
            'sort': {'score': 'desc', 'id': 'asc'},
            'query': '*:*'
        }
        customer_service_category = input_obj.get('customer_service_category', [])
        customer_service_category = list(map(lambda x: x[:-2] if x[-2:] == '相关' else x, customer_service_category))
        if not customer_service_category:
            # 需要slot
            question_params['query'] = 'keyword: (%s)' % ' AND '.join(query_word)
            question_params['facet'] = {'facetFields': ['keyword'], 'facetMincount': 1,
                                        'facetLimit': '8'}
            res = self.plat_sc.query(json.dumps(question_params), 'search/1.0', method='post', timeout=0.3)
            logger.info('greeting_generator, no customer_service_keyword, question_params:%s,res:%s' % (
                json.dumps(question_params), json.dumps(res)))
            if not res or res['code'] != 200:
                message = 'ai_question_sentence error'
                if not res:
                    message += ' with no res'
                else:
                    message += res.get('msg', '')
                raise AIServiceException(message)
            # 若标准问句小于等于max_rows条,直接返回
            if res.get('total') and res['total'] <= max_rows and res['total'] > 0:
                content = [{'question': temp['question'], 'question_type': constant.question_type.get(
                    'related')} for temp in res.get('data') if temp.get('question')]
                if content:
                    result['content'] = content
                    return result
            facet = res.get('facetResult', [])
            facet_list = None
            for facet_temp in facet:
                if facet_temp.get('field') == 'keyword' and facet_temp.get('valueCountMap'):
                    facet_list = list(facet_temp.get('valueCountMap').keys())
                    break
            if facet_list:
                facet_list = [temp for temp in facet_list if temp not in query_word][:4]
                if len(facet_list) > 1:
                    result['general_answer'] = '请选择<em>%s</em>相关的问题' % ''.join(query_word[:2])
                    result['slot'] = self.build_question_slot(facet_list)
                    return result
        else:
            # 得到score 最高的标准问句, 返回标准问句的相似问句
            query_format = 'keyword: (%s) AND (*:* OR keyword:(%s)^10)'
            question_params['query'] = query_format % (' AND '.join(query_word),
                                                       ' OR '.join(customer_service_category))
            res = self.plat_sc.query(json.dumps(question_params), 'search/1.0', method='post', timeout=0.3)
            logger.info(
                'greeting_generator, has customer_service_keyword, question_params:%s, result:%s' % (
                    json.dumps(question_params), json.dumps(res)))
            if res and res.get('code') == 200 and res.get('data'):
                content = [{'question': temp['question'], 'question_type': constant.question_type.get(
                    'related')} for temp in res.get('data', []) if temp.get('question')]
                if content:
                    result['content'] = content
        return result

    def build_question_slot(self, slot):
        result = []
        for temp in slot:
            slot_dict = {
                'answerCode': 'customer_service_category',
                'options': [
                    {
                        "conflict": [],
                        'field': 'customer_service_category',
                        'preDesc': '',
                        'type': 'single',
                        'content': '%s相关' % temp,
                        'defaultContent': '',
                        'desc': '',
                        'defaultDesc': '',
                        'isSpecialOption': 0,
                        'validator': '1'
                    }
                ]
            }
            result.append(slot_dict)
        return result


if __name__ == '__main__':
    import global_conf
    import json

    generator = GreetingGenerator(global_conf.cfg_path)
    input_obj = {
        "q": "如何修改账号密码",
        "sort": "customer_service",
        "organization_code": '09608b68d3ed48af998b8139b54fd069',
        # 'customer_service_category': ['健康币相关'],
        # "sort": "guide"
        # "sort": "customer_service"
        "fl": ['general_answer', 'match_type', 'question', 'card_flag', 'question_type', 'standard_question_id']
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))
