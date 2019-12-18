#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.active_2 import Active
from mednlp.dialog.builder.answer_builder import AnswerBuilderV2, DirectAnswerBuilder, AnswerBuilderV3
from mednlp.dialog.builder.card_builder import CardBuilderV2, AutoDiagnoseCardBuild, CardBuildGenerator, CardBuilderV3
from mednlp.dialog.builder.interactive_box_builder import InteractiveBoxBuilderV2, InteractiveBoxBuilderAutoDialogue,\
    InteractiveBoxGenerator, InteractiveBoxBuilderV3
from mednlp.dialog.builder.out_link_builder import OutLinkBuilderV2
from mednlp.dialog.dialogue_constant import Constant as constant

from mednlp.dialog.processer.processor.guide_processor import GreetingProcessor, GuideProcessor,\
    CustomerServiceProcessor
from mednlp.dialog.processer.processor.doctor_processor import DoctorProcessor
from mednlp.dialog.processer.processor.hospital_processor import HospitalProcessor
from mednlp.dialog.processer.processor.department_processor import DepartmentProcessor
from mednlp.dialog.processer.processor.xwyz_department_confirm_processor import XwyzDepartmentConfirmProcessor
from mednlp.dialog.processer.processor.xwyz_auto_diagnose_processor import XwyzAutoDiagnoseProcessor
from mednlp.dialog.processer.processor.xwyz_department_processor import XwyzDepartmentProcessor
from mednlp.dialog.processer.processor.auto_diagnose_processor import AutoDiagnoseProcessor
from mednlp.dialog.processer.processor.post_processor import PostProcessor
from mednlp.dialog.processer.processor.content_processor import ContentProcessor
from mednlp.dialog.processer.processor.xwyz_doctor_processor import XwyzDoctorProcessor
from mednlp.dialog.processer.processor.xwyz_hospital_processor import XwyzHospitalProcessor
from mednlp.dialog.processer.processor.xwyz_hospital_department_processor import xwyzHospitalDepartmentProcessor
from mednlp.dialog.processer.processor.xwyz_doctor_quality import xwyzDoctorQualityProcessor
from mednlp.dialog.processer.processor.xwyz_recent_haoyuan_time_processor import xwyzRecentHaoyuanTimeProcessor
from mednlp.dialog.processer.processor.xwyz_keyword_hospital_processor import xwyzKeywordHospitalProcessor
from mednlp.dialog.processer.processor.xwyz_hospital_quality_processor import xwyzHospitalQualityProcessor
from mednlp.dialog.processer.processor.sensitive_processor import SensitiveProcessor


from mednlp.dialog.processer.result_department_processor import ResultDepartmentProcessor
from mednlp.dialog.processer.jingdong_default_doctor_processor import JingdongDefaultDoctorProcessor
from mednlp.dialog.processer.jingdong_haoyuan_doctor_processor import JingdongHaoyuanDoctorProcessor
from mednlp.dialog.processer.jingdong_hospital_processor import JingdongHospitalProcessor
from mednlp.dialog.processer.jingdong_greeting_processor import JingdongGreetingProcessor
from mednlp.dialog.processer.jingdong_other_processor import JingdongOtherProcessor
from mednlp.dialog.processer.jingdong_keyword_doctor_processor import JingdongKeywordDoctorProcessor
from mednlp.dialog.processer.jingdong_keyword_hospital_processor import JingdongKeywordHospitalProcessor
from mednlp.dialog.processer.jingdong_keyword_post_processor import JingdongKeywordPostProcessor
from mednlp.dialog.configuration import IntentionConf


