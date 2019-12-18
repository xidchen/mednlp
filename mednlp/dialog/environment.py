#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import global_conf
from ailib.storage.db import DBWrapper
from mednlp.dialog.dialogue_sql import SQL_CONFIG
from mednlp.utils.utils import transform_dict_data
import json
from mednlp.dialog.configuration import logger, ai_client, sc_client
from mednlp.dialog.general_util import get_service_data
from mednlp.dialog.dialogue_constant import db, Constant
from mednlp.dialog.component_config import ModeIntention, get_config_card


class DialogueStatus(object):
    # 对话状态类
    entity_field_mapping = {'id': 'entity_id', 'name': 'entity_name'}
    entity_map = {
        'std_department': {
            'name': 'department',
        },
        'doctor': {
            'name': 'doctor',
        },
        'symptom': {
            'name': 'symptom',
        },
        'disease': {
            'name': 'disease',
        },
        'hospital_department': {
            'name': 'department',
        },
        'hospital': {
            'name': 'hospital',
        },
        'body_part': {
            'name': 'body_part',
        },
        'treatment': {
            'name': 'treatment',
        },
        'medicine': {
            'name': 'medicine',
        },
        'medical_word': {
            'name': 'medical_word'
        },
        'examination': {
            'name': 'examination'
        },
        'physical': {
            'name': 'physical'
        },
        'area': {
            'has_sub': 1,
            'sub': {
                'city': {
                    'name': 'city'
                },
                'province': {
                    'name': 'province'
                }
            }
        }
    }
    """
    用户可能会传入的实体:
    id: city、province、hospital、doctor
    name: hospitalName、doctorName、symptomName
    """
    user_entity_map = {
        'city': {
            'name': 'city',
            'store_key': 'id'
        },
        'province': {
            'name': 'province',
            'store_key': 'id'
        },
        'hospital': {
            'name': 'hospital',
            'store_key': 'id'
        },
        'doctor': {
            'name': 'doctor',
            'store_key': 'id'
        },
        'hospitalName': {
            'name': 'hospital',
            'store_key': 'name'
        },
        'doctorName': {
            'name': 'doctor',
            'store_key': 'name'
        },
        'symptomName': {
            'name': 'symptom',
            'store_key': 'name'
        }
    }

    def __init__(self):
        """
        定义所有成员变量
        entity_dict:
            eg: {'department': [{'id': '123', 'name': '神经内科'}]}
            注意点:
            1.entity_dict和user_entity_dict里的数据可能会重复，使用的时候去重即可，一般优先用user_entity_dict.
            2.若以后考虑到上下文的实体词,可以创建1个新的[]，存储历史的entity_dict和user_entity_dict
        """
        self.mode = None
        self.source = None
        self.organization = None
        self.original_input = None  # 原始输入(包括organization、source、input、dialogue),不会修改
        self.dialogue = {}  # dialogue key
        self.input = []     # 原始列表输入[{}, {}, {}] 有顺序的
        self.input_dict = {}   # input key

        # 运行过程中的数据
        self.intention = None  # 目的不明确的意图,需要意图识别
        self.intention_detail = None
        self.intention_combine = None  # 意图组合
        self.accompany_intention = [] # 伴随意图
        self.skill = None  # find_doctor、find_hospital、auto_diagnose(入参里auto_diagnosis转换为skill=auto_diagnose) # 目的明确的意图
        self.is_bottom = False  # 是否兜底, 默认不兜底

        self.conf = None    # 机构配置
        self.intention_conf = None  # 意图配置
        self.entity_dict = {}   # 分析后的实体词包括实体识别、分科, 分科后的科室词可以新定义1个key
        self.user_entity_dict = {}  # 用户输入的实体词(只保存city、province)

        self.active = None

        self.trace = []     # 整个请求的逻辑变换, 暂定为{action:2, intention:4} action:2 表示意图切换
        self.result = {'data': {}}

    @classmethod
    def generate(cls, request):
        # 根据request重新生成1个environment对象
        result = cls()
        result.simple_parse_request(request)  # 仅仅赋值
        return result

    def get(self, field_name, **kwargs):
        # 根据key获取实例的值
        result = None
        if kwargs.get('default'):
            result = kwargs['default']
        if hasattr(self, field_name):
            result = getattr(self, field_name)
        return result

    def simple_parse_request(self, request):
        # 简单赋值
        self.mode = request.get('mode', 'ai_qa')
        self.source = request['source']
        self.organization = request['organization']
        self.original_input = request
        self.dialogue = request.get('dialogue', {})
        self.input = request['input']
        self.reset_input()
        self.parse_user_entity()

    def reset_environment(self):
        self.simple_parse_request(self.original_input)
        self.entity_dict = {}
        self.intention = None
        self.intention_detail = None
        self.intention_combine = None
        self.accompany_intention = []
        self.skill = None
        self.intention_conf = None
        self.active = None



    def reset_input(self):
        # 重置 & 解析input
        self.input_dict = {}
        for temp in self.input:
            self.input_dict.update(copy.deepcopy(temp))

    def parse_entity(self, query=None):
        if 'q' not in self.input_dict:
            return
        params = {'q': self.input_dict['q']}
        entity_result = get_service_data(params, ai_client, 'entity_extract', method='post')
        for entity_obj in entity_result:
            entity_map_item = self.entity_map.get(entity_obj.get('type'))
            if entity_map_item:
                has_sub = entity_map_item.get('has_sub')
                if has_sub:
                    sub = entity_map_item.get('sub')
                    sub_type = entity_obj.get('sub_type')
                    entity_map_item = sub.get(sub_type)
            if entity_map_item:
                entity_temp = transform_dict_data({}, entity_obj, self.entity_field_mapping)
                if entity_temp:
                    self.entity_dict.setdefault(entity_map_item['name'], []).append(entity_temp)
        # confirm: 0:city 和 province 优先用问句解析、再用传参; 1:city 和 province 只用传参
        confirm_area = int(self.input_dict.get('confirm_area', 0))
        for temp in ('city', 'province'):
            if confirm_area == 1:
                if self.user_entity_dict.get(temp):
                    self.entity_dict['%s_default' % temp] = copy.deepcopy(self.user_entity_dict[temp])
            else:
                if self.entity_dict.get(temp):
                    self.entity_dict['%s_default' % temp] = copy.deepcopy(self.entity_dict[temp])
                elif self.user_entity_dict.get(temp):
                    self.entity_dict['%s_default' % temp] = copy.deepcopy(self.user_entity_dict[temp])

        return

    def add_entity(self, key, data):
        self.entity_dict.setdefault(key, []).extend([temp for temp in data if temp])

    def get_entity(self, source, key, attr, **kwargs):
        # 获取实体,source支持单值和[]
        result = []
        is_break = kwargs.get('is_break', False)
        source_temp = source
        key_temp = key
        if isinstance(source_temp, str):
            source_temp = [source]
            key_temp = [key]
        for index, temp in enumerate(source_temp):
            obj = getattr(self, temp).get(key_temp[index], [])
            result.extend([temp[attr] for temp in obj if temp.get(attr)])
            if result and is_break:
                break
        return result

    area_entity_params = {
        'city': ('city', {'fl': 'entity_id,name,tag_type', 'tag_type': '17'}),
        'province': ('province', {'fl': 'entity_id,name,tag_type', 'tag_type': '16'}),
    }

    def parse_user_entity(self):
        for key in self.user_entity_map:
            value = self.input_dict.get(key)
            if value and key in ('city', 'province') and str(value) == '0':
                # 若city、province 为0 ,则表示全国
                continue
            if 'symptomName' == key and value and '都没有' in value:
                continue
            if isinstance(value, str) and len(value.strip()) > 0:
                if self.area_entity_params.get(key):
                    # city、province需要调用tag_service
                    entity_key_temp, params_temp = self.area_entity_params[key]
                    params_temp['entity'] =value
                    tag_result = get_service_data(params_temp, sc_client, 'tag_service', method='get')
                    if len(tag_result) >= 1:
                        entity_temp = transform_dict_data({}, tag_result[0], {'id': 'entity_id', 'name': 'name'})
                        self.user_entity_dict.setdefault(self.user_entity_map[key]['name'], []).extend([entity_temp])
                        continue
                value = [{self.user_entity_map[key]['store_key']: temp} for temp in value.split(',') if temp]
                self.user_entity_dict.setdefault(self.user_entity_map[key]['name'], []).extend(value)

    def load_configuration(self):
        conf = Configuration.generation(self)
        self.conf = conf


