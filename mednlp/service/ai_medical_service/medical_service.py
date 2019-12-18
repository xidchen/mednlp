#!/usr/bin/python
#encoding=utf-8

import time
import json
import traceback
import global_conf
import mednlp.service.ai_medical_service.client.ai_client as ai_client
from mednlp.service.ai_medical_service.medical_service_control import MedicalServiceControl, logger
from mednlp.service.base_request_handler import BaseRequestHandler


control = MedicalServiceControl.create_instance()


class MedicalService(BaseRequestHandler):

    valid_obj_dict = {'hospital': ['hospital', 'json_hospital'],
                      'doctor': ['doctor', 'json_hospital'],
                      'post': ['post', 'json_post'],
                      'department': ['department'],
                      'diagnosis': ['diagnosis']}

    # 小微医助共 19 + 10 + 2 = 29 + 2 = 31种意图  无 hospitalRank和hospitalNearby
    intention_set = json.dumps(['department', 'departmentConfirm', 'departmentAmong', 'departmentSubset',
                                'hospital', 'hospitalDepartment', 'hospitalQuality', 'doctor',
                                'recentHaoyuanTime', 'doctorQuality', 'haoyuanRefresh', 'register',
                                'auto_diagnose', 'other',
                                'content', 'customerService', 'corpusGreeting', 'greeting',
                                'guide', 'keyword_doctor', 'keyword_hospital', 'keyword_department',
                                'keyword_disease', 'keyword_medicine', 'keyword_treatment', 'keyword_city',
                                'keyword_province', 'keyword_symptom', 'keyword_body_part',
                                'keyword_examination', 'keyword_medical_word'])

    ai_server = ai_client.AIClient(global_conf.cfg_path)

    def initialize(self, runtime, **kwargs):
        super(MedicalService, self).initialize(runtime, **kwargs)
        # self.control = MedicalServiceControl.create_instance(self.solr)

    def post(self):
        return self.get()

    def get(self):
        start_time = time.time() * 1000
        result = {}
        if not self.request.body:
            result['code'] = 1
            result['message'] = 'No query!'
            result['qtime'] = time.time() * 1000 - start_time
            self.write_result(result)
            return
        decoded_query = {}
        try:
            decoded_query = json.loads(self.request.body)
            result = control.control_2(decoded_query)
        except Exception as ex:
            result['message'] = traceback.format_exc()
            result['code'] = 1
            self.write_result(result, result['message'], result['code'])
        result['qtime'] = time.time() * 1000 - start_time
        self._logging(in_msg=decoded_query, out_msg=result)
        self.write_result(result)

    def _logging(self, in_msg, out_msg):
        log_info = {'in_msg': in_msg,
                    'out_msg': out_msg}
        logger.info(json.dumps(log_info, ensure_ascii=False))

if __name__ == '__main__':
    handlers = [(r'/medical_service', MedicalService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)


