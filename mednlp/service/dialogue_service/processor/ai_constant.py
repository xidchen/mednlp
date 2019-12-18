#!/usr/bin/python
#encoding=utf-8

#医生的默认回复列表（也用来处理返回标签的，返回标签的顺序和这个列表有关，不要轻易修改）
doctor_return_list = ['doctor_uuid', 'doctor_photo_absolute',
                        'doctor_name', 'doctor_technical_title',
                        'hospital_department_detail',
                        'specialty_disease', 'doctor_recent_haoyuan_detail',
                        'doctor_haoyuan_time', 'doctor_haoyuan_detail',
                        'is_service_package','is_health', 'sns_user_id',
                        'comment_score', 'total_order_count']

#医院的返回列表
hospital_return_list = ['hospital_uuid', 'hospital_name', 'hospital_level',
                        'hospital_photo_absolute', 'order_count',
                        'hospital_hot_department', 'distance_desc',
                        'hospital_rule', 'hospital_standard_department',
                        'hospital_department']

#文章的返回列表
post_return_list = ['topic_id', 'title', 'topic_content_nohtml',
                    'topic_nick_name', 'topic_technical_title',
                    'view_count', 'vote_count',
                    'title_highlight', 'topic_content_nohtml_highlight',
                    'nick_name', 'topic_type', 'content', 'content_highlight',
                    'help_show_type', 'technical_title_name']

#ai返回的id转化医生solr字段
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

q_field_dict = {'doctor':['departmentName', 'doctorName', 'diseaseName',
                          'hospitalName'],
                'hospital':['hospitalName', 'departmentName', 'diseaseName'],
                'post': ['treatmentName', 'symptomName', 'medicineName']}

#ai转化接口参数

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

#intentionDetail字段和返回字段值的对应关系
q_intention_dict = {'symptom': 'symptomName',
                    'disease': 'diseaseName',
                    'department': 'departmentName',
                    'hospital': 'hospitalName',
                    'treatment': 'treatmentName',
                    'medicine': 'medicineName',
                    'doctor': 'doctorName'}

#keyword意图对应的q在ai返回内容中的取值范围
keyword_q_param_name = ('symptomName', 'diseaseName', 'departmentName', 'hospitalName',
                    'treatmentName', 'medicineName', 'doctorName', 'body_partName')

#调用医院搜索接口中默认的参数
hospital_search_params = {'rows': '3',
                       'start': '0',
                       'do_spellcheck': '1',
                       'dynamic_filter':'1',
                       'opensource': '9',
                       'wait_time': 'all',
                       'haoyuan': '2'}

#调用医生搜索接口中默认的参数
doctor_search_params = {'contract': '1',
                        'rows': '18',
                        'start': '0',
                        'do_spellcheck': '1',
                        'travel': '0',
                        'sort': 'general',
                        'secondsort': '0',
                        'aggr_field': 'contract_register',
                        'opensource': '9'}

#调用文章搜索接口中默认的参数
post_search_params = {'rows': '3',
                      'start': '0',
                      'sort': 'help_general',
                      'topic_type': '1,3',
                      'exclude_type': '2',
                      'highlight': '1',
                      'highlight_scene': '1'
                    }

#默认的标签对象和对应的默认参数值构成的字典
default_search_params_dict = {'doctor': doctor_search_params,
                       'hospital': hospital_search_params,
                       'post': post_search_params}

#标签对象和对应的搜索url后缀构成的字典
url_dict = {'doctor': '/doctor_search?',
            'hospital': '/hospital_search?',
            'post': '/post_service?',
            'service_package': '/service_package?',
            'ai_dept': '/dept_classify_interactive?'}

#标签对应的返回内容中，json解析时的名字
return_json = {'doctor': 'docs',
               'hospital': 'hospital'}

#引导语列表
guiding_list = [
                {'title':'选医院', 'list':[{'text': u'上海哪家医院妇科好'},
                                            {'text': u'中国人民解放军总医院301医院怎么样'},
                                            {'text': u'上海华山医院有皮肤科吗'},
                                            {'text': u'北京哪家医院皮肤科好'},
                                            {'text': u'北京大学国际医院怎么样'},
                                            {'text': u'中日友好医院有消化内科吗'}
                                            ]},
                {'title':'查号源', 'list':[{'text': u'华东医院水润英什么时候放号'},
                                            {'text': u'华东医院水润英最近的号'},
                                            {'text': u'华东医院水润英还有没有号'},
                                            {'text': u'华山医院傅雯雯什么时候放号'},
                                            {'text': u'华山医院傅雯雯最近的号'},
                                            {'text': u'华山医院傅雯雯还有没有号'}
                                            ]},
                {'title':'选科室', 'list':[{'text': u'失眠挂什么科'},
                                            {'text': u'失眠应该挂内科还是神经内科'},
                                            {'text': u'失眠是挂神经内科吗'},
                                            {'text': u'胸闷挂什么科'},
                                            {'text': u'胸闷应该挂内科还是心血管内科'},
                                            {'text': u'胸闷是挂内科吗'}
                                            ]},
                {'title':'选医生', 'list':[{'text': u'全国哪位医生看白癜风好'},
                                            {'text': u'皮肤科上海哪位医生好'},
                                            {'text': u'傅雯雯看白癜风怎么样'},
                                            {'text': u'全国哪位医生看心脏病好'},
                                            {'text': u'心血管内科北京哪位医生好'},
                                            {'text': u'罗明看心脏病怎么样'}
                                            ]},
                {'title':'查资讯', 'list':[{'text': u'什么是癫痫'},
                                            {'text': u'糖尿病需要忌口吗'},
                                            {'text': u'幽门螺旋杆菌的治疗'},
                                            {'text': u'什么是颈椎病'},
                                            {'text': u'过敏性鼻炎注意事项'},
                                            {'text': u'癫痫如何治疗'}
                                            ]}
                ]