# 19 + 7 = 26个意图 (不包括自诊)
PROCESSER_DICT = {
    'ai_qa': {
        'department': DepartmentProcessor,
        'departmentConfirm': DepartmentProcessor,
        'departmentAmong': DepartmentProcessor,
        'departmentSubset': DepartmentProcessor,
        'hospitalDepartment': DepartmentProcessor,    # 分科 + 医院科室 + doctor  考虑hospital_uuid 和 doctor_source
        'doctor': DoctorProcessor,
        'recentHaoyuanTime': DoctorProcessor,
        'doctorQuality': DoctorProcessor,
        'haoyuanRefresh': DoctorProcessor,
        'register': DoctorProcessor,  # 查doctor  考虑hospital_uuid 和 doctor_source
        'hospital': HospitalProcessor,
        'hospitalQuality': HospitalProcessor,
        'hospitalNearby': HospitalProcessor,
        'hospitalRank': HospitalProcessor,  # 查hospital   考虑hospital_uuid
        'corpusGreeting': GreetingProcessor,
        'greeting': GreetingProcessor,  # 寒暄意图     语料库 + 很抱歉
        'guide': GuideProcessor,   # 固定语句    QUERY_VALUE_GUIDE
        'customerService': CustomerServiceProcessor,       # 客服意图   QUERY_VALUE_CUSTOMER_SERVICE
        'content': ContentProcessor,  # 内容意图    放入keyword+treatement里去了
        'auto_diagnose': AutoDiagnoseProcessor,            # 自诊意图,
        "keyword_disease": DepartmentProcessor,
        "keyword_department": DepartmentProcessor,
        "keyword_symptom": DepartmentProcessor,
        "keyword_doctor": DoctorProcessor,
        "keyword_hospital": HospitalProcessor,
        "keyword_treatment": PostProcessor,
        "keyword_medicine": PostProcessor,
        "sensitive": SensitiveProcessor
        # "hr_qa": 用策略做
    },
    'loudspeaker_box': {
        'department': ResultDepartmentProcessor,
        'departmentConfirm': ResultDepartmentProcessor,
        'departmentAmong': ResultDepartmentProcessor,
        'departmentSubset': ResultDepartmentProcessor,    # 科室
        'doctor': JingdongDefaultDoctorProcessor,
        'hospitalDepartment': JingdongDefaultDoctorProcessor,
        'doctorQuality': JingdongDefaultDoctorProcessor,      # 医生
        'recentHaoyuanTime': JingdongHaoyuanDoctorProcessor,
        'haoyuanRefresh': JingdongHaoyuanDoctorProcessor,
        'register': JingdongHaoyuanDoctorProcessor,           # 号源医生
        'hospital': JingdongHospitalProcessor,
        'hospitalQuality': JingdongHospitalProcessor,
        'hospitalNearby': JingdongHospitalProcessor,          # 医院
        'greeting': JingdongGreetingProcessor,                # greeting
        'content': JingdongKeywordPostProcessor,                # content
        'other': JingdongOtherProcessor,                       # other意图
        "keyword_department": JingdongKeywordDoctorProcessor,
        "keyword_doctor": JingdongKeywordDoctorProcessor,
        "keyword_disease": JingdongKeywordDoctorProcessor,
        "keyword_hospital": JingdongKeywordHospitalProcessor,
        "keyword_symptom": JingdongKeywordPostProcessor,
        "keyword_treatment": JingdongKeywordPostProcessor,
        "keyword_medicine": JingdongKeywordPostProcessor,
    },
    'xwyz': {   # 31个
        'department': XwyzDepartmentProcessor,  # 1
        'departmentConfirm': XwyzDepartmentConfirmProcessor, # 1
        'departmentAmong': XwyzDepartmentConfirmProcessor, # 1
        'departmentSubset': XwyzDepartmentConfirmProcessor, # 1
        "hospital": XwyzHospitalProcessor,  # 1
        "hospitalDepartment": xwyzHospitalDepartmentProcessor,  # 待确定
        "hospitalQuality": xwyzHospitalQualityProcessor,    # 1
        'doctor': XwyzDoctorProcessor,  # 1
        "doctorQuality": xwyzDoctorQualityProcessor, # 1
        "recentHaoyuanTime": xwyzRecentHaoyuanTimeProcessor,
        "haoyuanRefresh": xwyzRecentHaoyuanTimeProcessor,
        "register": xwyzRecentHaoyuanTimeProcessor,
        'auto_diagnose': XwyzAutoDiagnoseProcessor, # 1
        # "content": 策略,
        # 'customerService': CustomerServiceProcessor,  # 策略
        # 'corpusGreeting': GreetingProcessor,  # 策略
        # 'greeting': GreetingProcessor,    # 策略
        # 'guide': GuideProcessor,  # 策略
        "keyword_doctor": XwyzDoctorProcessor, # 1
        "keyword_department": XwyzDoctorProcessor, # 1
        "keyword_disease": XwyzDoctorProcessor, # 1
        "keyword_hospital": xwyzKeywordHospitalProcessor,   # 1
        # "keyword_medicine": 策略,
        # "keyword_treatment": 策略,
        # "keyword_city":   策略
        # "keyword_province" 策略
        # "keyword_symptom": 策略,
        # "keyword_body_part" 策略
        # "keyword_examination":策略
        # "keyword_medical_word"策略
        # "other": 策略
        "sensitive": SensitiveProcessor
    },
    'xwyz_doctor': {    # 31个
        'department': XwyzDepartmentProcessor,  # 1
        'departmentConfirm': XwyzDepartmentConfirmProcessor, # 1
        'departmentAmong': XwyzDepartmentConfirmProcessor, # 1
        'departmentSubset': XwyzDepartmentConfirmProcessor, # 1
        "hospital": XwyzHospitalProcessor, # 1
        "hospitalDepartment": xwyzHospitalDepartmentProcessor,
        "hospitalQuality": xwyzHospitalQualityProcessor, # 1
        'doctor': XwyzDoctorProcessor,  # 1
        "doctorQuality": xwyzDoctorQualityProcessor, # 1
        "recentHaoyuanTime": xwyzRecentHaoyuanTimeProcessor,
        "haoyuanRefresh": xwyzRecentHaoyuanTimeProcessor,
        "register": xwyzRecentHaoyuanTimeProcessor,
        'auto_diagnose': XwyzAutoDiagnoseProcessor, # 1
        # "content": a策略,
        # 'customerService': CustomerServiceProcessor,  # 策略
        # 'corpusGreeting': GreetingProcessor,  # 策略    # 1
        # 'greeting': GreetingProcessor,    # 策略    # 1
        # 'guide': GuideProcessor,  # 策略    # 1
        "keyword_doctor": XwyzDoctorProcessor,  # 1
        "keyword_department": XwyzDoctorProcessor,  # 1
        "keyword_disease": XwyzDoctorProcessor, # 1
        "keyword_hospital": xwyzKeywordHospitalProcessor,
        # "keyword_medicine": a策略,
        # "keyword_treatment": a策略,
        # "keyword_city":   a策略
        # "keyword_province" a策略
        # "keyword_symptom": a策略,
        # "keyword_body_part" a策略
        # "keyword_examination":a策略
        # "keyword_medical_word"a策略
        # "other": a策略
        "sensitive": SensitiveProcessor
    }
}

