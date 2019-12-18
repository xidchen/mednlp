#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
intention.py -- some model of intention recognition

Author: maogy <maogy@guahao.com>
Create on 2018-08-27 Monday.
"""

import re
from mednlp.dao.ai_service_dao import ai_services, transform_area
from mednlp.utils.utils import load_json, match_patterns, strip_all_punctuations, print_logger
from mednlp.model.similarity import TfidfSimilarity
from mednlp.model.intention_model import IntentionUnionModel
import global_conf
import numpy as np
import copy
import json
from ailib.client.ai_service_client import AIServiceClient


class IntentionStrategy(object):
    """
    功能：
    通过正则文件判断句式；
    关键字句式优先query analyzer，entity_extract来判断,支持多关键词；
    通过句子中包含的实体情况，判断该句式是否成立，不成立的改句式为other
    """
    mode_xwyz = 'xwyz'
    mode_xwyz_doctor = 'xwyz_doctor'
    sen_type_keyword = 'keyword'
    sen_type_multi_keywords = 'multiKeywords'
    sen_type_other = 'other'
    sen_type_corpus_greeting = 'corpusGreeting'
    sen_type_greeting = 'greeting'
    sen_type_guide = 'guide'
    sen_type_content = 'content'
    sen_type_auto_diagnose = 'auto_diagnose'
    sen_type_related_doctor = 'relatedDoctor'
    intention_customer_service = 'customerService'
    sen_type_department = 'department'
    regex = load_json(global_conf.model_dir + 'semantic_regex_intention.json')
    field_mapping = {'std_department': 'department'}
    sentence_required_field = load_json(global_conf.model_dir + 'sentence_require_field.json')
    # 实体识别里以下类型的可以抽取出来
    # 仅去掉normal
    extract_entity_field = {
        'symptom', 'disease', 'department', 'hospital', 'hospital_department', 'examination',
        'treatment', 'medicine', 'doctor', 'nation', 'province', 'city', 'body_part', 'medical_word'
    }
    # xwyz 关键词意图优先级序列
    keyword_prior = [
        'medicine', 'disease', 'treatment', 'department', 'doctor',
        'hospital', 'symptom', 'city', 'province', 'body_part', 'examination', 'medical_word']
    # xwyz_doctor 关键词意图优先级序列
    keyword_prior_doctor = [
        'city', 'province', 'doctor', 'department', 'disease', 'symptom',
        'body_part', 'treatment', 'hospital', 'medicine', 'examination', 'medical_word']
    # 非模型意图
    non_model_intention = ['relatedDoctor']
    keyword_intention = ['keyword_%s' % temp for temp in keyword_prior]
    stop_words = [u',', u'，', u'、', u' ', u'？', u'?', u'.', u'。',
                  u'了', u'的']
    all_intent_dict = {
        '号源是否更新': ('haoyuanRefresh', 0),
        '有没有号': ('register', 1),
        '医生最近号源时间': ('recentHaoyuanTime', 2),
        '选医生-限定词': ('doctor', 3),
        '医生如何': ('doctorQuality', 4),
        '该医院是否有该科室': ('hospitalDepartment', 5),
        '医院如何': ('hospitalQuality', 6),
        '选医院-限定词': ('hospital', 7),
        '选科室下的细分科室': ('departmentSubset', 8),
        '科室二选一': ('departmentAmong', 9),
        '选科室-限定词': ('department', 10),
        '是否这个科室': ('departmentConfirm', 11),
        '附近的医院': ('hospitalNearby', 12),
        '医院排序': ('hospitalRank', 13),
        '其他other': ('other', 14),
        '内容': ('content', 15),
        '客服': ('customerService', 16)
    }

    all_intents = list(set([intent_temp for _, (intent_temp, label_temp) in all_intent_dict.items()]))
    all_intents.extend(['corpusGreeting', 'guide', 'greeting', 'auto_diagnose', 'relatedDoctor', 'sensitive'])
    all_intents.extend(keyword_intention)
    # 构建意图字典{0:haoyuanRefresh, 1:register}
    num_label_intent_dict = {label_temp: intent_temp for _, (intent_temp, label_temp) in all_intent_dict.items()}
    # 构建意图字典{haoyuanRefresh:0, register:1}
    label_num_intent_dict = {intent_temp: label_temp for _, (intent_temp, label_temp) in all_intent_dict.items()}
    model_dims = 17

    patient_group_include_words = ('肺', '肾', '肝', '乳腺', '血液')

    with open(global_conf.model_dir + 'customerService_regex.txt') as f:
        customerService_set = [s.strip() for s in f.readlines()]

    with open(global_conf.model_dir + 'greeting_regex.txt') as f:
        greeting_set = [s.strip() for s in f.readlines()]

    with open(global_conf.exclude_auto_diagnose_symptom, encoding='utf-8', mode='r') as f:
        exclude_symptom_set = set(s.strip() for s in f.readlines() if s)

    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger')
        self.sc = AIServiceClient(global_conf.cfg_path, 'SearchService')
        union_version = kwargs.get('union_version', 7)
        self.intention_model = IntentionUnionModel(
            cfg_path=global_conf.cfg_path, model_section='INTENTION_CLASSIFY_UNION_MODEL',
            model_version=union_version, logger=self.logger)
        self.intention_model.predict('我头晕好几天了')
        # 敏感词pattern生成
        with open(global_conf.sensitive_dict_path, encoding='utf-8', mode='r') as f:
            sensitive_word_list = [s.strip().split(',') for s in  f.readlines()]
        sensitive_re_list = []
        for group in sensitive_word_list:
            sensitive_re_list.append(''.join(['(?=.*%s)' % temp for temp in group]))
        self.sensitive_pattern = '|'.join(sensitive_re_list)
        print_logger('test模型finish', self.logger, 1)

    def _get_entities(self, query, fields=set(), need_id=True, stop=0):
        """
        从entity_extract得到实体后，将实体type统一为本类要求的形式，并根据条件过滤实体
        :param query: string
        :param fields: 留下的实体类型
        :param need_id: 是否需要id
        :param stop: 是否开启停用词
        :return: [实体,]
        """

        param = {'q': query, 'stopword': stop}
        entities, err_msg = ai_services(param, 'entity_extract', 'post')
        if not entities:
            return []
        entities = transform_area(entities)
        refined_entities = []

        for seg in entities:
            if seg.get('type') in IntentionStrategy.field_mapping.keys():
                seg['type'] = IntentionStrategy.field_mapping[seg['type']]

            if (not fields) or (fields and seg.get('type') in fields):
                if not need_id:
                    refined_entities.append(seg)
                if need_id and seg.get('entity_id'):
                    refined_entities.append(seg)
        return refined_entities

    def check_greeting_intention(self, query):
        return match_patterns(strip_all_punctuations(query), IntentionStrategy.greeting_set)

    def check_guide_intention(self, query):
        words = u"(放|更新|预约|问诊|号|院|家|医生|大夫|专家|教授|副教授|主任|副主任|普通|科)"
        if not re.search(words, query):
            return IntentionStrategy.sen_type_guide
        else:
            return IntentionStrategy.sen_type_other

    def _keyword_by_mode(self, target_segs, mode, intention_set):
        """
        通过mode重组keyword意图.
        """
        keyword = target_segs[0]
        # 设置关键词意图
        intention = self.sen_type_keyword
        if len(target_segs) > 1:
            intention = self.sen_type_multi_keywords
            prior = self.keyword_prior
            if mode == self.mode_xwyz_doctor:
                prior = self.keyword_prior_doctor
            keyword = self._select_prior_entity(target_segs, prior)
        intention_entities = {
            'entities': target_segs,
            'intention': intention,
            'intentionDetails': keyword['type']
        }
        if mode == self.mode_xwyz_doctor:
            if keyword['type'] in ('symptom', 'body_part', 'treatment') and 'department' in intention_set:
                intention_entities['intention'] = 'department'
                intention_entities.pop('intentionDetails', None)
            elif keyword['type'] == 'hospital' and 'doctor' in intention_set:
                intention_entities['intention'] = 'doctor'
                intention_entities.pop('intentionDetails', None)

        if mode in (self.mode_xwyz, self.mode_xwyz_doctor) and self.sen_type_department in intention_set:
            # 关键词意图 & 关键词为症状/部位，意图为科室
            entity_types_temp = [temp['type'] for temp in target_segs if temp.get(
                'type') in ('symptom', 'body_part')]
            if entity_types_temp:
                intention_entities['intention'] = self.sen_type_department
        return intention_entities

    def _select_prior_entity(self, entities, priors):
        """
        获取最高优先级的实体.
        """
        for prior_type in priors:
            for entity in entities:
                if prior_type == entity['type']:
                    return entity
        return entities[0]

    def check_keyword_intentions(self, entity, mode, intention_set):
        """
        分词，去停用词，判断是否全是id；id为1个，keyword;id多余1个，keywords,并给出中心词
        优先qa，不行就extract_entity
        :param query:
        :return:
        """
        keeped_segs = [seg for seg in entity
                       if seg.get('entity_name') not in self.stop_words and seg.get('type') != 'district']
        if not keeped_segs:
            return None
        # 目标实体词必须在keyword_prior里,也就是对外开放的关键词意图范围
        target_segs = [seg for seg in keeped_segs if seg.get('type') in self.keyword_prior]
        if not target_segs or len(keeped_segs) != len(target_segs):
            # 有部分实体在keyword_prior, 有部分不在,则也不是关键词
            return None
        result = self._keyword_by_mode(target_segs, mode, intention_set)
        return result

    def check_intention_by_regex(self, query):
        """
        1、通过正则得出正则相关的句式
        2、其他句式丢到'other'
        :return:句式名字符串
        """
        for ints_to_pats in IntentionStrategy.regex:
            if match_patterns(query, list(ints_to_pats.values())[0]):
                return list(ints_to_pats.keys())[0]
        return IntentionStrategy.sen_type_other

    def _switch_entity_type(self, wanted, entities):
        """
        从实体的所有可能的类型当中，获取想要的类型
        :param wanted: 想要的
        :param entities: 实体集
        :return: 实体集
        """
        if not wanted:
            return entities

        for seg in entities:
            if wanted in seg.get('type_all'):
                seg['type'] = wanted
        return entities

    def _count_entities(self, entities):
        """
        统计实体类型出现次数
        :return:
        """
        count = {}
        for seg in entities:
            _type = seg.get('type')
            count.setdefault(_type, 0)
            count[_type] += 1

        return count

    def check_intention_and_entities(self, sen_type, entities):
        """
        1、检查实体类型，若句式下目标实体缺失，则判断备用类型有无目标类型，并返回替换原类型后的实体集，
        2、之后，判断句式是否满实体类型约束，否则转换句式到other
        :param sen_type: 句式
        :param entities: 实体集
        :return: 矫正后的句式和实体集
        """
        require = IntentionStrategy.sentence_required_field.get(sen_type)
        if not require:
            return sen_type, entities

        # 根据wanted_types配置，当目标类型不存在时，启用备选字段
        count = self._count_entities(entities)
        wanted_list = []
        if require.get('wanted_types'):
            wanted_list = require.pop('wanted_types')
            for wanted in wanted_list:
                if not count.get(wanted):
                    entities = self._switch_entity_type(wanted, entities)
            count = self._count_entities(entities)

        # 判断实体类型计数是否符合配置
        break_flag = False
        operate = {'OR': '%s==%s', '>': '%s>=%s', '+>': '%s>=%s'}
        for k, v in require.items():
            if k in operate:
                cnt = 0
                for kk, kv in v.items():
                    kk_v = count.get(kk, 0)
                    if '+>' == k:
                        kk_v = sum([count.get(temp, 0) for temp in kk.split(',')])
                    eval_str = operate[k] % (kk_v, kv)
                    if eval(eval_str):
                        cnt += 1
                if cnt == 0:
                    break_flag = True
                    break
            else:
                if count.get(k) != v:
                    break_flag = True
                    break

        if wanted_list:
            require.update({'wanted_types': wanted_list})

        if break_flag:
            return IntentionStrategy.sen_type_other, entities
        return sen_type, entities

    def check_auto_diagnose(self, entities, init_intention):
        """
        query是否符合 自诊意图
        1.关键词里有症状词
        2.内容意图下有症状词的
        此处主需要判断是否有医疗词即可
        """
        if not entities:
            return init_intention
        symptom_set = set(temp['entity_name'] for temp in entities if temp.get(
            'type')=='symptom' and temp.get('entity_name'))
        if symptom_set.difference(self.exclude_symptom_set):
            return self.sen_type_auto_diagnose
        return init_intention

    def check_sensitive(self, query):
        # 政治类敏感词 + 自定义字典
        params = {
            'q': query,
            'type': '10'
        }
        is_sensitive = False
        res = None
        try:
            res = self.sc.query(params, service='sensitive_word')
        except Exception as err:
            print_logger(err, self.logger, debug=1)
            print_logger('[%s]请求sensitive_word异常' % json.dumps(
                params, ensure_ascii=False), self.logger, debug=1)
        if res and res.get('result', {}).get('sensitive'):
            return True
        if re.match(self.sensitive_pattern, query):
            is_sensitive = True
        return is_sensitive

    def check_related_doctor(self, query, entities, intention_set):
        """
        校对是否是相关医生意图, 1.有医生词, 2.情感分析为positive
        :param query:
        :param entities:
        :return: 空{} 或者 {"intention": "related_doctor"}
        """
        result = {}
        if self.sen_type_related_doctor not in intention_set:
            return result
        doctor_entity = [temp for temp in entities if 'doctor' == temp.get('type')]
        if doctor_entity:
            params = {
                'source': 'aiself',
                'query': [
                    {'query_id': 0, 'query': query}
                ]
            }
            res, err_msg = ai_services(json.dumps(params), 'sentiment_service', 'post')
            if res:
                positive = res[0].get('positive')
                negative = res[0].get('negative')
                if positive and negative and float(positive) > float(negative):
                    result['intention'] = self.sen_type_related_doctor
                    result['entities'] = entities
            else:
                logger.error('sentiment_service 无数据, params:%s' % json.dumps(params, ensure_ascii=False))
        return result

    def check_intention_by_model(self, query, intention_set=None, **kwargs):
        """
        进入该方法的意图暂定为other,仅在模型score大于阈值
        且意图在intention_set集合里，返回模型意图，否则为other
        :param query:
        :return:  意图和score
        """
        debug = kwargs.get('debug', 0)
        threshold = 0.0  # 阈值
        # predict_result = np.zeros(self.model_dims)  # 融合后的分数列表
        is_use_union, union_result = self.intention_model.predict(query)
        predict_result = union_result
        # is_use_pos, pos_result = self.pos_char_model.predict(query)
        # if is_use_union:
        #     predict_result += union_result * 0.5  # 2018
        # if is_use_pos:
        #     predict_result += pos_result * 0.5
        if (not is_use_union):
            intent = self.sen_type_other
            score = None
            print_logger('7-char和pinyin都无判断结果,返回other意图', self.logger, debug)
        else:
            if intention_set is not None:
                for temp in range(0, self.model_dims):
                    if self.num_label_intent_dict.get(temp) not in intention_set:
                        predict_result[temp] = 0.0
            # 上次已对关闭所有意图做限制，这里默认肯定有意图存在，进行归一化
            predict_result = np.divide(predict_result, sum(predict_result))
            score = float(np.max(predict_result))
            intent = self.num_label_intent_dict[(np.argmax(predict_result))]
            if score < threshold:
                # score 小于阈值,设置意图为other
                intent = self.sen_type_other
                score = None
                print_logger('10-score 小于 threshold,返回other意图', self.logger, debug)
        return intent, score

    def get_intention_set(self, intention_set, exclude_intention_set):
        """
        获取意图集合
        :param
            intention_set
            exclude_intention_set
        :return:
            intention_set： 意图集合

           intention_set=None,全部意图
           intention_set=[], 无意图，直接返回other意图
           intention_set=[x1,x2,x3],说明意图在集合里挑选
        """
        if intention_set is None:  # None
            intention_set = set(copy.deepcopy(self.all_intents))
        elif not intention_set:  # []
            intention_set = set()
        else:
            # 判断是keyword还是keyword_,若传了keyword_,不可能传keyword意图
            intention_set = set(intention_set)
            intention_set.add(IntentionStrategy.sen_type_other)
            if 'keyword' in intention_set:
                intention_set.remove('keyword')
                intention_set |= copy.deepcopy(set(self.keyword_intention))
        intention_set = list(intention_set.difference(set(exclude_intention_set)))
        return intention_set

    def get_keyword_intention(self, info, query, mode, intention_set,
                              exclude_other_intention_set, log, need_entity):
        """
        得到关键词意图
        :return:
        """
        trace = log.get('trace', [])
        query_entities = self._get_entities(query, set(), need_id=False, stop=1)
        # 此处意图除了keyword 还有multiKeywords, department, doctor
        keyword_info = self.check_keyword_intentions(query_entities, mode, intention_set=intention_set)

        if keyword_info and keyword_info.get('intention'):
            keyword_intention = keyword_info['intention']
            keyword_intention_detail = keyword_info.get('intentionDetails', '')
            entities = keyword_info.get('entities')
            self.post_deal(info, entities, need_entity=need_entity)
            if 'multiKeywords' == keyword_intention:
                keyword_intention = 'keyword'
            # 当自诊意图在候选集里,判断是否是自诊意图
            if IntentionStrategy.sen_type_auto_diagnose in intention_set:
                keyword_intention = self.check_auto_diagnose(keyword_info.get('entities'), keyword_intention)
            # 将非细分keyword细分化,比如symptom 变为keyword_symptom
            keyword_intention_temp = keyword_intention
            if keyword_intention == 'keyword' and keyword_intention_detail:
                keyword_intention_temp = 'keyword_%s' % keyword_intention_detail
            # 如果意图在set集合里,则返回info
            if keyword_intention_temp in intention_set:
                # doctor,department,keyword细分意图
                info['intention'] = keyword_intention
                # 非自诊意图 & 有intentionDetails
                if keyword_intention.startswith('keyword'):
                    info['intentionDetails'] = keyword_intention_detail
                trace.append(1)
                log['keyword_intention'] = keyword_intention_temp
                return info

        #  只有关键词意图,无额外的意图,意图置为other返回
        if not exclude_other_intention_set.difference(set(self.keyword_intention)):
            info['intention'] = 'other'
            trace.append(2)
        return info

    def post_deal(self, info, entity, **kwargs):
        need_entity = kwargs.get('need_entity', True)
        if entity and need_entity:
            info['entities'] = entity
        return info

    def check_patient_group(self, query, mode, info, **kwargs):
        result = False
        entity = info.get('entities', [])
        for temp in entity:
            entity_name = temp.get('entity_name')
            if not entity_name:
                continue
            for include_words in self.patient_group_include_words:
                if include_words in entity_name:
                    return True
        return result

    accompany_intention_dict = {
        'patient_group': check_patient_group
    }

    def get_accompany_intention(self, query, mode, info, **kwargs):
        """
        伴随意图处理
        :param query: 用户问句
        :param mode: 模式 ai_qa/xwyz/xwyz_doctor
        :param info: 返回信息
        :param kwargs:
        :return:
        """
        result = []
        info['accompany_intention'] = result
        accompany_intention_set = kwargs.get('accompany_intention_set', [])
        for temp in accompany_intention_set:
            if self.accompany_intention_dict.get(temp):
                accompany_intention_result = self.accompany_intention_dict[temp](self, query, mode, info, **kwargs)
                if accompany_intention_result:
                    result.append(temp)
        return

    def get_intention_and_entities(self, query, mode, **kwargs):
        result = self._get_intention_and_entities(query, mode, **kwargs)
        self.get_accompany_intention(query, mode, result, **kwargs)
        return result

    def _get_intention_and_entities(self, query, mode, **kwargs):
        """获取意图和实体

        :param query: 用户问句
        :param mode: 模式,  xwyz/xwyz_doctor/ai_qa
        :param kwargs:
                intention_set: "",意图集合
                accompany_intention_set： [],伴随意图集合
                debug: 1/调试, 0/不调试
        :return:
            {
                "intention": "xxx",
                "entities": [
                    {
                        "entity_name": "头痛",
                        "type": "symptom",
                        "type_all": [
                            "symptom",
                            "doctor",
                            "disease"
                        ],
                        "entity_id": "4c045982-32a5-11e6-804e-848f69fd6b70",
                        "entity_id_all": [
                            "4c045982-32a5-11e6-804e-848f69fd6b70",
                            "8739194a-32a3-11e6-804e-848f69fd6b70",
                            "3cfc654a-9175-4c68-8e23-770e0af26f0f000"
                        ]
                    }
                ]
            }

        trace过程打点:
        1.关键词意图返回
        2.关键词无意图,且意图集合无别的意图
        3.正则后的意图 不在意图集合里,置为other
        4.模型预测
        5.意图校验不成功
        6.content意图无实体，置为other
        7.other意图有实体，置为content
        8.other意图有实体且是xwyz_doctor,置为department
        9.内容意图转自诊
        10.意图不在意图集合里
        11.返回relatedDoctor
        12.非模型意图, 若识别不成功 & 意图集合仅1个 ,返回other
        """
        debug = kwargs.get('debug', 0)
        need_entity = kwargs.get('need_entity', True)
        intention_set = kwargs.get('intention_set')
        exclude_intention_set = kwargs.get('exclude_intention_set', [])
        info = {}
        trace = []
        log = {'trace': trace}
        if debug:
            info['log'] = log
        intention_set = self.get_intention_set(intention_set, exclude_intention_set)
        if not intention_set:
            # 若意图集合为[], 返回other
            info['intention'] = IntentionStrategy.sen_type_other
            return info

        # 排除other以外的意图
        exclude_other_intention_set = set(copy.deepcopy(intention_set))
        exclude_other_intention_set.remove('other')

        if len(query) < 100:
            # 关键词只关注10个实体类型
            keyword_info = self.get_keyword_intention(
                info, query, mode, intention_set, exclude_other_intention_set, log, need_entity=need_entity)
            if keyword_info.get('intention'):
                return keyword_info

        refined_entities = self._get_entities(query, fields=self.extract_entity_field, need_id=False, stop=0)

        # 校对是否是敏感词意图
        if 'sensitive' in intention_set:
            if self.check_sensitive(query):
                info['intention'] = 'sensitive'
                info['entities'] = []
                return info

        # 符合医生相关词核对
        related_doctor_info = self.check_related_doctor(query, refined_entities, intention_set)
        if related_doctor_info.get('intention'):
            info['intention'] = related_doctor_info['intention']
            self.post_deal(info, related_doctor_info.get('entities'), need_entity=need_entity)
            trace.append(11)
            return info

        if 'hr_qa' in intention_set:
            info['intention'] = 'hr_qa'
            info['entities'] = []
            return info
        elif 'qa' in intention_set:
            info['intention'] = 'qa'
            info['entities'] = []
            return info

        # 非模型意图, 若识别不成功 & 意图集合仅1个 ,返回other
        if len(exclude_other_intention_set) == 1 and list(exclude_other_intention_set)[0] in self.non_model_intention:
            info['intention'] = 'other'
            self.post_deal(info, refined_entities, need_entity=need_entity)
            trace.append(12)
            return info

        model_score, model_intent = None, None
        regex_sen_type = self.check_intention_by_regex(query)
        log['regex_intention'] = regex_sen_type
        print_logger('2-regex结果:regex_sen_type: %s' % regex_sen_type, self.logger, debug)  # 正则结果
        if regex_sen_type not in intention_set:
            regex_sen_type = IntentionStrategy.sen_type_other
            print_logger('3-regex经意图集合判断,regex_sen_type: %s' % regex_sen_type, self.logger, debug)
            trace.append(3)
        if IntentionStrategy.sen_type_other == regex_sen_type:  # 意图为other,走模型
            # model_intent, model_score = self.check_intention_by_model_alter(query, intention_set, **{'debug': debug})
            model_intent, model_score = self.check_intention_by_model(query, intention_set, **{'debug': debug})
            regex_sen_type = model_intent  # 模型意图赋值
            trace.append(4)
            log['model_intention'] = model_intent
        intention, entities = self.check_intention_and_entities(regex_sen_type, refined_entities)

        if regex_sen_type != intention:
            # 意图校验不成功
            trace.append(5)

        # content意图 & 无实体,则设置为other意图 (防止model预测错误成content)
        if not entities and intention == self.sen_type_content:
            intention = self.sen_type_other
            trace.append(6)

        # content 意图
        if entities and (intention == self.sen_type_other):
            intention = IntentionStrategy.sen_type_content
            trace.append(7)
            if mode == self.mode_xwyz_doctor:
                intention = 'department'
                trace.append(8)

        # content意图的时候，判断是否是自诊意图
        if intention == self.sen_type_content and self.sen_type_auto_diagnose in intention_set:
            intention = self.check_auto_diagnose(entities, intention)
            trace.append(9)

        self.post_deal(info, entities, need_entity=need_entity)

        # other意图
        if intention == IntentionStrategy.sen_type_other:
            #  customerService
            if match_patterns(strip_all_punctuations(query), IntentionStrategy.customerService_set) \
                    and IntentionStrategy.intention_customer_service in intention_set:
                    info['intention'] = self.intention_customer_service
                    return info

            threshold = 0.4
            if mode == self.mode_xwyz_doctor:
                threshold = 0.6
            corpus_greeting_answer = TfidfSimilarity(
                global_conf.train_data_path + '/medical_robot/hanxuan_corpus.txt').best_answer(query, threshold)
            if corpus_greeting_answer and IntentionStrategy.sen_type_corpus_greeting in intention_set:
                # corpusGreeting
                info['intention'] = self.sen_type_corpus_greeting
                return info

            if self.check_greeting_intention(query) and IntentionStrategy.sen_type_greeting in intention_set:
                # greeting
                info['intention'] = self.sen_type_greeting
                return info

            intention = self.check_guide_intention(query)
        if intention not in intention_set:
            intention = IntentionStrategy.sen_type_other
            trace.append(10)
        info['intention'] = intention
        if model_intent == intention and model_score:
            # 模型意图和最后意图一致且score存在，则赋值
            info['score'] = model_score
        return info

    # 调试获取最优权重代码--------

    # 得到模型结果
    def get_models_result_optimize(self, query):
        is_use_char, char_result = self.intention_model.predict(query)  # 字符
        is_use_pinyin, pinyin_result = self.intention_pinyin_model.predict(query)  # 拼音
        is_use_pos, pos_result = self.pos_char_model.predict(query)
        is_use_word_pos, word_pos_result = self.word_pos_model.predict(query)
        return char_result, pinyin_result, pos_result, word_pos_result, \
               is_use_char, is_use_pinyin, is_use_pos, is_use_word_pos,

    def check_intention_by_model_alter(self, query, intention_set=None, **kwargs):
        """
                进入该方法的意图暂定为other,仅在模型score大于阈值
                且意图在intention_set集合里，返回模型意图，否则为other
                :param query:
                :return:  意图和score
                """
        debug = kwargs.get('debug', 0)
        threshold = 0.4  # 阈值
        predict_result = np.zeros(self.model_dims)  # 融合后的分数列表
        is_use_char, char_result = self.intention_model.predict(query)  # 字符
        is_use_pinyin, pinyin_result = self.intention_pinyin_model.predict(query)  # 拼音
        is_user_pos, pos_result = self.pos_char_model.predict(query)

        if is_use_char:
            predict_result += char_result * 0.5
            print_logger('4-意图char模型,result: %s , intent:%s' % (
                list(char_result), self.num_label_intent_dict[(np.argmax(char_result))]), self.logger, debug)
        if is_use_pinyin:
            predict_result += pinyin_result * 0.2
            print_logger('5-意图pinyin模型,result: %s , intent:%s' % (
                list(pinyin_result), self.num_label_intent_dict[(np.argmax(pinyin_result))]),
                         self.logger, debug)
        if is_user_pos:
            predict_result += pos_result * 0.7
            print_logger('6-意图pos_char模型,result: %s , intent:%s' % (
                list(pos_result), self.num_label_intent_dict[(np.argmax(pos_result))]),
                         self.logger, debug)
        if (not is_use_char) and (not is_use_pinyin) and (not is_user_pos):
            # 如果3个都没结果，则sum(result) == 0, 返回other
            intent = self.sen_type_other
            score = None
            print_logger('7-char和pinyin都无判断结果,返回other意图', self.logger, debug)
        else:
            # 根据融合的结果进行预测
            print_logger('8-未考虑意图集合的融合模型,result: %s , intent:%s, score:%s' % (
                list(predict_result), self.num_label_intent_dict[(np.argmax(predict_result))],
                float(np.max(predict_result))), self.logger, debug)
            if intention_set is not None:
                for temp in range(0, self.model_dims):
                    if self.num_label_intent_dict.get(temp) not in intention_set:
                        predict_result[temp] = 0.0
            # 上次已对关闭所有意图做限制，这里默认肯定有意图存在，进行归一化
            score = float(np.max(predict_result))
            intent = self.num_label_intent_dict[(np.argmax(predict_result))]
            print_logger('9-考虑意图集合的融合模型,result: %s , intent:%s, score:%s, threshold:%s' % (
                list(predict_result), intent, score, threshold), self.logger, debug)
            if score < threshold:
                # score 小于阈值,设置意图为other
                intent = self.sen_type_other
                score = None
                print_logger('10-score 小于 threshold,返回other意图', self.logger, debug)
        return intent, score

    def check_intention_by_model_alter_optimize(self, intention_set=None, **kwargs):
        # 调试参数
        debug = kwargs.get('debug', 0)
        threshold = float(kwargs.get('threshold', 0)) / 10  # 阈值
        predict_result = np.zeros(self.model_dims)  # 融合后的分数列表
        char_result = kwargs['char_result']
        pinyin_result = kwargs['pinyin_result']
        pos_result = kwargs['pos_result']
        word_pos_result = kwargs['word_pos_result']
        is_use_char = kwargs['is_use_char']
        is_use_pinyin = kwargs['is_use_pinyin']
        is_use_pos = kwargs['is_use_pos']
        is_use_word_pos = kwargs['is_use_word_pos']
        char_weight = float(kwargs['char_weight']) / 10
        pinyin_weight = float(kwargs['pinyin_weight']) / 10
        pos_weight = float(kwargs['pos_weight']) / 10
        word_pos_weight = float(kwargs['word_pos_weight']) / 10
        if is_use_char:
            predict_result += char_result * char_weight
            print_logger('4-意图char模型,result: %s , intent:%s' % (
                list(char_result), self.num_label_intent_dict[(np.argmax(char_result))]), self.logger, debug)
        if is_use_pinyin:
            predict_result += pinyin_result * pinyin_weight
            print_logger('5-意图pinyin模型,result: %s , intent:%s' % (
                list(pinyin_result), self.num_label_intent_dict[(np.argmax(pinyin_result))]),
                         self.logger, debug)
        if is_use_pos:
            predict_result += pos_result * pos_weight
            print_logger('6-意图pos_char模型,result: %s , intent:%s' % (
                list(pos_result), self.num_label_intent_dict[(np.argmax(pos_result))]),
                         self.logger, debug)
        if is_use_word_pos:
            predict_result += word_pos_result * word_pos_weight
            print_logger('7-意图word_pos_char模型,result: %s , intent:%s' % (
                list(word_pos_result), self.num_label_intent_dict[(np.argmax(word_pos_result))]),
                         self.logger, debug)
        if (not is_use_char) and (not is_use_pinyin) and (not is_use_pos) and (not is_use_word_pos):
            # 如果3个都没结果，则sum(result) == 0, 返回other
            intent = self.sen_type_other
            score = None
            print_logger('7-char和pinyin都无判断结果,返回other意图', self.logger, debug)
        else:
            # 根据融合的结果进行预测
            print_logger('8-未考虑意图集合的融合模型,result: %s , intent:%s, score:%s' % (
                list(predict_result), self.num_label_intent_dict[(np.argmax(predict_result))],
                float(np.max(predict_result))), self.logger, debug)
            if intention_set is not None:
                for temp in range(0, self.model_dims):
                    if self.num_label_intent_dict.get(temp) not in intention_set:
                        predict_result[temp] = 0.0
            # 上次已对关闭所有意图做限制，这里默认肯定有意图存在，进行归一化
            predict_result = np.divide(predict_result, sum(predict_result))  # 归一化
            score = float(np.max(predict_result))
            intent = self.num_label_intent_dict[(np.argmax(predict_result))]
            print_logger('9-考虑意图集合的融合模型,result: %s , intent:%s, score:%s, threshold:%s' % (
                list(predict_result), intent, score, threshold), self.logger, debug)
            if score < threshold:
                # score 小于阈值,设置意图为other
                intent = self.sen_type_other
                score = None
                print_logger('10-score 小于 threshold,返回other意图', self.logger, debug)
        return intent, score


if __name__ == '__main__':
    from ailib.utils.log import GLLog

    logger = GLLog('intention_recognition_input_output', level='info', log_dir=global_conf.log_dir).getLogger()
    intention = IntentionStrategy(logger=logger, version=6)
    question = '肺炎'
    # question = '头痛是挂神经内科吗'
    # result = intention.get_intention_and_entities(
    #     question, mode='xwyz', need_entity=True, debug=1, exclude_intention_set=[intention.sen_type_related_doctor],
    #     accompany_intention_set=['patient_group'])
    result = intention.get_intention_and_entities(
        question, mode='ai_qa', need_entity=True, intention_set=['hr_qa', 'sensitive'])
    # result = intention.get_intention_and_entities(
    #     '咨询脚指甲疾病挂哪个科室', mode='xwyz',
    #     intention_set=[
    #         "departmentConfirm", "departmentAmong", "departmentSubset",
    #         "hospital", "hospitalDepartment", "hospitalQuality", "doctor",
    #         "recentHaoyuanTime", "doctorQuality", "haoyuanRefresh", "register",
    #         "keyword", "greeting", "hospitalNearby", "hospitalRank", "customerService"],
    #     debug=1)
    print(json.dumps(result, ensure_ascii=False))
