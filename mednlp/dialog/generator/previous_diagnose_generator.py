#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
previous_diagnose_generator.py -- the service of previous diagnose list
Author: renyx <renyx@guahao.com>
Create on 2019-06-25 Tuesday.
"""
import traceback
import json
import global_conf
from ailib.utils.verify import check_is_exist_params
from mednlp.dialog.generator.ai_generator import AIGenerator
from mednlp.dialog.cg_constant import logger, array_field
from mednlp.dialog.cg_util import op_dict, previous_diagnose_dict


class PreviousDiagnoseGenerator(AIGenerator):
    name = 'previous_diagnose'
    input_field = [
        'age', 'sex',
        'symptom', 'time', 'reason',
        'degree', 'body_part', 'frequency',
        'accompany_symptom', 'medicine_detail', 'past_medical_history',
        'allergy_history', 'sbp', 'dbp',
        'medicine_effect', 'symptom_property', 'accompany_symptom_property',
        'menstruation_last_time', 'menstruation_interval_time', 'property_added',
        'frequency_added', 'first_body_part', 'description',
        'quantity'
    ]
    output_field = ['symptom', 'chief_complaint', 'medical_history',
                    'past_medical_history', 'allergic_history', 'disease_name']

    output_result_field = ['symptom', 'chief_complaint', 'medical_history',
                           'past_medical_history', 'allergic_history']

    field_trans = {}

    def __init__(self, cfg_path, **kwargs):
        super(PreviousDiagnoseGenerator, self).__init__(cfg_path, **kwargs)

    def pre_deal(self, input_obj):
        reason = input_obj.get('reason')
        if reason and '不清楚' in reason:
            input_obj['reason'] = ['不明原因']

    def generate(self, input_obj, **kwargs):
        # 症状 @ | 属性前缀 | 属性 | 属性后缀
        content = []
        result = {'content': content}
        data = {}
        check_is_exist_params(input_obj, ['symptom', 'age', 'sex'])
        symptom = input_obj['symptom']
        data['symptom'] = symptom
        self.pre_deal(input_obj)
        if input_obj.get('past_medical_history'):
            if '都没有' in input_obj['past_medical_history']:
                data['past_medical_history'] = '体健'
            else:
                data['past_medical_history'] = '、'.join(input_obj['past_medical_history'])
        if input_obj.get('allergic_history'):
            if '都没有' in input_obj['allergic_history']:
                data['allergic_history'] = '无'
            else:
                data['allergic_history'] = '对%s过敏' % '、'.join(input_obj['allergic_history'])
        data.update(self.parse_data(input_obj))
        self.diagnose(data, input_obj)
        fl = input_obj.get('fl', self.output_field)
        diagnose_list = data.get('diagnose', [])
        for temp in diagnose_list:
            content_item = {}
            for field, value in temp.items():
                if field not in fl and self.field_trans.get(field) not in fl:
                    continue
                if field in self.field_trans:
                    content_item[self.field_trans[field]] = value
                else:
                    content_item[field] = value
            content.append(content_item)

        for field in self.output_result_field:
            value = data.get(field)
            if value is None:
                continue
            if field not in fl and self.field_trans.get(field) not in fl:
                continue
            if field in self.field_trans:
                result[self.field_trans[field]] = value
            else:
                result[field] = value
        return result

    def diagnose(self, data, input_obj):
        diagnose_fields = {
            'chief_complaint': 'chief_complaint',  # 主诉
            'medical_history': 'medical_history',  # 现病史
            'past_medical_history': 'past_medical_history',  # 既往史
            'allergic_history': 'allergic_history',  # 过敏史
        }
        params = {
            'age': input_obj['age'],
            'sex': input_obj['sex'],
            'rows': input_obj.get('rows', 5),
            'mode': 0,
            'source': 'previous_diagnose_generator',
            'fl': 'disease_name'
        }
        for answer_field, diagnose_field in diagnose_fields.items():
            if data.get(answer_field):
                params[diagnose_field] = data[answer_field]
        logger.info('diagnose_service参数:%s' % json.dumps(params, ensure_ascii=False))
        try:
            res = self.ac.query(params, 'diagnose_service')
            if res and res.get('code') == 0 and res.get('data'):
                data['diagnose'] = res['data']
        except Exception as err:
            logger.error('diagnose_service异常,%s' % traceback.format_exc())
        return

    def parse_data(self, data):
        """
        组织现病史、主诉
        38个现病史在字典里、其他都是固定的格式组装
        每个症状的语句按照 前缀 当前值 后缀的方式拼接
        :param data:
        :return:
        """
        result = {}
        symptom = data['symptom']
        if previous_diagnose_dict.get(symptom):
            symptom_options = previous_diagnose_dict[symptom]
        else:
            symptom_options = previous_diagnose_dict['general']
        fill_result = []
        for temp in symptom_options:
            if data.get(temp['key']):
                # 伴随症状 填 都没有, 改成无伴随症状
                if temp['key'] == 'accompany_symptom':
                    if '都没有' in data[temp['key']]:
                        fill_result.append('无伴随症状。')
                        continue
                prefix = self.parse_ops(temp['prefix'], temp['key'], data=data)
                value = self.parse_ops(temp['center'], temp['key'], data=data, attribute_flag=1)
                suffix = self.parse_ops(temp['suffix'], temp['key'], data=data)
                fill_result.append('%s%s%s' % (prefix, value, suffix))
        if fill_result:
            medical_history = '患者%s' % ''.join(fill_result)
            if medical_history[-1] in (',', '，', '。', '.'):
                medical_history = medical_history[: -1]
            medical_history += '。'
            result['medical_history'] = medical_history
        time = data.get('time', [])
        result['chief_complaint'] = '%s%s' % (symptom, ''.join(time))
        return result

    def parse_ops(self, param_list, key, data, **kwargs):
        """
        根据op获取运算符, 无结果op会返回None
        :param param_list:
        :param value: 当前key对应的值
        :param kwargs:
            attribute_flag: 表示属性标志, 若所有的操作不符合,则返回该属性的值
        :return:
        """
        result = ''
        for temp in param_list:
            op = temp['op']
            fill_value = temp['fill_value']
            params = temp.get('params', [])
            temp = op_dict[op](fill_value=fill_value, key=key, params=params, data=data)
            if temp is not None:
                result = temp
                return result
        if kwargs.get('attribute_flag'):
            value = data[key]
            if key in array_field:
                value = '、'.join(value)
            result = value
        return result


if __name__ == '__main__':
    generator = PreviousDiagnoseGenerator(global_conf.cfg_path)
    input_obj = {
        "age": "3600",
        "sex": "1",
        "time": ["2天"],
        "reason": ["因劳累"],
        "symptom": "血糖升高",
        "property_added": ["血糖值为：22mmol/L"],
        "symptom_property": ["空腹血糖"],
        "accompany_symptom": ["恶心、发热、反酸"],
        "past_medical_history": ["高血压", "高血糖"],
        "allergy_history": ["花粉", "蜜蜂"]
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))