ANSWER_DBBUILDER_DICT = {
    'ai_qa': {
        # 'department': 'AnswerBuilderDBDeptClassify'
        'department': 'DefaultAnswerBuilder',
        'auto_diagnose': 'DirectAnswerBuilder'
    },
    'loudspeaker_box': {
        'department': DirectAnswerBuilder,
        'departmentConfirm': DirectAnswerBuilder,
        'departmentAmong': DirectAnswerBuilder,
        'departmentSubset': DirectAnswerBuilder,
        'doctor': DirectAnswerBuilder,
        'hospitalDepartment': DirectAnswerBuilder,
        'recentHaoyuanTime': DirectAnswerBuilder,
        'doctorQuality': DirectAnswerBuilder,
        'haoyuanRefresh': DirectAnswerBuilder,
        'register': DirectAnswerBuilder,
        'hospital': DirectAnswerBuilder,
        'hospitalQuality': DirectAnswerBuilder,
        'hospitalNearby': DirectAnswerBuilder,
        'keyword': DirectAnswerBuilder,
        'greeting': DirectAnswerBuilder,
        'other': DirectAnswerBuilder
    }
}


def build_auto_diagnose_active():
    # 自诊配置
    active = Active()
    active.set_card_builder(AutoDiagnoseCardBuild())
    active.set_answer_builder(DirectAnswerBuilder({}))
    active.set_interactive_box_builder(InteractiveBoxBuilderAutoDialogue(conf={}))
    process = AutoDiagnoseProcessor()
    # intention_conf = IntentionConf(None, None, None, 'auto_diagnose', [], None)
    # process.set_intention_conf(intention_conf)
    active.set_processer(process)
    return active


def build_generator_active(conf, mode):
    # 为标准输入输出构建结构
    active = Active()
    active.set_card_builder(CardBuildGenerator())
    active.set_answer_builder(AnswerBuilderV2())
    active.set_out_link_builder(OutLinkBuilderV2())
    active.set_interactive_box_builder(InteractiveBoxGenerator())
    return active

