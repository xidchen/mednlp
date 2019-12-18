#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.utils.utils import transform_dict_data
from mednlp.dao.ai_service_dao import ai_services
from mednlp.dialog.configuration import Constant as constant
from mednlp.dialog.configuration import logger
import json


class DepartmentClassifyProcessor(BasicProcessor):
    # 只处理门户科室分类结果

    def __init__(self):
        super(DepartmentClassifyProcessor, self).__init__()

    def process(self, query, **kwargs):
        """
        1.科室分诊
        result内字段:
        accuracy
        department_updated
        confirm
        among
        """
        result = {}
        self.set_params(query)
        ai_dept_result = self.department_interact()
        extends = ai_dept_result.pop('extends', {})
        self.ai_result.update(extends)
        result.update(ai_dept_result)
        return result

    def department_interact(self):
        """
        调用科室分诊:
        1.无数据或者中断,返回相关结果信息
        2.若需要交互，则返回result['ai_dept'],后续根据ai_dept会形成交互框
        result里的属性:
        isEnd
        isHelp

        特殊:
        accuracy
        department_updated
        confirm
        among

        departmentId
        departmentName

        取消:
        needSexAge
        departmentSymptom
        """
        result = {'is_end': 0, 'extends': {}}
        param = {'rows': 1}
        param['source'] = self.input_params.get('source')
        param['q'] = self.input_params['input']['q']
        transform_dict_data(param, self.input_params['input'],
                            {'symptom': 'symptomName', 'sex': 'sex', 'age': 'age'})
        if param.get('symptom') in ('都没有', ):
            param['symptom'] = '-1'
        if not self.input_params['input'].get('confirm_information'):
            # 质疑模式, interactive=2表示 科室分类认为传过去的age，sex都是错的，需要重新输入
            param['interactive'] = 2
        # APP传中断
        interrupt = True if self.input_params['input'].get('is_end') else False
        logger.info('dept_classify_interactive 参数: %s' % json.dumps(param))
        dept_data, err_msg = ai_services(param, 'dept_classify_interactive', 'post')
        result[constant.RESULT_FIELD_QUERY_CONTENT] = param['q']
        result[constant.RESULT_FIELD_SEARCH_PARAMS] = param
        if not dept_data:
            # result['err_msgs'] = err_msg
            result['is_help'] = 1
            result['is_end'] = 1
            return result

        dept_result = dept_data.get('depts')[0]
        dept_name = dept_result.get('dept_name')

        stop_interact = dept_data.get('isEnd') or interrupt
        if stop_interact and dept_name == 'unknow':
            result['is_help'] = 1
            result['is_end'] = 1
            return result

        if stop_interact:
            # ai_dept = {'department_updated': True}
            if dept_result.get('accuracy'):
                # ai_dept['accuracy'] = dept_result['accuracy']
                result['accuracy'] = dept_result.get('accuracy')
            # 重置departmentId
            if dept_result.get('dept_id'):
                result['extends']['departmentId'] = [dept_result.get('dept_id')]
                # ai_dept['departmentId'] = [dept_result.get('dept_id')]
                # result['departmentId'] = [dept_result.get('dept_id')]
            if dept_name:
                result['extends']['departmentName'] = [dept_name]
                # ai_dept['departmentName'] = [dept_name]
                # result['departmentName'] = [dept_name]
            result['department_updated'] = True
            dept_in_query = True if dept_result.get('dept_id') in self.ai_result.get(
                'departmentId', []) else False
            if dept_in_query:
                if self.intention_conf.intention == 'departmentConfirm':
                    # ai_dept['confirm'] = 1
                    result['confirm'] = 1
                if self.intention_conf.intention == 'departmentAmong':
                    # ai_dept['among'] = 1
                    result['among'] = 1
            result['is_end'] = 1
            # result[constant.QUERY_KEY_DEPARTMENT_CONFIRM_INFO] = ai_dept
            return result

        if not stop_interact:
            # 不停止交互,返回科室分类数据
            result[constant.QUERY_KEY_AI_DEPT] = dept_data
            # if dept_data.get('isSex') or dept_data.get('isAge'):
            #     result['needSexAge'] = 1
            # if dept_data.get('symptoms'):
            #     result['departmentSymptom'] = dept_data.get('symptoms')
            return result
