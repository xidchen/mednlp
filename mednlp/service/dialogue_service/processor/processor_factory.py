#!/usr/bin/python
#encoding=utf-8

from default_doctor_processor import DefaultDoctorProcessor
from default_doctor_post_processor import DefaultDoctorPostProcessor
from default_hospital_processor import DefaultHospitalProcessor
from hospital_department_processor import HospitalDepartmentProcessor
from keyword_hospital_processor import KeywordHospitalProcessor
from keyword_doctor_processor import KeywordDoctorProcessor
from keyword_post_processor import KeywordPostProcessor
from hospital_processor import HospitalProcessor
from hospital_quality_processor import HospitalQualityProcessor
from hospital_nearby_processor import HospitalNearByProcessor
from department_processor import DepartmentProcessor
from haoyuan_refresh_processor import HaoyuanRefreshProcessor
from recent_haoyuan_time_processor import RecentHaoyuanTimeProcessor
from register_processor import RegisterProcessor
from greeting_processor import GreetingProcessor
from guide_processor import GuideProcessor
#from corpus_greeting_processor import CorpusGreetingProcessor
from result_department_processor import ResultDepartmentProcessor
from jingdong_default_doctor_processor import JingdongDefaultDoctorProcessor
from jingdong_hospital_processor import JingdongHospitalProcessor
from jingdong_keyword_hospital_processor import JingdongKeywordHospitalProcessor
from jingdong_keyword_doctor_processor import JingdongKeywordDoctorProcessor
from jingdong_keyword_post_processor import JingdongKeywordPostProcessor

processor_dict = {'department': DepartmentProcessor(),
                  'departmentConfirm': DefaultDoctorProcessor(),
                  'departmentAmong': DefaultDoctorProcessor(),
                  'departmentSubset': DefaultDoctorProcessor(),
                  'doctor': DefaultDoctorProcessor(),
                  'hospitalDepartment': HospitalDepartmentProcessor(),
                  'recentHaoyuanTime': RecentHaoyuanTimeProcessor(),
                  'doctorQuality': DefaultDoctorPostProcessor(),
                  'haoyuanRefresh': HaoyuanRefreshProcessor(),
                  'register': RegisterProcessor(),
                  'hospital': HospitalProcessor(),
                  'hospitalQuality': HospitalQualityProcessor(),
                  'hospitalNearby': HospitalNearByProcessor(),
		  'greeting': GreetingProcessor(),
                  'guide': GuideProcessor(),
		  #'corpusGreeting': CorpusGreetingProcessor()
		}

jingdong_processor_dict = {'department': ResultDepartmentProcessor(),
			    	'departmentConfirm': ResultDepartmentProcessor(),
				'departmentAmong': ResultDepartmentProcessor(),
				'departmentSubset': ResultDepartmentProcessor(),
				'doctor': JingdongDefaultDoctorProcessor(),
				'hospitalDepartment': JingdongDefaultDoctorProcessor(),
				'recentHaoyuanTime': JingdongDefaultDoctorProcessor(),
				'doctorQuality': JingdongDefaultDoctorProcessor(),
				'haoyuanRefresh': JingdongDefaultDoctorProcessor(),
				'register': JingdongDefaultDoctorProcessor(),
                  		'hospital': JingdongHospitalProcessor(),
				'hospitalQuality': JingdongHospitalProcessor(),
				'hospitalNearby': JingdongHospitalProcessor(),
				}

#def get_processor_instance(intention, entity_dict):
#    processor_instance = ''
#    if intention and intention not in ('others', 'greeting'):
#        processor_instance = processor_dict.get(intention)
#        if intention == 'keyword':
#            if 'departmentName' in entity_dict or 'doctorName' in entity_dict or 'diseaseName' in entity_dict:
#                processor_instance = KeywordDoctorProcessor()
#            elif 'departmentName' in entity_dict:
#                processor_instance = KeywordHospitalProcessor()
#            elif 'symptomName' in entity_dict or 'treatmentName' in entity_dict or 'medicineName' in entity_dict:
#                processor_instance = KeywordPostProcessor()
#    return processor_instance


def get_processor_instance(intention, entity_dict, intention_details, input_params={}):
    if input_params and input_params.get('mode') == 'loudspeaker_box':
	return get_jingdong_processor_instance(intention, entity_dict, intention_details)
    else:
	return get_xwyz_processor_instance(intention, entity_dict, intention_details) 

def get_xwyz_processor_instance(intention, entity_dict, intention_details):
     processor_instance = ''
     if intention and intention not in ('others'):
         processor_instance = processor_dict.get(intention, '')
         if intention == 'keyword' and intention_details:
             if intention_details[0] in ('department', 'doctor', 'disease'):
                 processor_instance = KeywordDoctorProcessor()
             elif intention_details[0] in ('hospital',):
                 processor_instance = KeywordHospitalProcessor()
             elif intention_details[0] in ('symptom', 'treatment', 'medicine'):
                 processor_instance = KeywordPostProcessor()
     return processor_instance

def get_jingdong_processor_instance(intention, entity_dict, intention_details):
     processor_instance = ''
     if intention and intention not in ('others'):
         processor_instance = jingdong_processor_dict.get(intention, '')
         if intention == 'keyword' and intention_details:
             if intention_details[0] in ('department', 'doctor', 'disease'):
                 processor_instance = JingdongKeywordDoctorProcessor() 
	     elif intention_details[0] in ('hospital',):
                 processor_instance = JingdongKeywordHospitalProcessor()
             elif intention_details[0] in ('symptom', 'treatment', 'medicine'):
                 processor_instance = JingdongKeywordPostProcessor()
     return processor_instance
	

