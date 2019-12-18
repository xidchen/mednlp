#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
card_builder.py -- some builder of card

Author: maogy <maogy@guahao.com>
Create on 2018-10-04 Thursday.
"""
from mednlp.dialog.configuration import Constant as constant
from mednlp.utils.utils import transform_dict_data
import copy

class CardBuilderDB(object):
    """
    数据库配置的卡片构建器.
    """

    def __init__(self, conf, **kwargs):
        #self.fields = conf.get('field', ['doctor_name', 'doctor_uuid'])
        #self.rows = conf.get('rows', 2)
        self.conf = conf
        #self.conf_id = conf['conf_id']


class CardBuilder(object):
    """
    自定义配置的卡片构建器.
    """
    field_list = ['type', 'content']

    def __init__(self, conf, **kwargs):
        self.conf = conf

    def build(self,  response_data, query=None):
        card_obj = {}
        card_obj['content'] = []
        res_data = []
        if 'doctor_search' in response_data:
            card_obj['content'] = response_data['doctor_search']
            card_obj['type'] = 'doctor'
        elif 'hospital_search' in response_data:
            card_obj['content'] = response_data['hospital_search']
            card_obj['type'] = 'hospital'
        elif 'post_search' in response_data:
            card_obj['content'] = response_data['post_search']
            card_obj['type'] = 'post'
        elif 'diagnose' in response_data:
            card_obj['content'] = response_data['diagnose']
            card_obj['type'] = 'diagnose'
        return_obj = {}
        for field in self.field_list:
            if card_obj.get(field):
                return_obj[field] = card_obj.get(field)
        return return_obj       

    
class DefaultCardBuild(CardBuilderDB):

    field_list = ['conf_id', 'type', 'content']

    def __init__(self, conf, **kwargs):
        super(DefaultCardBuild, self).__init__(conf)
        self.card_type = ''
        self.id = conf.get('conf_id', None)
        self.content = []
        self.fl = conf.get('biz_conf', set())

    def get_id(self):
        return self.id

    def get_card_type(self):
        return self.card_type

    def get_fl(self):
        return self.fl

    def get_content(self):
        return self.content

    def build(self, response_data, query=None):
        card_obj = {}
        card_obj['type'] = self.card_type
        card_obj['conf_id'] = self.id
        card_obj['content'] = []
        res_data = []
        if 'doctor_search' in response_data:
            res_data = response_data['doctor_search']
            card_obj['type'] = 'doctor'
        elif 'hospital_search' in response_data:
            res_data = response_data['hospital_search']
            card_obj['type'] = 'hospital'
        elif 'post_search' in response_data:
            res_data = response_data['post_search']
            card_obj['type'] = 'post'
        elif 'diagnose' in response_data:
            card_obj['content'] = response_data['diagnose']
            card_obj['type'] = 'diagnose'
        for data_item in res_data:
            card_dict = {}
            for key,value in data_item.items():
                if key in self.fl and value:
                    card_dict[key] = value
            if card_dict:
                card_obj['content'].append(card_dict)
        return_obj = {}
        for field in self.field_list:
            if card_obj.get(field):
                return_obj[field] = card_obj.get(field)
        return return_obj       

class CardBuilderDBDeptClassify(CardBuilderDB):
    """
    卡片构建器
    """

    def __init__(self, conf, **kwargs):
        super(CardBuilderDBDeptClassify, self).__init__(conf)
        self.doctor_builder = CardBuilderDBDoctor(conf)

    def build(self, data):
        if data['is_end'] == 1 and data['doctor_search']:
            return self.doctor_builder.build((data['doctor_search']))
        else:
            return {}


class CardBuilderDBDoctor(CardBuilderDB):
    """
    医生卡片构建器.
    """

    field_dict = {
        'doctor_name': 'doctor_name',
        'doctor_uuid': 'doctor_uuid'
    }

    def build(self, data):
        if data['code'] != 0 or not data['docs']:
            return None
        doctor_res = []
        for doc in data['docs']:
            doc_item = {}
            for ai_field in self.fields:
                doc_item[ai_field] = doc[self.field_dict[ai_field]]
            doctor_res.append(doc_item)
            if len(doctor_res) >= self.rows:
                break
        result = {'type': 'doctor', 'conf_id': self.conf_id,
                  'content': doctor_res}
        return result


class AutoDiagnoseCardBuild(object):
    def __init__(self):
        pass

    def build(self, data, **kwargs):
        """
            card:{
                'type': 'diagnose',
                'content': [{
                        'disease_name': '',
                        'disease_id': '',
                        'medical_history': '',
                        'diagnose': [
                            {
                                'disease_name': '',
                                'disease_id': ''
                            },
                            {
                                 'disease_name': '',
                                'disease_id': ''
                            }
                        ]
                    },
                    {
                         'disease_name': '',
                        'disease_id': '',
                    }
                ]
            }
            """
        result = {}
        if not data.get('is_end') or data.get('card_return'):
            return result
        result['type'] = 'diagnose'
        result['content'] = [{}]
        if data.get('diagnose'):
            result['content'][0]['diagnose'] = data['diagnose']
        # 现病史放入card下
        medical_history = data.get('auto_diagnose', {}).get('medical_history')
        if medical_history:
            result['content'][0]['medical_history'] = medical_history
        else:
            result['content'][0]['medical_history'] = ''
        return result


class CardSkillRuleBuilder(object):

    def build(self, environment, data, result):
        card_type = data.get('card_type')
        card_key = constant.CARD_FLAG_DICT.get(card_type)
        if not data.get('card'):
            return result
        card_temp = {}
        card_temp['type'] = card_key
        card_temp['content'] = data['card']
        result['card'] = [card_temp]
        return result


class CardBuilderV3(object):

    def __init__(self):
        pass

    @classmethod
    def generate(cls):
        result = cls()
        return result

    def build_3(self, data, environment):
        # 如果处理器已经提供了answer, 用处理器的
        result = []
        card = data.get('card')
        if not card:
            return result
        if card and 'type' in card[0]:
            return card
        card_type = data.get('card_type')
        card_key = constant.CARD_FLAG_DICT.get(card_type)
        if card_key:
            card_temp = {}
            card_temp['type'] = card_key
            card_temp['content'] = data['card']
            return [card_temp]
        return result


class CardBuildGenerator(object):

    def build(self, data, intention_conf, **kwargs):
        result = []
        card_type = data.get('card_type')
        card_key = constant.CARD_FLAG_DICT.get(card_type)
        if not data.get('card'):
            return result
        card_temp = {}
        card_temp['type'] = card_key
        card_temp['content'] = data['card']
        result.append(card_temp)
        return result


class CardPartGenerator(object):
    def build(self, data, intention_conf, **kwargs):
        result = {}

        return result


class CardBuilderV2(object):
    def __init__(self):
        pass

    def build(self, data, intention_conf):
        result = []
        cards = intention_conf.card_dict
        for temp in cards:
            part = CardPart(cards[temp])
            card_result = part.build(data, intention_conf)
            result.append(card_result)
        return result


class CardPart(object):
    """
    卡片组件
    card下有out_link,card下的out_link有keyword
    card与keyword无直接对应联系
    """
    card_type_data_dict = {
        '1': constant.QUERY_KEY_DOCTOR_SEARCH,
        '2': constant.QUERY_KEY_DEPT_SEARCH,
        '3': constant.QUERY_KEY_HOSPITAL_SEARCH,
        '4': constant.QUERY_KEY_POST_SEARCH,
        '5': constant.QUERY_KEY_POST_SEARCH,
        '6': constant.QUERY_KEY_BAIKE_SEARCH
    }

    def __init__(self, part):
        """
        {
            'id': 449,
            type: int,
            content: []
        }
        :param part:
        """
        self.part = part

    def build(self, data, intention_conf, **kwargs):
        result = {}
        part_id = self.part['card_id']
        result['id'] = part_id
        contents = self.part.get('content', [])
        card_type = self.part['type']   # 卡片类型
        card_type_data = data.get(self.card_type_data_dict.get(str(card_type)), [])  # 卡片源数据
        result['type'] = card_type
        out_links = intention_conf.out_link_dict.get('card', {}).get(part_id, [])[:1]   # out_link此处只有1个
        for index_temp, data_temp in enumerate(card_type_data):
            if card_type in [4, 5]:
                topic_type = data_temp.get('topic_type')
                if not ((card_type == 4 and topic_type == 1) or (card_type == 5 and topic_type == 3)):
                    # 帖子卡片对应 帖子数据，大家帮卡片对应大家帮数据
                    continue
            # content数据组装
            content_list = result.setdefault('content', [])  # result['content'] = [{}]
            content_value_temp = {}
            for content_temp in contents:   # 每个card_content数据填充
                content_keys = content_temp.split(',')
                content_split_values = {}
                for key_temp in content_keys:
                    if key_temp in data_temp:
                        content_split_values[key_temp] = data_temp[key_temp]
                if content_split_values:
                    content_value_temp[content_temp] = content_split_values
            content_list.append(content_value_temp)
            # out_link组装
            out_link_list = result.setdefault('keyword', [])
            # 因为上面[:1]确保out_links每一组都只有一个
            for out_link_temp in out_links:
                out_link_part = OutLinkPart(out_link_temp)
                out_link_list.append(out_link_part.build(
                    data, intention_conf, ceil_data=data_temp, ceil_result={'index': index_temp}))
        return result

    def is_empty(self, card):
        result = False
        if not card.get('content'):
            result = True
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
        # 1-针对整个card的外链
        result = {}
        ceil_data = kwargs.get('ceil_data', {})
        # ceil_data_index = kwargs.get('ceil_data_index')
        # source = kwargs.get('source')
        # 此处暂时设置为0，需要注意
        # if 'out_link_build' == source:
        #     ceil_data_index = 0
        result.update(kwargs.get('ceil_result', {}))
        out_link_id = self.out_link['out_link_id']
        transform_dict_data(result, self.out_link, {'id': 'out_link_id'})
        # keyword 组装,保证location升序
        keywords = intention_conf.keyword_dict.get('out_link', {}).get(out_link_id, [])
        keywords.sort(key=lambda temp: temp.get('location', 10000))
        url_temp = self.out_link.get('text')
        if ceil_data.get('mapping_url'):
            url_temp = ceil_data['mapping_url']
        if keywords and url_temp:
            text = list(url_temp)
            last_keyword_len = 0
            for temp in keywords:
                if temp.get('location') and temp.get('ai_field'):
                    # 上层有传card指定类型的数据,则用上层传的,没有则用全局
                    ai_field_value = ceil_data.get(temp['ai_field'])
                    if ai_field_value:
                        start_temp = temp['location'] + last_keyword_len
                        text = text[:start_temp] + list(ai_field_value) + text[start_temp:]
                        last_keyword_len += len(ai_field_value)
            url_temp = ''.join(text)
        result['url'] = url_temp
        return result

