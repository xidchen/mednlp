#!/usr/bin/python
# encoding=utf-8

import sys
import json
import mednlp.service.ai_medical_service.ai_constant as ai_constant
from ailib.client.solr import Solr
import pdb
import global_conf
from mednlp.service.ai_medical_service import basic_common
import mednlp.service.ai_medical_service.client.ai_client as ai_client
from mednlp.dao.ai_service_dao import ai_services
import copy
import configparser
from mednlp.service.ai_medical_service.ai_search_common import check_entity, get_entity, build_dialogue_service_res
from mednlp.service.ai_medical_service.ai_constant import logger
from mednlp.utils.utils import read_config_info
from mednlp.dialog.dialogue_control import DialogueControl
from mednlp.dialog.dialogue_constant import stat_logger

control = DialogueControl()


class MedicalServiceControl(object):
    def __init__(self):
        config = read_config_info(sections=['XwyzOrganization', 'XwyzDoctorOrganization'])
        self.xwyz_organization = config['XwyzOrganization']['organization']
        self.xwyz_doctor_organization = config['XwyzDoctorOrganization']['organization']

    @staticmethod
    def create_instance():
        instance = MedicalServiceControl()
        return instance

    valid_obj_dict = {'hospital': ['hospital', 'json_hospital'],
                      'doctor': ['doctor', 'json_hospital', 'json_doctor'],
                      'post': ['post', 'json_post'],
                      'department': ['department'],
                      'diagnosis': ['diagnosis'],
                      'question': ['question']}

    # 小微医助共 19 + 10 + 2 = 29 + 2 = 31种意图  无 hospitalRank和hospitalNearby
    intention_set = json.dumps(['department', 'departmentConfirm', 'departmentAmong', 'departmentSubset',
                                'hospital', 'hospitalDepartment', 'hospitalQuality', 'doctor',
                                'recentHaoyuanTime', 'doctorQuality', 'haoyuanRefresh', 'register',
                                'auto_diagnose', 'other',
                                'content', 'customerService', 'corpusGreeting', 'greeting',
                                'guide', 'keyword_doctor', 'keyword_hospital', 'keyword_department',
                                'keyword_disease', 'keyword_medicine', 'keyword_treatment', 'keyword_city',
                                'keyword_province', 'keyword_symptom', 'keyword_body_part',
                                'keyword_examination', 'keyword_medical_word', 'sensitive'])
    accompany_intention_set = json.dumps(['patient_group'])

    ai_server = ai_client.AIClient(global_conf.cfg_path)

    def control_2(self, query_dict):
        result = {'data': {}}
        if 'source' not in query_dict:
            query_dict['source'] = 'bb'
        if query_dict.get('mode') == 'xwyz_doctor':
            query_dict['organization'] = self.xwyz_doctor_organization
        else:
            query_dict['organization'] = self.xwyz_organization
        input_params = self.get_input_params(query_dict)
        if input_params.get('input') and 'guiding' in input_params['input']:
            result['code'] = 0
            result['message'] = 'successful'
            result['data'] = {}
            result['data']['guiding'] = ai_constant.guiding_list
            return result
        res = control.control(query_dict)
        data = res.get('data')
        if data:
            stat_logger.info('###start###%s###end###' % json.dumps(
                {'input': query_dict, 'output': res}, ensure_ascii=False))
            build_dialogue_service_res(data, result['data'], input_params)
        else:
            stat_logger.info('dialogue_service无数据,###start###%s###end###' % json.dumps(
                {'input': query_dict}, ensure_ascii=False))
            result['data']['is_end'] = 1
            result['data']['isEnd'] = 1
            result['data']['intention'] = 'other'
        return result

    def control(self, query_str):
        result = {}
        """
        1.得到参数
        """
        query_dict = json.loads(query_str)  # 原输入不会被修改
        if 'source' not in query_dict:
            query_dict['source'] = 'bb'
        input_params = self.get_input_params(query_dict)
        if input_params.get('input') and 'guiding' in input_params['input']:
            result['code'] = 0
            result['message'] = 'successful'
            result['data'] = {}
            result['data']['guiding'] = ai_constant.guiding_list
            return result
        # 根据模式添加机构
        if query_dict.get('mode') == 'xwyz_doctor':
            query_dict['organization'] = self.xwyz_doctor_organization
        else:
            query_dict['organization'] = self.xwyz_organization
        auto_diagnosis = input_params.get('input', {}).get('auto_diagnosis')
        doctor_result = input_params.get('input', {}).get('doctor_result')
        # 1.识别意图
        ai_result, query_dict = self.get_ai_result(input_params, **{'auto_diagnosis': auto_diagnosis,
                                                                    'doctor_result': doctor_result,
                                                                    'query_dict': query_dict})
        accompany_intention = ai_result.get('data', {}).get('accompany_intention')
        input_params = self.get_input_params(query_dict)
        input_params['request_body'] = query_dict
        ai_result_copy = copy.deepcopy(ai_result)
        if ai_result and ai_result.get('data'):
            if input_params.get('test_intention'):
                ai_result['data']['intention'] = input_params.pop('test_intention')
            if 'intention' in ai_result['data']:
                ai_result['data'] = self.get_result(ai_result['data'], input_params)
                self.deal_accompany_intention(ai_result['data'], accompany_intention)
            result = ai_result
        else:
            result['code'] = 1
            result['message'] = 'No aiserver result!'
        return result

    def deal_accompany_intention(self, data, accompany_intention):
        if not accompany_intention:
            return
        if 'patient_group' in accompany_intention:
            request_params = {'skill': 'question_answer', 'q': '微医病友群'}
            patient_group_out_link = {
                'name': '微医病友群',
                'action': 3,
                'type': 4,
                'location': 1,
                'text': json.dumps(request_params, ensure_ascii=False)
            }
            data.setdefault('out_link', []).append(patient_group_out_link)

    def is_empty(self, ai_result):
        """
        other意图 需要纠错
        """
        result = False
        if ai_result and isinstance(ai_result, dict):
            data = ai_result.get('data')
            intention = data.get('intention')
            intentionDetails = data.get('intentionDetails', [])
            if (intention in ('other', 'greeting', 'guide', 'corpusGreeting') or (
                            intention == 'keyword' and 'treatment' in intentionDetails)):
                result = True
        return result

    def is_data_empty(self, ai_result):
        """
        数据为空的意图
        """
        flag = True
        if ai_result and ai_result.get('data'):
            if ai_result.get('data').get('valid_object'):
                obj = ai_result.get('data').get('valid_object')
                if obj and obj[0] in self.valid_obj_dict:
                    for item in self.valid_obj_dict[obj[0]]:
                        if ai_result.get('data').get(item):
                            flag = False
            data = ai_result.get('data')
            if data.get('interactive_box') or data.get('needSexAge') or data.get('departmentSymptom'):
                flag = False
            if data.get('intention') in ('customerService', ) and data.get('answer'):
                flag = False
        return flag

    def spellcheck(self, request_data):
        """
        纠错逻辑：根据q去chinese_correct进行纠错，若has_error=True或者1，说明
        纠错了，用resp['data']['correct']代替['input']['q']，变成str返回,
        上层获取到None不进行重查，获取到str进行重查
        """
        result = None
        request_params = copy.deepcopy(request_data)
        if request_params.get('input', [{}])[0].get('q'):
            params = {
                'q': request_params['input'][0]['q'],
                'mode': 1,
                'source': '789'
            }
            resp = self.ai_server.query(
                params, False, service='chinese_correct')
            if resp.get('data'):
                has_error = resp['data'].get('has_error')
                if has_error and resp['data'].get('correct'):
                    request_params['input'][0]['q'] = resp['data']['correct']
                    result = request_params
        return result

    def get_ai_result(self, input_params=None, **kwargs):
        ai_result = {}
        # 科室意图的分离
        auto_diagnosis = kwargs.get('auto_diagnosis')
        doctor_result = kwargs.get('doctor_result')
        query_dict = kwargs.get('query_dict')
        # if input_params and input_params.get('test_intention'):
        #     ai_result['data'] = {'intention': input_params.pop('test_intention'), 'intentionDetails': []}
        #     query_dict.pop('test_intention')
        #     return ai_result, query_dict
        if auto_diagnosis:
            ai_result['data'] = {'intention': 'auto_diagnose', 'intentionDetails': []}
            return ai_result, query_dict
        if doctor_result:
            ai_result['data'] = {'intention': 'departmentSubset', 'intentionDetails': []}
            dialogue = query_dict.setdefault('dialogue', {})
            dialogue['intention'] = 'departmentSubset'
            return ai_result, query_dict

        if query_dict:
            dialogue = query_dict.get('dialogue', {})
            if dialogue.get('intention'):
                ai_result['data'] = {'intention': dialogue['intention'],
                                     'intentionDetails': dialogue.get('intentionDetails', [])}
                return ai_result, query_dict

        if input_params and input_params.get('input') and input_params.get('input').get('q'):
            query = input_params['input']['q']
            mode = input_params.get('mode', 'xwyz')
            ints_ents, err_msg_intention = self.get_intention(query, mode=mode)
        if ints_ents:
            ai_result['data'] = ints_ents
        return ai_result, query_dict

    def get_input_params(self, query_dict=None):
        params = {}
        if query_dict:
            params = copy.deepcopy(query_dict)
            if params.get('input'):
                input_dict = {}
                for input_item in params.get('input'):
                    input_dict.update(input_item)
                params['input'] = input_dict
        return params

    def get_result(self, ai_result, input_params):
        intention_object = ''
        final_result = ai_result
        # 获取处理实例
        intention_object = basic_common.get_intention_instance(ai_result)
        if intention_object:
            # 获取实例处理结果
            intention_object.set_params(ai_result, input_params, self.solr)
            # pdb.set_trace()
            final_result = intention_object.get_intention_result()
        entity_params = {'entity_service': [1]}
        if final_result.get('isEnd'):
            entity_params.setdefault('entity_service', []).append(2)
        entity = get_entity(input_params.get('input', {}).get('q'), holder=self.ac)
        entity_info = check_entity(entity, **entity_params)
        if entity_info.get('exist_entity'):
            final_result['exist_entity'] = entity_info['exist_entity']
        if entity_info.get('service_list') and 'service_list' not in final_result:
            final_result['service_list'] = entity_info['service_list']
        if not (final_result.get('intention') in ('greeting', 'corpusGreeting', 'guide')):
            final_result['greeting_num'] = 0
        return final_result

    def get_intention(self, q, mode):
        params = {
            'q': str(q),
            'mode': mode,
            'intention_set': self.intention_set,
            'accompany_intention_set': self.accompany_intention_set
        }
        data = {}
        err_msg = {}
        try:
            data, err_msg = ai_services(params, 'intention_recognition', 'get')  # 已经retry3次了
        except:
            pass
        if isinstance(data, list):
            data = {}
        if data.get('intentionDetails'):
            data['intentionDetails'] = data.get('intentionDetails').split(',')
        """
        content, other, keyword_examination, keyword_medical_word转换成keyword_treatment
        """
        if (data.get('intention') in ('content', 'other')
            or (data.get('intention') == 'keyword' and data.get('intentionDetails')
                and 'examination' in data['intentionDetails'])
            or (data.get('intention') == 'keyword' and data.get('intentionDetails')
                and 'medical_word' in data['intentionDetails'])):
            data['intention'] = 'keyword'
            data['intentionDetails'] = ['treatment']
        return data, err_msg

    def _logging(self, in_msg, out_msg):
        log_info = {'in_msg': in_msg,
                    'out_msg': out_msg}
        logger.info(json.dumps(log_info, ensure_ascii=False))


if __name__ == '__main__':
    decoded_query_ai_qa = {
        "dialogue": {
        },
        "input": [
            {
                # 'q': '徐召祯有号么'
                'q': '腰椎间盘突出挂什么科',
                # "q": "头痛是挂神经内科还是外科吗",
                # "q": "头痛是挂内科下的什么科",
                # "q": "西湖怎么走",
                # "q": "头痛是挂内科吗"
                # "q": "头痛挂什么科",
                # "q": "神经内科医生"
                # "q": "失眠是挂外科还是耳鼻喉科",
                # "q": "头tong怎么办",
                # "doctor_result": 1
                # "q": "guke",
                # "q": "人工",
                # "province": "24",
                # "city": "552"
                'symptomName': '都没有'
            },
        ],
        "mode": "xwyz",
        "organization": "20e69819207b4b359f5f67a990454027",
        # "source": "c9ace68e78c345489bcf3007f9c04f6a"
    }
    control_process = MedicalServiceControl.create_instance()
    query = decoded_query_ai_qa
    result = control_process.control_2(query)
    print(json.dumps(result, indent=True, ensure_ascii=False))
    # print('aa')
    # test_medical_s()
