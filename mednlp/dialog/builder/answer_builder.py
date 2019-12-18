#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
answer_builder.py -- the module of answer_builder

Author: maogy <maogy@guahao.com>
Create on 2018-10-02 Tuesday.
"""
import re
from mednlp.utils.utils import unicode_python_2_3
from mednlp.utils.utils import transform_dict_data
from mednlp.dialog.configuration import Constant as constant, transform_answer_keyword
import copy
from mednlp.dialog.component_config import departmentNameAnswerKeyword, confirmAnswerKeywod, amongAnswerKeywod,\
    accuracyAnswerKeywod, queryContentAnswerKeywod, areaAnswerKeyword


class AnswerBuilderDB(object):
    """
    数据库配置的文案构建器.
    """

    def __init__(self, conf, **kwargs):
        self.answer_format = conf.get('text','')
        self.conf_id = conf.get('conf_id', '')
        self.normal_type = 'normal'
        self.keyword_type = 'keyword'
        self.item_list = self._parse_format(self.answer_format)

    def _parse_format(self, answer_format):
        # begin_mark = '#_u{#_p{'
        # end_mark = '}#_p}#_u'
        begin_mark = '#_p{'
        end_mark = '}#_p'
        item_list = []
        self.keyword_type = 'keyword'
        while len(answer_format) > 0:
            try_item_list = []
            index = answer_format.find(begin_mark)
            if index == -1:
                item_list.append({'text': answer_format, 'type': self.normal_type})
                break
            try_item_list.append({'text': answer_format[0: index],
                                  'type': self.normal_type})
            answer_format = answer_format[index+len(begin_mark):]
            index = answer_format.find(end_mark)
            if index == -1:
                item_list.append({'text': answer_format, 'type': self.normal_type})
                break
            try_item_list.append({'text': answer_format[0: index],
                                  'type': self.keyword_type})
            answer_format = answer_format[index+len(end_mark):]
            item_list.extend(try_item_list)
        return item_list

    def build(self, data, **kwargs):
        result = {'conf_id': self.conf_id}
        if len(self.item_list) < 1:
            result['text'] = data.get('answer')
            return result
        content = ''
        keywords = []
        for item in self.itme_list:
            if item['type'] == self.normal_type:
                content += item['text']
                continue
            entities = data.get('entities')
            for entity in entities:
                if entity['type'] == item['text']:
                    entity_name = entity['entity_name']
                    keyword_item = {
                        'id': entity['entity_id'],
                        'name': entity_name,
                        'location':[len(content), len(content)+len(entity_name)]}
                    keywords.append(keyword_item)
                    content += entity_name
        result['text'] = content
        result['keyword'] = keyword
        return result
                

# class AnswerBuilderDBDeptClassify(AnswerBuilderDB):
#     """
#     科室分诊的结果文案构建.
#     """
#
#     open_fields = ['department_name']
#     # open_fields = ['department_name', 'score', 'accuracy']
#
#     def build(self, data):
#         if data['is_end'] == 1:
#             return self.build_end(data)
#         else:
#             return {'text': '请录入更多信息'}
#
#     def build_end(self, data):
#         result = {}
#         if not data.get('doctor_search'):
#             result['text'] = '未找到医生'
#             return result
#         content = ''
#         keywords = []
#         for item in self.item_list:
#             if item['type'] == self.normal_type:
#                 content += item['text']
#                 continue
#             if not item['text'] in self.open_fields:
#                 continue
#             if item['text'] == 'department_name':
#                 kw = self._build_keyword_dept(unicode_python_2_3(content), data)
#                 if kw:
#                     keywords.append(kw)
#                     content += kw['name']
#         result['text'] = content
#         result['keyword'] = keywords
#         return result
#
#     def _build_keyword_dept(self, content, data):
#         if not data['data'] or not data['data']['depts']:
#             return None
#         dept = data['data']['depts'][0]
#         keyword = {'id': dept['dept_id'], 'name': dept['dept_name'],
#                    'location': [len(content),
#                                 len(content)+len(dept['dept_name'])]}
#         return keyword


