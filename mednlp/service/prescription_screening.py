#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: FH <fenghui@guahao.com>
Created on 2019/10/18 19:54
"""
import json

import global_conf
from ailib.utils.log import GLLog
from ailib.utils.exception import AIServiceException
from ailib.utils.exception import ArgumentLostException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.dao.prescription_screening_dao import PrescriptionScreeningDao

reason_medicine_check_dao = PrescriptionScreeningDao()
logger = GLLog('prescription_screening', log_dir=global_conf.out_log_dir, level='info').getLogger()


class PrescriptionScreening(BaseRequestHandler):
    not_none_field = ['source', 'doctor_user_id', 'age', 'sex',
                      'pregnancy_status', 'diagnosis', 'medicine']

    def initialize(self, runtime=None, **kwargs):
        super(PrescriptionScreening, self).initialize(runtime, **kwargs)

    def post(self):
        try:
            if self.request.body:
                input_obj = json.loads(self.request.body)
                self.get(input_obj=input_obj)
        except Exception:
            raise AIServiceException(self.request.body)

    def get(self, **kwargs):
        self.asynchronous_get(**kwargs)

    def _get(self, **kwargs):
        # 获取并检测参数
        input_obj = kwargs.get('input_obj')
        self.check_parameter(input_obj)

        # 返回结果字典与日志模板
        result = {'data': {}}
        log_template = '###interfaceStart###%s###interfaceEnd###'

        # 根据【患者】主诉信息获取症状列表
        chief_complaint = input_obj.get('chief_complaint', '')
        symptoms = reason_medicine_check_dao.extract_symptom(chief_complaint)
        input_obj['symptoms'] = symptoms

        # 获取【治疗方案】中的药品信息
        medicines = input_obj.get('medicine', [])
        if medicines:
            common_prescription_names = []
            medicine_ids = set()
            for medicine in medicines:
                medicine_id = medicine.get('medicine_id')
                common_name = medicine.get('common_name')
                if medicine_id:
                    medicine_ids.add(medicine_id)
                if common_name:
                    common_prescription_names.append(common_name)

            # 根据药品ID获取药品信息
            medicine_infos = {}
            if medicine_ids:
                medicine_infos = reason_medicine_check_dao.get_medicine_info(medicine_ids)
                for medicine in medicines:
                    # 从【治疗方案】中获取的药品信息
                    medicine_id = medicine.get('medicine_id', '')
                    common_name = medicine.get('common_name', '')
                    specification = medicine.get('common_name', '')

                    # 从【处方共享平台】获取的药品信息
                    medicine_info_dt = medicine_infos.get(medicine_id, {})
                    if medicine_info_dt:
                        if not common_name:
                            medicine['common_name'] = medicine_info_dt.get('common_name', '')
                            common_prescription_names.append(common_name)
                        if specification:
                            medicine['specification'] = medicine_info_dt.get('specification', '')
            input_obj['common_prescription_names'] = common_prescription_names

            # 从本地json文件中获取合理用药药品信息
            common_prescription_names = set(common_prescription_names)
            reason_medicine_infos = reason_medicine_check_dao.get_data_from_local(common_prescription_names)

            # 根据合理用药json解析出来的信息提供合理用药提示
            if reason_medicine_infos:
                for medicine in medicines:
                    result['data'] = reason_medicine_check_dao.check_all_field(
                        medicine=medicine,
                        medicine_infos=medicine_infos,
                        reason_medicine_infos=reason_medicine_infos,
                        input_obj=input_obj,
                        result=result['data']
                    )
        # 接口日志信息
        input_obj['interface'] = '合理用药检测'
        input_obj['result'] = result['data']
        input_obj['is_tip'] = 0
        for tip_obj in result['data'].values():
            for tip in tip_obj.values():
                if tip:
                    input_obj['is_tip'] = 1
        logger.info(log_template % json.dumps(input_obj, ensure_ascii=False))
        return result

    def check_parameter(self, parameters):
        """
        检测接口入参必填项是否填写
        :param parameters: 必填参数列表
        :return: 如果必填项未填写，则直接报错
        """
        for field in self.not_none_field:
            if self.get_argument('source', ''):
                if not self.get_argument(field, ''):
                    raise ArgumentLostException([field])
            else:
                if field not in parameters:
                    raise ArgumentLostException([field])


if __name__ == '__main__':
    handlers = [(r'/prescription_screening', PrescriptionScreening, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
