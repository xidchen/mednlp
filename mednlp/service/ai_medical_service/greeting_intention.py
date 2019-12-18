#!/usr/bin/python
# encoding=utf-8


import json

import global_conf
from mednlp.model.similarity import TfidfSimilarity
from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service import basic_intention
from mednlp.service.ai_medical_service.ai_constant import logger


class GreetingIntention(basic_intention.BasicIntention):
    """
    寒暄处理的意图
    包含三种意图，一种guide，引导意图，返回固定格式'你好，小微目前仅支持医疗相关问题，请问有什么可以帮您吗'
    还有2中意图，一个greeting，一个customer_service，
    调用相似问句接口，有结果返回结果，没结果返回默认范围格式
    默认返回固定格式'你好，请问有什么可以帮助您？'
    """

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            ai_search_common.greeting_build_dialogue_service(data, result)
        result['intention'] = 'greeting'
        result['intentionDetails'] = []
        return result

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return
        logger.info("未走dialogue_service, 参数:%s" % json.dumps(self.input_params['input']))
        # return
        # if self.ai_result.get('intention') == 'guide':
        #     self.ai_result['answer'] = '你好，小微目前仅支持医疗相关问题，请问有什么可以帮您吗？'
        #     self.ai_result['isEnd'] = 1
        # else:
        #     threshold = 0.6
        #     answer = '你好，请问有什么可以帮助您？'
        #     query = ''
        #     if self.input_params.get('input') and self.input_params.get('input').get('q'):
        #         query = self.input_params.get('input').get('q')
        #     corpus_greeting_answer = TfidfSimilarity(
        #         global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
        #     if corpus_greeting_answer:
        #         answer = corpus_greeting_answer
        #     self.ai_result['answer'] = answer
        #     self.ai_result['isEnd'] = 1
        # self.ai_result['intention'] = 'greeting'

    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result
