#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mednlp.dialog.generator.search_generator import SearchGenerator
from ailib.utils.exception import AIServiceException
from mednlp.dialog.configuration import Constant as constant


class BaikeSearchGenerator(SearchGenerator):
    name = 'baike_search'
    input_field = ['q', 'rows']

    field_trans = {
        'word_id': 'word_id',
        'name': 'word_name',
        'name_highlight': 'word_name_highlight',
        'introduction': 'word_introduction',
        'type': 'word_type',
        constant.GENERATOR_CARD_FLAG: constant.GENERATOR_CARD_FLAG
    }
    output_field = ['word_id', 'word_name', 'word_name_highlight', 'word_introduction', 'word_type',
                    constant.GENERATOR_CARD_FLAG, constant.GENERATOR_EXTEND_SEARCH_PARAMS]
    # 疾病 > 症状 > 药品 > 科室 > 治疗
    word_types = ['disease', 'symptom', 'medicine', 'std_department',
                  'hospital_department', 'treatment']

    def __init__(self, cfg_path, **kwargs):
        super(BaikeSearchGenerator, self).__init__(cfg_path, **kwargs)

    def generate(self, input_obj, **kwargs):
        result = {}
        param = {
            'state': '2',
            'match_type': '1',
            'highlight': '1',
            'fl': 'introduction,word_id,name,name_highlight,type',
            'start': '0',
            'rows': '1'
        }
        for field in self.input_field:
            value = input_obj.get(field)
            if not value:
                continue
            param[field] = value
        center_word = self.get_center_word(input_obj.get('q'))
        content = result.setdefault('content', [])
        if center_word:
            param['q'] = center_word
            res = self.sc.query(param, 'baike_word', method='get')
            if not res or res['code'] != 0:
                message = 'dept_search error'
                if not res:
                    message += ' with no res'
                else:
                    message += res.get('message')
                raise AIServiceException(message)
            baike_words = res.get('data')
            fl = input_obj.get('fl', self.output_field)
            for temp in baike_words:
                content_item = {}
                for field, value in temp.items():
                    if field not in fl and self.field_trans.get(field) not in fl:
                        continue
                    if field in self.field_trans:
                        content_item[self.field_trans[field]] = value
                    else:
                        content_item[field] = value
                if constant.GENERATOR_CARD_FLAG in fl:
                    content_item[constant.GENERATOR_CARD_FLAG] = constant.GENERATOR_CARD_FLAG_BAIKE
                content.append(content_item)
            if constant.GENERATOR_EXTEND_SEARCH_PARAMS in fl:
                result[constant.GENERATOR_EXTEND_SEARCH_PARAMS] = {'q': param.get('q', '')}
                # result.setdefault(constant.GENERATOR_EXTEND, {})[constant.GENERATOR_EXTEND_SEARCH_PARAMS] = {
                #     'q': param.get('q', '')}
        return result

    def get_center_word(self, query):
        result = None
        if not query:
            return result
        word_dict = {
            'disease': [],
            'symptom': [],
            'medicine': [],
            'std_department': [],
            'hospital_department': [],
            'treatment': []
        }
        # 得到百科中心词   疾病 > 症状 > 药品 > 科室 > 治疗
        # 如果有q, 进行实体识别, 获取第一个词
        entity_result = constant.ai_server.query({'q': query}, 'entity_extract')
        if entity_result and entity_result.get('data'):
            for entity_obj in entity_result.get('data'):
                if entity_obj['type'] in self.word_types:
                    word_dict[entity_obj['type']].append(entity_obj['entity_name'])
            for word_type_temp in self.word_types:
                if word_dict[word_type_temp]:
                    result = word_dict[word_type_temp][0]
                    break
        return result

if __name__ == '__main__':
    import global_conf
    import json

    generator = BaikeSearchGenerator(global_conf.cfg_path)
    input_obj = {
        "q": "头痛",
        # "fl": ['word_type', 'word_name',
        #        'word_id'
        #     , constant.GENERATOR_EXTEND_SEARCH_PARAMS
        #        ]
    }
    result = generator.generate(input_obj=input_obj)
    print(json.dumps(result, indent=True))