class Configuration(object):
    # 配置对象
    def __init__(self):
        self.organization = None
        self.mode = None
        self.config_id = None           # 配置id
        self.environment = None
        self.hospital_source = None    # 医院来源:1-自定义接入医院，2-全平台医院
        self.intention_aggregate = []  # 意图集合
        self.intention_aggregate_bottom = []  # 兜底意图集合
        self.sub_intention = {}  # 子意图
        self.sub_intention_bottom = {}  # 兜底子意图
        self.exception_answer_dict = {}  # 异常字典
        self.hospital_relation = []  # 医院相关属性

    @classmethod
    def generation(cls, environment):
        result = cls()
        result.environment = environment
        result.organization = environment.organization
        result.mode = environment.mode
        result.load_org_data()
        return result

    def get_exception_answer(self, key):
        # 加载异常, 若无配置,返回空字符串
        result = self.exception_answer_dict.get(str(key), {}).get('answer_text', '')
        return result

    def get_intention_set(self, bottom=False):
        # 返回意图列表
        if not bottom:  # 非兜底
            intention_org_temp = self.sub_intention
        else:
            intention_org_temp = self.sub_intention_bottom
        result = list(intention_org_temp.keys())
        return result

    def load_org_data(self):
        # step1:获取配置id
        config_rows = db.get_rows(
            SQL_CONFIG['organization']['config_id'] % {'org_id': self.organization})
        if not config_rows:
            raise Exception('机构[%s]无激活的配置id' % self.organization)
        self.config_id = config_rows[0]['id']
        self.hospital_source = config_rows[0]['hospital_source']
        # step2:获取自定义异常文案
        exception_rows = db.get_rows(SQL_CONFIG['answer']['exception'] % {'config_id': self.config_id})
        self.exception_answer_dict = {str(temp['answer_type']): temp for temp in exception_rows if temp}

        # step3:获取意图集合 & 获取兜底父意图
        intention_set_rows = db.get_rows(
            SQL_CONFIG['intention']['intention_set'] % {'config_id': self.config_id})
        if intention_set_rows:
            for temp in intention_set_rows:
                self.intention_aggregate.append(temp)
                if temp.get('is_catch_all_set') and 1 == int(temp['is_catch_all_set']):
                    self.intention_aggregate_bottom.append(temp)

        # step4:获取意图集合下的子意图列表
        sub_intention_set_rows = db.get_rows(
            SQL_CONFIG['intention']['sub_intention_set'] % {'config_id': self.config_id})
        if ModeIntention['mode'].get(self.mode, {}).get('sub_intention_set'):
            for temp in ModeIntention['mode'][self.mode]['sub_intention_set']:
                add_sub_intention_set_temp = {}
                add_sub_intention_set_temp['intention_code'] = temp
                add_sub_intention_set_temp['is_unified_state'] = 0
                add_sub_intention_set_temp['id'] = Constant.UN_CREATE_INTENTION_ID
                add_sub_intention_set_temp['intention_set_id'] = Constant.UN_CREATE_INTENTION_SET_ID
                sub_intention_set_rows.append(add_sub_intention_set_temp)
        if sub_intention_set_rows:
            for temp in sub_intention_set_rows:
                self.sub_intention[temp['intention_code']] = temp
                # 获取兜底子意图
                if self.intention_aggregate_bottom and temp['intention_set_id'] == self.intention_aggregate_bottom[0]['id']:
                    self.sub_intention_bottom[temp['intention_code']] = temp
        # step5:医生相关属性
        hospital_relation_rows = db.get_rows(
            SQL_CONFIG['organization']['hospital_relation'] % {'config_id': self.config_id})
        self.hospital_relation = hospital_relation_rows
        # 加载配置结束

    def create_intention_conf(self):
        # 获取intention_set_id,交给IntentionConf去获取下面的answer,card,outlink,keyword
        # 创建意图配置, 此intention是二级意图,到底用什么配置,需要根据意图列表的属性
        # 获取符合的intention_set_id,代表最后输出的格式配置
        intention_set_id = -1
        intention_combine = self.environment.intention_combine
        if self.sub_intention.get(intention_combine):
            if self.sub_intention[intention_combine]['is_unified_state'] == 1:
                intention_set_id = self.sub_intention[intention_combine]['intention_set_id']  # 启用集合统一文案
            else:
                # 加载默认集合文案
                intention_set_id = self.get_sub_intention_default_set(intention_combine, intention_set_id)
        if -1 == intention_set_id:
            # 不可能找不到默认配置,此处抛出异常
            raise Exception('config[%s]找不到intention_set_id' % self.config_id)
        # 加载配置
        intention_conf = IntentionConf.generation(intention_set_id, self.environment, self)
        return intention_conf

    def get_sub_intention_default_set(self, intention_code, default):
        intention_set_id = default
        sub_intention_default_set_rows = db.get_rows(
            SQL_CONFIG['intention']['sub_intention_default_set'] % {
                'config_id': self.config_id, 'intention_code': intention_code})
        if sub_intention_default_set_rows:
            intention_set_id = sub_intention_default_set_rows[0].get('intention_set_id', default)
        # 如果intention_code是配置创建支持的,则返回no_id
        if self.sub_intention.get(intention_code, {}).get('intention_set_id') == Constant.UN_CREATE_INTENTION_SET_ID:
            intention_set_id = Constant.UN_CREATE_INTENTION_SET_ID
        return intention_set_id