xwyz_keyword_treatment_strategy = {
    'strategy_name': 'keyword_treatment',
    'fixed_params': {},
    'changed _params': ['q'],
    'q_strategy_type': constant.Q_TYPE_ENTITY_ASSEMBLE
}

xwyz_doctor_keyword_treatment_strategy = {
    'strategy_name': 'keyword_treatment',
    'fixed_params': {'rows': 3},  #
    'changed _params': ['q'],
    'q_strategy_type': constant.Q_TYPE_ENTITY_ASSEMBLE
}

xwyz_customer_service_strategy = {
    'strategy_name': 'greeting',
    'fixed_params': {'sort': 'customer_service', 'organization_code': constant.organization_dict['question_config_organization']},
    'changed _params': ['q'],
    'q_strategy_type': constant.Q_TYPE_FIXED,
    'strategy_params': {'return_type': 2}
}

xwyz_guide_strategy = {
    'strategy_name': 'greeting',
    'fixed_params': {'sort': 'guide'},
    'changed _params': ['q'],
    'q_strategy_type': constant.Q_TYPE_FIXED
}

xwyz_greeting_strategy = {
    'strategy_name': 'greeting',
    'fixed_params': {'sort': 'greeting'},
    'changed _params': ['q'],
    'q_strategy_type': constant.Q_TYPE_FIXED
}




STRATEGY_DICT = {
    'xwyz': {
        "keyword_treatment": xwyz_keyword_treatment_strategy,
        "content": xwyz_keyword_treatment_strategy,
        "other": xwyz_keyword_treatment_strategy,
        "keyword_examination": xwyz_keyword_treatment_strategy,
        "keyword_medical_word": xwyz_keyword_treatment_strategy,
        "Keyword_symptom": xwyz_keyword_treatment_strategy,
        "keyword_medicine": xwyz_keyword_treatment_strategy,
        "keyword_city": xwyz_keyword_treatment_strategy,
        "keyword_province": xwyz_keyword_treatment_strategy,
        "keyword_body_part": xwyz_keyword_treatment_strategy,
        'customerService': xwyz_customer_service_strategy,
        'corpusGreeting': xwyz_greeting_strategy,
        'greeting': xwyz_greeting_strategy,
        'guide': xwyz_guide_strategy,
    },
    'xwyz_doctor': {
        "keyword_treatment": xwyz_doctor_keyword_treatment_strategy,
        "content": xwyz_doctor_keyword_treatment_strategy,
        "other": xwyz_doctor_keyword_treatment_strategy,
        "keyword_examination": xwyz_doctor_keyword_treatment_strategy,
        "keyword_medical_word": xwyz_doctor_keyword_treatment_strategy,
        "Keyword_symptom": xwyz_doctor_keyword_treatment_strategy,
        "keyword_medicine": xwyz_doctor_keyword_treatment_strategy,
        "keyword_city": xwyz_doctor_keyword_treatment_strategy,
        "keyword_province": xwyz_doctor_keyword_treatment_strategy,
        "keyword_body_part": xwyz_doctor_keyword_treatment_strategy,
        'customerService': xwyz_customer_service_strategy,  # 策略
        'corpusGreeting': xwyz_greeting_strategy,  # 策略
        'greeting': xwyz_greeting_strategy,    # 策略
        'guide': xwyz_guide_strategy,  # 策略
    }
}


def build_active_2(environment):
    """
    构建processor、cardBuild、answerBuild、out_linkBuild、InteractiveBox
    1.0:根据意图获取对应处理器,这个处理器应该配置相关的build
    2.0(未来): 根据意图的配置获取对应的处理器组,每个处理器配置相关的build,然后组装
    """
    mode = environment.mode
    intention_combine = environment.intention_combine
    active = Active()
    active.set_card_builder(CardBuilderV3())
    active.set_answer_builder(AnswerBuilderV3())
    active.set_out_link_builder(OutLinkBuilderV2())
    active.set_interactive_box_builder(InteractiveBoxBuilderV3())
    process_name = PROCESSER_DICT.get(mode, {}).get(intention_combine)
    if process_name:
        process = process_name()
        active.set_processer(process)
        return active
    strategy_info = STRATEGY_DICT.get(mode, {}).get(intention_combine)
    if not strategy_info:
        raise Exception('该mode[%s]对应意图[%s]没有配置对应的处理器' % (mode, intention_combine))
    active.is_strategy = True
    active.strategy_info = strategy_info
    return active


