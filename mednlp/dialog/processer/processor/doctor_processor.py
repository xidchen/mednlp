# !/usr/bin/env python
# encoding=utf-8

import json
from mednlp.dialog.processer.processor.basic_processor_v2 import BasicProcessor
from mednlp.dialog.configuration import Constant as constant
import mednlp.dialog.processer.ai_search_common as ai_search_common


class DoctorProcessor(BasicProcessor):
    # 处理返回医生的意

    default_rows = 2

    fl_return_dict = {
        'doctor_photo_absolute': 'doctor_picture',
        'doctor_uuid': 'doctor_uuid',
        'doctor_name': 'doctor_name',
        'doctor_technical_title': 'doctor_title',
        'hospital_department_detail': '',   # hospital_uuid,hospital_name,department_uuid,department_name
        'doctor_recent_haoyuan_detail': '',     # recent_haoyuan_date, recent_haoyuan_time, haoyuan_fee
        'comment_score': 'comment_score',
        'total_order_count': 'total_order_count',
        'specialty_disease': '',    # specialty_disease
        'doctor_haoyuan': 'doctor_haoyuan'
    }

    def initialize(self):
        self.search_params = {
            'start': '0',
            'rows': self.default_rows,
            # 'contract': '1',
            # 'do_spellcheck': '1',
            # 'travel': '0',
            'sort': 'general',
            # 'secondsort': '0',
            # 'aggr_field': 'contract_register',
            'opensource': '27'
        }

    def process(self, query, **kwargs):
        """
        doctor_search参数组装,q有则查，无则返回空list
        查doctor_search有一个区域扩展功能
        :param query:
        :param kwargs:
        :return:
        {
            doctor_search:[],
            is_end:1,
            code:0
        }

        http://192.168.1.46:2000/mtc_doctor_search?start=0&rows=6&contract=1&do_spellcheck=1&travel=0&sort=general&
        secondsort=0&aggr_field=contract_register&q=神经内科&city=552&province=24&
        ai_organization=993c190641e846d7bc3eaf57abfee3aa&fl=doctor_uuid,doctor_photo_absolute,doctor_name,
        doctor_technical_title,hospital_department_detail,specialty_disease,doctor_recent_haoyuan_detail,
        doctor_haoyuan_time,doctor_haoyuan_detail,is_service_package,is_health,sns_user_id,comment_score,
        total_order_count

        # 正确：
        http://192.168.1.46:2000/mtc_doctor_search?debug=1&start=0&rows=12&sort=general&q=胃痛&city=552&province=24
        &organize_code=c9ace68e78c345489bcf3007f9c04f6a&fl=doctor_photo_absolute,doctor_uuid,doctor_name,
        doctor_technical_title,hospital_department_detail,doctor_recent_haoyuan_detail,
        comment_score,total_order_count,specialty_disease,doctor_haoyuan

        http://192.168.1.46:2000/service_package?rows=100&fl=expert_id,package_code&sort=general&
        expert=7246449b-b587-47d1-bce6-22f48ada51c1000,CCF26DB04E8E1DF9E040A8C0790228AB000,
        521a8a61-9b6c-409b-a2e0-c8893a4654b8000
        """
        result = {}
        self.set_rows()
        self.set_params(query, **kwargs)    # set ai_result + input_params
        _params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        if not q_content:
            _params['q'] = self.input_params.get('input', {}).get('q')
        # 添加省份,城市参数
        self.search_params.update(_params)
        # 上层指定的q,比如departmentProcess
        if kwargs.get('ceil_q'):
            self.search_params['q'] = kwargs['ceil_q']

        # 获取hospital_relation
        hospital_relation = self.intention_conf.configuration.hospital_relation
        hospital_ids = [temp['hospital_uuid'] for temp in hospital_relation if temp.get('hospital_uuid')]
        if constant.CONFIG_HOSPITAL_SOURCE_ALL != self.intention_conf.configuration.hospital_source:
            # hospital_source配置成 非 全平台医院
            if not hospital_ids:
                # 医院没配，肯定找不到医生,也就不需要严格依赖于搜索了
                result['code'] = 0
                result['is_end'] = 1
                return result
            organization_id = self.intention_conf.configuration.organization
            self.search_params['organize_code'] = organization_id

        self.search_params['fl'] = ','.join(self.fl_return_dict.keys())
        response, area = ai_search_common.get_extend_response(self.search_params, self.input_params, 'mtc_doctor')
        doctor_data = self.get_doctor_data(response, hospital_ids=hospital_ids)
        if doctor_data:
            result[constant.QUERY_KEY_DOCTOR_SEARCH] = doctor_data
        result['code'] = response['code']
        result['search_params'] = self.search_params
        result['is_end'] = 1
        return result

    def set_rows(self):
        self.search_params['rows'] = super(
            DoctorProcessor, self).basic_set_rows(1, default_rows=self.default_rows)

    def get_doctor_data(self, response, hospital_ids):
        result = []
        if response and response.get('totalCount', 0) > 0:
            for temp in response.get('data', []):
                doctor_temp = {}
                for fl_key, return_key in self.fl_return_dict.items():
                    if fl_key in temp:
                        if 'hospital_department_detail' == fl_key:
                            hosp_dept_temps = temp[fl_key]
                            if not hosp_dept_temps:
                                continue
                            self.deal_hospital_department_detail(doctor_temp, hosp_dept_temps, hospital_ids)
                        elif 'specialty_disease' == fl_key:
                            doctor_temp['specialty_disease'] = [disease.split(
                                '|')[1] for disease in temp[fl_key] if disease]
                        elif 'doctor_recent_haoyuan_detail' == fl_key:
                            recent_haoyuan = temp[fl_key].split('|')
                            doctor_temp['recent_haoyuan_date'] = recent_haoyuan[1]
                            doctor_temp['recent_haoyuan_time'] = recent_haoyuan[2]
                            doctor_temp['haoyuan_fee'] = recent_haoyuan[5]
                        else:
                            doctor_temp[return_key] = temp[fl_key]
                result.append(doctor_temp)
        return result

    def deal_hospital_department_detail(self, doctor_dict, hosp_dept_info, hospital_ids):
        if constant.CONFIG_HOSPITAL_SOURCE_ALL != self.intention_conf.configuration.hospital_source:
            # 如果没有配置全平台医院,数据库配了什么医院,找这家医院的数据出来即可
            for hosp_dept_temp in hosp_dept_info:
                hosp_dept_details = hosp_dept_temp.split('|')
                for hospital_id_temp in hospital_ids:
                    if hospital_id_temp == hosp_dept_details[0]:
                        doctor_dict['hospital_uuid'] = hosp_dept_details[0]
                        doctor_dict['hospital_name'] = hosp_dept_details[1]
                        doctor_dict['department_uuid'] = hosp_dept_details[2]
                        doctor_dict['department_name'] = hosp_dept_details[3]
                        break
            return
        """
        # 如果配置了全平台医院,则按照搜索词来定
        1.科室名和医院名   与医院科室名和医院名匹配, 若无则与标准科室名和医院名匹配
        2.科室名  与医院科室名匹配, 若无则与标准科室名匹配
        3.1和2都无则取第一家医院
        """
        hosp_uuid = ''
        hosp_name = ''
        dept_uuid = ''
        dept_name = ''
        if 'departmentName' in self.ai_result and 'hospitalName' in self.ai_result:
            # 对应1
            for hosp_dept_temp in hosp_dept_info:
                hosp_dept_details = hosp_dept_temp.split('|')
                if (hosp_dept_details[3] in self.ai_result.get(
                        'departmentName') and hosp_dept_details[1] in self.ai_result['hospitalName']):
                    # 医院 和 医院科室名匹配上
                    hosp_uuid = hosp_dept_details[0]
                    hosp_name = hosp_dept_details[1]
                    dept_uuid = hosp_dept_details[2]
                    dept_name = hosp_dept_details[3]
            if not hosp_uuid:
                for hosp_dept_temp in hosp_dept_info:
                    hosp_dept_details = hosp_dept_temp.split('|')
                    if (hosp_dept_details[5] in self.ai_result.get(
                            'departmentName') and hosp_dept_details[1] in self.ai_result['hospitalName']):
                        hosp_uuid = hosp_dept_details[0]
                        hosp_name = hosp_dept_details[1]
                        dept_uuid = hosp_dept_details[2]
                        dept_name = hosp_dept_details[3]
        if not hosp_uuid and 'departmentName' in self.ai_result:
            # 对应2
            for hosp_dept_temp in hosp_dept_info:
                hosp_dept_details = hosp_dept_temp.split('|')
                if hosp_dept_details[3] in self.ai_result['departmentName']:
                    hosp_uuid = hosp_dept_details[0]
                    hosp_name = hosp_dept_details[1]
                    dept_uuid = hosp_dept_details[2]
                    dept_name = hosp_dept_details[3]
            if not hosp_uuid:
                for hosp_dept_temp in hosp_dept_info:
                    hosp_dept_details = hosp_dept_temp.split('|')
                    if hosp_dept_details[5] in self.ai_result['departmentName']:
                        hosp_uuid = hosp_dept_details[0]
                        hosp_name = hosp_dept_details[1]
                        dept_uuid = hosp_dept_details[2]
                        dept_name = hosp_dept_details[3]
        if not hosp_uuid:
            # 对应3
            hosp_dept_details = hosp_dept_info[0].split('|')
            hosp_uuid = hosp_dept_details[0]
            hosp_name = hosp_dept_details[1]
            dept_uuid = hosp_dept_details[2]
            dept_name = hosp_dept_details[3]
        doctor_dict['hospital_uuid'] = hosp_uuid
        doctor_dict['hospital_name'] = hosp_name
        doctor_dict['department_uuid'] = dept_uuid
        doctor_dict['department_name'] = dept_name
        return