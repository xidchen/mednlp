#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
full_code_config_strategy.py -- the strategy of full field config by code

Author: maogy <maogy@guahao.com>
Create on 2019-01-19 Saturday.
"""


import json
import copy
import traceback
import global_conf
from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.exception import AIServiceException


class FullCodeConfigStrategy(object):

    def __init__(self, conf, **kwargs):
        self.conf = conf
        self.execute = conf['execute']
        # self.cgc = AIServiceClient(global_conf.cfg_path, 'AIService', port=5401)
        # self.cgc = AIServiceClient(global_conf.cfg_path, 'AIService', port=12000)
        self.cgc = AIServiceClient(global_conf.cfg_path, 'AIService')

    def run(self, input_obj, **kwargs):
        result = {}
        try:
            for exe in self.execute:
                self._run_exe(exe, input_obj, result, **kwargs)
                if result.get('slot'):
                    return result
        except Exception:
            traceback.print_exc()
            raise Exception(traceback.format_exc())
        # print('result:'+str(result))
        return result

    def _run_exe(self, exe, input_obj, result, **kwargs):
        if exe.get('processer'):
            return exe['processer'](input_obj, result)
        output_field = exe.get('output', [])
        raise_exception = kwargs.get('raise_exception', True)
        # 1: 有slot直接return; 2:返回全部
        return_type = kwargs.get('return_type', 1)
        global_need_output_field = []
        for field in output_field:
            if field in input_obj or field in result:
                continue
            global_need_output_field.append(field)
        card_field = exe.get('output_card', [])
        need_output_field = copy.deepcopy(global_need_output_field)
        need_output_field.extend(card_field)
        if not need_output_field:
            return
        input_param = {'fl': need_output_field}
        for field in exe['input']:
            if field in input_obj:
                input_param[field] = input_obj[field]
            elif field in result:
                input_param[field] = result[field]
        params = {'source': '789', 'generator': exe['generator'],
                  'method': 'generate', 'parameter': input_param}
        params_str = json.dumps(params, ensure_ascii=False)
        res = self.cgc.query(params_str, 'content_generation')
        if not res or not res['data']:
            if raise_exception:
                raise AIServiceException('query content_generation error!%s' % params_str)
        data = res.get('data', {})
        if data.get('slot'):
            result['slot'] = data['slot']
            if return_type == 1:
                return

        content = data.get('content', [])
        for field in global_need_output_field:
            if content and field in content[0]:
                result[field] = content[0][field]
            if field not in result and field in data:
                result[field] = data[field]
        if card_field and content:
            result.setdefault('card', []).extend(content)

        if self.conf.get('card_type'):
            result['card_type'] = self.conf['card_type']
        # print(result)
        return

            