class DefaultAnswerBuilder(AnswerBuilderDB):

    field_list = ['conf_id','text', 'keyword']

    def __init__(self, conf, **kwargs):
        super(DefaultAnswerBuilder, self).__init__(conf)
        self.id = conf.get('conf_id', None)
        self.answer_tips = conf.get('text', None)
        self.keyword = []
        self.url_dict_list = []
        if conf.get('biz_conf'):
            self.keyword = conf.get('biz_conf')
            self.url_dict_list = conf.get('biz_conf')
            self.fl = conf.get('biz_conf', [])


    def split_params(self, answer_tips = ''):
        """
        把回复的答案模版拆分，拆分出每个模版的位置
        """
        url_index_list = []
        text_index_list = []
        if answer_tips:
            url_index_list = self.get_index_list("#_u",answer_tips )
            text_index_list = self.get_index_list("#_p",answer_tips )
        return url_index_list,text_index_list

    def get_index_list(self, re = '', str = ''):
        """
        re:需要获取的字符串类型
        str:需要截取的字符串
        获取字符串中符合re的起始位置
        """
        index_list = []
        if str:
            i = 0
            index = 0
            lenth = len(str)
            while i < lenth and index != -1:
                index = str.find(re, i)
                # print index
                i = index + 1
                index_list.append(index)
        return index_list
   
    def get_keyword_list(self, url_index_list, text_index_list, url_list, params_dict, answer_tips):
        """
        url_index_list: 符合超链接模版的字符串所在位置的列表，每个元素的格式为[start,end]，代表起始和结束的位置
        text_index_list: 符合普通替换字符的字符串所在的位置的列表，每个元素的格式为[start,end]
        url_list: 从数据库中取出的超链接需要的solr字符串列表，每个元素的格式为{'id':1,'dic_solr_name': ['hospital_name', 'doctor_name']}
        params_dict: 从数据库中取出的所有文本替换的solr字符串字段，数据格式为{'department_name':'pifu'}
        answer_tips: 文本模版
        这个函数最终用来返回内容模版的content参数，对象的格式为[{'hospital_name': 'zhonghua', 'location': [0, 32], 'doctor_name': 'asdddd', 'department_name': 'pifu'}, {'location': [36, 58], 'doctor_name': 'asdddd', 'hospital_name': 'zhonghua'}, {'location': [62, 99], 'department_name': 'pifu'}, {'location': [105, 128], 'department_name': 'pifu'}]
        """
        keyword = []
        #j = 0
        for i in range(0, len(url_index_list)-1, 2):
            url_location = [url_index_list[i],url_index_list[i+1]+3]
            url_params_dict = {'location': url_location}
            sub_str = answer_tips[url_index_list[i]:url_index_list[i+1]+3]
            param_list = self.find_all_params(sub_str)
            #  if j < len(url_list) and url_list[j].get('dic_solr_name'):
            #      param_list.extend(url_list[j].get('dic_solr_name'))
            param_list.extend(url_list)
            for param  in param_list:
                if param in params_dict:
                    url_params_dict[param] = params_dict[param]
            #   j = j + 1
            keyword.append(url_params_dict)
        for k in range(0, len(text_index_list)-1, 2):
            file_list = []
            flag = False
            for i in range(0, len(url_index_list) - 1, 2):
                if text_index_list[k] > url_index_list[i] and text_index_list[k] < url_index_list[i+1]:
                    flag = True
            if not flag:
                key_location = [text_index_list[i], text_index_list[i + 1]+3]
                key_params_dict = {'location': key_location}
                sub_str = answer_tips[text_index_list[i]:text_index_list[i + 1]+3]
                param_list = self.find_all_params(sub_str)
                for param in param_list:
                    if param in params_dict:
                        key_params_dict[param] = params_dict[param]
                keyword.append(key_params_dict)
        return keyword

    def find_all_params(self, sub_text):
        params_list = []
        if sub_text:
            it = re.finditer(r'#_p{(\w+)}#_p', sub_text)
            for match in it:
                params_list.append(match.group(1))
        return params_list

    def get_id(self):
        return self.id

    def get_keyword(self):
        return self.keyword

    def get_fl(self):
        return self.fl

    def get_answer_tips(self):
        return self.answer_tips

    def build(self, response_data, inputs=None, **kwargs):
        answer_obj = {}
        answer_obj['text'] = self.answer_tips
        answer_obj['conf_id'] = self.id
        answer_obj['keyword'] = []
        url_index_list, text_index_list = self.split_params(self.answer_tips)
        param_dict = {}
        if response_data.get('doctor_search'):
            param_dict = response_data['doctor_search'][0]
        elif response_data.get('hospital_search'):
            param_dict = response_data['hospital_search'][0]
        elif response_data.get('post_search'):
            param_dict = response_data['post_search'][0]
        keyword = self.get_keyword_list(url_index_list, text_index_list, self.url_dict_list, param_dict, self.answer_tips)
        if keyword:
            answer_obj['keyword'] = keyword
        return_obj = {}
        for field in self.field_list:
            if answer_obj.get(field):
                return_obj[field] = answer_obj.get(field)
        return return_obj


