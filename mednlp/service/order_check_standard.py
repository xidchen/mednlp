#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-07-29 Monday
@Desc:	业务质检服务
"""

import json
import codecs
import global_conf
from mednlp.model.order_check_standard_model import OrderCheckStandardModel


class OrderCheckStandard():

    def __init__(self):
        self.is_proactive_model = OrderCheckStandardModel(cfg_path=global_conf.cfg_path, check_type='is_proactive')
        self.is_detailed_model = OrderCheckStandardModel(cfg_path=global_conf.cfg_path, check_type='is_detailed')
        self.is_clear_model = OrderCheckStandardModel(cfg_path=global_conf.cfg_path, check_type='is_clear')
        self.is_warm_model = OrderCheckStandardModel(cfg_path=global_conf.cfg_path, check_type='is_warm')
        self.is_review_model = OrderCheckStandardModel(cfg_path=global_conf.cfg_path, check_type='is_review')

        self.check_type_dict = {
            '2': self.is_proactive,
            '3': self.is_detaile,
            '4': self.is_clear_m,
            '5': self.is_warm,
            '6': self.is_review
        }

    def _get_doctor_reply(self, consult_info):
        reply_list = consult_info.get('doctor_reply_list', [])
        return '|'.join(filter(lambda r: not (r.startswith('通话时长') or r in ('已拒绝', '对方已拒绝，点击重拨')), reply_list))

    def is_proactive(self, consult_info):
        "2 - 主动问诊"
        doctor_reply = self._get_doctor_reply(consult_info)
        if not doctor_reply:
            return None
        model_result = self.is_proactive_model.predict(doctor_reply)
        if not model_result:
            # 默认合规
            return None
        if model_result[0][1] < 0.6:
            return None
        elif model_result[0][0] == 0:
            return False
        else:
            return True

    def is_detaile(self, consult_info):
        "3 - 疾病分析细致"
        doctor_reply = self._get_doctor_reply(consult_info)
        if not doctor_reply:
            return None
        model_result = self.is_detailed_model.predict(doctor_reply)
        if not model_result:
            # 默认合规
            return None
        if model_result[0][1] < 0.6:
            return None
        elif model_result[0][0] == 0:
            return False
        else:
            return True

    def is_clear_m(self, consult_info):
        "4 - 明确指导意见"
        doctor_reply = self._get_doctor_reply(consult_info)
        if not doctor_reply:
            return None
        model_result = self.is_clear_model.predict(doctor_reply)
        if not model_result:
            # 默认合规
            return None
        if model_result[0][1] < 0.7:
            return None
        elif model_result[0][0] == 0:
            return False
        else:
            return True

    def is_clear_r(self, consult_info):
        consult_reply_type_list = consult_info.get('consult_reply_type_list')
        doctor_reply_list = list(filter(lambda x: x.startswith('1|'), consult_reply_type_list))
        # 语音回复暂不处理
        for reply in doctor_reply_list:
            if '语音回复' in reply:
                return None
            if '看看' in reply:
                return None
            if '可以' in reply:
                return None

        patient_continue_ask_count = 0
        for reply in consult_reply_type_list:
            if reply.startswith('0|'):
                patient_continue_ask_count += 1
                if patient_continue_ask_count > 2:
                    return False
            elif reply.startswith('1|'):
                patient_continue_ask_count = 0

        return True

    def is_warm(self, consult_info):
        "5 - 有温度"
        doctor_reply = self._get_doctor_reply(consult_info)
        if not doctor_reply:
            return None
        model_result = self.is_warm_model.predict(doctor_reply)
        if not model_result:
            # 默认合规
            return None
        if model_result[0][1] < 0.6:
            return None
        elif model_result[0][0] == 0:
            return False
        else:
            return True

    def is_review(self, consult_info):
        if self.is_review_r(consult_info):
            return True
        return self.is_review_m(consult_info)

    def is_review_m(self, consult_info):
        "6 复诊指导 - 模型"
        doctor_reply = self._get_doctor_reply(consult_info)
        if not doctor_reply:
            return None
        model_result = self.is_review_model.predict(doctor_reply)
        if not model_result:
            return None
        if model_result[0][1] < 0.8:
            return None
        elif model_result[0][0] == 0:
            return False
        else:
            return True

    def is_review_r(self, consult_info):
        "6 复诊指导 - 规则"

        doctor_reply_list = consult_info.get('doctor_reply_list', [])
        doctor_reply = ''
        for drl in doctor_reply_list:
            #  TODO: <29-08-19, chaipf> # 过滤无意义内容：语音、病历
            doctor_reply += drl

        for key in ('复诊', '复查', '找我看下', '问我', '关注我', '咨询我'):
            if key in doctor_reply:
                return True
        return False

    def order_check(self, consult_info, check_codes=['2', '3', '4', '5', '6']):
        compliance_codes = []
        violation_codes = []
        unchecked_code = []

        for code in check_codes:
            func = self.check_type_dict[code]
            check_result = func(consult_info)
            if check_result is None:
                unchecked_code.append(str(code))
                continue
            if check_result:
                compliance_codes.append(str(code))
            else:
                violation_codes.append(str(code))
        return compliance_codes, violation_codes, unchecked_code


if __name__ == '__main__':
    # consult_info = {'doctor_reply_list': ["你好", "你好", "这种情况考虑可能还是受孕时间晚", "现在查血hcg就能够确定是否怀孕了，假如怀孕时间太短，b超是看不出来的。明天去查血看看。", "不客气", "化验结果提示怀孕", "hcg不能确定怀孕具体时间", "可以一周后复查B超看看"]}
    # print(order_check(consult_info))
    ocs = OrderCheckStandard()
    ocs.order_check('4l4be2d0l7191031081727506')
