#!/usr/bin/python
#encoding=utf-8

from mednlp.service.ai_medical_service.default_doctor_intention import DefaultDoctorIntention
from mednlp.service.ai_medical_service.default_doctor_post_intention import DefaultDoctorPostIntention
from mednlp.service.ai_medical_service.default_hospital_intention import DefaultHospitalIntention
from mednlp.service.ai_medical_service.hospital_department_intention import HospitalDepartmentIntention
from mednlp.service.ai_medical_service.keyword_hospital_intention import KeywordHospitalIntention
from mednlp.service.ai_medical_service.keyword_doctor_intention import KeywordDoctorIntention
from mednlp.service.ai_medical_service.keyword_post_intention import KeywordPostIntention
from mednlp.service.ai_medical_service.hospital_intention import HospitalIntention
from mednlp.service.ai_medical_service.hospital_quality_intention import HospitalQualityIntention
from mednlp.service.ai_medical_service.hospital_nearby_intention import HospitalNearByIntention
from mednlp.service.ai_medical_service.department_intention import DepartmentIntention
from mednlp.service.ai_medical_service.haoyuan_refresh_intention import HaoyuanRefreshIntention
from mednlp.service.ai_medical_service.recent_haoyuan_time_intention import RecentHaoyuanTimeIntention
from mednlp.service.ai_medical_service.register_intention import RegisterIntention
from mednlp.service.ai_medical_service.auto_diagnose_intention import AutoDiagnoseIntention
from mednlp.service.ai_medical_service.department_classify_intention import DepartmentClassifyIntention
from mednlp.service.ai_medical_service.new_default_hospital_intention import NewDefaultHospitalIntention
from mednlp.service.ai_medical_service.customer_service_intention import CustomerServiceIntention
from mednlp.service.ai_medical_service.greeting_intention import GreetingIntention
from mednlp.service.ai_medical_service.sensitive_intention import SensitiveIntention

intention_dict = {'department': DepartmentClassifyIntention(),
                  'departmentConfirm': DepartmentIntention(),
                  'departmentAmong': DepartmentIntention(),
                  'departmentSubset': DepartmentIntention(),
                  'doctor': DefaultDoctorIntention(),
                  'hospitalDepartment': HospitalDepartmentIntention(),
                  'recentHaoyuanTime': RecentHaoyuanTimeIntention(),
                  'doctorQuality': DefaultDoctorPostIntention(),
                  'haoyuanRefresh': HaoyuanRefreshIntention(),
                  'register': RegisterIntention(),
                  'hospital': NewDefaultHospitalIntention(),
                  'hospitalQuality': HospitalQualityIntention(),
                  'hospitalNearby': HospitalNearByIntention(),
                  'auto_diagnose': AutoDiagnoseIntention(),
                  'corpusGreeting': GreetingIntention(),
                  'greeting': GreetingIntention(),
                  'customerService': CustomerServiceIntention(),
                  'guide': GreetingIntention(),
                  'sensitive': SensitiveIntention()
                  #'new_hospital': NewDefaultHospitalIntention(),
                  #'department_classify': DepartmentClassifyIntention()
                 }
                  

def get_intention_instance(ai_result):
    intention_instance = ''
    if 'intention' in ai_result and ai_result['intention'] not in ('others'):
        intention = ai_result['intention']
        intention_instance = intention_dict.get(intention)
        if intention == 'keyword' and ai_result.get('intentionDetails'):
            if ai_result['intentionDetails'][0] in ('department', 'doctor', 'disease'):
                intention_instance = KeywordDoctorIntention()
            elif ai_result['intentionDetails'][0] in ('hospital',):
                intention_instance = KeywordHospitalIntention()
            elif ai_result['intentionDetails'][0] in ('symptom', 'treatment', 'medicine'):
                intention_instance = KeywordPostIntention()
            else:
                intention_instance = KeywordPostIntention()
    return intention_instance


