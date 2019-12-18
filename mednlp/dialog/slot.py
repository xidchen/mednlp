#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
slot.py -- module for slot
槽类
Author: maogy <maogy@guahao.com>
Create on 2018-08-04 Saturday.
"""

from copy import deepcopy
import mednlp.dialog.dialog_constant as constant
from mednlp.utils.utils import unicode2str
from mednlp.dialog.dialog_deal import deal_diagnose_service_age
import mednlp.dialog.dialog_deal as deal
import json


class SlotManagerFactory(object):
    """
    槽位管理工厂类.
    """

    def __init__(self, **kwargs):
        pass

    def get_slot_manager(self, conf, **kwargs):
        """
        槽位管理工厂类.
        参数:
        conf->槽位管理类名.
        返回值->槽位管理实例.
        """
        biz = kwargs[constant.BIZ_FIELD]
        slot_manage = conf.get('manager', BaseSlotManager)(conf, biz=biz)
        return slot_manage

# 工厂类单例
slot_manager_factory = SlotManagerFactory()


class BaseSlotManager(object):
    """
    槽位管理类.
    """
    """
    以下的SLOT_***_FIELD 以配置为主定义
    diagnose_slot_conf = {
        'manager': PreviousDiagnoseSlotManager,
        'slot': [
            {'name': 'sex', 'ask': '请选择性别：'},
            {'name': 'symptom', 'ask': '请输入症状，如“头晕”，“头晕，小腿痉挛”：'},
            {'name': 'is_treatment', 'ask': '请问是否做过治疗？',
             'sub_slot': [{'condition': 1, 'conf': treatment_slot_conf}]},
            {'name': 'past_medical_history', 'ask': '请问是否有以下疾病史？'},
    ]}
    """

    def __setitem__(self, k, v):
        self.k = v

    def __getitem__(self, k):
        if k == 'name':
            return self.name

    def __init__(self, conf=None, conf_handler=None, **kwargs):
        """
        初始化函数.
        参数:
        conf->slot配置
        conf_handler->slot配置生成句柄.
        """
        self.conf = conf
        if conf_handler:
            self.conf = conf_handler()

    def _init_slot(self, **kwargs):
        """
        根据slot配置,初始化slot.
        仅初始化当前Manager下的slot，填充name,ask,sub_slot
        """
        slots = []
        field_from_conf = [constant.SLOT_NAME_FIELD, constant.SLOT_ASK_FIELD, constant.SLOT_FLAG_FIELD,
                           constant.SLOT_SUB_SLOT_FIELD, constant.SLOT_CONTENT_FIELD,
                           constant.SLOT_HANDLER_FIELD,
                           constant.SLOT_POST_HANDLER_FIELD, constant.SLOT_TEXT_HANDLER_FIELD]
        for conf_s in self.conf.get('slot', []):
            slot = {field: conf_s[field] for field in field_from_conf if conf_s.get(field)}
            slots.append(slot)
        return slots

    def fill_slot(self, dialogs, **kwargs):
        """
        根据对话内容填充槽位.
        填充value
        参数:
        dialogs->历史对话内容,格式:[{'key':, 'value':}, {'key':, 'value':}].
        返回值->已填充槽位,空缺槽位
        """
        biz = kwargs[constant.BIZ_FIELD]
        # 外部处理器来处理slot对象
        pre_handler = self.conf.get(constant.SLOT_PRE_HANDLER_FIELD)
        if pre_handler:
            pre_handler_params = self.conf.get(constant.SLOT_PRE_HANDLER_PARAMS_FIELD, {})
            pre_handler_params['biz'] = biz
            pre_handler(self, dialogs, **pre_handler_params)
        slots = self._init_slot(biz=biz)
        filled_slots = []
        for dialog in dialogs:
            for index, slot in enumerate(slots):
                if dialog['key'] == slot[constant.SLOT_NAME_FIELD]:
                    # handler 处理, return 是否继续处理
                    if slot.get(constant.SLOT_HANDLER_FIELD):
                        # 比如症状词无法识别,需要用户继续输入症状词,该slot仍是blank_slot
                        if not slot[constant.SLOT_HANDLER_FIELD](slot, dialogs, biz=biz):
                            break
                    filled_slot = deepcopy(slot)
                    filled_slot[constant.SLOT_VALUE_FIELD] = dialog['value']
                    filled_slots.append(filled_slot)
                    del slots[index]
                    if filled_slot.get(constant.SLOT_SUB_SLOT_FIELD):
                        handler_conf = None
                        # 如果有sub_slot, 则需要判断是否应该添加子slot以及怎么添加
                        for sub_slot_temp in filled_slot.get(constant.SLOT_SUB_SLOT_FIELD):
                            """ 2种场景会赋值handler_conf
                        1.无condition这个key;2.有condition这个key 并且value = condition里的某个值"""
                            if ((constant.SLOT_CONDITION_FIELD not in sub_slot_temp) or
                                    (sub_slot_temp[constant.SLOT_CONDITION_FIELD] == unicode2str(dialog['value'][0]))):
                                handler_conf = sub_slot_temp.get(constant.SLOT_CONF_FIELD)
                                break
                        if not handler_conf:
                            continue
                        # get handler end, then operate handler
                        sub_sm_temp = slot_manager_factory.get_slot_manager(handler_conf, biz=biz)
                        # 子slot 与父slot 建立关系,在build_answer 时会用到
                        filled_slot[constant.SLOT_SUB_MANAGER_FIELD] = sub_sm_temp
                        sub_filled_slots, sub_blank_slots = sub_sm_temp.fill_slot(dialogs, biz=biz)
                        # 找到当前sub的index，在其后面添加子slot
                        filled_slots.extend(sub_filled_slots)
                        if sub_blank_slots:
                            slots = sub_blank_slots + slots
                    break
        # 此处while是对blank_slot进行post_handler,若del slot[0]后,新的slots[0]也有post_handler
        while len(slots) > 0 and slots[0].get('post_handler'):
            # 此处的post_handler要pop掉，防止while循环执行post_handler
            slots[0].pop('post_handler')(filled_slots, slots, dialogs, biz=biz)
        return filled_slots, slots

    def build_answer(self, slots, dialogs, slot_dict=None, **kwargs):
        """
        根据填充的slot构建回答内容.
        参数:
        slots->已经填充完成的槽,结构:[{'name':,'value':,'ask':}]
        返回值->回答内容,结构:{key1:value1, key2:value2,...}
        """
        answer = {}
        if not slot_dict:
            slot_dict = {}
        names = kwargs.get('names', [])
        for temp in names:
            slot = slot_dict.get(temp)
            answer[temp] = slot[constant.SLOT_VALUE_FIELD]
        return answer

    def build_slot_answer(self, slots, dialogs, **kwargs):
        """
        构建需要填槽的回答.
        参数:
        slots->已经填充完成的槽,结构:[{'name':,'value':,'ask':}]
        返回值->回答内容,结构:{key1:value1, key2:value2,...}
        """
        answer_field = {'answer': constant.SLOT_ASK_FIELD,
                        'card_type': constant.SLOT_NAME_FIELD,
                        'card_content': constant.SLOT_CONTENT_FIELD,
                        'extends': constant.SLOT_EXTENDS}
        answer = {}
        for key, slot_key in answer_field.items():
            if slots[0].get(slot_key):
                answer[key] = slots[0][slot_key]
        return answer

    # @deprecated
    def select_slot(self, dialogs):
        """
        选择slot,按照slot顺序和已填充的slot,选出第一个未填充的slot.
        参数:无
        返回值->slot,格式:{'name':, 'ask':}
        """
        filled_slots, slots = self.fill_slot(dialogs)
        for slot in slots:
            if 'value' not in slot:
                return slot
        return None


class SymptomSlotManager(BaseSlotManager):
    """
    症状管理器
    """
    def build_answer(self, slots, dialogs, slot_dict=None, **kwargs):
        """
        根据填充的slot构建回答内容.
        参数:
        slots->已经填充完成的槽,结构:[{'name':,'value':,'ask':}]
        返回值->回答内容,结构:{key1:value1, key2:value2,...}
        """
        biz = kwargs['biz']
        answer = {}
        symptom_value = []
        symptom_entities = set()
        symptoms_dict = {}
        org_symptom = []
        if not slot_dict:
            slot_dict = {}
        """
        获取症状相关数据,
        symptom 直接放入symptom_value，而symptom|xxxx|time_happen等key放入dict中
        格式为{失眠:{time_happen:25天, cause:value}, 头痛:{time_happen:22天, cause:value}}
        方便 每个症状的相关问题统一描述
        """
        # get 原始症状问句
        for temp in dialogs:
            if constant.symptom_key == temp.get('key') and temp.get(constant.DIALOG_ORG_VALUE):
                # org_symptom是一个list
                org_symptom = temp[constant.DIALOG_ORG_VALUE]
                break
            # if temp.get(constant.)
        for key_temp, value_temp in slot_dict.items():
            keys = key_temp.split('|')
            if keys[0] == 'symptom':
                answer[key_temp] = value_temp.get('value')
                if len(keys) == 1:
                    symptom_value = value_temp.get('value')
                elif len(keys) == 3:
                    name = constant.aes_util.decrypt(keys[1])
                    symptom_entities.add(name)
                    sub_symptom = symptoms_dict.setdefault(name, {})
                    sub_symptom.setdefault('properties', {})
                    # sub_symptom = symptoms_dict.setdefault(keys[1], {})
                    sub_symptom['name'] = name
                    properties = sub_symptom.setdefault('properties', {})
                    properties[keys[2]] = value_temp.get(constant.SLOT_VALUE_FIELD)
        chief_complaint = []   # 主诉
        medical_history = []    # 现病史
        # if org_symptom:
        #     chief_complaint.extend(org_symptom)
        # 选择模板
        dialog_property = deal.dialog_property
        if constant.BIZ_AUTO_DIAGNOSE == biz:
            dialog_property = deal.dialog_property_auto_diagnose
        # 拼装主诉 和 现病史
        for symptom_name_temp in symptom_entities:
            symptom_data = symptoms_dict.get(symptom_name_temp)     # 某个症状
            properties = symptom_data.get('properties', {})     # 症状的属性
            medical_history_temp = ''       # 1个症状的描述
            for property_key, handler in deal.dialog_property_order:
                dialog_padding = {'name': symptom_name_temp}
                if isinstance(property_key, dict):
                    # {'other': '出现%(name)s'}
                    medical_history_temp += property_key.get('other') % dialog_padding
                    continue
                # 属性值
                property_temp = properties.get(property_key)
                property_deal_temp = ''
                # 对话模板, 是否单值
                dialog_template, is_single = dialog_property.get(property_key)
                if handler:
                    medical_history_temp += handler(symptom_name_temp, property_temp)
                else:
                    # 有对话模板以及有属性值，才继续
                    if not (property_temp and dialog_template):
                        continue
                    # 若值是 [以上都不是, 不清楚, 不明因素] 则continue
                    if property_temp[0] in [constant.OPTION_FUZZY_NOT_ALL, constant.OPTION_FUZZY_NOT_KNOW,
                                            constant.OPTION_FUZZY_NO_FACTORY]:
                        continue
                    property_deal_temp = '、'.join(property_temp)
                    dialog_padding = {'name': symptom_name_temp, 'value': property_deal_temp}
                    medical_history_temp = medical_history_temp + dialog_template % dialog_padding
                if 'time_happen' == property_key:
                    chief_complaint.append(symptom_name_temp + property_temp[0])
            medical_history.append(medical_history_temp)
        # 若无chief_complaint,主诉是症状名
        if not chief_complaint:
            answer['chief_complaint'] = ' '.join(symptom_value)
        else:
            answer['chief_complaint'] = ' '.join(chief_complaint)
        # org_symptom是一定会有的，没有逻辑就不对了
        answer['diagnose_chief_complaint'] = '%s。%s' % (' '.join(org_symptom), answer['chief_complaint'])
        medical_history_str = '患者'
        for index, temp in enumerate(medical_history):
            if temp.strip()[-1] == ',':
                medical_history[index] = temp.strip()[:-1] + '。'
        medical_history_str += ' '.join(medical_history)
        # if medical_history_str == '患者':
        #     medical_history_str = ''
        answer['medical_history'] = medical_history_str
        answer['diagnose_medical_history'] = medical_history_str
        return answer


class TreatmentSlotManager(BaseSlotManager):
    """
    治疗方式槽位管理
    """
    def build_answer(self, slots, dialogs, slot_dict=None, **kwargs):
        """
        根据填充的slot构建回答内容.
        参数:
        slots->已经填充完成的槽,结构:[{'name':,'value':,'ask':}]
        返回值->回答内容,结构:{key1:value1, key2:value2,...}
        """
        orig_answer = kwargs.get('orig_answer')
        answer = {}
        if not slot_dict:
            slot_dict = {}
        treatment_field = ['is_treatment', 'treatment']
        for field in treatment_field:
            if slot_dict.get(field):
                answer[field] = slot_dict.get(field).get('value')
                # 治疗方法信息放入现病史
                if 'treatment' == field:
                    medical_history = orig_answer.get('medical_history', '')
                    medical_history_temp = medical_history + '且有相关治疗陈述:' + unicode2str(answer[field][0])
                    if medical_history_temp[-1] not in constant.punctuation:
                        medical_history_temp += '.'
                    orig_answer['medical_history'] = medical_history_temp
        orig_answer.update(answer)
        return {}


class PreviousDiagnoseSlotManager(BaseSlotManager):
    # """
    # 预问诊槽位管理.
    # """

    def build_answer(self, slots, dialogs, slot_dict=None, **kwargs):
        """
        根据填充的slot构建回答内容.
        参数:
        slots->已经填充完成的槽,结构:[{'name':,'value':,'ask':}]
        返回值->回答内容,结构:{key1:value1, key2:value2,...}
        """
        biz = kwargs[constant.BIZ_FIELD]
        logger = constant.BIZ_DICT[biz][constant.BIZ_LOGGER_FIELD]
        answer = {}
        if not slot_dict:
            slot_dict = {}
        for conf_temp in self.conf.get('slot', []):  # 7种
            if slot_dict.get(conf_temp[constant.SLOT_NAME_FIELD]):
                slot_temp = slot_dict.get(conf_temp[constant.SLOT_NAME_FIELD])
                if slot_temp.get(constant.SLOT_SUB_MANAGER_FIELD):
                    # 支持sub_manager自己更新answer,return {},也支持返回有数据的{}
                    answer.update(slot_temp[constant.SLOT_SUB_MANAGER_FIELD].build_answer(
                        slots, dialogs, slot_dict, **{'orig_answer': answer, constant.BIZ_FIELD: biz}))
                elif slot_temp.get(constant.SLOT_TEXT_HANDLER_FIELD):
                    answer[slot_temp[constant.SLOT_NAME_FIELD]] = \
                        slot_temp[constant.SLOT_TEXT_HANDLER_FIELD](
                            slot_temp[constant.SLOT_VALUE_FIELD], biz=biz, orig_answer=answer)
                else:
                    answer[slot_temp[constant.SLOT_NAME_FIELD]] = slot_temp[constant.SLOT_VALUE_FIELD]

        # 已经有answer了,进行诊断
        diagnose_fields = {'age': 'age',
                           'sex': 'sex',
                           'diagnose_chief_complaint': 'chief_complaint',  # 主诉
                           'diagnose_medical_history': 'medical_history',   # 现病史
                           # 'chief_complaint': 'chief_complaint',  # 主诉
                           # 'medical_history': 'medical_history',  # 现病史
                           'past_medical_history': 'past_medical_history',   # 既往史
                           'allergic_history': 'allergic_history',   # 过敏史
                           }
        # 自诊和预问诊都采用高覆盖
        params = {
            'rows': 5,
            'mode': 0,
            'source': constant.DIAGNOSE_SOURCE
        }
        if constant.BIZ_DICT[biz].get(constant.DIAGNOSE_PARAMS_FL):
            params['fl'] = constant.BIZ_DICT[biz][constant.DIAGNOSE_PARAMS_FL]
        for answer_field, diagnose_field in diagnose_fields.items():
            if answer.get(answer_field) and len(answer[answer_field]) > 0:
                answer_result = answer[answer_field]
                if 'age' == answer_field:
                    params[diagnose_field] = deal_diagnose_service_age(unicode2str(answer_result[0]))
                elif 'sex' == answer_field:
                    params[diagnose_field] = constant.diagnose_params_dict['sex'].get(unicode2str(answer_result[0]))
                else:
                    if isinstance(answer_result, list):
                        params[diagnose_field] = unicode2str(','.join(answer_result))
                    else:
                        params[diagnose_field] = unicode2str(answer_result)

        # 如果params里没有主诉,则返回空的diagnose
        if not params.get('chief_complaint'):
            answer['diagnose'] = []
            answer.pop('diagnose_medical_history', None)
            answer.pop('diagnose_chief_complaint', None)
            return answer

        try:
            diagnose_query = constant.aisc.query(params, 'diagnose_service', method='get')
            diagnose_result = []
            if diagnose_query and diagnose_query.get('data'):
                for data in diagnose_query['data']:
                    diagnose_result_temp = {}
                    for field, display_field in constant.BIZ_DICT[biz][constant.DIAGNOSE_FL].items():
                        if data.get(field):
                            data_value_temp = data[field]
                            if 'advice_code' == field:
                                data_value_temp = constant.DIAGNOSE_ADVICE_DICT[str(data_value_temp)]
                            diagnose_result_temp[display_field] = data_value_temp
                    diagnose_result.append(diagnose_result_temp)

            answer['diagnose'] = diagnose_result
            answer.pop('diagnose_medical_history', None)
            answer.pop('diagnose_chief_complaint', None)

        except Exception as err:
            logger.error(err)
            logger.error(constant.EXCEPTION_REMOTE % (
                'PreviousDiagnoseSlotManager_build_answer', 'diagnose_service', json.dumps(params)))
            raise Exception('诊断服务异常')
        # 对medical_history 进行处理,若对medical_history == 患者,置为空字符串
        if answer.get('medical_history') == '患者':
            answer['medical_history'] = ''
        return answer

    # def build_slot_answer(self, slots):
    #     """
    #     构建需要填槽的回答.
    #     参数:
    #     slots->已经填充完成的槽,结构:[{'name':,'value':,'ask':}]
    #     返回值->回答内容,结构:{key1:value1, key2:value2,...}
    #     """
    #     answer = {'answer': slots[0][self.SLOT_ASK_FIELD],
    #               'card_type': slots[0][self.SLOT_NAME_FIELD]}
    #     return answer