class IntentionConf():
    # Configuration是固定的,而该意图配置是根据业务逻辑由Configuration动态生成,最后展现跟IntentionConf配套

    @classmethod
    def generation(cls, intention_set_id, environment, configuration):
        result = cls()
        result.intention_set_id = intention_set_id
        result.intention = environment.intention
        result.intention_details = environment.intention_detail
        result.intention_combine = environment.intention_combine
        result.configuration = configuration
        result.environment = environment
        result.load_data()
        result.deal_card()
        result.deal_out_link()
        result.deal_keyword()
        return result

    def __init__(self):
        self.intention_set_id = None
        self.intention = None
        self.intention_details = None
        self.intention_combine = None
        self.configuration = None
        self.environment = None

        self.card = []
        self.answer = []  # 对外输出  [{key:value}]
        self.out_link = []
        self.keyword = []

        self.card_dict = {}  # 对外输出
        self.out_link_dict = {}  # 对外输出
        self.keyword_dict = {}  # 对外输出

    def get(self, field_name, **kwargs):
        # 根据key获取实例的值
        result = None
        if kwargs.get('default'):
            result = kwargs['default']
        if hasattr(self, field_name):
            result = getattr(self, field_name)
        return result

    def get_configuration(self):
        return self.configuration

    def is_empty(self):
        # 京东音箱的配置在数据库里为空,但也需要执行后续逻辑
        if Constant.VALUE_MODE_JD_BOX == self.environment.mode:
            return False
        # answer, card都没有,意图不在5种意图，表示空
        if len(self.answer) == 0 and len(self.card_dict) == 0 and self.intention not in (
                        Constant.INTENTION_CORPUS_GREETING, Constant.INTENTION_GREETING, Constant.INTENTION_GUIDE,
                        Constant.INTENTION_CUSTOMER_SERVICE, Constant.INTENTION_AUTO_DIAGNOSE):
            return True
        return False

    def load_data(self):
        self.card = list(db.get_rows(SQL_CONFIG['card']['base'] % {'intention_set_id': self.intention_set_id}))
        self.answer = list(db.get_rows(SQL_CONFIG['answer']['base'] % {'intention_set_id': self.intention_set_id}))
        self.out_link = list(db.get_rows(SQL_CONFIG['out_link']['base'] % {'intention_set_id': self.intention_set_id}))
        self.keyword = list(db.get_rows(SQL_CONFIG['keyword']['base'] % {'intention_set_id': self.intention_set_id}))

    def deal_card(self):
        """
        card格式比较特殊,
        {card_id: {content: [], type:int, card_id:int}, card_id:{}}
        """
        self.card_dict = {}
        if self.environment.mode in Constant.VALUE_MODE_MENHU:    # 门户的直接读取配置文件
            self.card_dict = get_config_card(self.environment.mode, self.intention_combine, self.intention_set_id)
            return
        for temp in self.card:
            id = temp['card_id']
            card_type = temp['type']  # 卡片类型
            key_dict = self.card_dict.setdefault(temp['card_id'], {})
            if not key_dict.get('type'):
                key_dict['type'] = card_type
            if not key_dict.get('id'):
                key_dict['card_id'] = id
            if 'card_num' in temp and 'card_num' not in key_dict:
                key_dict['card_num'] = temp['card_num']
            if temp.get('ai_field'):
                key_dict.setdefault('content', []).append(temp['ai_field'])

    def deal_out_link(self):
        """
        {
            intention:{
                biz_id:[]
            },
            answer: {
                biz_id:[]
            },
            card: {
                biz_id: [],
                biz_id: []
            }
        }
        """
        self.out_link_dict = {}
        for temp in self.out_link:
            key_temp = Constant.out_link_dict_key.get(str(temp['relation']))
            if key_temp:
                key_dict = self.out_link_dict.setdefault(key_temp, {})
                biz_id = temp['biz_id']
                key_dict.setdefault(biz_id, []).append(temp)

    def deal_keyword(self):
        """
        {
            answer:{
                biz_id:[]
            },
            card: {
                biz_id:[]
            },
            out_link: {
                biz_id: [],
                biz_id: []
            }
        }
        """
        self.keyword_dict = {}
        if self.environment.mode in Constant.VALUE_MODE_MENHU:
            # 若mode=xwyz & intention是固定的意图, 走配置项
            return
        for temp in self.keyword:
            key_temp = Constant.keyword_dict_key.get(str(temp['relation']))
            if key_temp:
                key_dict = self.keyword_dict.setdefault(key_temp, {})
                biz_id = temp['biz_id']
                key_dict.setdefault(biz_id, []).append(temp)


