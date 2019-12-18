#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnosed_referral_remind.py -- 诊断转诊提醒

Author: renyx <renyx@guahao.com>
Create on 2019-10-30 Wednesday.
"""
import json
import pdb
import traceback
import time
import re
import global_conf
from ailib.utils.exception import AIServiceException
from ailib.utils.verify import check_is_exist_params
from ailib.utils.exception import ArgumentLostException
from ailib.utils.log import GLLog
from mednlp.service.base_request_handler import BaseRequestHandler
from ailib.client.ai_service_client import AIServiceClient

logger = GLLog('diagnosed_referral_remind_input_output', level='info', log_dir=global_conf.log_dir).getLogger()
ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')


class DiagnosedReferralRemindControl(object):
    answer_dict = {
        '高血压': """诊断高血压后，由于需要做一些基础检查项目进行风险评估，基于风险评估结果进行用药方案决策，考虑村卫生室未开展相关项目，故建议转诊至对应医院进一步就诊。\n<color>当收缩压小于160，舒张压小于100，且无心梗、糖尿病、心衰、肾病、COPD等合并症时，请考虑转入乡镇卫生院；</color>\n<color>其他情况请转入县医院门诊心内科进一步就诊。</color>""",
        '糖尿病': '诊断糖尿病后，由于需要做一些基础检查项目进行风险评估，基于风险评估结果进行用药方案决策，考虑村卫生室未开展相关项目，故建议转诊至对应医院进一步就诊。'
    }
    icd2_label = 'a7bSzM9Q'
    hypertension_pattern = r'^I10.*'    # 高血压
    exclude_hypertension_icd2 = ('I10.x00x009', 'I10.x00x015', 'I10.x00x016', 'I10.x00x017', 'I10.x01')
    diabetes_pattern = r'^(E11|E14).*'  # 糖尿病

    def control(self, query_dict):
        """
        转诊规则：无高血压标签、诊断为高血压、医院等级为村医则提醒，糖尿病同理
        """
        result = None
        hospital_level = int(query_dict['hospital_level'])
        if hospital_level != 1:
            return result
        disease = self.filter_disease(query_dict['disease'])  # 诊断疾病
        disease_tag = query_dict['disease_tag']  # 疾病标签
        answer = []
        for temp in ('糖尿病', '高血压'):
            if temp not in disease_tag and temp in disease:
                answer.append(self.answer_dict[temp])
        if not answer:
            return result
        return answer

    def filter_disease(self, disease):
        result = []
        params = {
            "name": disease,
            "ef":  ["name", "label"],
            "label": [self.icd2_label],
            "label_field": [self.icd2_label],
            "type": ["disease"]
        }
        param_str = json.dumps(params, ensure_ascii=False)
        res = ai_client.query(param_str, 'entity_service')
        if res.get('code') and res.get('code') != 0:
            logger.error('entity_service请求异常,params:%s' % param_str)
            return result
        for temp in res.get('data', {}).get('entity'):
            label = temp.get('label', {}).get(self.icd2_label, '')
            if re.match(self.diabetes_pattern, label):
                result.append('糖尿病')
            elif re.match(self.hypertension_pattern, label) and label not in self.exclude_hypertension_icd2:
                result.append('高血压')
        return result


control = DiagnosedReferralRemindControl()


class DiagnosedReferralRemind(BaseRequestHandler):

    def initialize(self, runtime=None, **kwargs):
        super(DiagnosedReferralRemind, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        """
        :arg
            source:int
            tag:[]    标签
            disease:[]    诊断结果
            hospital_level:int  医院等级 村医=1
        """
        start_time = time.time() * 1000
        result = {'data': {}}
        query = self.request.body
        if not query:
            raise ArgumentLostException(fields=['request.body'])
        query_dict = json.loads(query)
        try:
            check_is_exist_params(query_dict, ['source', 'disease_tag', 'disease', 'hospital_level'])
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
    handlers = [(r'/diagnosed_referral_remind', DiagnosedReferralRemind, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
    # data = {
    #     "hospital_level": 1,
    #     "disease_tag": ["糖尿病"],
    #     "disease": ["临界性高血压", "青春期高血压"],
    #     "source": 11
    # }
    # control = DiagnosedReferralRemindControl()
    # result = control.control(data)
    # print(result)
