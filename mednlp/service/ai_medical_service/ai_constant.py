#!/usr/bin/python
# encoding=utf-8

from ailib.client.ai_service_client import AIServiceClient
from ailib.utils.log import GLLog
import global_conf

logger = GLLog('medical_service_input_output', level='info',
               log_dir=global_conf.log_dir).getLogger()

ac = AIServiceClient(global_conf.cfg_path, 'AIService')

RESULT_EXTENDS_FIELDS = (
    'departmentId', 'departmentName', 'doctorId', 'doctorName',
    'diseaseId', 'diseaseName', 'hospitalId', 'hospitalName',
    'treatmentId', 'treatmentName', 'medicineId', 'medicineName',
    'symptomId', 'symptomName', 'cityId', 'cityName',
    'provinceId', 'provinceName')

# 医生的默认回复列表（也用来处理返回标签的，返回标签的顺序和这个列表有关，不要轻易修改）
doctor_return_list = ['doctor_uuid', 'doctor_photo_absolute',
                      'doctor_name', 'doctor_technical_title',
                      'hospital_department_detail',
                      'specialty_disease', 'doctor_recent_haoyuan_detail',
                      'doctor_haoyuan_time', 'doctor_haoyuan_detail',
                      'is_service_package', 'is_health', 'sns_user_id',
                      'comment_score', 'total_order_count', 'is_patient_praise',
                      'base_rank', 'contract_register',
                      'is_consult_serviceable', 'doctor_introduction', 'feature',
                      'doctor_consult_detail', 'is_consult_phone', 'phone_consult_fee',
                      'serve_type', 'accurate_package_code', 'accurate_package_price'
                      ]

# 医院的返回列表
hospital_return_list = ['hospital_uuid', 'hospital_name', 'hospital_level',
                        'hospital_photo_absolute', 'order_count',
                        'hospital_hot_department', 'distance_desc',
                        'hospital_rule', 'hospital_standard_department',
                        'hospital_department']

# 文章的返回列表
post_return_list = ['topic_id', 'title', 'topic_content_nohtml',
                    'topic_nick_name', 'topic_technical_title',
                    'view_count', 'vote_count',
                    'title_highlight', 'topic_content_nohtml_highlight',
                    'nick_name', 'topic_type', 'content', 'content_highlight',
                    'help_show_type', 'technical_title_name',
                    'topic_vote_count', 'topic_view_count']

# ai返回的id转化医生solr字段
doctor_params_dict = {
    'departmentName': 'department_aliases',
    'doctorId': 'doctor_uuid',
    'diseaseName': 'disease',
    'hospitalId': 'hospital_uuid',
    'cityId': 'city_id',
    'provinceId': 'province_id'
}

hospital_params_dict = {
    'hospitalId': 'hospital_uuid',
    'cityId': 'city_id',
    'provinceId': 'province_id',
    'diseaseName': 'hospital_diseases',
    'departmentName': 'hospital_standard_department'
}

ai_params_dict = {'doctor': doctor_params_dict,
                  'hospital': hospital_params_dict}

return_list_dict = {'doctor': doctor_return_list,
                    'hospital': hospital_return_list,
                    'post': post_return_list}

post_params_list = ['treatmentName', 'symptomName', 'medicineName',
                    'doctorName', 'departmentName', 'diseaseName',
                    'postDoctorName']

q_field_dict = {'doctor': ['departmentName', 'doctorName', 'diseaseName',
                           'hospitalName'],
                'hospital': ['hospitalName', 'departmentName', 'diseaseName'],
                'post': ['treatmentName', 'symptomName', 'medicineName']}

# ai转化接口参数

doctor_search_params = {'hospitalId': 'hospital',
                        'departmentId': 'department',
                        'doctorId': 'doctor',
                        'diseaseName': 'disease_name',
                        'provinceId': 'province',
                        'cityId': 'city'
                        }

hospital_search_params = {'hospitalId': 'hospital',
                          'provinceId': 'province',
                          'cityId': 'city'
                          }

ai_search_params_dict = {'doctor': doctor_search_params,
                         'hospital': hospital_search_params}

