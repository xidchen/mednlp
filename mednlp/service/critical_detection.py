#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
critical_detection.py -- 危急值提醒

Author: renyx <renyx@guahao.com>
Create on 2019-10-30 Wednesday.
"""
import configparser
import json
import pdb
import traceback
import time
import global_conf
from ailib.utils.exception import AIServiceException
from ailib.utils.verify import check_is_exist_params
from ailib.utils.exception import ArgumentLostException
from ailib.utils.log import GLLog
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.dialog.dialogue_util import get_service_data
from ailib.client.ai_service_client import AIServiceClient

logger = GLLog('critical_detection_input_output', level='info', log_dir=global_conf.log_dir).getLogger()
ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')


class CriticalDetectionControl(object):

    def __init__(self):
        config_parser = configparser.ConfigParser()
        config_parser.optionxform = str
        config_parser.read(global_conf.cfg_path)
        self.organization = config_parser.get('GP', 'organization')

    def control(self, query_dict):
        """
        """
        result = None
        inspection = query_dict.get('inspection')
        if not inspection:
            return result
        params = {
            'organizeCode': self.organization,
            'ruleGroupName': '检验危急情况检测',
        }
        init_question_answer = []
        error_inspection = []
        for temp in inspection:
            question_temp = {}
            if 'key' not in temp or 'value' not in temp:
                error_inspection.append(temp)
                continue
            question_temp['questionCode'] = temp['key']
            question_temp['questionAnswer'] = temp['value']
            question_temp['questionAnswerUnit'] = temp.get('unit', '')
            init_question_answer.append(question_temp)
        if error_inspection:
            logger.error('error_inspection:%s' % json.dumps(error_inspection, ensure_ascii=False))
        if not init_question_answer:
            return result
        params['initQuestionAnswer'] = init_question_answer
        answer = []
        rule_result = get_service_data(json.dumps(params, ensure_ascii=False), ai_client,
                                       'rule_engine', result={}, throw=True, logger=logger)
        rule_content = rule_result.get('ruleContents', [])
        for rule_temp in rule_content:
            if rule_temp.get('isEnd') == 1 and rule_temp.get('status') == 0 and rule_temp.get('action')\
                    and rule_temp['action'].get('value'):
                answer.append(rule_temp['action']['value'])
        return answer


control = CriticalDetectionControl()


class CriticalDetection(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(CriticalDetection, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        """
        :arg
        """
        start_time = time.time() * 1000
        result = {'data': {}}
        query = self.request.body
        if not query:
            raise ArgumentLostException(fields=['request.body'])
        query_dict = json.loads(query)
        try:
            check_is_exist_params(query_dict, ['source'])
            answer = control.control(query_dict)
            if answer:
                result['data']['answer'] = answer
        except AIServiceException as ai_err:
            logger.info('入参:%s' % json.dumps({'input': query_dict}, ensure_ascii=False))
            logger.error(traceback.format_exc())
            logger.error(ai_err.message)
            raise ai_err
        except Exception as e:
            logger.info('入参:%s' % json.dumps({'input': query_dict}, ensure_ascii=False))
            logger.error(traceback.format_exc())
            raise Exception(str(e))
        result['qtime'] = time.time() * 1000 - start_time
        logger.info('入参出参:%s' % json.dumps({'input': query_dict, 'output': result}, ensure_ascii=False))
        return result


if __name__ == '__main__':
    handlers = [(r'/critical_detection', CriticalDetection, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
    # data = {
    #     "inspection": [
    #         {"key": "fastBlooGluc", "value": ["4.3"], "unit": "mmol/L"}
    #     ],
    #     "source": "aa"
    # }
    # control = CriticalDetectionControl()
    # result = control.control(data)
    # for temp in result:
    #     print(temp)