class DirectAnswerBuilder(AnswerBuilderDB):
    """
    数据库配置的文案构建器.
    """

    def __init__(self, conf, **kwargs):
        super(DirectAnswerBuilder, self).__init__(conf)
        self.id = conf.get('conf_id', None)

    def build(self, response_data, inputs=None, **kwargs):
        answer_obj = {}
        if self.id:
            answer_obj['conf_id'] = self.id
        if response_data.get('answer'):
            answer_obj['text'] = response_data.get('answer')
        return answer_obj

class AnswerBuilder(object):

    def __init__(self, conf, **kwargs):
        self.id = conf.get('conf_id', None)

    def build(self, response_data, inputs=None, **kwargs):
        answer_obj = {}
        if self.checkout_has_result(response_data):
            answer_obj['text'] = '有结果--已为您查询到结果'
        else:
             answer_obj['text'] = '无结果：未查询到相关信息'
        return answer_obj

    def checkout_has_result(self, response_data={}):
        answer_field = ['doctor_search', 'hospital_search', 'post_search']
        has_result = False
        if response_data:
            for field in answer_field:
                if response_data.get(field):
                    has_result = True
        return has_result


class AnswerBuilderV2(object):

    def __init__(self):
        pass

    def build(self, data, intention_conf, **kwargs):
        """

        :param data:
        :param intention_conf:
        :return:
        { answer: [
            {
                'text': str,
                conf_id: int,
                keyword:[
                    {
                        action: int,
                        location:5,
                        text: str,

                    }
                ]
            }
        ]
        }
        """
        result = []
        general_result = self.build_general_answer(data, **kwargs)
        if general_result:
            return general_result
        # xwyz模式根据特殊key添加文案
        if intention_conf.configuration.mode in constant.VALUE_MODE_MENHU:
            self.deal_xwyz_answer(result, data, intention_conf)
        # card处理
        answers = intention_conf.answer
        for temp in answers:
            part = AnswerPart(temp)
            result.append(part.build(data, intention_conf))
        return result

    def deal_xwyz_answer(self, result, data, intention_conf):
        self.deal_departmentConfirm_answer(result, data, intention_conf)
        self.deal_auto_diagnose_answer(result, data, intention_conf)
        self.deal_department_answer(result, data, intention_conf)

    def deal_department_answer(self, result, data, intention_conf):
        if intention_conf.intention in ('department',):
            department_confirm_answer_dict = {'id': '%s_no_id' % intention_conf.get_intention(),
                                              'text': '小微为您推荐一个和您情况最匹配的科室：'}
            result.append(department_confirm_answer_dict)

    def deal_doctor_answer(self, result, data, intention_conf):
        if intention_conf.intention in ('doctor',):
            doctor_answer_dict = {}
            if data.get(constant.QUERY_KEY_DOCTOR_SEARCH):
                doctor_answer_dict = {'id': '%s_no_id' % intention_conf.intention,
                                              'text': '以下是为您推荐的专家：'}
            else:
                doctor_answer_dict = {'id': '%s_no_id' % intention_conf.intention,
                                      'text': '对不起，小微没有查到相关的专家'}
            result.append(doctor_answer_dict)


    def deal_departmentConfirm_answer(self, result, data, intention_conf):
        if intention_conf.intention in ('departmentConfirm', 'departmentAmong', 'departmentSubset'):
            # if data.get()
            """
            confirm=1:是的，小微的意见与您一致，准确度为98.94%,以下是为您推荐的神经内科专家：
            among=1:经过小微的智能判断，推荐就诊神经内科，准确度为98.93%,以下是为您推荐的神经内科专家：
            confirm和among都无:
            小微有不同的看法呢，推荐就诊神经内科，准确度为98.93%,以下是为您推荐的神经内科专家：
            departmentSubset：
            小微推荐就诊神经内科，准确度为98.94%,以下是为您推荐的神经内科专家：

            accuracy 准确率
            departmentId
            departmentName
            department_updated 是否更新
            confirm = 1
            among = 1
            """
            department_confirm_answer_dict = {'id': '%s_no_id' % intention_conf.intention, 'keyword': []}
            answer_text_params = {'accuracy_part': '', 'query_content': '', 'part_2': '', 'department_name': ''}
            extends = data.get('extends', {})
            base_answer = '%(part_1)s%(part_2)s%(accuracy_part)s以下是为您推荐的%(department_name)s专家:'
            if extends.get('departmentName'):
                # 必须放在第一个,confirm会重置  part_2
                department_name = extends['departmentName'][0]
                answer_text_params['part_2'] = '推荐就诊%s，' % department_name
                answer_text_params['department_name'] = department_name
                # 添加keyword
                transform_answer_keyword(departmentNameAnswerKeyword, department_confirm_answer_dict['keyword'],
                                         {'text': department_name})
            if intention_conf.intention == 'departmentSubset':
                answer_text_params['part_1'] = '小微'
            elif data.get('confirm'):
                answer_text_params['part_1'] = '是的，小微的意见与您一致，'
                transform_answer_keyword(confirmAnswerKeywod, department_confirm_answer_dict['keyword'],
                                         {'text': data['confirm']})
                answer_text_params['part_2'] = ''
            elif data.get('among'):
                answer_text_params['part_1'] = '经过小微的智能判断，'
                transform_answer_keyword(amongAnswerKeywod, department_confirm_answer_dict['keyword'],
                                         {'text': data['among']})
            else:
                answer_text_params['part_1'] = '小微有不同的看法呢，'
            if data.get('accuracy'):
                answer_text_params['accuracy_part'] = '准确度为%s，' % data['accuracy']
                transform_answer_keyword(accuracyAnswerKeywod, department_confirm_answer_dict['keyword'],
                                         {'text': data['accuracy']})
            if data.get('query_content'):
                transform_answer_keyword(queryContentAnswerKeywod, department_confirm_answer_dict['keyword'],
                                         {'text': data['query_content']})
            if data.get('area'):
                transform_answer_keyword(areaAnswerKeyword, department_confirm_answer_dict['keyword'],
                                         {'text': data['area']})
            department_confirm_answer_dict['text'] = base_answer % answer_text_params
            result.append(department_confirm_answer_dict)


    def deal_auto_diagnose_answer(self, result, data, intention_conf):
        if intention_conf.intention in ('auto_diagnose'):
            department_confirm_answer_dict = {'id': '%s_no_id' % intention_conf.intention, 'keyword': []}
            answer_text_params = {'accuracy_part': '', 'part_2': ''}
            base_answer = '''小微推荐就诊%(department_name)s，%(accuracy_part)s
            以下是为您推荐的%(department_name)s专家:'''
            extends = data.get('extends')
            if extends.get('departmentName'):
                department_name = extends['departmentName'][0]
                answer_text_params['department_name'] = department_name
                transform_answer_keyword(departmentNameAnswerKeyword, department_confirm_answer_dict['keyword'],
                                         {'text': department_name})
            if data.get('accuracy'):
                answer_text_params['accuracy_part'] = '准确度为%s，' % data['accuracy']
                transform_answer_keyword(accuracyAnswerKeywod, department_confirm_answer_dict['keyword'],
                                         {'text': data['accuracy']})
            if data.get('query_content'):
                transform_answer_keyword(queryContentAnswerKeywod, department_confirm_answer_dict['keyword'],
                                         {'text': data['query_content']})
            if data.get('area'):
                transform_answer_keyword(areaAnswerKeyword, department_confirm_answer_dict['keyword'],
                                         {'text': data['area']})
            result.append(department_confirm_answer_dict)

    def build_general_answer(self, data, **kwargs):
        result = []
        boxs = kwargs.get('interactive_box')
        if boxs:
            for box_temp in boxs:
                # 每个交互框都需要有文案,以此来判断,并且删除box_answer
                answer_temp = box_temp.pop(constant.BOX_ANSWER, None)
                if answer_temp and answer_temp.get(constant.ANSWER_FIELD_TEXT):
                    answer_code = 'answer_%s' % len(result)
                    answer_temp[constant.ANSWER_FIELD_CODE] = answer_code   # 给answer产生一个唯一码,现在使用result的下表
                    result.append(answer_temp)
                    box_temp[constant.BOX_FIELD_ANSWER_CODE] = answer_code
        interactives = kwargs.get('interactive')
        if interactives:
            for box_temp in interactives:
                answer_temp = box_temp.pop(constant.BOX_ANSWER, None)
                answer_code = box_temp.get(constant.INTERACTIVE_ANSWER_CODE)
                if answer_temp and answer_code:
                    answer_dict = {constant.ANSWER_FIELD_CODE: answer_code, constant.ANSWER_FIELD_TEXT: answer_temp}
                    result.append(answer_dict)
        if data.get(constant.ANSWER_GENERAL_ANSWER):
            result.append({'text': data[constant.ANSWER_GENERAL_ANSWER]})
        return result


