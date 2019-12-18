#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
configuration.py -- the configure module of dialog

Author: maogy <maogy@guahao.com>
Create on 2018-10-01 Monday.
"""

import mednlp.dao.dialog_dao as dialog_dao
from mednlp.dialog.dialogue_sql import SQL_CONFIG
from mednlp.utils.utils import byte2str, row_byte2str
from ailib.client.ai_service_client import AIServiceClient
import global_conf
from mednlp.dialog.component_config import ComponentConfig, ModeIntention, get_config_card, ModeOutlink,\
    organization_intention_config
import copy
from ailib.client.http_client import HttpClient
from ailib.utils.log import GLLog
from mednlp.model.similarity import TfidfSimilarity
import configparser

logger = GLLog('dialogue_service_input_output', level='info', log_dir=global_conf.log_dir).getLogger()
content_generation_logger = GLLog('content_generation_input_output',
                                  level='info', log_dir=global_conf.log_dir).getLogger()
ai_client = AIServiceClient(global_conf.cfg_path, 'AIService')
sc_client = AIServiceClient(global_conf.cfg_path, 'SearchService')

# {mode:{intention:{'conf':[{'field':回传字段,'type':类型,1-单选框,2-复选框,3-文本框,'content':[]可选内容数组,无则需生成},]}}}
INTERACTIVE_BOX_CONF = {
    'ai_qa': {
        'department': {
            'conf': [
                {'field': 'sex', 'type': 1, 'content': ['男', '女']},
                {'field': 'age', 'type': 1, 'content': ['天']},
                {'field': 'symptom', 'type': 2}
            ]
        }
    }
}

# 机构
organization_dict = {}


def get_entity(input_params):
    entity_map = {'std_department': {'departmentName': 'entity_name',
                                     'departmentId': 'entity_id'},
                  'doctor': {'doctorName': 'entity_name',
                             'doctorId': 'entity_id'},
                  'symptom': {'symptomName': 'entity_name',
                              'symptomId': 'entity_id'},
                  'disease': {'diseaseName': 'entity_name',
                              'diseaseId': 'entity_id'},
                  'hospital_department': {'departmentName': 'entity_name',
                                          'departmentId': 'entity_id'},
                  'hospital': {'hospitalName': 'entity_name',
                               'hospitalId': 'entity_id'},
                  'body_part': {'bodyPartName': 'entity_name',
                                'bodyPartId': 'entity_id'},
                  'treatment': {'treatmentName': 'entity_name',
                                'treatmentId': 'entity_id'},
                  'medicine': {'medicineName': 'entity_name',
                               'medicineId': 'entity_id'},
                  'medical_word': {'medicalWordName': 'entity_name',
                                   'medicalWordId': 'entity_id'},
                  'examination': {'examinationName': 'entity_name',
                                  'examinationId': 'entity_id'},
                  'area': {'city': {'cityName': 'entity_name',
                                    'cityId': 'entity_id'},
                           'province': {'provinceName': 'entity_name',
                                        'provinceId': 'entity_id'}
                           }
                  }
    input_change_params = {'city': 'cityId',
                           'province': 'provinceId',
                           'hospital': 'hospitalId',
                           'doctor': 'doctorId',
                           'hospitalName': 'hospitalName',
                           'doctorName': 'doctorName',
                           'symptomName': 'symptomName',
                           'sex': 'sex',
                           'age': 'age'
                           }
    entity_dict = {}
    if 'q' in input_params:
        q = input_params['q']
        params = {'q': str(q)}
        entity_result = Constant.ai_server.query(params, 'entity_extract')
        if entity_result and entity_result.get('data'):
            for entity_obj in entity_result.get('data'):
                if entity_map.get(entity_obj.get('type')):
                    entity_map_item = entity_map.get(entity_obj.get('type'))
                    for item in entity_map_item:
                        sub_type = entity_obj.get('sub_type')
                        if sub_type and entity_obj.get('type') == 'area':
                            if sub_type == item:
                                for sub_item in entity_map_item[sub_type]:
                                    if entity_obj.get(entity_map_item[item][sub_item]):
                                        entity_dict.setdefault(sub_item, []).append(
                                            entity_obj.get(entity_map_item[item][sub_item]))
                            continue
                        entity_dict.setdefault(item, []).append(entity_obj.get(entity_map_item[item]))

    for param in input_change_params:
        if input_params.get(param):
            value = input_params.get(param)
            if isinstance(value, str):
                value = value.split(',')
            if param in ('city', 'province'):
                # 如果语句里已经有了地区,就不用默认定位了
                if entity_dict.get('cityId') or entity_dict.get('provinceId'):
                    continue
                entity_dict.setdefault(input_change_params[param], []).extend(value)
                continue
            entity_dict[input_change_params[param]] = []
            if isinstance(value, list):
                entity_dict[input_change_params[param]].extend(value)
            else:
                # 输入本身是非 list, str类型的数据
                entity_dict[input_change_params[param]].append(value)
    return entity_dict


def get_search_params(input_params, **kwargs):
    entity_dict = get_entity(input_params)
    params = {}
    q_content = get_keyword_q_params(entity_dict, **kwargs)
    if q_content:
        params['q'] = q_content
    return params


def get_keyword_q_params(ai_result, **kwargs):
    """
    ai_result: ai的结果
    通过ai的结果转化成q参数的具体方法
    具体原理: 首先扫描所有实体，具体对应实体在keyword_q_param_name中
                把所有的实体通过空格组合成一个q参数
                如果q参数依然为空，把区域参数作为实体传入q参数中
    """
    # keyword意图对应的q在ai返回内容中的取值范围
    keyword_q_param_name = ('symptomName', 'diseaseName', 'departmentName', 'hospitalName',
                            'treatmentName', 'medicineName', 'doctorName', 'body_partName',
                            'medicalWordName', 'examinationName')
    if not ai_result:
        ai_result = {}
    params_set = keyword_q_param_name
    in_params_set = kwargs.get('in_params_set')
    if in_params_set:
        params_set = in_params_set
    q_list = []
    q_content = ''
    for param in params_set:
        if ai_result.get(param):
            q_list.append(' '.join(ai_result.get(param)))
    if q_list:
        q_content = ' '.join(q_list)
    elif ai_result.get('cityName'):
        q_content = ' '.join(ai_result.get('cityName'))
    elif ai_result.get('provinceName'):
        q_content = ' '.join(ai_result.get('provinceName'))
    return q_content


def get_ai_field_value(data, ceil_data_index, field_name):
    result = None
    for key in Constant.QUERY_KEY_LIST:
        if not data.get(key):
            continue
        if isinstance(data[key], dict):
            result = data[key].get(field_name)
        elif isinstance(data[key], list):
            if ceil_data_index < len(data[key]):
                result = data[key][ceil_data_index].get(field_name)
        if result:
            break
    return result

def get_organization_dict():
    if organization_dict:
        return organization_dict
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(global_conf.cfg_path)
    xwyz_organization = config.items('XwyzOrganization')[0][1]
    question_config_organization = config.items('XwyzOrganization')[1][1]
    xwyz_doctor_organization = config.items('XwyzDoctorOrganization')[0][1]
    organization_dict[Constant.VALUE_MODE_XWYZ] = xwyz_organization
    organization_dict[Constant.VALUE_MODE_XWYZ_DOCTOR] = xwyz_doctor_organization
    organization_dict['question_config_organization'] = question_config_organization
    return organization_dict


def transform_answer_keyword(copyed_object, dest, value):
    """
    :param copyed_object: 被复制对象
    :param dest: 存放的地方
    :param value: 具体k_v值
    :return:
    """
    copy_value = copy.deepcopy(copyed_object)
    copy_value.update(value)
    dest.append(copy_value)


def deal_input(query, **kwargs):
    # 把origin_input数据放入result字典里
    result = {}
    inputs = format_input(query[Constant.QUERY_FIELD_ORIGIN_INPUT], **kwargs)
    [result.update(temp) for temp in inputs]
    # 得到last_q
    dialogue = query.get(Constant.QUERY_FIELD_DIALOGUE, {})
    if dialogue.get(Constant.QUERY_FIELD_DIALOGUE_PREVIOUS_Q):
        result['q'] = dialogue[Constant.QUERY_FIELD_DIALOGUE_PREVIOUS_Q]
    # 删除key
    del_keys = query.get(Constant.QUERY_FIELD_DEL_KEYS, [])
    for del_key_temp in del_keys:
        result.pop(del_key_temp, None)
    return result


def format_input(inputs, **kwargs):
    format_input = []
    for temp in inputs:
        new_input = {}
        for key, value in temp.items():
            if isinstance(value, (list, set, tuple, dict)):
                new_input[str(key)] = value
                continue
            new_input[str(key)] = str(value)
        format_input.append(new_input)
    return format_input


class Constant(object):
    ai_server = AIServiceClient(global_conf.cfg_path, 'AIService')

    INTENTION_KEYWORD = 'keyword'  # 关键词意图
    INTENTION_OTHER = 'other'  # 其他意图
    INTENTION_CORPUS_GREETING = 'corpusGreeting'
    INTENTION_GREETING = 'greeting'
    INTENTION_GUIDE = 'guide'
    INTENTION_CUSTOMER_SERVICE = 'customerService'
    INTENTION_AUTO_DIAGNOSE = 'auto_diagnose'

    # CONFIG配置意图
    UN_CREATE_INTENTION_ID = 'no_id'
    UN_CREATE_INTENTION_SET_ID = 'no_intention_set_id'

    # 数据库配置的关键词意图
    INTENTION_CONF_KEYWORD_DETAILS = ['department', 'disease', 'symptom', 'doctor',
                                      'hospital', 'medicine', 'treatment', 'examination',
                                      'medical_word', 'city', 'province', 'body_part']
    INTENTION_SYMPTOM_RELEVANT = 'symptom_relevant' # 症状相关词
    EXCEPTION_ANSWER_CODE_NO_INTENTION = '4'  # 异常文案-未识别意图
    EXCEPTION_ANSWER_CODE_NO_RESULT = '5'  # 异常文案-无结果返回
    EXCEPTION_ANSWER_CODE_NO_CONFIG = '6'  # 异常文案-启用自定义且未配置

    CONFIG_HOSPITAL_SOURCE_CUSTOM = 1  # 自定义接入医院
    CONFIG_HOSPITAL_SOURCE_ALL = 2  # 全医院平台

    PROCESS_FIELD_CEIL_PROCESS_INFO = 'ceil_process_info'
    general_organization = '68a5364faca7422db4a28d422ae3bc2a'

    # 客服服务
    kf = HttpClient(global_conf.cfg_path, 'WangXunKeFuService')
    # tf-idf服务
    # tf_idf = None
    # tf_idf = TfidfSimilarity(global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt')

    out_link_dict_key = {
        '1': 'intention',
        '2': 'answer',
        '3': 'card'
    }

    question_type = {
        'related': '1',    # 相关的问句
        'config_recommend': '2'  # 配置推荐
    }

    keyword_dict_key = {
        '1': 'answer',
        '2': 'card',
        '3': 'out_link'
    }

    # result 相关key
    RESULT_DATA = 'data'
    RESULT_CODE = 'code'
    RESULT_MESSAGE = 'message'

    # 交互框构建的时候,每个交互框有自己的answer,最后这个answer需要包装到answer组件上,该key做一个临时保留,不对外暴露
    BOX_ANSWER = 'box_answer'  # 交互框answer
    INTERACTIVE_ANSWER_CODE = 'answerCode'

    # field
    ANSWER_FIELD_TEXT = 'text'
    ANSWER_FIELD_CODE = 'code'

    BOX_FIELD_ANSWER_CODE = 'answer_code'  # 交互框对应answer的唯一码key

    # query 代表 request.body，是一个字符串
    QUERY_FIELD_ORIGIN_INPUT = 'origin_input'
    QUERY_FIELD_INPUT = 'input'
    QUERY_FIELD_MODE = 'mode'
    QUERY_FIELD_ORGANIZATION = 'organization'
    QUERY_FIELD_INPUT_PARAMS = 'input_params'
    QUERY_FIELD_DEL_KEYS = 'del_keys'
    QUERY_FIELD_DIALOGUE = 'dialogue'
    QUERY_FIELD_DIALOGUE_PREVIOUS_Q = 'previous_q'

    RESULT_FIELD_SEARCH_PARAMS = 'search_params'
    RESULT_FIELD_QUERY_CONTENT = 'query_content'
    RESULT_FIELD_SHOW_GUIDING = 'show_guiding'
    RESULT_FIELD_GREETING_NUM = 'greeting_num'

    # 控制字段
    CONTROL_FIELD_RESTART_INTENTION = 'restart_intention'
    CONTROL_FIELD_RESTART_QUERY = 'restart_query'  # 重新意图识别后, query_dict重置放入该key中

    # value
    VALUE_MODE_AI_QA = 'ai_qa'
    VALUE_MODE_JD_BOX = 'loudspeaker_box'
    VALUE_MODE_XWYZ = 'xwyz'
    VALUE_MODE_XWYZ_DOCTOR = 'xwyz_doctor'

    # 门户包含 xwyz 和 xwyz_doctor
    VALUE_MODE_MENHU = (VALUE_MODE_XWYZ, VALUE_MODE_XWYZ_DOCTOR)

    REQUEST_OK = 200


    # generator
    GENERATOR_CARD_FLAG = 'card_flag'
    GENERATOR_CARD_FLAG_TOPIC = 'topic'  # 帖子
    GENERATOR_CARD_FLAG_HELP = 'help'  # 大家帮
    GENERATOR_CARD_FLAG_POST = 'post'  # 帖子 + 大家帮
    GENERATOR_CARD_FLAG_POST_BAIKE = 'post_baike'  # 帖子+大家帮+百科
    GENERATOR_CARD_FLAG_BAIKE = 'baike'  # 百科
    GENERATOR_CARD_FLAG_DOCTOR = 'doctor'   # 医生
    GENERATOR_CARD_FLAG_HOSPITAL = 'hospital'   # 医院
    GENERATOR_CARD_FLAG_DEPARTMENT = 'department'  # 科室
    GENERATOR_CARD_FLAG_QUESTION = 'question'  # 问句

    GENERATOR_EXTEND = 'extend'
    GENERATOR_EXTEND_SEARCH_PARAMS = 'search_params'
    GENERATOR_EXTEND_QUERY_CONTENT = 'query_content'
    GENERATOR_EXTEND_IS_CONSULT = 'is_consult'
    GENERATOR_AREA = 'area'

    # 交互框类型
    INTERACTIVE_TYPE_PROGRESS = 'progress'  # 进度条
    INTERACTIVE_TYPE_AREA = 'area'  # 地区

    CARD_FLAG_DICT = {
        'doctor': 1,
        'department': 2,
        'hospital': 3,
        'topic': 4,
        'help': 5,
        'post': 7,
        'post_baike': 8,
        'question': 9
    }

    # query_result
    QUERY_KEY_AI_DEPT_XWYZ = 'ai_dept_xwyz'
    QUERY_KEY_AI_DEPT = 'ai_dept'  # 科室分类
    QUERY_KEY_DOCTOR_SEARCH = 'doctor_search'  # 医生搜索
    QUERY_KEY_DEPT_SEARCH = 'dept_search'  # 科室搜索
    QUERY_KEY_HOSPITAL_SEARCH = 'hospital_search'  # 医生搜索
    QUERY_KEY_POST_SEARCH = 'post_search'  # post查询
    QUERY_KEY_BAIKE_SEARCH = 'baike_search'  # 百科查询
    QUERY_KEY_GREETING = 'greeting'  # 先预料,再默认语句
    QUERY_KEY_GUIDE = 'guide'  # 默认语句
    QUERY_KEY_CUSTOMER_SERVICE = 'customerService'  # 客服意图

    QUERY_KEY_DEPARTMENT_CONFIRM_INFO = 'department_confirm_info'

    QUERY_KEY_LIST = [QUERY_KEY_AI_DEPT, QUERY_KEY_DOCTOR_SEARCH, QUERY_KEY_DEPT_SEARCH, QUERY_KEY_HOSPITAL_SEARCH,
                      QUERY_KEY_POST_SEARCH, QUERY_KEY_GREETING, QUERY_KEY_GUIDE, QUERY_KEY_CUSTOMER_SERVICE]

    QUERY_VALUE_GUIDE = '你好,小微目前仅支持医疗相关问题,请问有什么可以帮您吗?'
    QUERY_VALUE_CUSTOMER_SERVICE = '''若需要人工客服帮忙，请直接联系医院相关工作人员'''
    QUERY_TEXT_AI_DEPT = '请问'
    # QUERY_KEY_IS_END = 'is_end'
    ANSWER_GENERAL_ANSWER = 'general_answer'

    HAS_PROCESS_DATA_KEY = [QUERY_KEY_AI_DEPT, QUERY_KEY_DOCTOR_SEARCH, QUERY_KEY_DEPT_SEARCH,
                            QUERY_KEY_HOSPITAL_SEARCH, QUERY_KEY_POST_SEARCH, QUERY_KEY_BAIKE_SEARCH,
                            ANSWER_GENERAL_ANSWER]

    RESULT_EXTENDS_FIELDS = (
        'departmentId', 'departmentName', 'doctorId', 'doctorName',
        'diseaseId', 'diseaseName', 'hospitalId', 'hospitalName',
        'treatmentId', 'treatmentName', 'medicineId', 'medicineName',
        'symptomId', 'symptomName', 'cityId', 'cityName',
        'provinceId', 'provinceName')


class Configuration2(object):
    # 对话服务配置对象v2
    def __init__(self, db, organization, mode, **kwargs):
        self.db = db
        self.organization = organization
        self.mode = mode
        self.config_id = None  # 机构激活配置id
        self.intention_aggregate = []  # 意图集合
        self.intention_aggregate_bottom = []  # 兜底意图
        self.sub_intention = {}  # 子意图
        self.sub_intention_bottom = {}  # 兜底子意图
        self.exception_answer_dict = {}  # 异常字典
        self.hospital_relation = []  # 医院相关属性
        self.exist_entity = 0   # 0:不存在实体、1:存在实体
        self.entity = []    # 实体
        self.load_org_data()
        self.check_data()

    def get_mode(self):
        return self.mode

    def set(self, field_name, holder):
        setattr(self, field_name, holder)
        return getattr(self, field_name)

    def get(self, field_name, **kwargs):
        # 根据key获取实例的值
        result = None
        if kwargs.get('default'):
            result = kwargs['default']
        if hasattr(self, field_name):
            result = getattr(self, field_name)
        return result

    def check_data(self):
        # 校验数据
        if not self.config_id:
            raise Exception('机构[%s]无激活的配置id' % self.organization)

    def load_org_data(self):
        # step1:获取配置id
        config_rows = self.db.get_rows(
            SQL_CONFIG['organization']['config_id'] % {'org_id': self.organization})
        if not config_rows:
            # 无config_id,后续操作无意义,在check_data里会抛出校对异常
            return
        self.config_id = config_rows[0]

        # step2:获取自定义异常文案
        exception_rows = self.db.get_rows(SQL_CONFIG['answer']['exception'] % {'config_id': self.config_id['id']})
        if exception_rows:
            for temp in exception_rows:
                temp['answer_text'] = byte2str(temp['answer_text'])
                self.exception_answer_dict[str(temp['answer_type'])] = temp

        # step3:获取意图集合
        intention_set_rows = self.db.get_rows(
            SQL_CONFIG['intention']['intention_set'] % {'config_id': self.config_id['id']})
        if intention_set_rows:
            # 设置intention_aggregate & 获取兜底父意图
            for temp in intention_set_rows:
                temp['intention_set_name'] = byte2str(temp['intention_set_name'])
                self.intention_aggregate.append(temp)
                if temp.get('is_catch_all_set') and 1 == int(temp['is_catch_all_set']):
                    self.intention_aggregate_bottom.append(temp)

        # step4:获取非默认子意图列表
        sub_intention_set_rows = self.db.get_rows(
            SQL_CONFIG['intention']['sub_intention_set'] % {'config_id': self.config_id['id']})
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
                intention_code_temp = byte2str(temp['intention_code'])
                temp['intention_code'] = intention_code_temp
                self.sub_intention[intention_code_temp] = temp
                # 获取兜底子意图
                if self.intention_aggregate_bottom:
                    if str(temp['intention_set_id']) == str(self.intention_aggregate_bottom[0]['id']):
                        self.sub_intention_bottom[intention_code_temp] = temp
        # step5:医生相关属性
        hospital_relation_rows = self.db.get_rows(
            SQL_CONFIG['organization']['hospital_relation'] % {'config_id': self.config_id['id']})
        self.hospital_relation = hospital_relation_rows
        # self.hospital_relation = [row_byte2str(temp, ['hospital_uuid']) for temp in hospital_relation_rows]

        # 加载配置结束

    def get_exception_answer(self, key):
        # 加载异常, 若无配置,返回空字符串
        result = self.exception_answer_dict.get(str(key), {}).get('answer_text', '')
        return result

    def get_intention_set(self, bottom=False):
        # 返回意图列表
        result = []
        if not bottom:
            # 非兜底
            intention_org_temp = self.sub_intention
        else:
            intention_org_temp = self.sub_intention_bottom
        result = list(intention_org_temp.keys())
        return result

    def create_intention_conf(self, intention, intention_details):
        """
        仅仅获取intention_set_id,交给IntentionConf去获取下面的answer,card,outlink,keyword
        :param intention:
        :param intention_details:
        :return:
        """
        # 创建意图配置, 此intention是二级意图,到底用什么配置,需要根据意图列表的属性
        intention_conf_name = intention
        if (Constant.INTENTION_KEYWORD == intention and len(intention_details) == 1
            and intention_details[0] in Constant.INTENTION_CONF_KEYWORD_DETAILS):
            # 关键词意图 & 意图集合在配置中，变成类似keyword_symptom,符合数据库配置
            intention_conf_name = '%s_%s' % (intention, intention_details[0])
        # 获取符合的intention_set_id,代表最后输出的格式配置
        intention_set_id = -1
        if self.sub_intention.get(intention_conf_name):
            if self.sub_intention[intention_conf_name]['is_unified_state'] == 1:
                # 启用集合统一文案
                intention_set_id = self.sub_intention[intention_conf_name]['intention_set_id']
            else:
                # 加载默认集合文案
                intention_set_id = self.get_sub_intention_default_set(intention_conf_name, intention_set_id)
        if -1 == intention_set_id:
            # 不可能找不到默认配置,此处抛出异常
            raise Exception('config[%s]找不到intention_set_id' % self.config_id)
        # 加载配置
        intention_conf = IntentionConf(self.db, intention_set_id,
                                       intention_conf_name, intention, intention_details, self)
        return intention_conf

    def get_sub_intention_default_set(self, intention_code, default):
        intention_set_id = default
        sub_intention_default_set_rows = self.db.get_rows(
            SQL_CONFIG['intention']['sub_intention_default_set'] % {
                'config_id': self.config_id['id'], 'intention_code': intention_code})
        if sub_intention_default_set_rows:
            intention_set_id = sub_intention_default_set_rows[0].get('intention_set_id', default)
        # 如果intention_code是配置创建支持的,则返回no_id
        if self.sub_intention.get(intention_code, {}).get('intention_set_id') == Constant.UN_CREATE_INTENTION_SET_ID:
            intention_set_id = Constant.UN_CREATE_INTENTION_SET_ID
        return intention_set_id


class IntentionConf():
    # Configuration是固定的,而该意图配置是根据业务逻辑由Configuration动态生成,最后展现跟IntentionConf配套

    def __init__(self, db, intention_set_id, conf_name, intention, intention_details, configuration, **kwargs):
        if kwargs.get('auto_diagnosis') == 1:
            # 自诊
            self.intention = self.intention = intention
            self.intention_details = intention_details
            self.intention_combination = intention
            return
        # self.conf_name = conf_name
        self.configuration = configuration
        self.intention = intention
        self.intention_details = intention_details
        self.intention_combination = intention
        if self.intention == 'keyword' and intention_details:
            self.intention_combination = 'keyword_%s' % intention_details[0]
        self.db = db
        self.intention_set_id = intention_set_id

        self.answer = []  # 对外输出  [{key:value}]
        self.card = []
        self.out_link = []
        self.keyword = []

        self.card_dict = {}  # 对外输出
        self.out_link_dict = {}  # 对外输出
        self.keyword_dict = {}  # 对外输出

        self.load_data()
        self.deal_card()
        self.deal_out_link()
        self.deal_keyword()

    def get(self, field_name, **kwargs):
        # 根据key获取实例的值
        result = None
        if kwargs.get('default'):
            result = kwargs['default']
        if hasattr(self, field_name):
            result = getattr(self, field_name)
        return result

    def get_intention(self):
        return self.intention

    def get_card_dict(self):
        return self.card_dict

    def get_configuration(self):
        return self.configuration

    def is_empty(self):
        if Constant.VALUE_MODE_JD_BOX == self.configuration.mode:
            # 京东音箱的配置在数据库里为空,但也需要执行后续逻辑
            return False
        # answer, card, out_link都没有,意图不在5种意图，表示空    # outlink是否需要设置?
        if len(self.answer) == 0 and len(self.card_dict) == 0 and len(self.out_link_dict) == 0 \
                and self.intention not in (
                        Constant.INTENTION_CORPUS_GREETING, Constant.INTENTION_GREETING, Constant.INTENTION_GUIDE,
                        Constant.INTENTION_CUSTOMER_SERVICE, Constant.INTENTION_AUTO_DIAGNOSE):
            return True
        return False

    def load_data(self):
        # if self.configuration.mode in Constant.VALUE_MODE_MENHU:
        #     # 若mode=xwyz & intention是固定的意图, 走配置项
        #     return
        self.answer = list(self.db.get_rows(SQL_CONFIG['answer']['base'] % {
            'intention_set_id': self.intention_set_id}))
        self.card = list(self.db.get_rows(SQL_CONFIG['card']['base'] % {
            'intention_set_id': self.intention_set_id}))
        self.out_link = list(self.db.get_rows(SQL_CONFIG['out_link']['base'] % {
            'intention_set_id': self.intention_set_id}))
        self.keyword = list(self.db.get_rows(SQL_CONFIG['keyword']['base'] % {
            'intention_set_id': self.intention_set_id}))

    def deal_card(self):
        """
        card格式比较特殊,
        {card_id: {content: [], type:int, card_id:int}, card_id:{}}
        """
        self.card_dict = {}
        if self.configuration.mode in Constant.VALUE_MODE_MENHU:
            intention_temp = self.intention
            if intention_temp == 'keyword':
                intention_temp = '%s_%s' % (self.intention, self.intention_details[0])
            self.card_dict = get_config_card(self.configuration.mode, intention_temp, self.intention_set_id)
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
        for card_temp in ComponentConfig['card']:
            if self.intention in card_temp['intention']:
                card_config_temp = copy.deepcopy(card_temp['config'])
                self.card_dict[card_config_temp['card_id']] = card_config_temp
        # organization = self.configuration.get('organization')
        # organization_intention_card = organization_intention_config.get(organization, {}).get(
        #     self.intention_combination, {})
        # if organization_intention_card.get('card'):
        #     card_config_temp = copy.deepcopy(organization_intention_card['card'])
        #     self.card_dict = card_config_temp


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
        :return:
        """
        self.out_link_dict = {}
        # if self.configuration.mode in Constant.VALUE_MODE_MENHU:
        # 若mode=xwyz & intention是固定的意图, 走配置项
        # self.out_link.extend(self.get_config_outlink())
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
        if self.configuration.mode in Constant.VALUE_MODE_MENHU:
            # 若mode=xwyz & intention是固定的意图, 走配置项
            return
        for temp in self.keyword:
            key_temp = Constant.keyword_dict_key.get(str(temp['relation']))
            if key_temp:
                key_dict = self.keyword_dict.setdefault(key_temp, {})
                biz_id = temp['biz_id']
                key_dict.setdefault(biz_id, []).append(temp)

    def get_config_outlink(self):
        out_links = []
        for temp in ModeOutlink.get(self.configuration.mode, []):
            if self.intention in temp['intention'] and temp.get('config'):
                for config_temp in temp['config']:
                    config_copy = copy.deepcopy(config_temp)
                    config_temp['intention_set_id'] = self.intention_set_id
                    if config_copy.get('relation') == 1:
                        config_copy['biz_id'] = self.intention_set_id
                    out_links.append(config_copy)
        return out_links


