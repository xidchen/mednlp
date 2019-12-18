#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import global_conf
from mednlp.dialog.active_2 import Active
from ailib.utils.exception import ArgumentLostException
from ailib.client.ai_service_client import AIServiceClient
from mednlp.utils.utils import get_search_plat_keys
from mednlp.dialog.builder.answer_builder import AnswerSkillRuleBuilder
from mednlp.dialog.configuration import Constant as constant, get_organization_dict


class QuestionAnswerSkill(object):
    """
    固定问答对技能
    """
    def __init__(self):
        self.plat_sc = AIServiceClient(global_conf.cfg_path, 'SEARCH_PLATFORM_SOLR')
        self.search_plat_dict = get_search_plat_keys(section_key='SEARCH_PLATFORM_SOLR')
        self.qa_question_key = self.search_plat_dict['CAT_AI_QUESTION_PRIMARYKEY']
        organization_dict = get_organization_dict()
        self.question_config_organization = organization_dict['question_config_organization']
        self.active = Active()

    def process(self):
        result = {'isEnd': 1, 'dialogue': {}}
        # 请求接口获取问句的答案
        answer = self.query_search_plat()
        self.active.set('answer_builder', AnswerSkillRuleBuilder())
        self.active.builder_skill({'answer': [{'text': answer}]}, result)
        return {'data': result}

    @classmethod
    def generate(cls, environment):
        result = cls()
        result.environment = environment
        result.dialogue = result.environment.get('dialogue', default={})
        return result

    def query_search_plat(self):
        input_dict = self.environment.get('input_dict')
        organization = self.environment.get('organization')
        if self.environment.get('mode') in constant.VALUE_MODE_MENHU:
            organization = self.question_config_organization
        if not input_dict.get('q'):
            # 非法请求
            raise ArgumentLostException(['q'])
        params = {
            'cat': 'ai_qa_question',
            'primaryKey': self.qa_question_key,
            'start': 0,
            'rows': 1,
            'fl': 'answer',
            'filter': ['question_str:%s' % str(input_dict['q']).strip(), 'is_deleted:0', 'status:0'],
            'query': '*:*'
        }
        if organization:
            params['filter'].append('organize_code:%s' % organization)
        res = self.plat_sc.query(json.dumps(params, ensure_ascii=False), 'search/1.0', method='post', timeout=0.3)
        answer = None
        if res and res.get('code') == constant.REQUEST_OK and res.get('data'):
            answer = res.get('data')[0].get('answer')
        if not answer:
            answer = '你好，小微目前仅支持医疗相关问题，请问有什么可以帮您吗？'
        return answer
