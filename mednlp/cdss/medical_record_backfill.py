# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-08-07 Wednesday
@Desc:	病历回填
"""

import re
from collections import OrderedDict
from data.dict.medical_record_backfill_rule import symptom_backfill_rule, rule_templates


class BackFillTemplate:
    """病历回填模板"""

    def __init__(self):
        pass

    def render(self, symptom, answers):
        """
        数据结构:

        函数流程:
            遍历每一节
                获取keys内容 {}
                根据条件，选择模板
                渲染模板 加入到渲染结果中
            “,”拼接为一句话
        """

        if not answers:
            return ''

        if symptom in symptom_backfill_rule:
            rules = symptom_backfill_rule[symptom]
        else:
            rules = symptom_backfill_rule['common']

        res_item = []
        for rule in rules:
            for template, fun in rule_templates[rule]:
                if fun(answers):
                    res_item.append(template.format(**answers))
                    break
        res_item = [ri for ri in res_item if ri]
        if res_item:
            return '，'.join(res_item) + '。'
        return ''

    def render_chief_complaint(self, argument):
        symptom = argument.get('symptom', '')
        disease_time = ''
        aggravation_time = ''
        for entity in argument.get('main_symptom'):
            if entity['name'] == '病程':
                options = entity['value']
                if options:
                    disease_time = options[0]['content']
            if entity['name'] == '加重时间(非必填)':
                options = entity['value']
                if options:
                    aggravation_time = options[0]['content']
        if not symptom:
            return ''
        chief_complaint = symptom
        if disease_time:
            chief_complaint += disease_time
        if aggravation_time:
            chief_complaint += '，加重' + aggravation_time
        return chief_complaint + '。'

    def render_medical_history(self, argument):
        """现病史回填"""
        symptom = argument.get('symptom')
        answers = {'症状': symptom}
        # main
        for entity in argument.get('main_symptom'):
            answers[entity['name']] = '、'.join([option['content'] for option in entity['value']])

        accompanying_symptom = []
        accompanying_symptom_details = []
        for entity in argument.get('accompanying_symptoms'):
            name, options = entity['name'], entity['value']
            if name == '':
                name = '伴随症状'
            for option in options:
                content = option['content']
                detail_info = OrderedDict()
                for detail in option['details']:
                    if detail['value']:
                        detail_info[detail['name']] = '、'.join(detail['value'])
                if '病程' in detail_info:
                    content += detail_info['病程']
                    del detail_info['病程']
                if '时间' in detail_info and '体重下降量' in detail_info:
                    content += '，{}内体重下降{}'.format(detail_info['时间'], detail_info['体重下降量'])
                    del detail_info['时间']
                    del detail_info['体重下降量']
                if '时间' in detail_info and '体重增加量' in detail_info:
                    content += '，{}内体重增加{}'.format(detail_info['时间'], detail_info['体重增加量'])
                    del detail_info['时间']
                    del detail_info['体重增加量']

                for key, val in detail_info.items():
                    if val:
                        content += '，' + '{}:{}'.format(key, val)

                accompanying_symptom.append(option['content'])
                if content != option['content']:
                    accompanying_symptom_details.append(content)
        answers['伴随症状'] = '、'.join(accompanying_symptom)
        if accompanying_symptom_details:
            answers['伴随症状'] += '。伴随症状情况如下：'
            answers['伴随症状'] += '；'.join(accompanying_symptom_details)
        return self.render(symptom, answers)

    def simple_render(self, content, is_contain_key=True):
        if not content:
            return ''

        res = []
        if isinstance(content, dict):
            for key, val in content.items():
                res.append(key + ':' + val)
        if isinstance(content, list):
            for item in content:
                res.append(item['content'])
        if res:
            return '，'.join(res) + '。'
        return ''

    def _trans_entity_no_details(self, entities, split_char='、'):
        answers = {}
        if not entities:
            return answers
        for entity in entities:
            answers[entity['name']] = split_char.join([option['content'] for option in entity['value']])
        return answers

    def _remove_bracket(self, content):
        content = re.sub(r'\(.*\)', '', content)
        content = re.sub(r'（.*）', '', content)
        return content

    def _remove_other(self, content):
        return content.replace('其他:', '')

    def render_past_history(self, argument):
        entities = argument.get('past_history')
        if not entities:
            return ''

        answers = {}
        for entity in entities:
            name, options = entity['name'], entity['value']
            answers[name] = options

        # 既往史
        past_history = []
        if '疾病史' in answers:
            for option in answers['疾病史']:
                name = option['content']
                if name:
                    past_history_item = []
                    systolic_blood_pressure, diastolic_blood_pressure = '', ''
                    detail_info = []
                    disease_time = ''
                    for detail in option['details']:
                        if not detail['value']:
                            continue
                        if detail['name'] == '疾病年限':
                            disease_time = detail['value'][0]
                            continue
                        if detail['name'] == '平素收缩压' or detail['name'] == '平素收缩血压':
                            systolic_blood_pressure = detail['value'][0]
                            continue
                        if detail['name'] == '平素舒张压' or detail['name'] == '平素舒张血压':
                            diastolic_blood_pressure = detail['value'][0]
                            continue
                        detail_info.append('{}:{}'.format(detail['name'], '、'.join(detail['value'])))
                    if disease_time:
                        past_history_item.append('{}前诊断为{}'.format(disease_time, name))
                    else:
                        past_history_item.append(name)
                    if systolic_blood_pressure and diastolic_blood_pressure:
                        past_history_item.append(
                            '平素血压{}/{}'.format(systolic_blood_pressure[:-4], diastolic_blood_pressure))
                    elif systolic_blood_pressure:
                        past_history_item.append('平素收缩压：' + systolic_blood_pressure)
                    elif diastolic_blood_pressure:
                        past_history_item.append('平素舒张压：' + diastolic_blood_pressure)

                    past_history_item.extend(detail_info)
                    past_history.append('，'.join(past_history_item))

        # 手术史
        surgical_history = []
        if '手术史' in answers:
            for option in answers['手术史']:
                name = option['content']
                surgical_history_item = []
                if name:
                    surgical_time = ''
                    detail_info = []
                    for detail in option['details']:
                        if not detail['value']:
                            continue
                        if detail['name'] == '手术距今时长':
                            surgical_time = detail['value'][0]
                            continue
                        detail_info.append('{}:{}'.format(detail['name'], '、'.join(detail['value'])))
                    if surgical_time:
                        # surgical_history_item.append(name + surgical_time)
                        surgical_history_item.append('{}前行{}'.format(surgical_time, name))
                    else:
                        surgical_history_item.append(name)
                    surgical_history_item.extend(detail_info)
                    surgical_history.append('，'.join(surgical_history_item))

        allergic_history = self.simple_render(answers.get('过敏史'))
        blood_history = self.simple_render(answers.get('输血史'))
        res = []
        if past_history:
            res.append('既往疾病史：' + '；'.join(past_history) + '。')
        if surgical_history:
            res.append('既往手术史：' + '，'.join(surgical_history) + '。')
        if allergic_history:
            res.append('过敏史: ' + allergic_history)
        if blood_history:
            res.append('输血史: ' + blood_history)
        if res:
            return '\n'.join(res)
        return '既往体检。'

    def render_personal_history(self, argument):
        answers = self._trans_entity_no_details(argument.get('personal_history'), '；')
        res = answers.get('个人史', '')
        if res:
            return res + '。'
        return '无。'
        # return self.simple_render(answers, False)

    def render_allergic_history(self, argument):
        answers = self._trans_entity_no_details(argument.get('allergy_history'))
        return self.simple_render(answers, False)

    def render_family_history(self, argument):
        res = []
        for content in argument.get('family_history'):
            if content['name'] == '家族史':
                for option in content['value']:
                    details = option.get('details', [])
                    family_relation = ''
                    for detail in details:
                        if detail['name'] == '关系':
                            family_relation = '、'.join(detail['value'])
                    if option['content'] == '不详':
                        res.append('不详')
                    elif option['content'] == '其他':
                        res.append(option['content'])
                    else:
                        res.append(family_relation + '患' + option['content'])
        if res:
            return '，'.join(res) + '。'
        return '家人体健。'

    def render_marriage_history(self, argument):
        answers = self._trans_entity_no_details(argument.get('marital_history'))
        return self.simple_render(answers, True)

    def render_menstrual_history(self, argument):
        answers = self._trans_entity_no_details(argument.get('menstrual_history'))
        return self.simple_render(answers, True)

    def render_physical_examination(self, argument):
        entities = argument.get('common_signs')
        res = []
        for entity in entities:
            name, options = entity['name'], entity['value']
            item = []
            for option in options:
                detail_info = {}
                for detail in option['details']:
                    detail_info[detail['name']] = '、'.join(detail['value'])
                back_fill_content = ''
                if '部位' in detail_info and '腹部包块' != option['content']:
                    back_fill_content = detail_info['部位'] + option['content']
                    del detail_info['部位']
                for key, val in detail_info.items():
                    back_fill_content += val
                if not option['details']:
                    if option['content']:
                        back_fill_content += option['content']
                item.append(back_fill_content)
            if item:
                res.append(name + '  ' + '，'.join(item) + '。')
        return '\n'.join(res)

    def render_general_info(self, argument):
        entities = argument.get('examination')
        res = []
        for entity in entities:
            item = []
            name, options = entity['name'], entity['value']
            for option in options:
                _item = []
                for detail in option['details']:
                    _item.append('{}: {}'.format(detail['name'], '、'.join(detail['value'])))
                if _item:
                    item.append(option['content'] + '：' + '，'.join(_item))
                else:
                    item.append(option['content'])
            if item:
                res.append(name + '：' + '，'.join(item))

        entities = argument.get('general_info')
        # res = []
        for entity in entities:
            name, options = entity['name'], entity['value']
            for option in options:
                res.append(name + '：' + option['content'])

        for check in argument.get('check'):
            name = check.get('name')
            finding = check.get('finding')
            conclusion = check.get('conclusion')
            if name:
                check_info = []
                if finding:
                    check_info.append('检查所见：' + finding)
                if conclusion:
                    check_info.append('检查结论：' + conclusion)
                if check_info:
                    res.append(name + '：' + '；'.join(check_info))
        return '；'.join(res)

    def render_other_info(self, argument):
        """血压值、血糖值等"""
        return {}

    def get_back_fill(self, argument):
        res = {'chief_complaint': self.render_chief_complaint(argument),
               'medical_history': self.render_medical_history(argument),
               'past_medical_history': self.render_past_history(argument),
               'personal_history': self.render_personal_history(argument),
               'allergic_history': self.render_allergic_history(argument),
               'family_history': self.render_family_history(argument),
               'marriage_history': self.render_marriage_history(argument),
               'menstrual_history': self.render_menstrual_history(argument),
               'physical_examination': self.render_physical_examination(argument),
               'general_info': self.render_general_info(argument)}
        res.update(self.render_other_info(argument))
        for key, val in res.items():
            res[key] = self._remove_other(self._remove_bracket(val))

        # 无内容回填
        if not res['past_medical_history']:
            res['past_medical_history'] = '既往体健。'
        if not res['general_info']:
            res['general_info'] = '无。'
        if not res['physical_examination']:
            res['physical_examination'] = '无殊。'
        return res

    def make_medical_history(self, argument) -> str:
        """现病史回填 - 全科诊断使用"""
        symptom = argument.get('symptom', '')
        answers = {'症状': symptom}

        for entity in argument.get('main_symptom', []):
            answers[entity['name']] = '、'.join([option['content'] for option in entity['value']])

        accompanying_symptom = []
        for entity in argument.get('accompanying_symptoms', []):
            name, options = entity['name'], entity['value']
            if name == '':
                name = '伴随症状'
            for option in options:
                content = option['content']
                detail_info = OrderedDict()
                for detail in option['details']:
                    if detail['value']:
                        detail_info[detail['name']] = '、'.join(detail['value'])
                if '病程' in detail_info:
                    content += detail_info['病程']
                    del detail_info['病程']
                if '时间' in detail_info and '体重下降量' in detail_info:
                    content += '，{}内体重下降{}'.format(detail_info['时间'], detail_info['体重下降量'])
                    del detail_info['时间']
                    del detail_info['体重下降量']
                if '时间' in detail_info and '体重增加量' in detail_info:
                    content += '，{}内体重增加{}'.format(detail_info['时间'], detail_info['体重增加量'])
                    del detail_info['时间']
                    del detail_info['体重增加量']

                for key, val in detail_info.items():
                    if val:
                        content += '，' + '{}:{}'.format(key, val)

                accompanying_symptom.append(option['content'])
        answers['伴随症状'] = '、'.join(accompanying_symptom)

        if not answers:
            return ''
        medical_history = ''
        if '病程' in answers:
            medical_history += answers['病程'] + '前'
        if '诱因' in answers:
            medical_history += answers['诱因']

        medical_history += '出现'

        if '部位' in answers:
            medical_history += answers['部位']

        medical_history += argument.get('symptom', '')

        if '发作特点' in answers:
            medical_history += '，呈' + answers['发作特点']

        if '伴随症状' in answers:
            medical_history += '，伴随' + answers['伴随症状']
        if '加重因素' in answers:
            medical_history += '，' + answers['加重因素'] + '加重'
        if '缓解因素' in answers:
            medical_history += '，' + answers['缓解因素'] + '可以缓解'

        medical_history += '。'
        return medical_history


if __name__ == '__main__':
    st = BackFillTemplate()
    arguments = {'病程': '2小时', '诱因': '不洁净饮食', '程度': '轻度', '症状': '腹泻',
                 '性质': '胀痛', '发作特点': '阵发性', '缓解因素': '进食后', '部位': '其他',
                 '加重因素': '夜间', '伴随症状': '发热、寒战、腹泻'}
    arguments_str = '{"age":10958,"sex":1,"visit_type":1,"fl":"*","source":28,"orderNo":"2710462366543618000","birthday":"1989-09-17","symptom":"腹痛","activeCategoryIndex":0,"activeSymptomIndex":1,"critical_situation":[],"menstrual_history":[],"family_history":[],"common_signs":[],"examination":[],"marital_history":[],"past_history":[],"general_info":[],"treatment_process":[],"personal_history":[],"accompanying_symptoms":[{"name":"","value":[{"details":[],"content":"腹胀"},{"details":[],"content":"恶心"}]}],"main_symptom":[{"name":"病程","value":[{"content":"3小时","details":[]}]},{"name":"部位","value":[{"details":[],"content":"右上腹"}]},{"name":"诱因","value":[{"details":[],"content":"进食油腻食物后"}]},{"name":"性质","value":[{"details":[],"content":"绞痛或痉挛性疼痛"}]},{"name":"发作特点","value":[{"details":[],"content":"持续性，但强弱有变"}]},{"name":"程度","value":[{"details":[],"content":"中度（日常生活和工作受到影响）"}]},{"name":"缓解因素","value":[{"details":[],"content":"排便后"}]},{"name":"加重因素","value":[{"details":[],"content":"进食后"}]}]}'
    import json

    arguments = json.loads(arguments_str)
    print(st.make_medical_history(arguments))
    # print(st.render('腹泻', arguments))
