#!/usr/bin/python
#encoding=utf-8
import copy
import json
from mednlp.service.ai_medical_service.ai_constant import logger
from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service.basic_intention import BasicIntention


class SensitiveIntention(BasicIntention):

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            ai_search_common.greeting_build_dialogue_service(data, result)
        result['intention'] = 'sensitive'
        result['intentionDetails'] = []
        return result

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return
        logger.info("未走dialogue_service, 参数:%s" % json.dumps(self.input_params['input']))