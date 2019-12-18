#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
examination.py -- the class of medical examination explain

Author: chenxd
Create on 2019-03-13 Wednesday.
"""
import os
import re
import json
import global_conf
from mednlp.kg.examination_conf import exam_status, en_to_cn_status, rule_item, physical_exam
from ailib.client.ai_service_client import AIServiceClient
from mednlp.kg.standard_entity import StandardEntity
from mednlp.kg.examination_status import get_status
import logging
from time import time

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

ai_content = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')


# explain_txt = json.load(open(global_conf.dict_path + 'examination_explain.txt'))
# standaradmodel = StandardEntity()

class ExaminationExplain(StandardEntity):

    def __init__(self):
        super(ExaminationExplain, self).__init__()

    def index_trans(self, item_exam, **kwargs):
        value = item_exam.get('value', '')
        name = item_exam.get('name', '')
        category_name = item_exam.get('category_name')
        reference = item_exam.get('reference')
        reference_upper = item_exam.get('reference_upper')
        reference_lower = item_exam.get('reference_lower')
        # if not(reference or reference_upper or reference_lower):
        #     return None
        age = kwargs.get('age')
        gender = kwargs.get('gender')
        abnormal_result = {}
        abnormal_result['item_name'] = name
        ## 指标项名称
        if name and category_name:
            abnormal_result['name'] = category_name + '|' + name
        elif name:
            abnormal_result['name'] = name
        elif category_name:
            abnormal_result['name'] = category_name
        else:
            pass
        # 异常值判定
        if value and value == reference:
            abnormal_result['status'] = 'normal'
        elif exam_status.get(value):
            abnormal_result['status'] = exam_status.get(value)
        # 数值比较
        if isinstance(reference, dict):
            reference_upper, reference_lower = self._reference_modify(reference, gender=gender)

        elif not (reference_lower and reference_upper):
            if reference:
                reference_upper, reference_lower = self._reference_modify(reference)
        if reference or reference_lower or reference_upper:
            if name in ['脉率', '心率', '呼吸频率', 'BMI']:
                abnormal_result['status'] = self._special_status(name, value, reference_lower, reference_upper)
            else:
                try:
                    if float(value) < float(reference_lower):
                        abnormal_result['status'] = 'down'
                    elif float(value) > float(reference_upper):
                        abnormal_result['status'] = 'raise'
                    elif float(value) >= float(reference_lower) \
                            and float(value) <= float(reference_upper):
                        abnormal_result['status'] = 'normal'
                except:
                    pass

        return abnormal_result

    def _special_status(self, name, value, reference_lower, reference_upper):
        '''
        特殊指标的特殊状态
        :param name: 指标名
        :param value: 指标值
        :param reference_lower:下限
        :param reference_upper: 上线
        :return:特殊状态
        '''
        res = ''
        if name in ['脉率', '心率', '呼吸频率']:
            try:
                if float(value) < float(reference_lower):
                    res = 'slower'
                elif float(value) > float(reference_upper):
                    res = 'accelerate'
                elif float(value) >= float(reference_lower) \
                        and float(value) <= float(reference_upper):
                    res = 'normal'
            except:
                pass
        elif name == 'BMI':
            try:
                if float(value) < 18.5:
                    res = 'low_weight'
                elif float(value) > 28:
                    res = 'fat_weight'
                elif float(value) >= 24 \
                        and float(value) <= 27.9:
                    res = 'over_weight'
                else:
                    res = 'normal'
            except:
                pass
        return res

    def _reference_modify(self, reference, **kwargs):
        gender = kwargs.get('gender')
        if gender:
            reference = reference[gender]
        reference_upper, reference_lower = '', ''
        match_result = re.findall('\d{1,}\.?\d{0,}', reference)
        if len(match_result) == 2:
            reference_upper = match_result[-1]
            reference_lower = match_result[0]
        return reference_upper, reference_lower

    def get_rule_result(self, fl, examination_trans, age, gender):
        result_dict = {}
        if examination_trans:
            if 'abnormal_explain' in fl:
                result = []
                for dict_ex in examination_trans:
                    dict_new = {}
                    # print('--->dict_ex',dict_ex)
                    text = ''
                    status_explanation, status_advice, examination_id = self.abnormal_explain(dict_ex)
                    if status_explanation:
                        text = status_explanation
                        dict_ex['status_explanation'] = status_explanation
                        dict_new['text'] = text
                        dict_new['advice'] = status_advice
                        dict_new['type'] = 1
                        dict_new['examination_name'] = [dict_ex.get('item_name')]
                        dict_new['examination_id'] = [examination_id]
                        result.append(dict_new)
                result_dict['abnormal_explain'] = result
            if 'combo_explain' in fl:  # 全部项，包含正常和异常
                result = self.combo_explain(examination_trans)
                result_dict['combo_explain'] = result
            if 'advise' in fl:  ##调用辅助诊断的接口，给出辅助诊断的结果
                result = self.diagnosis_result(examination_trans, age, gender)
                result_dict['advise'] = result
        return result_dict

    def abnormal_explain(self, examination_trans):
        '''
        获取单项解读的结果
        :param examination_trans:指标状态字典
        :return:字典列表
        '''
        status_explanation_res = ''
        status_advice_res = ''
        examination_id = ''
        if isinstance(examination_trans, dict):
            name = examination_trans.get('name')
            item_name = examination_trans.get('item_name')
            status = examination_trans.get('status')
            status_explanation = status + '_explanation'
            status_advice = status + '_advice'
            if status != 'normal':
                result_data = self.get_stand_entity(name, status)  # 调用entity_service接口
                # 当配置的只有阳性的解读，值为强阳性或者中度阳性也给出阳性的解读
                if result_data and not result_data.get(status_explanation) \
                        and (status in ['moderate_positive', 'strong_positive']):
                    result_data = self.get_stand_entity(name, 'positive')  # 调用entity_service接口
                    status_explanation = 'positive_explanation'
                    status_advice = 'positive_advice'
                if not result_data:
                    result_data = self.get_stand_entity(item_name, status)  # 调用entity_service接口
                # print('---')
                # print(result_data)
                if result_data:
                    examination_id = result_data.get('id')
                    status_explanation_res = result_data.get(status_explanation)
                    status_advice_res = result_data.get(status_advice, '')
                    if not status_explanation:
                        standard_name = result_data.get('standard_name')
                        if standard_name and standard_name != name:
                            result_data_stad = self.get_stand_entity(standard_name, status)  # 调用entity_service接口
                            if result_data_stad:
                                status_explanation_res = result_data_stad.get(status_explanation)
                                status_advice_res = result_data_stad.get(status_advice, '')
            return status_explanation_res, status_advice_res, examination_id

    def combo_explain(self, examination_trans):
        '''
        组合项解读
        :param examination_trans:
        :return:字典列表
        '''
        items = []
        examination_name = []
        examination_id = []
        dict_new = {}
        rule_flow = rule_item  # 暂时补充
        for exam in examination_trans:
            id = ''
            dict_item = {}
            name = exam.get('name')
            if name in rule_flow:  # 暂时补充
                rule_flow.remove(name)  # 暂时补充
            item_name = exam.get('item_name')
            examination_name.append(item_name)
            status = exam.get('status')
            dict_item['itemValue'] = status
            result_data = self.get_stand_entity(name, status)  # 调用entity_service接口
            if result_data:
                id = result_data.get('id')
            examination_id.append(id)
            dict_item['itemCode'] = name
            items.append(dict_item)
        # 暂时补充
        if rule_flow:
            for items1 in rule_flow:
                items.append({'itemCode': items1, 'itemValue': '1'})
        params = {'items': items}
        # print('规则引擎的输入:',params)
        try:
            time_begin = time()
            analyzedata = ai_content.query(json.dumps(params, ensure_ascii=False),
                                           service='combined_examination', method='post')
            time_end = time()
            run_time = (time_end - time_begin) * 1000
            logging.info('接口名: combined_examination 参数: ' + str(params) + ' 请求类型 : post' + ' 运行时间: %.2f ms' % run_time)

            analyzeresult = analyzedata.get('data')
            # print('规则引擎的结果',analyzeresult)
            text = ''
            if analyzeresult:
                text = analyzeresult.get('analyzeResult')
        except:
            text = ''
        dict_new['text'] = text
        dict_new['advice'] = ''
        dict_new['type'] = '2'
        dict_new['examination_name'] = examination_name
        dict_new['examination_id'] = examination_id
        result = [dict_new]
        return result

    def diagnosis_result(self, examination_trans, age, gender):
        '''
        调用辅助诊断的接口，返回最可能的三种疾病（ps：性别需要调整）
        这里性别为男1，女2  和辅助诊断的相反
        :param examination_trans: 字典
        :param age: 年龄
        :param gender: 性别
        :return: 字典列表
        '''

        if str(gender) == '1':
            sex = '2'
        elif str(gender) == '2':
            sex = '1'
        else:
            sex = gender
        physical_examination = []
        inspection_list = []
        if examination_trans:
            for exam in examination_trans:
                name = exam.get('name')
                status = exam.get('status')
                if status not in ['normal', 'negative']:
                    cn_status = en_to_cn_status.get(status)
                    if cn_status == '降低':
                        cn_status = '下降'
                    content = str(name) + str(cn_status)
                    if name in physical_exam:
                        if content not in physical_examination:
                            physical_examination.append(content)
                    else:
                        if content not in inspection_list:
                            inspection_list.append(content)

        if physical_examination or inspection_list:
            inspection = ",".join(inspection_list)
            physical = ",".join(physical_examination)
            params = {'physical_examination': physical, 'general_info': inspection, 'sex': sex,
                      'age': age}  # , 'rows': 3}
            time_begin = time()
            diagnosis_result = ai_content.query(params, service='diagnose_service', method='get')
            time_end = time()
            run_time = (time_end - time_begin) * 1000
            logging.info('接口名: diagnose_service 参数: ' + str(params) + ' 请求类型 : get' + ' 运行时间: %.2f ms' % run_time)

            diag_res = diagnosis_result.get('data')
            result = ''
            disease_list = [x.get('entity_name') for x in diag_res if x.get('score') > 0]
            if diag_res and len(disease_list) >= 3:
                result = '睿医智能医生提示：患者可能诊断是{}、{}、{}，结果仅供参考，请结合临床判断。'.format(
                    disease_list[0], disease_list[1], disease_list[2])
            else:
                result = '睿医智能医生提示：{},诊断依据不足，请结合其他临床症状进行判断。'.format(inspection + ',' + physical)
        else:
            result = '您的检验结果未见明显异常，建议保持健康生活，坚持定期体检。'
        return result

    def get_explain(self, fl, examination, age=None, gender=None):
        '''

        :param fl:类别
        :param examination:检查检验单【指标1情况，指标2情况,...】
        :param gender: 性别
        :param age: 年龄
        :return: [指标1异常解读，指标2异常解读]
        '''
        result = {}
        examination_trans = []
        status = ''
        if 'status' in fl:
            status = get_status(examination, age=age, sex=gender)
            fl.remove('status')
        if fl:
            for item_exam in examination:
                examination_trans.append(self.index_trans(item_exam, gender=gender, age=age))
            result = self.get_rule_result(fl, examination_trans, age=age, gender=gender)
        if status:
            result['status'] = status
        return result


if __name__ == '__main__':
    model = ExaminationExplain()
    fl = ['advise', 'abnormal_explain']
    age = '15'
    gender = '2'
    items = [{"reference": "36.0-37.4", "category_name": "", "name": "收缩压", "value": "3.5"}]
    # print(result0)
    result = model.get_explain(fl, items, gender=gender, age=age)
    print(result)
