# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify_model.py -- the service of dept_classify

Author: caoxg <caoxg@guahao.com>
Create on 2018-6-29 星期三.
"""


import os
import sys
import time
import re
from ailib.model.base_model import BaseModel
import global_conf
from ailib.storage.db import DBWrapper
from ailib.client.ai_service_client import AIServiceClient
import json


class CheckPrescriptionModel(BaseModel):
    def initialize(self, **kwargs):
        """
        初始化数据库连接，装载处方模板中的所有数据
        :param kwargs: 
        :return: 无
        """
        self.db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB')
        self.load_data()
        self.search = AIServiceClient(cfg_path=global_conf.cfg_path,
                                      service='SearchService')

    def load_data(self):
        """
        装载数据库中处方模板中的数据并关联药品数据
        :return: 无
        """
        sql = """
        select
            sp.department_name,
            sp.patient_sex,
            sp.diagnosis,
            cp.name  common_name,
            sp.specification,
            sp.number,
            sp.administration_route,
            sp.dose,
            sp.frequency,
            sp.days,
            sp.doctor_title,
            sp.allergic
        from  ai_union.std_prescription sp
        inner join medicine.common_preparation  cp 
        on sp.common_preparation_uuid = cp.id 
        where sp.is_deleted = 0
        """
        prescriptions = self.db.get_rows(sql)
        medical_dict = {}
        key_field = ['patient_sex', 'common_name', 'specification', 'number',
                     'administration_route', 'frequency', 'dose', 'days',
                     'diagnosis']
        for p in prescriptions:
            key_list = [str(p[field]) for field in key_field if p[field]]
            key = '|'.join(key_list)
            dept_name = p['department_name']
            allergic = str(p['allergic'])
            doctor_title = int(p['doctor_title']) if p.get('doctor_title') and p['doctor_title'] else 1
            dept_allergic = medical_dict.setdefault(key, [])
            dept_allergic.append({'dept_name': dept_name, 'doctor_title': doctor_title,'allergic': allergic})
        self.medical_dict = medical_dict

    def _get_doctor_dept(self, doctor_user_id):
        """
        通过医生的user_id查找医生所在的科室
        :return: 医生所在的科室
        """
        pre_depts = [u'耳鼻咽喉头颈科', u'妇产科', u'眼科', u'外科', u'内科', u'中医科']
        res = self.search.query({'weiyi_doctor': doctor_user_id, 'fl': 'standard_department_detail,doctor_technical_title'},
                                service='doctor_search', method='get')
        doctor_title = 1
        depts = []
        if not (res['code'] == 0 and res['count'] == 1 and res['docs']
                and res["docs"][0].get("standard_department_detail")):
            return depts, doctor_title
        if len(res["docs"][0]["standard_department_detail"]) > 1:  # 医生有多个一级科室时返回空列表
            return [], doctor_title
        if res["docs"][0].get('doctor_technical_title'):
            doctor_technical_title = res["docs"][0].get('doctor_technical_title')
            if doctor_technical_title == '主治医师':
                doctor_title = 2
            elif doctor_technical_title == '副主任医师':
                doctor_title = 3
            elif doctor_technical_title == '主任医师':
                doctor_title = 4
        for detail in res["docs"][0]["standard_department_detail"]:
            items = detail.strip().split('|')
            # 20190514-暂时放开对科室的限制，使数据中的科室都可以生效(此为临时方案)
            # if len(items) >= 2 and items[1] in pre_depts:
            #     depts.append(str(items[1]))
            for index in range(1, len(items), 2):  # 20190514-暂时放开对科室的限制
                depts.append(str(items[index]))
        return list(set(depts)), doctor_title

    def predict(self, doctor_user_id='123123147302', sex=2, age=1, diagnosis='', pregnancy_status=0, medicine={}):
        """
        :param sex: 患者的性别
        :param age: 患者的年龄
        :param diagnosis: 医生诊断
        :param pregnancy_status: 患者状态
        :param medicine: 药品信息（包含药品通用名、药品规格、药品大包装数量，盒等，给药频次，用药剂量，用药天数，过敏信息）
        :return: 返回给处方是否合规
        """
        reason = '处方在数据库中不存在'
        if pregnancy_status != 0:
            reason = '患者状态不合格'
            return 0, reason
        if age < 19 or age > 64:
            print('age_true')
            reason = '患者年龄不合格'
            return 0, reason
        dept_name, doctor_title = self._get_doctor_dept(doctor_user_id)
        # 20190514-暂时放开对科室的限制，使数据中的科室都可以生效(此为临时方案)
        # if not dept_name or len(dept_name) > 1:
        #     reason = '医生科室不合格:%s'
        #     reason = reason % (' '.join(dept_name))
        #     return 0, reason
        if not dept_name:  # 20190514-暂时放开对科室的限制
            reason = '医生科室不合格:%s'
            reason = reason % (' '.join(dept_name))
            return 0, reason
        _sex = '0'
        if str(sex) == '1':
            _sex = '2'
        elif str(sex) == '2':
            _sex = '1'
        medicine_key_list = [str(_sex), ]
        medicine_key_field = ['name', 'specification', 'number',
                              'administration_route', 'frequency',
                              'dose', 'days']
        for field in medicine_key_field:
            medicine_key_list.append(str(medicine[field]))
        medicine_key_list.append(str(diagnosis))
        allergic_str = str(medicine.get('allergic', ''))
        if not allergic_str:
            allergic = '0'
        elif allergic_str == "继用":
            allergic = '1'
        else:
            allergic = '2'
        medicine_key = '|'.join(medicine_key_list)
        dept_allergic = self.medical_dict.get(medicine_key, [])
        for info in dept_allergic:
            # 20190514-暂时放开对科室的限制，使数据中的科室都可以生效(此为临时方案)
            # if dept_name[0] != info.get('dept_name'):
            #     continue
            if info.get('dept_name', '') not in dept_name:
                continue
            if info['allergic'] == '0' or allergic == info['allergic']:
                if info.get('doctor_title') > doctor_title:
                    reason = '医生职称不合格'
                    continue
                return 1, '处方合格'
        return 0, reason