class Environment(object):
    entity_map = {
        'std_department': {
            'name': 'department',
        },
        'doctor': {
            'name': 'doctor',
        },
        'symptom': {
            'name': 'symptom',
        },
        'disease': {
            'name': 'disease',
        },
        'hospital_department': {
            'name': 'department',
        },
        'hospital': {
            'name': 'hospital',
        },
        'body_part': {
            'name': 'body_part',
        },
        'treatment': {
            'name': 'treatment',
        },
        'medicine': {
            'name': 'medicine',
        },
        'medical_word': {
            'name': 'medical_word'
        },
        'examination': {
            'name': 'examination'
        },
        'area': {
            'has_sub': 1,
            'sub': {
                'city': {
                    'name': 'city'
                },
                'province': {
                    'name': 'province'
                }
            }
        }
    }

    input_change_params = {
        # 'hospital': 'hospitalId',
        # 'hospitalName': 'hospitalName',
        # 'doctor': 'doctorId',
        # 'doctorName': 'doctorName',
        # 'symptomName': 'symptomName',
        # 'sex': 'sex',
        # 'age': 'age'
    }

    def __init__(self):
        """
        获取数据中利用的参数为:input_dict,entity
        """
        self.db = None
        self.flag = 'a'
        self.request = None  # 原始请求参数

        # 原始对话信息处理
        self.input = []
        self.source = None
        self.mode = None
        self.organization = None
        self.dialogue = {}
        self.input_dict = {}

        # NLU信息, 实体 & 意图
        """
        {
            "city": {
                '杭州':{
                        name:xx,
                        id: xx
                        },
                '绍兴':{
                        name:xx,
                        id:xx
                        }
                    }
        }
        """
        self.entity = {}    # 实际存储实体, 格式为{'disease': []}
        self.entity_distinct = {}   # 为entity去重用, 格式为{'disease': {'name': 1}},业务里不用
        self.intention = None
        self.intention_detail = None
        self.intention_combine = None  # 意图组合

        # configuration
        self.conf = None
        self.intention_conf = None


        self.card_builder = None
        self.answer_builder = None
        self.interactive_builder = None

    def skill_builder(self, data, result):
        if self.card_builder:
            self.card_builder.build(environment=self, data=data, result=result)
        if self.interactive_builder:
            self.interactive_builder.build(environment=self, data=data, result=result)
        if self.answer_builder:
            self.answer_builder.build(environment=self, data=data, result=result)
        return result



    @classmethod
    def generate(cls, request, db):
        # 根据request重新生成1个environment对象
        result = cls()
        result.db = db
        result.simple_parse_request(request)    # 仅仅赋值
        return result

    def get(self, field_name, **kwargs):
        # 根据key获取实例的值
        result = None
        if kwargs.get('default'):
            result = kwargs['default']
        if hasattr(self, field_name):
            result = getattr(self, field_name)
        return result

    def set(self, field_name, holder):
        setattr(self, field_name, holder)
        return getattr(self, field_name)

    def add_entity(self, entity, entity_type):
        # 往self.entity 里添加实体
        if not entity.get('name'):
            # 实体中名字需要存在
            return
        if not self.entity_distinct.get(entity_type, {}).get(entity['name']):
            self.entity.setdefault(entity_type, []).append(entity)
            self.entity_distinct.setdefault(entity_type, {})[entity['name']] = entity

    # def parse_request(self, request):
    #     """
    #     解析request,
    #     1.基本的字段赋值 (input, source, mode, organization, dialogue)
    #     2.input字段生成input_dict (input_dict)
    #     3.q解析 & 相应参数解析成实体,后续实体若有加入,在entity里加入 (entity),该step根据是否有q进行
    #     """
    #     self.simple_parse_request(request)
    #     self.reset_entity()
    #     self.parse_input_dict_entity()
        # self.generate_conf()

    def simple_parse_request(self, request):
        self.request = request
        self.input = request.get('input')
        self.source = request.get('source')
        self.mode = request.get('mode', 'ai_qa')
        self.organization = request.get('organization')
        self.dialogue = request.get('dialogue', {})
        self.reset_input()

    def reset_input(self):
        # 解析input, 重置
        self.input_dict = {}
        for temp in self.input:
            self.input_dict.update(copy.deepcopy(temp))

    def reset_entity(self):
        # 只有request执行完成后, 才能实体解析
        # 重置
        self.entity = {}
        self.entity_distinct = {}
        if 'q' not in self.input_dict:
            return
        params = {'q': self.input_dict['q']}
        entity_result = get_service_data(params, ai_client, 'entity_extract')
        for entity_obj in entity_result:
            entity_map_item = Environment.entity_map.get(entity_obj.get('type'))
            if entity_map_item:
                has_sub = entity_map_item.get('has_sub')
                if has_sub:
                    sub = entity_map_item.get('sub')
                    sub_type = entity_obj.get('sub_type')
                    entity_map_item = sub.get(sub_type)
            if entity_map_item:
                entity_temp = transform_dict_data({}, entity_obj, {'id': 'entity_id', 'name': 'entity_name'})
                if entity_temp:
                    self.add_entity(entity_temp, entity_type=entity_map_item['name'])
        return

    def del_entity_type(self, entity_type):
        self.entity.pop(entity_type, None)
        self.entity_distinct.pop(entity_type, None)

    def parse_input_dict_entity(self):
        """
        对input_dict的相关参数进行变换
        'hospital': 'hospitalId',
        'hospitalName': 'hospitalName',
        'doctor': 'doctorId',
        'doctorName': 'doctorName',
        'symptomName': 'symptomName',
        'sex': 'sex',
        'age': 'age'
        """
        for key in self.input_change_params:
            value = self.input_dict.pop(key, None)
            if value:
                if isinstance(value, str):
                    value = value.split(',')
                self.input_dict[self.input_change_params[key]] = value

        area_entity_params = {
            'city': ('city', {'fl': 'entity_id,name,tag_type', 'tag_type': '17'}),
            'province': ('province', {'fl': 'entity_id,name,tag_type', 'tag_type': '16'}),
        }
        # 当confirm_area = 1 或者 confirm_area = 0 & query 无
        """
        confirm
        0:city 和 province 优先用问句解析、再用传参
        1:city 和 province 只用传参
        """
        confirm_area = self.input_dict.get('confirm_area')
        if confirm_area == 1:
            self.entity.pop('city', None)
            self.entity_distinct.pop('city', None)
            self.entity.pop('province', None)
            self.entity_distinct.pop('province', None)
        query_with_area = False
        if self.entity.get('city') or self.entity.get('province'):
            query_with_area = True
        if not query_with_area:
            for key_temp, (entity_key_temp, params_temp) in area_entity_params.items():
                if self.input_dict.get(key_temp):
                    # 若实体里已有entity_key_temp or 输入无key_temp, 不进行tag查询
                    params_temp['entity'] = self.input_dict[key_temp]
                    tag_result = get_service_data(params_temp, sc_client, 'tag_service', method='get')
                    if len(tag_result) >= 1:
                        entity_temp = transform_dict_data({}, tag_result[0], {'id': 'entity_id', 'name': 'name'})
                        self.add_entity(entity_temp, entity_type=entity_key_temp)
        return


if __name__ == '__main__':
    db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB', autocommit=True)
    params = {
        "input": [
            {
                "q": "头痛是杭州挂神经内科还是外科吗外科",
                "province": "24",
                "city": "552",
                "hospital": "12434343",
                "hospitalName": '北京,协和'
                ,'confirm_area': 1
            },
        ],
        "mode": "xwyz",
        "organization": "20e69819207b4b359f5f67a990454027",
        "source": "c9ace68e78c345489bcf3007f9c04f6a"
    }
    # environment = Environment.generate(params, db)
    environment = DialogueStatus.generate(params)
    # result = environment.parse_entity()
    environment.parse_entity()
    environment.parse_user_entity()
    configuration = Configuration.generation(environment)
    print('ok')
    # print(json.dumps(environment.get('entity'), indent=True))
