#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
entity_extract.py -- extract medical entities from content via priority order
Author : chenxd
Create on 2018.12.17
"""

import re
import jieba
import string
import global_conf
from mednlp.text.mmseg import MMSeg
from collections import OrderedDict
from mednlp.text.sex_age_ner import AgeSexTrans
from mednlp.text.value_normalization import ValueNormalization2


age_model = AgeSexTrans()
ins_value_model = ValueNormalization2()


class OptimizeExtract(object):

    stopwords = {
        'doctor': {'医生', '医师', '主任', '副主任', '大夫', '院长', '副院长'},
        'body_part': {'部'},
        'hospital': {'医院', '诊所', '院'}
    }

    def __init__(self):
        super(OptimizeExtract, self).__init__()
        # 导入医院科室和标注科室的匹配字典
        department_std_dict = {}
        with open(global_conf.department_std_match_path, 'r') as f:
            for line in f.readlines():
                if line:
                    hosp_dept, std_dept, std_id = re.split('\t', line.strip())
                    department_std_dict[hosp_dept] = [std_dept, std_id]
        self.department_std_dict = department_std_dict

    def dict_choose(self, priority_dict_order):
        """
        字典选择开关优化，名称映射到字典实际名称
        :param priority_dict_order: 原始字典列表
        :return: 新的转换后的字典
        """
        priority_dict_list = []
        for dict_type in priority_dict_order:
            if dict_type == 'disease':  # 在concatenate，部位+症状/特定词=疾病（后续过滤掉纯部位词）
                priority_dict_list.extend(['disease', 'disease_all', 'body_part'])
            elif dict_type == 'symptom':  # 在concatenate，部位+症状/特定词=症状（后续过滤掉纯部位词）
                priority_dict_list.extend(['symptom_wy', 'symptom_wy_synonym_extend', 'body_part'])
            elif dict_type == 'hospital':  # 在concatenate，地域+医院=医院（后续过滤掉纯地域词）
                priority_dict_list.extend(['hospital', 'hospital_brand', 'area'])
            elif dict_type == 'department':  # 在concatenate，部位+科室=医院科室（后续过滤掉纯部位词）
                priority_dict_list.extend(['std_department', 'hospital_department', 'body_part'])
            elif dict_type == 'physical':  # 在concatenate，部位+特定词=体征（后续过滤掉纯部位词）
                priority_dict_list.extend(['physical', 'body_part'])
            elif dict_type == 'examination_item':  # 在concatenate，部位+特定词=检查项目（后续过滤掉纯部位词）
                priority_dict_list.extend(['examination_item', 'body_part'])
            elif dict_type == 'examination_result':  # 在concatenate，部位+特定词=检查结果（后续过滤掉纯部位词）
                priority_dict_list.extend(['examination_result', 'body_part'])
            else:
                priority_dict_list.append(dict_type)
        if len(priority_dict_list) >= 1:
            priority_dict_list.extend(['core', 'medical_word'])

        return priority_dict_list

    def dict_choose_kg(self, priority_dict_order):
        """
        字典选择开关优化，名称映射到字典实际名称
        :param priority_dict_order: 原始字典列表
        :return: 新的转换后的字典
        """
        priority_dict_list = []
        for dict_type in priority_dict_order:
            if dict_type == 'disease':  # 在concatenate，部位+症状/特定词=疾病（后续过滤掉纯部位词）
                priority_dict_list.extend(['disease', 'body_part'])
            elif dict_type == 'symptom':  # 在concatenate，部位+症状/特定词=症状（后续过滤掉纯部位词）
                priority_dict_list.extend(['symptom_wy', 'body_part'])
            elif dict_type == 'hospital':  # 在concatenate，地域+医院=医院（后续过滤掉纯地域词）
                priority_dict_list.extend(['hospital', 'hospital_brand', 'area'])
            elif dict_type == 'department':  # 在concatenate，部位+科室=医院科室（后续过滤掉纯部位词）
                priority_dict_list.extend(['std_department', 'hospital_department', 'body_part'])
            elif dict_type == 'physical':  # 在concatenate，部位+特定词=体征（后续过滤掉纯部位词）
                priority_dict_list.extend(['physical', 'body_part'])
            elif dict_type == 'examination_item':  # 在concatenate，部位+特定词=检查项目（后续过滤掉纯部位词）
                priority_dict_list.extend(['examination_item', 'body_part'])
            elif dict_type == 'examination_result':  # 在concatenate，部位+特定词=检查结果（后续过滤掉纯部位词）
                priority_dict_list.extend(['examination_result', 'body_part'])
            else:
                priority_dict_list.append(dict_type)
        if len(priority_dict_list) >= 1:
            priority_dict_list.extend(['core', 'medical_word'])

        return priority_dict_list

    def extract_optimize(self, sentence, medical_entities):
        """
        :param sentence: 原始句子
        :param medical_entities: extract的结果
        :return: extract_optimize后的结果
        """
        # medical_entities = medical_entities.copy()
        ## 医院总的抽取方式： 地域 + （附属）？第？【一-十】（人民）？（附属）？（医院）{0，2}
        for key in list(medical_entities.keys()):
            values = medical_entities[key]
            # print key, values
            if values['type'] == 'area':
                entity_patt0 = values['entity_name'] + '([医科大学院]{0,4}第[零一二三四五六七八九十]{0,3}[附属]{0,2}(?:院|医院))'
                entity_patt1 = values['entity_name'] + '([医科大学院]{0,4}[附属]{1,2}第?[一二三四五六七八九十](?:院|医院)?)'
                entity_patt2 = values['entity_name'] + '第?[一二三四五六七八九十]?(人民|中心|县级|区级|中医)?(?:院|医院)'
                for entity_patt in [entity_patt0, entity_patt1, entity_patt2]:
                    if re.findall(entity_patt, sentence):
                        pattern_finditer = re.finditer(entity_patt, sentence)
                        for entity_hos in pattern_finditer:
                            position = entity_hos.span()
                            entity_name = entity_hos.group()
                            key_new = '{0}\t{1}\t{2}'.format(entity_name, str(position[0]), str(position[1]))
                            priority_medical_entity = {
                                'entity_name': entity_name, 'loc': (position[0], position[1] - 1),
                                'entity_id': '', 'entity_id_all': '',
                                'type': 'hospital', 'type_all': ['hospital']
                            }
                            medical_entities[key_new] = priority_medical_entity

        return medical_entities

    def age_extract(self, sentence, medical_entities):
        """
        获取年龄，并转化为符合的形式
        :param sentence: 原始句子
        :param medical_entities: 实体字典
        :return: 附带年龄属性的实体字典
        """
        age_list = age_model.obtain_age(sentence)
        if age_list:
            for ai in age_list:
                name = ai.get('age')
                position = ai.get('position')
                age_range = ai.get('type', '')
                age_property = {'age': name}
                if age_range:
                    age_property['age_range'] = age_range
                key_new = '{0}\t{1}\t{2}'.format(name, str(position[0]), str(position[1]))
                new_entity_dict = {
                    'entity_name': name, 'loc': (position[0], position[1]),
                    'type': 'crowd', 'type_all': ['crowd'],
                    'property': age_property
                }

                # print(new_entity_dict)
                medical_entities[key_new] = new_entity_dict
        return medical_entities

    def hospital_optimize(self, entities):
        """
        医院实体识别优化,医院品牌支持. 有问题，会剔除医院后面部分症状
        参数:
        entities->实体列表,结构[{'entity_name':,'type':}].
        """
        new_entities = []
        entity_point = 0
        for index, entity in enumerate(entities):
            if index < entity_point:
                continue
            name = entity.get('entity_name')
            entity_type = entity.get('type')
            if entity_type == 'hospital_brand':
                new_name, entity_point_add = self._build_hospital_brand(
                    name, entities[index + 1: index + 6])
                entity_point = index + entity_point_add + 1
                e_item = {'type': 'hospital', 'entity_name': new_name, 'entity_id': '', 'entity_id_all': []}
                new_entities.append(e_item)
            else:
                new_entities.append(entity)
        return new_entities

    def _build_hospital_brand(self, brand, entities):
        """
        构建医院品牌的医院实体.
        """
        is_find_hospital = False
        hospital_name = brand
        h_len = 0
        h_index = 0
        for entity in entities:
            name = entity.get('entity_name')
            if h_len > 5:
                break
            hospital_name += name
            h_index += 1
            if name in ['医院', '附医']:
                is_find_hospital = True
                break
            h_len += len(name)
        if is_find_hospital:
            return hospital_name, h_index
        else:
            h_index = 0
        return brand, h_index

    def _check_area_sub_type(self, entity):
        entity_id = entity['entity_id']
        if int(entity_id) < 34:
            return 'province'
        elif int(entity_id) < 582:
            return 'city'
        elif entity['entity_name'] == '全国':
            return 'nation'
        elif int(entity_id) > 581:
            return 'district'
        return ''

    def department_optimize(self, entities):
        """
        科室实体识别优化,添加医院科室的 标注科室
        参数:
        entities->实体列表,结构[{'entity_name':,'type':}].
        """
        new_entities = []
        for index, entity in enumerate(entities):
            name = entity.get('entity_name')
            entity_type = entity.get('type')
            if entity_type == 'hospital_department' and self.department_std_dict.get(name):
                dict_dept = self.department_std_dict.get(name)
                entity['std_department'] = dict_dept[0]
                entity['std_id'] = dict_dept[-1]

            new_entities.append(entity)
        return new_entities

    def area_optimize(self, entities, extractor):
        """
        地区优化,(直辖市id处理,省市区子类型区分,医院名抽取地区).
        参数:
        entities->实体列表.
        """
        new_entities = []
        for index, entity in enumerate(entities):
            new_entities.append(entity)
            entity_type = entity.get('type')
            entity_type_all = entity.get('type_all')
            entity_id = entity.get('entity_id')
            entity_id_all = entity.get('entity_id_all')

            if not entity_type and not entity_type_all:
                continue
            if entity_id and 'area' == entity_type:
                try:
                    entity_id_all.sort(key=int)
                except Exception:
                    pass
                entity['entity_id'] = entity_id_all[0]
                entity['sub_type'] = self._check_area_sub_type(entity)
            if 'hospital' == entity_type:
                entity_name = entity['entity_name']
                # extractor = MMSeg(['area'], uuid_all=True, is_uuid=True, update_dict=False, is_all_word=False)
                result = extractor.cut(entity_name)
                if result and len(result) == 1:
                    for area_name, area_id in result.items():
                        area_id = list(area_id)
                        area_id.sort(key=int)

                        n_item = {
                            'entity_name': area_name, 'entity_id': area_id[0],
                            'type': 'area', 'entity_id_all': area_id
                        }
                        n_item['sub_type'] = self._check_area_sub_type(n_item)
                        new_entities.append(n_item)
        return new_entities

    def age_sex_optimize(self, age_sex_property, entities):
        """
        属性，年龄和性别抽取，年龄分段
        :param age_sex_property:属性开关
        :param entities:实体的字典列表
        :return:实体的字典列表
        """
        new_entities = []
        for index, entity in enumerate(entities):
            entity_type = entity.get('type')
            entity_name = entity.get('entity_name')
            prop = {}
            if entity_type == 'crowd':
                if 'sex' in age_sex_property:
                    if re.findall('男', entity_name):
                        prop['sex'] = '2'
                    elif re.findall('女', entity_name):
                        prop['sex'] = '1'
                if 'age' in age_sex_property:
                    age_word, age_range = age_model.age_section(entity_name)
                    if age_range:
                        prop['age'] = age_word
                        prop['age_range'] = age_range
                if prop:
                    entity['age_sex_property'] = prop
            new_entities.append(entity)
        return new_entities

    def redistrict(self, entities):
        """
        实体中出现重叠分错现象：不过敏，有关节炎，有关怀孕，和梅毒等,医生名错误等
        :param entities: 实体列表
        :return: 实体列表
        """
        for index, entity in enumerate(entities):
            name = entity.get('entity_name')
            # entity_type = entity.get('type')
            if name in ['节炎', '敏', '毒'] and index > 0:
                if name == '节炎' and entities[index - 1].get('entity_name') == '有关':
                    entities[index - 1]['entity_name'] = '有'
                    entities[index]['entity_name'] = '关节炎'
                    entities[index]['type'] = 'disease'
                    entities[index]['type_all'] = ['disease']
                    entities[index]['entity_id'] = '44264'
                    entities[index]['entity_id_all'] = ['44264']
                elif name == '敏' and entities[index - 1].get('entity_name') == '不过':
                    entities[index - 1]['entity_name'] = '不'
                    entities[index]['entity_name'] = '过敏'
                    entities[index]['type'] = 'disease'
                    entities[index]['type_all'] = ['disease']
                    entities[index]['entity_id'] = 'add_disease20181011_00037'
                    entities[index]['entity_id_all'] = ['add_disease20181011_00037']
                elif name == '毒' and entities[index - 1].get('entity_name') == '和梅':
                    entities[index - 1]['entity_name'] = '和'
                    entities[index - 1]['type'] = 'normal'
                    entities[index - 1]['type_all'] = ['normal']
                    entities[index - 1].pop('entity_id')
                    entities[index - 1].pop('entity_id_all')
                    entities[index]['entity_name'] = '梅毒'
                    entities[index]['type'] = 'disease'
                    entities[index]['type_all'] = ['disease']
                    entities[index]['entity_id'] = '2f59071a-31df-11e6-804e-848f69fd6b70'
                    entities[index]['entity_id_all'] = ['38630', '2f59071a-31df-11e6-804e-848f69fd6b70']
            elif name in ['余天', '余年', '余周', '周天', '周期']:
                entities[index]['type'] = 'normal'
                entities[index]['type_all'] = ['normal']
                try:
                    entities[index].pop('entity_id')
                    entities[index].pop('entity_id_all')
                except Exception:
                    pass
            ### 错误的医生名
            elif re.findall('放$', name) and index < len(entities) - 1:
                # print(name)
                # 对于模式：人名 + 放号 识别为 医生名+ 号 （李明放号么）
                if entities[index + 1].get('entity_name') == '号':
                    entities[index + 1]['entity_name'] = '放号'
                    entities[index]['entity_name'] = name[:-1]
            elif name == '周四维' and index < len(entities) - 1:
                # print(name)
                if entities[index + 1].get('entity_name') == '彩超':
                    entities[index]['entity_name'] = '周'
                    entities[index]['type'] = 'normal'
                    entities[index]['type_all'] = ['normal']
                    entities[index].pop('entity_id')
                    entities[index].pop('entity_id_all')
                    entities[index + 1]['entity_name'] = '四维彩超'
                    entities[index + 1]['type'] = 'examination'
                    entities[index + 1]['type_all'] = ['examination']
                    entities[index + 1]['entity_id'] = 'add_examination_20181011_000151'
                    entities[index + 1]['entity_id_all'] = ['add_examination_20181011_000151']

        return entities

    def stop_word_filter(self, entities):
        """
        停止词过滤
        参数:
        entities->实体列表.
        """
        new_entities = []
        entity_type_last = None
        for entity in entities:
            entity_name = entity.get('entity_name')
            if self.stopwords.get(entity_type_last):
                if str(entity_name) in self.stopwords[entity_type_last]:
                    entity_type_last = entity.get('type')
                    continue
            new_entities.append(entity)
            entity_type_last = entity.get('type')
        return new_entities

    def disease_type(self, result_entity):
        """
        type_all 含有症状和疾病， 如果实体中包含病/症等，type划分为disease
        """
        if result_entity:
            type_all = result_entity['type_all']
            name = result_entity['entity_name']
            if ('disease' in type_all) and ('symptom' in type_all):
                if re.findall('[病癌症瘤炎疹癜冒压疸孕出喘节化裂肿石]$', name):
                    result_entity['type'] = 'disease'
                else:
                    result_entity['type'] = 'symptom'
        return result_entity

    def inspection_value_optimize(self, sentence, medical_entities):
        """
        属性：检查检验结果转化
        :param sentence: 输入句子
        :param medical_entities: 实体字典
        :return:  加入值转化后的字典
        """
        medical_entity_keys = list(medical_entities.keys())
        for keys in medical_entity_keys:
            entities = medical_entities[keys]
            en_type = entities.get('type')
            en_name = entities.get('entity_name')
            loc = entities.get('loc')
            if en_type in ['physical', 'examination']:
                # new_sentence = sentence[loc[1]:(loc[1]+10)]
                new_sentence = sentence[loc[0]:]
                if en_name in ['体温', '温度', 'T', 'T3']:
                    new_dict = ins_value_model.get_temperature_new(new_sentence)
                    if en_name == 'T3' and not new_dict:
                        new_dict = ins_value_model.get_value_num_new(en_name, en_type, new_sentence)

                else:
                    new_dict = ins_value_model.get_value_new(en_name, en_type, new_sentence)
                    if not new_dict:
                        new_dict = ins_value_model.get_value_num_new(en_name, en_type, new_sentence)
                # print(en_name, new_dict)
                if new_dict:
                    en_word = new_dict.get('entity_name')
                    # new_loc = [new_dict['loc'][0] + loc[1], new_dict['loc'][1] + loc[1]]
                    new_loc = [new_dict['loc'][0] + loc[0], new_dict['loc'][1] + loc[0]]
                    new_dict['loc'] = new_loc
                    key = '{0}\t{1}\t{2}'.format(str(en_word), str(new_loc[0]), str(new_loc[1]))
                    medical_entities[key] = new_dict

        return medical_entities


class EntityExtractBasic(OptimizeExtract):
    """
    医学实体抽取器（按照优先级）
    用于抽取文本中的医学实体以及ID
    """

    def __init__(self, priority_dict_order=None):
        super(EntityExtractBasic, self).__init__()
        # 中英文标点
        en_punctuation = set(string.punctuation)
        cn_punctuation = {',', '?', '、', '。', '“', '”', '《', '》', '！',
                          '，', '：', '；', '？', '（', '）', '【', '】'}
        self.punctuation = {p for p in en_punctuation | cn_punctuation}
        # 默认辞典的优先级
        dic_base_path = global_conf.dict_mmseg_path
        self.dict_mmseg = re.split('/', dic_base_path)[-2]
        if self.dict_mmseg == 'mmseg_kg':
            self.default_dict_order = [
                'core', 'std_department', 'hospital', 'hospital_department',
                'symptom_wy', 'disease', 'body_part', 'treatment', 'medicine',
                'area', 'doctor', 'examination_item', 'examination_result',
                'inspection_item', 'physical', 'hospital_brand',
                'hospital_grade', 'doctor_level', 'crowd', 'medical_word']
        else:
            self.default_dict_order = [
                'core', 'std_department', 'hospital', 'hospital_department',
                'symptom_wy', 'symptom_wy_synonym_extend',
                'disease', 'disease_all', 'body_part', 'treatment', 'medicine',
                'area', 'doctor', 'examination_item', 'examination_result',
                'inspection_item', 'physical', 'hospital_brand',
                'hospital_grade', 'doctor_level', 'crowd', 'medical_word']
        # 初始化优先级，如果用户未指定，则使用默认优先级
        print(self.dict_mmseg)
        if not priority_dict_order:
            self.priority_dict_order = self.default_dict_order
        else:
            self.priority_dict_order = self.dict_choose(priority_dict_order)
        # 对于优先级中的每一个辞典，依次构造 extractor
        self.extractors = {}
        for dict_type in self.priority_dict_order:
            self.extractors[str(dict_type)] = MMSeg(
                [dict_type], uuid_all=True, is_uuid=True, update_dict=False, is_all_word=True)
        # 加载 jieba
        jieba.initialize()

    def extract(self, sentence, priority_dict_list=None, entity_property=None, verbose=False):
        """
        抽取医学实体(按照按照优先级)
        :param verbose: 是否打印详细信息, default=False
        :param entity_property:
        :param priority_dict_list: 
        :param sentence: 待抽取的句子
        :return medical_entity dict
        """
        # Medical entities ranked with priority order
        if not priority_dict_list:
            priority_dict_list = []
        if not entity_property:
            entity_property = []
        sentence = re.sub('b超', 'B超', sentence)
        sentence = re.sub('(Ct|cT)', 'CT', sentence)
        priority_medical_entities = {}
        if 'age' in entity_property or 'sex' in entity_property:
            priority_dict_list.append('crowd')
        # print(sentence)
        ###多次遍
        # print(priority_dict_list)
        if priority_dict_list:
            if self.dict_mmseg == 'mmseg_kg':
                priority_dict_order = self.dict_choose_kg(priority_dict_list)
            else:
                priority_dict_order = self.dict_choose(priority_dict_list)
        else:
            priority_dict_order = self.default_dict_order

        for dict_type in priority_dict_order:

            extractor = self.extractors[dict_type]
            medical_entities = extractor.cut(sentence)

            for k, v in medical_entities.items():
                v = list(v)
                # find all sub string indexes
                # 特殊需要转义的字符,11个具有特殊意义的字符，在字典中的话，这里匹配不到需要做下变换
                k1 = k
                sp_cha = ['$', ')', '(', '*', '?', '{', '[', '+', '.', '|', '^']
                for i in sp_cha:
                    if i in k:
                        k1 = k1.replace(i, ('\\' + i))
                # print(k1)
                beg_indexes = [m.start() for m in re.finditer(k1, sentence)]
                for beg_index in beg_indexes:
                    end_index = beg_index + len(k) - 1
                    key = '{0}\t{1}\t{2}'.format(str(k), str(beg_index), str(end_index))
                    if key in priority_medical_entities:
                        priority_medical_entities[key]['type_all'].append(dict_type)
                        priority_medical_entities[key]['entity_id_all'].extend(v)
                    else:
                        priority_medical_entity = {
                            'entity_name': k, 'loc': (beg_index, end_index),
                            'entity_id': v[0], 'entity_id_all': v,
                            'type': dict_type, 'type_all': [dict_type]
                        }
                        priority_medical_entities[key] = priority_medical_entity

        if verbose:
            print('------------------------------------------')
            print('Detailed info of priority_medical_entities')
            for _, e in priority_medical_entities.items():
                for k, v in e.items():
                    print(k, v)
            print('------------------------------------------')

        return priority_medical_entities

    def filter(self, medical_entities, verbose=False):
        """
        :param verbose: 是否打印详细信息, default=False
        :param medical_entities: 待过滤的实体
        :return filter_medical_entities(dict) 过滤以后的实体dict
        """
        # filter_medical_entities 存储过滤之后到实体
        filter_entity_keys = []
        filter_medical_entities = OrderedDict()

        # 处理 medical_entities 为空的情况
        if not medical_entities:
            return filter_medical_entities

        medical_entities = OrderedDict(
            sorted(medical_entities.items(), key=lambda x: (x[1]['loc'][0], -x[1]['loc'][1])))
        medical_entity_keys = list(medical_entities.keys())
        i = 0
        j = i + 1
        while j < len(medical_entity_keys):
            current_entity_key = medical_entity_keys[i]
            next_entity_key = medical_entity_keys[j]
            current_end_index = medical_entities[current_entity_key]['loc'][1]
            next_beg_index = medical_entities[next_entity_key]['loc'][0]

            # 如果下一个实体开始的index < 当前实体结束的index, 则过滤掉；否则保留
            if next_beg_index <= current_end_index:
                j = j + 1
            else:
                filter_entity_keys.append(current_entity_key)
                i = j
                j = i + 1

        filter_entity_keys.append(medical_entity_keys[i])
        # 依据过滤之后的 filter_entity_key 重构 filter_medical_entities
        for entity_key in filter_entity_keys:
            filter_medical_entities[entity_key] = medical_entities[entity_key]

        if verbose:
            print('-------------------------------')
            print('Detailed info of filter_medical_entities:')
            for _, e in filter_medical_entities.items():
                for k, v in e.items():
                    print(k, v)
            print('-------------------------------')

        return filter_medical_entities

    def jieba_cut(self, sentence, medical_entities, verbose=False):
        """
        照句子顺序抽取实体
        Parameters:
            sentence-> 原句子
            filter_medical_entities-> 经过过滤以后的实体
            loc_on->是否开启loc字段，方便调试，默认为False
            verbose->是否打印详细信息, default=False
            返回值 -> seq_medical_entities() 按照语句顺序抽取的实体
        """
        order_medical_entities = OrderedDict(
            sorted(medical_entities.items(), key=lambda x: (x[1]['loc'][0])))

        order_entity_keys = list(order_medical_entities.keys())
        current_sentence = sentence

        for entity_key in order_entity_keys:
            if order_medical_entities[entity_key].get('entity_text'):
                e = order_medical_entities[entity_key].get('entity_text')
            else:
                e = order_medical_entities[entity_key]['entity_name']
            split_by_e = current_sentence.split(e, 1)
            # print(e, split_by_e)
            if len(split_by_e) >= 2:
                unknown_word = split_by_e[0]
                current_sentence = split_by_e[1]
            else:
                unknown_word = ''
                current_sentence = split_by_e[0]

            if unknown_word == '':
                continue
            tokens = jieba.tokenize(unknown_word)
            for token in tokens:
                order_medical_entity = {'entity_name': token[0],
                                         'type': 'normal'}
                if token[0] in self.punctuation:
                    order_medical_entity['type'] = 'punctuation'

                base = len(sentence) - len(current_sentence) - len(e) - len(unknown_word)
                beg_index = base + token[1]
                end_index = base + token[2] - 1
                order_medical_entity['loc'] = (beg_index, end_index)
                key = '{0}\t{1}\t{2}'.format(
                    str(order_medical_entity['entity_name']),
                    str(beg_index), str(end_index))
                order_medical_entities[key] = order_medical_entity

        # handle the last split exception
        # print current_sentence
        if current_sentence != '':
            unknown_word = current_sentence
            tokens = jieba.tokenize(unknown_word)
            for token in tokens:
                order_medical_entity = {'entity_name': token[0],
                                         'type': 'normal'}
                if token[0] in self.punctuation:
                    order_medical_entity['type'] = 'punctuation'

                base = len(sentence) - len(current_sentence)
                beg_index = base + token[1]
                end_index = base + token[2] - 1
                order_medical_entity['loc'] = (beg_index, end_index)
                key = '{0}\t{1}\t{2}'.format(str(order_medical_entity['entity_name']),
                                             str(beg_index), str(end_index))
                order_medical_entities[key] = order_medical_entity

        order_medical_entities = OrderedDict(
            sorted(order_medical_entities.items(), key=lambda x: (x[1]['loc'][0])))
        seq_medical_entities = order_medical_entities

        if verbose:
            print('----------------------------------------')
            for _, e in seq_medical_entities.items():
                for k, v in e.items():
                    print(k, v)
            print('----------------------------------------')
        return seq_medical_entities

    def concatenate(self, medical_entities, verbose=False):
        """
        对于 body_part+symptom 的模式统一识别为 symptom, ID 设置为 Not Defined
        Parameters:
            medical_entities-> 按语句顺序抽取的实体信息
            verbose->是否打印详细信息, default=False
            返回值 -> concatenate_medical_entities() body_part+symptom 统一识别为 symptom
        """
        key_list = list(medical_entities.keys())
        pos = 1
        while pos < len(key_list):
            prev_ = key_list[pos - 1]
            current_ = key_list[pos]
            prev_entity = medical_entities[prev_]['entity_name']
            prev_type = medical_entities[prev_]['type']
            current_entity = medical_entities[current_]['entity_name']
            current_type = medical_entities[current_]['type']
            ## 先判断 多组合词的情况，防止下面的部位和症状组合影响位置
            if (pos >= 2 and current_type in ['symptom_wy', 'symptom_wy_synonym_extend']
                    and len(current_entity) <= 2):
                prev2_ = key_list[pos - 2]
                prev2_seq = medical_entities.get(prev2_)
                if prev2_seq:
                    # prev_entity2 =  prev2_seq['entity_name']
                    prev_type2 = medical_entities[prev2_]['type']
                else:
                    prev_entity2, prev_type2 = '', ''
                if prev_type2 == 'body_part' and prev_entity in [
                    '有', '有点', '有些', '经常', '一点', '很', '也', '微',
                    '十分', '总是', '轻微', '剧烈', '一直', '长']:
                    if self._merge_entity_three(prev2_, prev_, current_, 'symptom',
                                                medical_entities):
                        # !!! very important !!!
                        pos = pos + 2

            if prev_type == 'body_part':
                # #对于模式：body_part + symptom 识别为 symptom
                if current_type in ['symptom_wy', 'symptom_wy_synonym_extend']:
                    if self._merge_entity(prev_, current_, 'symptom',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1
                elif current_entity in [
                    '增大', '增粗', '变粗', '变大', '疼', '痛', '扩张', '偏小',
                    '偏大', '超大', '有包', '长包', '臭', '减小', '变小',
                    '发软', '变硬', '发硬', '堵塞', '增生', '疼痛', '不适', '难受']:  ##部位发生变化类的词补充
                    if self._merge_entity(prev_, current_, 'symptom',
                                          medical_entities):
                        pos = pos + 1

                elif current_entity in ['双侧', '部', '单侧', '右侧', '左侧', '两边',
                                        '左边', '右边', '内侧', '外侧']:
                    if self._merge_entity(prev_, current_, 'body_part',
                                          medical_entities):
                        pos = pos + 1

                # 对于模式：body_part + std_department 识别为 std_department
                elif current_type == 'std_department' or current_entity == '科' or current_entity == '专科':
                    if self._merge_entity(prev_, current_, 'hospital_department',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1
                # 对于模式：body_part + 特殊疾病限定词 识别为 疾病
                elif current_entity in ['癌', '结节', '瘤', '肿瘤', '脱臼', '病', '疾病']:
                    if self._merge_entity(prev_, current_, 'disease',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1

                # 对于模式：body_part + 特殊检查限定词 识别为 检查
                elif current_entity in ['CT', 'cT', 'ct', 'B超', 'b超', '检查', 'Ct']:
                    if self._merge_entity(prev_, current_, 'examination',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1

            ### 地域和医院组合
            if prev_type == 'area':
                # 对于模式：body_part + symptom 识别为 symptom
                if current_type in ['hospital', 'hospital_brand']:
                    if self._merge_entity(prev_, current_, 'hospital',
                                          medical_entities):
                        pos = pos + 1
                elif current_entity == '医院':
                    if self._merge_entity(prev_, current_, 'hospital',
                                          medical_entities):
                        pos = pos + 1

            ## 疾病+药/疫苗 = 药物
            if prev_type in ['symptom_wy', 'symptom_wy_synonym_extend', 'disease', 'disease_all']:
                # 对于模式：疾病+药/疫苗识别为 药物
                if current_entity in ['药', '药物', '疫苗']:
                    if self._merge_entity(prev_, current_, 'medicine',
                                          medical_entities):
                        pos = pos + 1

            ## 方位词/部位 + 疾病和症状 = 疾病和症状
            if current_type in ['symptom_wy', 'symptom_wy_synonym_extend', 'disease', 'disease_all']:
                current_type = re.split('_', current_type)[0]
                if prev_entity in ['左', '右', '双侧', '单侧', '右侧', '左侧']:
                    if self._merge_entity(prev_, current_, current_type,
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1

            ## 多个部位连续时组合为一个部位
            if current_type == 'body_part':
                # 对于模式：body_part + body_part 识别为 body_part
                if prev_type == 'body_part' or prev_entity in [
                    '左', '右', '双侧', '单侧', '右侧', '左侧', '两边', '左边', '右边']:
                    if self._merge_entity(prev_, current_, 'body_part',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1
                # 对于模式：特定词 + body_part 识别为 检查
                elif prev_entity in ['检查', '查']:
                    if self._merge_entity(prev_, current_, 'examination',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1
            # 如果手术前是治疗则统一为治疗
            if current_entity == '手术':
                if prev_type == 'treatment':
                    if self._merge_entity(prev_, current_, 'treatment',
                                          medical_entities):
                        # !!! very important !!!
                        pos = pos + 1

            pos = pos + 1

        concatenate_medical_entities = OrderedDict(
            sorted(medical_entities.items(), key=lambda x: (x[1]['loc'][0])))

        if verbose:
            print('----------------------------------------')
            for _, e in concatenate_medical_entities.items():
                for k, v in e.items():
                    print(k, v)

        return concatenate_medical_entities

    def _merge_entity(self, prev, current, entity_type, entities):
        """
        合并相邻实体为新的类型.
        参数:
        prev->上一个实体的key.
        current->当前实体的key.
        entity_type->新实体类型.
        entitys->实体字典集.
        返回值->合并成功则为true,合并失败则false.
        """
        prev_entity = entities[prev]['entity_name']
        prev_beg_index = int(entities[prev]['loc'][0])
        prev_end_index = int(entities[prev]['loc'][1])
        current_entity = entities[current]['entity_name']
        current_beg_index = int(entities[current]['loc'][0])
        current_end_index = int(entities[current]['loc'][1])
        if int(current_beg_index) == int(prev_end_index) + 1:
            new_entity = {'entity_name': str(prev_entity + current_entity),
                          'type': entity_type, 'entity_id': '',
                          'entity_id_all': [],
                          'loc': (prev_beg_index, current_end_index)}
            new_key = '{0}\t{1}\t{2}'.format(
                new_entity['entity_name'],
                str(prev_beg_index), str(current_end_index))
            entities[new_key] = new_entity
            del entities[prev]
            del entities[current]
            return True
        return False

    ### 合并三个词
    def _merge_entity_three(self, prev2, prev, current, entity_type, entities):
        """
        合并相邻实体为新的类型.
        参数:
        prev2->上面第2个实体的key
        prev->上一个实体的key.
        current->当前实体的key.
        entity_type->新实体类型.
        entities->实体字典集.
        返回值->合并成功则为true,合并失败则false.
        """
        prev_entity2 = entities[prev2]['entity_name']
        prev_beg_index2 = int(entities[prev2]['loc'][0])
        prev_end_index2 = int(entities[prev2]['loc'][1])
        prev_entity = entities[prev]['entity_name']
        prev_beg_index = int(entities[prev]['loc'][0])
        prev_end_index = int(entities[prev]['loc'][1])
        current_entity = entities[current]['entity_name']
        current_beg_index = int(entities[current]['loc'][0])
        current_end_index = int(entities[current]['loc'][1])

        if (int(current_beg_index) == int(prev_end_index) + 1
                and int(prev_beg_index) == int(prev_end_index2) + 1):
            new_entity = {
                'entity_name': str(prev_entity2) + str(prev_entity) + str(
                    current_entity), 'type': entity_type, 'entity_id': '',
                'entity_id_all': [],
                'loc': (prev_beg_index2, current_end_index)}
            new_key = '{0}\t{1}\t{2}'.format(
                new_entity['entity_name'],
                str(prev_beg_index2), str(current_end_index))
            entities[new_key] = new_entity
            del entities[prev2]
            del entities[prev]
            del entities[current]
            return True
        return False

    def dict_tran_list(self, medical_entities):
        """
        将OrderedDict 转为 字典列表[{},{},{}]
        (后续优化都建立在字典列表上，因此这里转化掉，方便后续添加优化开关)
        :param medical_entities: 有序字典
        :return: 字典列表[{},{},{},{}]
        """
        entities = []
        for name, entity in medical_entities.items():
            entities.append(entity)
        return entities

    def result_optimize(self, medical_entities, loc_on=True, verbose=False):
        """
        按照接口需要的形式重新组装实体
        Parameters:
            seq_medical_entities-> 按语句顺序抽取的实体信息
            loc_on->是否开启loc字段，方便调试，默认为False
            verbose->是否打印详细信息, default=False
            返回值 -> result_medical_entities() 按照接口需要的实体
        """
        result_medical_entities = []
        dict_type_dict = {
            'core': 'normal', 'symptom_wy_synonym_extend': 'symptom',
            'symptom_wy': 'symptom', 'disease_all': 'disease'
        }

        for medical_entity in medical_entities:
            result_entity = {'entity_name': medical_entity['entity_name'],
                             'type': medical_entity['type']}
            if medical_entity.get('entity_text'):
                result_entity['entity_text'] = medical_entity['entity_text']
            if medical_entity.get('sub_type'):
                result_entity['sub_type'] = medical_entity['sub_type']
            if medical_entity.get('std_department'):
                result_entity['std_department'] = medical_entity['std_department']
                result_entity['std_id'] = medical_entity['std_id']
            if medical_entity.get('property'):
                result_entity['property'] = medical_entity['property']
            if result_entity['type'] in dict_type_dict:
                result_entity['type'] = dict_type_dict[result_entity['type']]
            result_entity['type_all'] = set()
            for t_type in medical_entity.get('type_all', [result_entity['type']]):
                if t_type in dict_type_dict:
                    result_entity['type_all'].add(dict_type_dict[t_type])
                else:
                    result_entity['type_all'].add(t_type)
            result_entity['type_all'] = list(result_entity['type_all'])
            result_entity = self.disease_type(result_entity)
            if ('entity_id' in medical_entity) and (medical_entity['type'] != 'core'):
                result_entity['entity_id'] = medical_entity['entity_id']
                result_entity['entity_id_all'] = list(set(
                    medical_entity['entity_id_all']))

            if loc_on:
                result_entity['loc'] = medical_entity['loc']

            result_medical_entities.append(result_entity)

        if verbose:
            print('----------------------------------------')
            for e in result_medical_entities:
                for k, v in e.items():
                    print(k, v)
            print('----------------------------------------')
        return result_medical_entities

    def check(self, sentence, medical_entities):
        if sentence == '':
            if not medical_entities:
                return True
        # print sentence
        beg_index = medical_entities[0]['loc'][0]
        pre_beg_index = beg_index
        pre_end_index = medical_entities[0]['loc'][1]
        current_beg_index = pre_beg_index
        current_end_index = pre_end_index
        # print bool( beg_index != 0 )
        if beg_index != 0:
            return False

        for i in range(1, len(medical_entities)):
            current_beg_index = medical_entities[i]['loc'][0]
            current_end_index = medical_entities[i]['loc'][1]

            if current_beg_index != pre_end_index + 1:
                return False
            else:
                pre_beg_index = current_beg_index
                pre_end_index = current_end_index

        # print current_end_index + 1, len(sentence)
        if current_end_index + 1 == len(sentence):
            return True
        else:
            return False


class Entity_Extract(EntityExtractBasic):

    def __init__(self):
        super(Entity_Extract, self).__init__()

    def result(self, content, type_list, entity_property, is_stop_word):
        medical_entities = self.extract(
            content, priority_dict_list=type_list, entity_property=entity_property, verbose=False)
        # print('medical_entities' ,medical_entities)
        medical_entities = self.extract_optimize(content, medical_entities)
        # print('extract_optimize' ,medical_entities)
        if 'age' in entity_property:
            medical_entities = self.age_extract(content, medical_entities)
        ## 添加检查值分类
        if 'value' in entity_property:
            medical_entities = self.inspection_value_optimize(content, medical_entities)
        filter_entities = self.filter(medical_entities, verbose=False)
        # print(filter_entities)
        ## 添加检查值分类
        # filter_entities = self.inspection_value_optimize(content, filter_entities)

        seq_entities = self.jieba_cut(content, filter_entities, verbose=False)
        concatenate_entities = self.concatenate(seq_entities, verbose=False)
        entity_list = self.dict_tran_list(concatenate_entities)
        if 'area' in type_list or not type_list:
            area_extractor = self.extractors['area']
            entity_list = self.area_optimize(entity_list, extractor=area_extractor)
        # 医院优化
        entity_list = self.hospital_optimize(entity_list)
        ## 科室标注化
        entity_list = self.department_optimize(entity_list)
        ## 性别年龄
        if entity_property:
            entity_list = self.age_sex_optimize(entity_property, entity_list)
        entity_list = self.redistrict(entity_list)
        # print('---------')
        # print('entity_list', entity_list)
        # print('----------')
        if is_stop_word == '1':
            entity_list = self.stop_word_filter(entity_list)
        result_entities = self.result_optimize(entity_list, loc_on=False, verbose=False)
        return result_entities

    def result_filter(self, content, type_list=None, property_list=None, is_stop_word=0):
        """
        锁定type_list的范围，将无关的实体类别置换为normal（因为有组合词，引入的实体类别比给定的多，因此需要剔除）
        :param property_list:
        :param content: 文本
        :param type_list: 实体类别列表
        :param is_stop_word: 是否启用停词
        :return: 实体识别结果
        """
        type_all = ['core', 'department', 'hospital', 'symptom', 'disease',
                    'body_part', 'treatment', 'medicine', 'area', 'doctor',
                    'inspection_item', 'examination_item', 'examination_result'
                    'physical', 'hospital_grade', 'doctor_level',
                    'medical_word', 'crowd']
        type_list = [x for x in type_list if x in type_all]
        # print(type_list)
        result_entities = self.result(
            content, type_list, entity_property=property_list, is_stop_word=is_stop_word)
        if 'department' in type_list:
            type_list.extend(['std_department', 'hospital_department'])
        new_result_entities = []
        if type_list:
            if result_entities:
                for dict_entity in result_entities:
                    type_entity = dict_entity.get('type')
                    new_dict = {}
                    if type_entity not in type_list:
                        new_dict['entity_name'] = dict_entity.get('entity_name')
                        new_dict['type'] = 'normal'
                        new_dict['type_all'] = ['normal']
                        new_result_entities.append(new_dict)
                    else:
                        new_result_entities.append(dict_entity)
        else:
            new_result_entities = result_entities
        return new_result_entities


if __name__ == '__main__':
    # cut_content = '眼红肿，左眼白内障，右臂红肿，小臂骨折，有手臂专科么？眼科，还是脸科'
    # cut_content = '20余天前，有助于怀孕，有助于关节炎，有关心脏病，有关关节炎，有关怀孕，和梅毒，不过敏'
    # cut_content = '乳腺癌疫苗，高血压药物，新生儿舌头下面有一根筋挂什么科？,腋下有包'
    # cut_content = '碘[125I]血管紧张素I放射免疫分， 细菌（高倍）, 痰细菌培养+药敏,十二指肠先天性闭锁、缺如和狭窄'
    # cut_content = '贫血，男性，27岁, T37.5℃，游离T3:10.20Pmol/L,T3 42.5,白细胞：37mol/l，红细胞48.5,'
    cut_content_0 = '幼儿园体检建议立即复查，请问很严重吗？'
    type_list_0 = []
    # type_list = ['22']
    property_list_0 = []
    ee = Entity_Extract()
    # result_entities = entity_extractor.result(cut_content,type_list)
    # print(Encode(result_entities))
    nre = ee.result_filter(cut_content_0, type_list_0, property_list_0)
    print(nre)