class Configuration(object):
    """
    对话服务配置对象.
    """

    # conf:{intention:{'answer':{'conf_id':,'text':,'biz_conf'},
    #                  'card':{'conf_id', 'type',},
    #                  'out_link':{'conf_id',},
    #                  'is_custom':}}

    # conf:{
    #     intention:
    #         {
    #             'answer':{
    #                 'conf_id': '',
    #                  'text': '',
    #                  'biz_conf': ''
    #              },
    #             'card': {
    #                     'conf_id': '',
    #                     'type': '',
    #                 },
    #             'out_link(按钮)':{
    #                         'conf_id': ''
    #                     },
    #            'is_custom': ''
    #         }
    # }
    def __init__(self, organization, mode, db=None, intention=''):
        self.db = db
        self.organization = organization
        self.mode = mode
        self._load(self.organization, self.mode, intention)

    def _load(self, organization, mode, intention=''):
        if mode == 'ai_qa':
            self._load_ai_qa(organization, intention='')
            self._fill_interactive_box_conf()
        elif mode == 'loudspeaker_box':
            self._load_ai_qa(organization, intention='')

    def _load_ai_qa(self, organization, intention=''):
        # 加载数据库里的东西  {'department': {}, 'departmentConfirm': {}}
        self.conf = dialog_dao.load_dialog_conf(self.db, organization)
        print((self.conf))
        # fill not custom intention

    def _fill_interactive_box_conf(self):
        interactive_box_conf = INTERACTIVE_BOX_CONF['ai_qa']
        for intention, conf_item in interactive_box_conf.items():
            intention_conf = self.conf.setdefault(intention, {})
            intention_conf['interactive_box'] = conf_item
        return

    def get_intention(self):
        return list(self.conf.keys())

    def get_answer_conf(self, intention):
        return self._get_item_conf(intention, 'answer')

    def get_card_conf(self, intention):
        return self._get_item_conf(intention, 'card')

    def get_out_link_conf(self, intention):
        return self._get_item_conf(intention, 'out_link')

    def get_interactive_box_conf(self, intention):
        return self._get_item_conf(intention, 'interactive_box')

    def _get_item_conf(self, intention, item_type):
        intention_conf = self.conf.get(intention)
        print('intention conf:' + str(intention_conf))
        print('type:' + item_type)
        if not intention_conf:
            return intention_conf
        return intention_conf.get(item_type)


if __name__ == '__main__':
    from ailib.storage.db import DBWrapper
    import global_conf

    database = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB', autocommit=True)
    input_params = {
        'organization': '993c190641e846d7bc3eaf57abfee3aa',
        'input': {
            'q': '头痛挂什么科,上海地区'
        }
    }
    # conf = Configuration2(database, input_params['organization'], 'ai_qa')
    # print(conf.get_intention_set(False))
    # print(conf.create_intention_conf('keyword', ['symptom']))
    # intention_conf = conf.create_intention_conf('hospitalNearby', ['symptom'])
    # print('end')
    result = get_search_params(input_params['input'])
    print(result)