class AnswerPart(object):
    # answer 下只有out_link,answer下的out_link无keyword
    def __init__(self, answer):
        self.answer = answer

    def build(self, data, intention_conf, **kwargs):
        """
        :param data:
        :param intention_conf:
        :return:
        {
                'text': str,
                conf_id: int,
                keyword:[
                    {
                        action: int,
                        location:5,
                        text: str
                    }
                ]
            }
        """
        result = {}
        answer_id = self.answer['answer_id']
        transform_dict_data(result, self.answer, {'text': 'text'})
        result['id'] = answer_id
        # out_link 组装
        out_links = intention_conf.out_link_dict.get('answer', {}).get(answer_id, [])
        for temp in out_links:
            out_link_part = OutLinkPart(temp)
            result.setdefault('keyword', []).append(out_link_part.build(data, intention_conf))
        # 针对keyword,对text进行处理
        if result.get('keyword'):
            text = list(self.answer['text'])
            last_len = 0
            result['keyword'].sort(key=lambda temp: temp.get('location', [10000, 10000])[0])
            for temp in result['keyword']:
                keyword_name_temp = temp.pop('name', None)
                if temp.get('location') and keyword_name_temp:
                    start_temp = temp['location'][0] + last_len
                    end_temp = temp['location'][1] + last_len
                    temp['location'] = [start_temp, end_temp]   # 更新location
                    text = text[:start_temp] + list(keyword_name_temp) + text[start_temp:]
                    # text = text[:temp['location'][0]] + list(keyword_name_temp) + text[temp['location'][0]:]
                    last_len += len(keyword_name_temp)
            result['text'] = ''.join(text)
        return result


