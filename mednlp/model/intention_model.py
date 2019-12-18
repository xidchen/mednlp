#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
intention_model.py -- the service of intention_service

Author: renyx <renyx@guahao.com>
Create on 2018-09-07 Friday
"""


import sys
import numpy as np
import global_conf
from ailib.utils.log import GLLog
from pypinyin import pinyin, Style, lazy_pinyin
from keras.models import model_from_json
from mednlp.utils.utils import unicode2str
from ailib.model.base_model import BaseModel
from mednlp.text.vector import Intent2Vector
from keras.preprocessing.sequence import pad_sequences
from mednlp.utils.utils import print_logger, unicode_python_2_3
import jieba.posseg as psg
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser
from mednlp.dao.ai_service_dao import ai_services
from onnet.arch.models.tf_serving.model import TFServeModel
from mednlp.utils.utils import read_config_info


class IntentionModel(BaseModel):

    def initialize(self, model_version=0, **kwargs):
        # 初始化对模型,词典
        self.logger = kwargs.get('logger')
        self.model_version = model_version
        self.load_model()
        self.intent2vec = Intent2Vector(dict_path=global_conf.dept_classify_char_dict_path)

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        self.model = model

    def predict(self, text, num=100, **kwargs):
        words_list = self.intent2vec.get_vector(text)
        # print_logger(self.logger, 'words_list: ')
        if not words_list:
            print_logger('IntentionModel%s无words_list' % text, self.logger, debug=1)
            return False, None
        predict_x = pad_sequences([words_list], maxlen=num)
        intent_value = self.model.predict(predict_x)
        return True, intent_value[0]

    def direct_predict(self, words_list, num=100):
        predict_x = pad_sequences([words_list], maxlen=num)
        intent_value = self.model.predict(predict_x)
        return intent_value[0]


class IntentionPinyinModel(BaseModel):

    def initialize(self, model_version=0, **kwargs):
        # 初始化对模型,词典
        self.logger = kwargs.get('logger')
        self.model_version = model_version
        self.load_model()
        self.intent2vec = Intent2Vector(dict_path=global_conf.intention_classify_pinyin_dict_path)

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        self.model = model

    def predict(self, text, num=100, **kwargs):
        text_temp = []
        if text:
            result_temp = pinyin(unicode_python_2_3(text), style=Style.NORMAL, errors='ignore')
            text_temp = [pinyin_temp[0] for pinyin_temp in result_temp]
        words_list = self.intent2vec.get_vector(text_temp)
        # print_logger(self.logger, 'words_list: ')
        if not words_list:
            print_logger('IntentionPinyinModel%s无words_list' % text, self.logger, debug=1)
            return False, None
        predict_x = pad_sequences([words_list], maxlen=num)
        intent_value = self.model.predict(predict_x)
        return True, intent_value[0]

    def direct_predict(self, words_list, num=100):
        predict_x = pad_sequences([words_list], maxlen=num)
        intent_value = self.model.predict(predict_x)
        return intent_value[0]


class IntentionPosModel(BaseModel):

    def initialize(self, model_version=0, **kwargs):
        # 初始化对模型,词典
        self.logger = kwargs.get('logger')
        self.model_version = model_version
        self.load_model()
        self.intent2vec = Intent2Vector(dict_path=global_conf.intention_classify_pos_char_dict_path)

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        self.model = model

    def predict(self, text, num=100, **kwargs):
        text_temp = []
        if text:
            try:
                params = {'q': unicode2str(text)}
                data, _ = ai_services(params, 'entity_extract', 'post')
                if data:
                    text_temp = self.filter_pos(data)
            except:
                print_logger('[%s]请求实体异常' % text, self.logger, debug=1)
        words_list = self.intent2vec.get_vector(text_temp)
        # print_logger(self.logger, 'words_list: ')
        if not words_list:
            print_logger('IntentionPosModel%s无words_list' % text, self.logger, debug=1)
            return False, None
        predict_x = pad_sequences([words_list], maxlen=num)
        intent_value = self.model.predict(predict_x)
        return True, intent_value[0]

    def direct_predict(self, words_list, num=100):
        predict_x = pad_sequences([words_list], maxlen=num)
        intent_value = self.model.predict(predict_x)
        return intent_value[0]

    def filter_pos(self, data):
        # 过滤转换实体
        transform_type = {
            'symptom': 'symptom',
            'disease': 'disease',
            'std_department': 'std_department',
            'hospital_department': 'hospital_department',
            'hospital': 'hospital',
            'body_part': 'body_part',
            'treatment': 'treatment',
            'medicine': 'medicine',
            'area': 'area',
            'doctor': 'doctor',
            'hospital_grade': 'hospital_grade',
            'doctor_level': 'doctor_level',
            'physical': 'physical',
            'examination': 'examination',
            'medical_word': 'medical_word'
        }
        # 过滤实体
        result = []
        for index, data_temp in enumerate(data):
            type = data_temp['type']
            entity_name = data_temp['entity_name']
            # type in transform_type.keys() and ( len =0 or ( len >=1 and entity_name not in result[-1] )
            # if type in transform_type.keys() and entity_name not in result[-1]:
            if len(result) >= 1 and entity_name in data[index - 1]['entity_name'] and type == 'area':
                continue
            if type in transform_type.keys():
                # if type in transform_type.keys() and ( len(result) ==0 or (len(result) >= 1 and entity_name not in result[-1]) ):
                entity_name = transform_type[type]
                result.append(entity_name)
            else:
                result.extend(entity_name)
        return result


class IntentionUnionModel(BaseModel):

    def initialize(self, model_version=7, **kwargs):
        # 初始化对模型,词典
        self.logger = kwargs.get('logger')
        self.model_version = model_version
        self.char_dic = Intent2Vector(dict_path=global_conf.dept_classify_char_dict_path)
        self.pinyin_dic = Intent2Vector(dict_path=global_conf.intention_classify_pinyin_dict_path)
        self.pos_dic = Intent2Vector(dict_path=global_conf.intention_classify_pos_char_dict_path)
        tf_serving_config = read_config_info(sections=['TFServing'])
        serving_ip = tf_serving_config['TFServing']['IP']
        serving_port = tf_serving_config['TFServing']['PORT']
        part_url = tf_serving_config['TFServing']['BASE_URL']
        model_version_url = '/intention_union/versions/' + str(self.model_version)
        model_url = 'http://' + serving_ip + ':' + serving_port + '/' + part_url + model_version_url
        self.model = TFServeModel(model_url)

    def load_model(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        model.load_weights(model_weight, by_name=True)
        self.model = model

    def entity_extra(self, text, **kwargs):
        text_temp = []
        if text:
            try:
                params = {'q': text}
                data, _ = ai_services(params, 'entity_extract', 'post')
                if data:
                    text_temp = self.filter_pos(data)
            except:
                print_logger('[%s]请求实体异常' % text, self.logger, debug=1)
        return text_temp

    def get_union_vector(self, text):
        char_vec, pinyin_vec, pos_vec = [], [], []
        text_list = self.entity_extra(text)
        if not text_list:
            return char_vec, pinyin_vec, pos_vec
        for (entity_name, type) in text_list:
            for word in entity_name:
                pinyin_result = lazy_pinyin(word, style=Style.NORMAL, errors='ignore')
                if pinyin_result:
                    pinyin_result = pinyin_result[0]
                else:
                    pinyin_result = '<PAD>'
                char_vec.append(self.char_dic.get_word_vector(word))
                pinyin_vec.append(self.pinyin_dic.get_word_vector(pinyin_result))
                pos_vec.append(self.pos_dic.get_word_vector(type))
        return char_vec, pinyin_vec, pos_vec

    def filter_pos(self, data):
        # 过滤转换实体
        transform_type = {
            'symptom': 'symptom',
            'disease': 'disease',
            'std_department': 'std_department',
            'hospital_department': 'hospital_department',
            'hospital': 'hospital',
            'body_part': 'body_part',
            'treatment': 'treatment',
            'medicine': 'medicine',
            'area': 'area',
            'doctor': 'doctor',
            'hospital_grade': 'hospital_grade',
            'doctor_level': 'doctor_level',
            'physical': 'physical',
            'examination': 'examination',
            'medical_word': 'medical_word'
        }
        # 过滤实体
        result = []
        for index, data_temp in enumerate(data):
            type = data_temp['type']
            entity_name = data_temp['entity_name']
            if len(result) >= 1 and entity_name in data[index - 1]['entity_name'] and type == 'area':
                continue
            if type in transform_type.keys():
                result.append((entity_name, transform_type[type]))
            else:
                # 非医学实体词都拆分成单字 [(赛,赛), (车,车)]
                normal_list = [(temp, temp) for temp in entity_name]
                result.extend(normal_list)
        return result

    def predict(self, text, num=100, **kwargs):
        # 获取char_list, pinyin_list, y_list
        char_vec, pinyin_vec, pos_vec = self.get_union_vector(text)
        if not char_vec:
            print_logger('IntentionUnionModel%s无words_list' % text, self.logger, debug=1)
            return False, None
        char_vec = pad_sequences([char_vec], maxlen=num)
        pinyin_vec = pad_sequences([pinyin_vec], maxlen=num)
        pos_vec = pad_sequences([pos_vec], maxlen=num)
        intent_value = self.model.predict({'char_x:0': char_vec, 'pinyin_x:0': pinyin_vec, 'pos_x:0': pos_vec})
        return True, intent_value[0]


if __name__ == '__main__':
    logger = GLLog('intention_service_input_output', level='info', log_dir=global_conf.log_dir).getLogger()
    # intent = IntentionModel(cfg_path=global_conf.cfg_path, model_section='INTENTION_CLASSIFY_MODEL', logger=logger)
    # intent_pinyin = IntentionPinyinModel(cfg_path=global_conf.cfg_path,
    #                                      model_section='INTENTION_CLASSIFY_PINYIN_MODEL', logger=logger)
    # intent_pos = IntentionPosModel(cfg_path=global_conf.cfg_path, model_version=2,
    #                                      model_section='INTENTION_CLASSIFY_POS_MODEL', logger=logger)
    # word_pos_model = IntentionWordPosModel(cfg_path=global_conf.cfg_path, model_version=2,
    #                                        model_section='INTENTION_CLASSIFY_WORD_POS_MODEL', logger=logger)
    intent_union = IntentionUnionModel(cfg_path=global_conf.cfg_path, model_version=7,
                                        model_section='INTENTION_CLASSIFY_UNION_MODEL', logger=logger)
    aa = '宁波的赛车宁波市眼科医院怎样'
    # result = intent.predict(aa)
    # result = intent_pinyin.predict(aa)
    is_use_pos, result = intent_union.predict(aa)
    # is_use_pos, result = word_pos_model.predict(aa)
    print(is_use_pos)
    print(result)
    print(np.argmax(result))
    print(np.max(result))