def build_active(environment):
    # 构建active的工厂方法., 所有的意图都在配置里,超出配置会raise 异常
    mode = environment.mode
    conf = environment.intention_conf
    intention = environment.intention
    intention_details = environment.intention_detail
    active = Active()
    active.set_card_builder(CardBuilderV2())
    active.set_answer_builder(AnswerBuilderV2())
    active.set_out_link_builder(OutLinkBuilderV2())
    active.set_interactive_box_builder(InteractiveBoxBuilderV2())
    if constant.VALUE_MODE_JD_BOX == mode:
        # 京东音箱文案配置
        active.set_answer_builder(DirectAnswerBuilder({}))
    if intention != constant.INTENTION_KEYWORD:
        # 非keyword意图, 采用对应mode下的意图
        process_name = PROCESSER_DICT.get(mode, {}).get(intention)
        if not process_name:
            raise Exception('该mode[%s]对应意图[%s]没有配置对应的处理器' % (mode, intention))
        process = process_name()
    else:
        # keyword意图下
        process = get_processor_instance(intention, intention_details, mode)
        if not process:
            raise Exception('该mode[%s]对应keyword意图[%s]没有配置对应的处理器' % (
                mode, ''.join(intention_details)))
    process.set_intention_conf(conf)
    active.set_processer(process)
    return active


def get_processor_instance(intention, intention_details, mode='ai_qa'):
    if mode == 'ai_qa':
        return get_xwyz_processor_instance(intention, intention_details)
    elif mode == 'loudspeaker_box':
        return get_jingdong_processor_instance(intention, intention_details)
    elif mode in constant.VALUE_MODE_MENHU:
        return get_menhu_xwyz_processor_instance(intention, intention_details)


def get_menhu_xwyz_processor_instance(intention, intention_details):
    processor_instance = None
    if intention == 'keyword' and intention_details:
        if intention_details[0] in ('department', 'doctor', 'disease'):
            pass
            # processor_instance = XwyzDoctorProcessor()
        elif intention_details[0] in ('hospital'):
            pass
            # processor_instance = XwyzDoctorProcessor()
        elif intention_details[0] in ('symptom', 'treatment', 'medicine'):
            # content, other,keyword_examination, keyword_medical_word意图转换成keyword_treatment
            pass
        else:
            # city, province, body_part
            pass
    return processor_instance


def get_xwyz_processor_instance(intention, intention_details):
    # keyword小微医助处理器
    # KeywordDoctorProcessor,KeywordHospitalProcessor,KeywordPostProcessor
    processor_instance = DoctorProcessor()   # 兜底用医生处理器
    if intention and intention not in ('others',):
        if intention == 'keyword' and intention_details:
            if intention_details[0] in ('department', 'disease', 'symptom'):
                # 分科+查doctor
                processor_instance = DepartmentProcessor()      # 分科 + 医院科室 + doctor  考虑hospital_uuid,doctor_source
            elif intention_details[0] in ('doctor',):
                # 查doctor
                processor_instance = DoctorProcessor()  # 查doctor  考虑hospital_uuid 和 doctor_source
            elif intention_details[0] in ('hospital',):
                # 查hospital
                processor_instance = HospitalProcessor()     # 查hospital   考虑hospital_uuid
            elif intention_details[0] in ('treatment', 'medicine'):
                # 查post
                processor_instance = PostProcessor()    # 查大家帮 或者 帖子
    return processor_instance

def get_jingdong_processor_instance(intention, intention_details):
    # keyword京东音箱处理器
    # JingdongKeywordDoctorProcessor, JingdongKeywordHospitalProcessor,JingdongKeywordPostProcessor
    processor_instance = JingdongKeywordDoctorProcessor()
    if intention and intention not in ('others',):
        if intention == 'keyword' and intention_details:
            if intention_details[0] in ('department', 'doctor', 'disease'):
                processor_instance = JingdongKeywordDoctorProcessor()
            elif intention_details[0] in ('hospital',):
                processor_instance = JingdongKeywordHospitalProcessor()
            elif intention_details[0] in ('symptom', 'treatment', 'medicine'):
                processor_instance = JingdongKeywordPostProcessor()
    return processor_instance