# intentionDetail字段和返回字段值的对应关系
q_intention_dict = {'symptom': 'symptomName',
                    'disease': 'diseaseName',
                    'department': 'departmentName',
                    'hospital': 'hospitalName',
                    'treatment': 'treatmentName',
                    'medicine': 'medicineName',
                    'doctor': 'doctorName'}

# keyword意图对应的q在ai返回内容中的取值范围
keyword_q_param_name = ('symptomName', 'diseaseName', 'departmentName', 'hospitalName',
                        'treatmentName', 'medicineName', 'doctorName', 'body_partName',
                        'medicalWordName', 'examinationName')

# 调用医院搜索接口中默认的参数
hospital_search_params = {'rows': '3',
                          'start': '0',
                          'do_spellcheck': '1',
                          'dynamic_filter': '1',
                          'opensource': '9',
                          'wait_time': 'all'}

# 调用医生搜索接口中默认的参数
doctor_search_params = {'rows': '18',
                        'start': '0',
                        'do_spellcheck': '1',
                        'travel': '0',
                        'sort': 'general',
                        'secondsort': '0',
                        'aggr_field': 'contract_register',
                        'opensource': '9'}

# 调用文章搜索接口中默认的参数
post_search_params = {'rows': '50',
                      'start': '0',
                      'sort': 'help_general',
                      'topic_type': '1,3',
                      'exclude_type': '2',
                      'highlight': '1',
                      'highlight_scene': '1',
                      'exclude_post_heat_status': '1',
                      'digest': '2'
                      }

# 默认的标签对象和对应的默认参数值构成的字典
default_search_params_dict = {'doctor': doctor_search_params,
                              'hospital': hospital_search_params,
                              'post': post_search_params}

# 标签对象和对应的搜索url后缀构成的字典
url_dict = {'doctor': '/doctor_search?',
            'hospital': '/hospital_search?',
            'post': '/post_service?',
            'service_package': '/service_package?',
            'search_dept': '/department_search?',
            'ai_dept': '/dept_classify_interactive?',
            'sentence_similarity': '/sentence_similarity?',
            'tag_service': '/tag_service?',
            'std_dept': '/std_department?'}

# 标签对应的返回内容中，json解析时的名字
return_json = {'doctor': 'docs',
               'hospital': 'hospital',
               'search_dept': 'department'}

# 引导语列表
guiding_list = [{'list': [{'text': '头痛发烧'},
                          {'text': '失眠挂什么科'},
                          {'text': '骨科上海哪家医院好'},
                          {'text': '糖尿病哪位医生好'},
                          {'text': '哪个医院看颈椎病好'},
                          {'text': '幽门螺旋杆菌怎么治疗'},
                          {'text': '傅雯雯医生什么时候放号'},
                          {'text': '张平医生怎么样'},
                          ]},
                {'title': '分科', 'list': [{'text': '头疼挂什么科'}],
                 'introduction': '告诉我症状，为您匹配对应的就诊科室'},
                {'title': '选医院', 'list': [{'text': '上海肿瘤哪家医院好'}]},
                {'title': '找医生', 'list': [{'text': '糖尿病哪位医生好'}]},
                {'title': '查资讯', 'list': [{'text': '过敏性鼻炎注意事项'},]}
                ]

baike_trans = {
    'word_id': 'word_id',
    'name': 'word_name',
    'name_highlight': 'word_name_highlight',
    'introduction': 'word_introduction',
    'type': 'word_type'
}

post_trans = {
    'topic_id': 'topic_id',
    'topic_type': 'topic_type',
    'title': 'topic_title',
    'title_highlight': 'topic_title_highlight',
    'topic_content_nohtml': 'topic_content_nohtml',
    'topic_content_nohtml_highlight': 'topic_content_nohtml_highlight',
    'content': 'post_content',
    'content_highlight': 'post_content_highlight',
    'topic_nick_name': 'topic_nick_name',
    'topic_technical_title': 'topic_technical_title',
    'topic_vote_count': 'topic_vote_count',
    'topic_view_count': 'topic_view_count',
    'vote_count': 'post_vote_count',
    'view_count': 'post_view_count',
    'nick_name': 'post_nick_name',
    'help_show_type': 'help_show_type',
    'technical_title_name': 'post_technical_title_name'
}