class OutLinkPart(object):
    # out_link 组件
    def __init__(self, out_link):
        self.out_link = out_link

    def build(self, data, intention_conf, **kwargs):
        """
        :param data:
        :param intention_conf:
        :return:
        {
            content: str,   外链内容，URL或文本
            action: int,     外链动作：1-链接跳转，2-返回文本
            outlink_start_location: int     外联位置
        }
        """
        result = {}
        result['location'] = [self.out_link['location'],
                              self.out_link['location'] + len(self.out_link['name']) - 1]
        transform_dict_data(result, self.out_link, {'id': 'out_link_id', 'text': 'text', 'name': 'name'})
        if '1' == str(self.out_link['type']):
            # out_link的type为1表示 对外输出的超链接类型
            result['type'] = 1

        # # keyword 组装
        # keywords = intention_conf.keyword_dict.get('out_link', {}).get(out_link_id, [])
        # if keywords and result.get('text'):
        #     text = list(result['text'])
        #     for temp in keywords:
        #         if temp.get('location') and temp.get('ai_field'):
        #             # 上层有传card指定类型的数据,则用上层传的,没有则用全局
        #             ai_field_value = ceil_data.get(temp['ai_field'])
        #             # if not ai_field_value:
        #             #     ai_field_value = get_ai_field_value(data, ceil_data_index, temp['ai_field'])
        #             if ai_field_value:
        #                 text[temp['location']] = ai_field_value
        #     result['text'] = ''.join(text)
        return result


class AnswerSkillRuleBuilder(object):
    # skill的交互框构建器
    def __init__(self):
        pass

    def build(self, environment, data, result):
        answer = data.get('answer')
        answer_result = []
        if answer:
            for temp in answer:
                answer_dict = {}
                transform_dict_data(answer_dict, temp, {'code': 'code', 'id': 'id',
                                                        'keyword': 'keyword', 'text': 'text'})
                answer_result.append(answer_dict)
        if answer_result:
            result['answer'] = answer_result
        return result


class AnswerBuilderV3(object):

    def __init__(self):
        pass

    @classmethod
    def generate(cls):
        result = cls()
        return result

    def build_3(self, data, environment):
        # 如果处理器已经提供了answer, 用处理器的
        result = []
        answer = data.get('answer')
        if answer:
            return answer
        if data.get(constant.ANSWER_GENERAL_ANSWER):
            result.append({'text': data[constant.ANSWER_GENERAL_ANSWER]})
        return result