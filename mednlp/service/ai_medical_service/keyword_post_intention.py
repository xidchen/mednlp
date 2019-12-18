#!/usr/bin/python
#encoding=utf-8

from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service.basic_intention import BasicIntention
import json
from mednlp.service.ai_medical_service.department_classify_intention import DepartmentClassifyIntention
from mednlp.service.ai_medical_service.ai_constant import logger


class KeywordPostIntention(BasicIntention):
    """
    处理返回关键字文章的意图
    """

    #调用文章搜索接口中默认的参数
    post_search_params = {'rows': '50',
                            'start': '0',
                            'sort': 'help_general',
                            'topic_type': '1,3',
                            'exclude_type': '2',
                            'highlight': '1',
                            'highlight_scene': '1',
                            'match_type': '4',
                            'exclude_post_heat_status': '1',
                            'digest':'2'
                    }
    def checkout_result(self):
        if self.input_params.get('mode','xwyz') == 'xwyz':
            return True
        else:
            return False

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            if data.get('intention') == 'department':
                ai_search_common.department_classify_build_dialogue_service(data, result)
            else:
                ai_search_common.post_build_dialogue_service(data, result)
        return result

    def get_default_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            if data.get('intention') == 'departmentSubset':
                ai_search_common.department_build_dialogue_service(data, result)
            else:
                ai_search_common.post_build_dialogue_service(data, result)
        return result

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return
        logger.info("未走dialogue_service, 参数:%s" % json.dumps(self.input_params['input']))
        # 1.查post
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'post')
        response = ai_search_common.query(search_params, self.input_params, 'post')
        post_obj_list = ai_search_common.get_post_obj(response, self.ai_result, fl_list)
        json_obj_list = ai_search_common.get_post_json_obj(response, self.ai_result, fl_list)
        title_list = []
        title_list_json = ''
        for obj in json_obj_list:
            if 'title' in obj:
                title_list.append(str(obj['title']))

        if title_list:
            # 有数据则调 相似度接口，把最相似的插入到第一个
            title_list_json = (json.dumps(title_list, ensure_ascii=False))
            query = self.input_params.get('input').get('q')
            params = {}
            params['q'] = query
            params['contents'] = title_list_json
            response = ai_search_common.get_sentence_similar(params, self.input_params)
            if response and response.get('data') and response.get('data').get('content'):
                ai_title = response.get('data').get('content')
                index = 0
                for i in range(len(json_obj_list)):
                    if ai_title == json_obj_list[i].get('title', ''):
                        index = i
                        break
                ai_post = json_obj_list.pop(index)
                json_obj_list.insert(0,ai_post)

            self.ai_result['post'] = post_obj_list[0:1]
            self.ai_result['json_post'] = json_obj_list[0:1]
            self.ai_result['valid_object'] = ['post']
            self.ai_result['query_content'] = q_content
            self.ai_result['search_params'] = ai_params
        else:
            # 无数据则转换成分科意图
            self.ai_result['intention'] = 'department'
            intention_object = DepartmentClassifyIntention()
            intention_object.set_params(self.ai_result, self.input_params, self.solr)
            self.ai_result = intention_object.get_intention_result()

    def get_default_result(self):
        result = self.get_default_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return
        ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result)
        search_params, fl_list = ai_search_common.get_search_params(
                            ai_params, self.input_params, 'post', [], self.post_search_params)
        response = ai_search_common.query(search_params, self.input_params, 'post')
        post_obj_list = ai_search_common.get_post_obj(response, self.ai_result, fl_list)
        if len(post_obj_list) > 0:
            json_obj_list = ai_search_common.get_post_json_obj(response, self.ai_result, fl_list)
            title_list = []
            title_list_json = ''
            for obj in json_obj_list:
                if 'title' in obj:
                    title_list.append(str(obj['title']))
            if title_list:
                title_list_json = (json.dumps(title_list, ensure_ascii=False))
                query = self.input_params.get('input').get('q')
                params = {}
                params['q'] = query
                params['contents'] = title_list_json
                response = ai_search_common.get_sentence_similar(params, self.input_params)
                if response and response.get('data') and response.get('data').get('content'):
                    ai_title = response.get('data').get('content')
                    index = 0
                    for i in range(len(json_obj_list)):
                        if ai_title == json_obj_list[i].get('title', ''):
                            index = i
                            break
                    ai_post = json_obj_list.pop(index)
                    json_obj_list.insert(0,ai_post)
            self.ai_result['post'] = post_obj_list[0:3]
            self.ai_result['json_post'] = json_obj_list[0:3]
            self.ai_result['valid_object'] = ['post']
            self.ai_result['query_content'] = q_content
        else:
            params = {'q': q_content}
            for item in ('sex','age','symptomName'):
                if self.input_params.get('input') and self.input_params['input'].get(item):
                    params[item] = self.input_params['input'].get(item)
            ai_dept_response = ai_search_common.get_ai_dept(params, self.input_params)
            depts = ai_dept_response['data']['depts']
            dept_name_list = []
            for dept in depts:
                if dept.get('dept_name') and dept['dept_name'] != 'unknow':
                    dept_name_list.append(dept['dept_name'])
            if dept_name_list:
                params_set = ['departmentName']
                self.ai_result['departmentName'] = dept_name_list
                self.ai_result['intention'] = 'department'
                ai_params, q_content = ai_search_common.ai_to_q_params(self.ai_result, True, params_set)
                search_params, fl_list = ai_search_common.get_search_params(
                    ai_params, self.input_params, 'doctor')
                response, area = ai_search_common.get_extend_response(search_params,
                                                                      self.input_params, 'doctor')
                doctor_obj_list = ai_search_common.get_doctor_obj(response, self.ai_result)
                self.ai_result['is_consult'] = ai_search_common.get_consult_doctor(
                    response, self.ai_result)
                self.ai_result['doctor'] = doctor_obj_list
                self.ai_result['valid_object'] = ['doctor']
                self.ai_result['query_content'] = q_content
            else:
                json_obj_list = ai_search_common.get_post_json_obj(response, self.ai_result, fl_list)
                self.ai_result['post'] = post_obj_list[0:3]
                self.ai_result['json_post'] = json_obj_list[0:3]
                self.ai_result['valid_object'] = ['post']
                self.ai_result['query_content'] = q_content
        self.ai_result['search_params'] = ai_params

    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result

