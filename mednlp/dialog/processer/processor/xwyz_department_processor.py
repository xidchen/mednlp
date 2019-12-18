# !/usr/bin/env python
# encoding=utf-8

from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
import json
import copy
from mednlp.dialog.dialogue_constant import Constant as constant, ai_sc, logger, search_sc
import mednlp.dialog.processer.common as common
import mednlp.dialog.processer.ai_search_common as ai_search_common
from mednlp.dialog.dialogue_util import fill_department_classify_params, is_valid_auto_diagnose
from mednlp.dialog.general_util import get_service_data
from mednlp.utils.utils import transform_dict_data


class XwyzDepartmentProcessor(BasicProcessor):
    department_classify_dict = {'age': 'age',
                                'sex': 'sex',
                                'symptomName': 'symptom'}

    std_dept_transform_dict = {
        'common_disease': 'common_disease',
        'introduction': 'introduction',
        'department_uuid': 'std_dept_id'}

    def __init__(self):
        super(XwyzDepartmentProcessor, self).__init__()

    def process_2(self, environment):
        """
        1.调用科室分类生成器获取slot、content信息,若有slot,则直接return
        2.content信息需添加标准科室属性common_disease、introduction、department_uuid
        3.q是否能自诊
        """
        result = {'is_end': 1}
        classify_dept_params = {
            'source': 188,
            'generator': 'department_classify_interactive',
            'method': 'generate',
            'parameter': {
                'q': environment.input_dict['q'],
                'level': 4,
                'return_type': 1,
                'fl': ['department_id', 'department_name', 'accuracy', 'slot']
            }
        }
        fill_department_classify_params(environment.input_dict, classify_dept_params['parameter'])
        res = get_service_data(json.dumps(classify_dept_params, ensure_ascii=False), ai_sc,
                               'content_generation', throw=True, logger=logger)
        if res.get('slot'):
            result['is_end'] = 0
            result['slot'] = res['slot']
            return result
        content = res.get('content', [])
        environment.add_entity(constant.ENTITY_DEPARTMENT_CLASSIFY, [transform_dict_data({}, temp, {
            'id': 'department_id', 'name': 'department_name'}) for temp in content])
        for temp in content:
            std_dept_id = temp.pop('department_id', None)
            if not std_dept_id:
                continue
            std_dept_params = {'std_dept': std_dept_id, 'rows': 1, 'fl': 'common_disease, introduction, std_dept_id'}
            res = get_service_data(std_dept_params, search_sc, 'std_department', method='get', data_key='docs')
            if res:
                transform_dict_data(temp, res[0], {'common_disease': 'common_disease', 'introduction': 'introduction',
                                                   'department_uuid': 'std_dept_id'})
        if content:
            card = [{'type': constant.CARD_FLAG_DICT['department'], 'content': content}]
            result['card'] = card
        # 探测自诊
        auto_diagnose_params = {'input': [], 'source': 'bb'}
        for key_temp in ('sex', 'age'):
            value_temp = environment.input_dict.get(key_temp)
            if value_temp is not None:
                auto_diagnose_params['input'].append({'key': key_temp, 'value': [value_temp]})
        auto_diagnose_params['input'].append({'key': 'symptom', 'value': [environment.input_dict['q']]})
        if is_valid_auto_diagnose(auto_diagnose_params):
            result['valid_auto_diagnose'] = 1
        # ai_search_common.extends_progress_result(result, self.ai_result)  # 不懂什么原理
        result['answer'] = [{"text": "小微为您推荐一个和您情况最匹配的科室："}]
        return result


    def process(self, query, **kwargs):
        """
        额外字段:valid_auto_diagnose
        """
        result = {'is_end': 1}
        self.set_params(query)
        q_content = self.input_params['input'].get('q')
        params = {'q': q_content, 'level': 4}
        result[constant.RESULT_FIELD_SEARCH_PARAMS] = params
        if not self.input_params['input'].get('confirm_information'):
            # 质疑模式, interactive=2表示 科室分类认为传过去的age，sex都是错的，需要重新输入
            params['interactive'] = 2

        url = common.get_ai_service_url()
        ai_dept_response = ai_search_common.query(params, self.input_params, 'ai_dept', url)
        if ai_dept_response and ai_dept_response.get('data', {}).get('isEnd') == 0:
            result[constant.QUERY_KEY_AI_DEPT] = ai_dept_response['data']
            result['is_end'] = 0
            return result

        # 如果需要交互信息, 则返回ai_dept
        if ai_dept_response and ai_dept_response.get('data', {}).get('depts'):
            depts = [temp for temp in ai_dept_response['data']['depts'] if temp.get(
                'dept_name') and temp['dept_name'] != 'unknow']
            dept_json_list = []
            for dept in depts[0:2]:
                dept_json = {}
                self.ai_result.setdefault('departmentName', []).append(dept['dept_name'])
                dept_json['accuracy'] = dept.get('accuracy')
                dept_json['department_name'] = dept.get('dept_name')
                dept_id = dept.get('dept_id')
                department_search_params = {'std_dept': dept_id,
                                            'rows': 1,
                                            'fl': 'common_disease, introduction, std_dept_id'}
                std_dept_response = ai_search_common.query(department_search_params, self.input_params, 'std_dept')
                if std_dept_response.get('docs'):
                    std_dept_item = std_dept_response.get('docs')[0]
                    dept_json['common_disease'] = std_dept_item.get('common_disease', [])
                    dept_json['introduction'] = std_dept_item.get('introduction', '')
                    dept_json['department_uuid'] = std_dept_item.get('std_dept_id', '')
                if dept_json:
                    dept_json_list.append(dept_json)
            if dept_json_list:
                result[constant.QUERY_KEY_DEPT_SEARCH] = dept_json_list
        auto_diagnose_params = {'input': [], 'source': 'bb'}
        for key_temp in ('sex', 'age'):
            if self.input_params.get(key_temp):
                auto_diagnose_params['input'].append({'key': key_temp, 'value': [self.input_params[key_temp]]})
        auto_diagnose_params['input'].append({'key': 'symptom', 'value': [q_content]})
        if ai_search_common.is_valid_auto_diagnose(auto_diagnose_params):
            result['valid_auto_diagnose'] = 1
        ai_search_common.extends_progress_result(result, self.ai_result)
        return result
