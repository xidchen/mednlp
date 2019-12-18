#!/usr/bin/env python
# encoding=utf-8

import xlrd
import xlwt
from mednlp.text.vector import Intent2Vector
import global_conf
# from mednlp.model.intention_model import IntentionModel, IntentionPinyinModel
from mednlp.model.intention_model import IntentionModel, IntentionPinyinModel,\
    IntentionPosModel, IntentionUnionModel
from ailib.utils.log import GLLog
import numpy as np
from mednlp.model.intention import IntentionStrategy
import mednlp.dialog.dialog_constant as constant
from mednlp.utils.utils import unicode2str
import requests
import json
import time
from mednlp.utils.utils import print_time


# 总的字典表(模型)
all_intent_dict = {
    '号源是否更新': ('haoyuanRefresh', 0, 0),                # 2
    '有没有号': ('register', 1, 0),                           # 0
    '医生最近号源时间': ('recentHaoyuanTime', 2, 0),       # 24
    '选医生-限定词': ('doctor', 3, 1),                       # 52
    '医生如何': ('doctorQuality', 4, 1),                    # 0
    '该医院是否有该科室': ('hospitalDepartment', 5, 2),     # 0
    '医院如何': ('hospitalQuality', 6, 2),                    # 1
    '选医院-限定词': ('hospital', 7, 2),                      #  238
    '选科室下的细分科室': ('departmentSubset', 8, 3),       # 0
    '科室二选一': ('departmentAmong', 9, 3),                # 0
    '选科室-限定词': ('department', 10, 3),                  # 689
    '是否这个科室': ('departmentConfirm', 11, 3),            # 2
    '附近的医院': ('hospitalNearby', 12, 2),                   # 0
    '医院排序': ('hospitalRank', 13, 2),                       # 0
    '意图不明确': ('other', 14, 4),
    '其他other': ('other', 14, 4),
    '内容': ('content', 15, 5),
    '客服': ('customerService', 16, 4)
}

intent_dict = {eng_word: num_second_intent for cn_word, (
    eng_word, num_second_intent, num_first_intent) in all_intent_dict.items()}

num2eng_dict = {num_second_intent: eng_word for cn_word, (
    eng_word, num_second_intent, num_first_intent) in all_intent_dict.items()}

# other_include_intent = ['keyword', 'corpusGreeting', 'guide', 'greeting', 'customerService', 'content']
other_include_intent = ['corpusGreeting', 'guide', 'greeting']


# 服务
service_all_intent_dict = {
    '号源是否更新': ('haoyuanRefresh', 0, 0),                # 2
    '有没有号': ('register', 1, 0),                           # 0
    '医生最近号源时间': ('recentHaoyuanTime', 2, 0),       # 24
    '选医生-限定词': ('doctor', 3, 1),                       # 52
    '医生如何': ('doctorQuality', 4, 1),                    # 0
    '该医院是否有该科室': ('hospitalDepartment', 5, 2),     # 0
    '医院如何': ('hospitalQuality', 6, 2),                    # 1
    '选医院-限定词': ('hospital', 7, 2),                      #  238
    '选科室下的细分科室': ('departmentSubset', 8, 3),       # 0
    '科室二选一': ('departmentAmong', 9, 3),                # 0
    '选科室-限定词': ('department', 10, 3),                  # 689
    '是否这个科室': ('departmentConfirm', 11, 3),            # 2
    '附近的医院': ('hospitalNearby', 12, 2),                   # 0
    '医院排序': ('hospitalRank', 13, 2),                       # 0
    '其他other': ('other', 14, 4),
    '内容': ('content', 15, 5),
    '自诊': ('auto_diagnose', 16, 6),
    '关键词': ('keyword', 17, 7),
    '客服': ('customerService', 18, 8)
}

service_intent_dict = {eng_word: num_second_intent for cn_word, (
    eng_word, num_second_intent, num_first_intent) in service_all_intent_dict.items()}

service_num2eng_dict = {num_second_intent: eng_word for cn_word, (
    eng_word, num_second_intent, num_first_intent) in service_all_intent_dict.items()}

# vector
lstm_char_vec = Intent2Vector(dict_path=global_conf.dict_path + 'dept_classify_char_vocab.dic')
lstm_pinyin_vec = Intent2Vector(dict_path=global_conf.dict_path + 'intention_pinyin_vocab.dic')
lstm_pos_char_vec = Intent2Vector(dict_path=global_conf.dict_path + 'intention_char_pos_vocab.dic')

logger = GLLog('intention_service_input_output', level='info', log_dir=global_conf.log_dir).getLogger()

# intention_w = None
intention_w = IntentionStrategy(version=7)

def getIntention():
    return intention_w


# 获取测试数据
def get_train_test_data(r_path='train_test_dialog_finally.xlsx', filter_func=None, final_func=None, **kwargs):
    data = xlrd.open_workbook(r_path)
    sheet_index = int(kwargs.get('sheet_index', 1))
    table = data.sheets()[sheet_index]  # 获取test数据
    intent_dict_temp = intent_dict
    all_intent_dict_temp = all_intent_dict
    # is_service(是否服务) = 1, intent_dict 换成
    is_service = int(kwargs.get('is_service', 0))
    if is_service:
        intent_dict_temp = service_intent_dict
        all_intent_dict_temp =  service_all_intent_dict
    # 行数
    rows = table.nrows
    # 列数
    cols = table.ncols
    print('rows: ', rows)
    print('cols: ', cols)
    result = {num_second_intent: {'X': []} for cn_word, (
        eng_word, num_second_intent, num_first_intent) in all_intent_dict_temp.items()}
    none_count = 0
    for row_num in range(1, rows):
        row_data = table.row_values(row_num)
        x = row_data[0].strip().replace(' ', '')
        y = row_data[1].strip()
        y_num = intent_dict_temp.get(y)
        if y_num is None:
            # 排除掉非模型的意图
            print(x)
            none_count += 1
            continue
        if filter_func:
            deal_data, is_used = filter_func(x)
            if is_used:
                result[y_num]['X'].append(x)
                result[y_num].setdefault('deal_X', []).append(deal_data)
        else:
            # 无filter表示直接存储数据
            # try:
            result[y_num]['X'].append(x)
            # except:
            #     pass
    if final_func:
        result = final_func(result)
    # 总数
    print(sum([len(value_temp['X']) for key, value_temp in result.items()]))
    print('get_train_test_data none_count:%s' % none_count)
    return result


# def filter_char_model(x):
#     # True：表示利用此数据
#     result = lstm_char_vec.get_vector(x)
#     if result:
#         return result, True
#     return None, False


# def filter_pinyin_model(x):
#     # True：表示利用此数据
#     result = lstm_pinyin_vec.get_vector(x)
#     if result:
#         return result, True
#     return None, False

def get_lxsx_write(f=None):
    if not f:
        f = xlwt.Workbook()
    style0 = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = '宋体'
    font.height = 0x00FF
    style0.font = font
    # sheet0 = f.add_sheet(sheet_name, cell_overwrite_ok=True)
    return f, style0


def print_test_xlsx(data, w_path):
    lxsx_writer, style = get_lxsx_write()
    sheet = lxsx_writer.add_sheet('result', cell_overwrite_ok=True)
    sheet.write(0, 0, 'query', style)
    sheet.write(0, 1, '标注label', style)
    sheet.write(0, 2, '模型label', style)
    sheet.write(0, 3, '是否一致(0[不一致], 1[一致])', style)
    index_test = 1
    for key_label, result_dict in data.items():
        X = result_dict.get('X', [])
        Y = result_dict.get('Y', [])
        Y_compare = result_dict.get('Y_compare', [])
        for x_index, x_temp in enumerate(X):
            sheet.write(index_test, 0, x_temp, style)
            sheet.write(index_test, 1, key_label, style)
            sheet.write(index_test, 2, Y[x_index], style)
            if Y_compare[x_index]:
                sheet.write(index_test, 3, 1, style)
            else:
                sheet.write(index_test, 3, 0, style)
            index_test += 1
    lxsx_writer.save(w_path)
    print('save successful')


def test_char_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
    print('test_char_model:')
    raw_data = get_train_test_data(r_path=r_path, **kwargs)
    char_model = IntentionModel(cfg_path=global_conf.cfg_path,
                                model_section='INTENTION_CLASSIFY_MODEL', logger=logger, **kwargs)
    # label, {X:[], deal_X:[]}
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            is_user_char, y_array = char_model.predict(x_temp)
            if not is_user_char:
                print('index:%s, query:%s' % (index, x_temp))
            y = int(np.argmax(y_array))
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
        classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
        raw_data[label]['acc'] = classify_acc
        print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
            label, num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
    Y_all = sum([len(data_dict['Y']) for _, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict['Y_compare']) for _, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    print('Y_compare_all: %s' % Y_compare_all)
    print('Y_all: %s' % Y_all)
    print('acc_all: %s' % acc)
    if kwargs.get('w_path'):
        print_test_xlsx(raw_data, w_path=kwargs['w_path'])
        print('char print_test_xlsx successful!!!')
    return raw_data


def test_union_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
    print('test_union_model:')
    raw_data = get_train_test_data(r_path=r_path, **kwargs)
    union_model = IntentionUnionModel(cfg_path=global_conf.cfg_path,
                                model_section='INTENTION_CLASSIFY_UNION_MODEL', logger=logger, **kwargs)
    # label, {X:[], deal_X:[]}
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            is_user_char, y_array = union_model.predict(x_temp)
            if not is_user_char:
                print('index:%s, query:%s' % (index, x_temp))
            y = int(np.argmax(y_array))
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
        classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
        raw_data[label]['acc'] = classify_acc
        print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
            label, num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
    Y_all = sum([len(data_dict['Y']) for _, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict['Y_compare']) for _, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    print('Y_compare_all: %s' % Y_compare_all)
    print('Y_all: %s' % Y_all)
    print('acc_all: %s' % acc)
    if kwargs.get('w_path'):
        print_test_xlsx(raw_data, w_path=kwargs['w_path'])
        print('union print_test_xlsx successful!!!')
    return raw_data

def test_pinyin_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
    print('test_pinyin_model:')
    raw_data = get_train_test_data(r_path=r_path, **kwargs)
    pinyin_model = IntentionPinyinModel(cfg_path=global_conf.cfg_path,
                                        model_section='INTENTION_CLASSIFY_PINYIN_MODEL', logger=logger, **kwargs)
    # label, {X:[], deal_X:[]}
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            is_use_pinyin, y_array = pinyin_model.predict(x_temp)
            if not is_use_pinyin:
                print('index:%s, query:%s' % (index, x_temp))
            y = int(np.argmax(y_array))
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
        classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
        raw_data[label]['acc'] = classify_acc
        print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
            label, num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
        # print('label_num:%s  label:%s  acc:%s' % (label, num2eng_dict[label], classify_acc))
    Y_all = sum([len(data_dict['Y']) for _, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict['Y_compare']) for _, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    print('Y_compare_all: %s' % Y_compare_all)
    print('Y_all: %s' % Y_all)
    print('acc_all: %s' % acc)
    if kwargs.get('w_path'):
        print_test_xlsx(raw_data, w_path=kwargs['w_path'])
        print('pinyin print_test_xlsx successful!!!')
    return raw_data


def test_pos_char_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
    print('test_pos_char_model:')
    raw_data = get_train_test_data(r_path=r_path, **kwargs)
    # pos_char_model = None
    pos_char_model = IntentionPosModel(cfg_path=global_conf.cfg_path,
                                       model_section='INTENTION_CLASSIFY_POS_MODEL', logger=logger, **kwargs)
    # label, {X:[], deal_X:[]}
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            is_use_pos, y_array = pos_char_model.predict(x_temp)
            if not is_use_pos:
                print('index:%s, query:%s' % (index, x_temp))
            y = int(np.argmax(y_array))
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
        if len(data_dict_temp['X']) == 0:
            print('label_num:%s,  label:%s无数据' % (label, num2eng_dict[label]))
        else:
            classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
            raw_data[label]['acc'] = classify_acc
            print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
                label, num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
        # print('label_num:%s  label:%s  acc:%s' % (label, num2eng_dict[label], classify_acc))
    Y_all = sum([len(data_dict.get('Y', [])) for _, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict.get('Y_compare', [])) for _, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    print('Y_compare_all: %s' % Y_compare_all)
    print('Y_all: %s' % Y_all)
    print('acc_all: %s' % acc)
    if kwargs.get('w_path'):
        print_test_xlsx(raw_data, w_path=kwargs['w_path'])
        print('pos_char print_test_xlsx successful!!!')
    return raw_data


# def test_word_pos_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
#     print('test_word_pos_model:')
#     raw_data = get_train_test_data(r_path=r_path, **kwargs)
#     # pos_char_model = None
#     word_pos_model = IntentionWordPosModel(cfg_path=global_conf.cfg_path,
#                                        model_section='INTENTION_CLASSIFY_WORD_POS_MODEL', logger=logger, **kwargs)
#     # label, {X:[], deal_X:[]}
#     for label, data_dict_temp in raw_data.items():
#         for index, x_temp in enumerate(data_dict_temp['X']):
#             is_use_pos, y_array = word_pos_model.predict(x_temp)
#             if not is_use_pos:
#                 print('index:%s, query:%s' % (index, x_temp))
#             y = int(np.argmax(y_array))
#             raw_data[label].setdefault('Y', []).append(y)
#             raw_data[label].setdefault('Y_compare', []).append(label == y)
#         classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
#         raw_data[label]['acc'] = classify_acc
#         print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
#             label, num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
#         # print('label_num:%s  label:%s  acc:%s' % (label, num2eng_dict[label], classify_acc))
#     Y_all = sum([len(data_dict['Y']) for _, data_dict in raw_data.items()])
#     Y_compare_all = sum([sum(data_dict['Y_compare']) for _, data_dict in raw_data.items()])
#     acc = float(Y_compare_all) / Y_all
#     print('Y_compare_all: %s' % Y_compare_all)
#     print('Y_all: %s' % Y_all)
#     print('acc_all: %s' % acc)
#     return raw_data


def get_url_data(x_temp):
    # params = {'q': unicode2str(x_temp), 'mode': 'xwyz'}
    # response = constant.aisc.query(params, service='intention_recognition', method='get')
    url_format = 'http://192.168.4.30:9300/intention_recognition?mode=xwyz&q=%s'
    url = url_format % x_temp
    response = json.loads(requests.get(url).text)
    return response['data']


def test_intention_interface(r_path='train_test_dialog_finally.xlsx', **kwargs):
    # 意图接口,统计准确率, 一级,二级
    print('test_intention_interface:')
    raw_data = get_train_test_data(r_path=r_path, **kwargs)
    intention = getIntention()
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            y_dict = intention.get_intention_and_entities(x_temp, 'xwyz', exclude_intention_set=['relatedDoctor'])
            # y_dict = get_url_data(x_temp)
            y = y_dict['intention']
            if y in other_include_intent:
                y = 'other'
            y = service_intent_dict[y]
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
            if y != 14:
                # other 的话排除掉， 分子是label == y,分母是 y !=14 的数据
                raw_data[label].setdefault('exclude_acc_fenzi', []).append(label == y)
                raw_data[label].setdefault('exclude_acc_fenmu', []).append(y)
        if len(data_dict_temp['X']) == 0:
            print('label_num:%s,  label:%s, 无数据' % (label, service_num2eng_dict[label]))
        else:
            classify_acc = float(sum(raw_data[label].get('Y_compare', []))) / len(data_dict_temp['X'])
            raw_data[label]['acc'] = classify_acc
            print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
                label, service_num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
        # print('label_num:%s  label:%s  num:%s acc:%s' % (label, num2eng_dict[label], len(data_dict_temp['X']), classify_acc))
    Y_all_ex_other = sum([len(data_dict.get('exclude_acc_fenmu', [])) for _v1, data_dict in raw_data.items()])
    Y_compare_all_ex_other = sum([sum(data_dict.get('exclude_acc_fenzi', [])) for _v1, data_dict in raw_data.items()])
    acc_ex_other = float(Y_compare_all_ex_other) / Y_all_ex_other
    print('Y_compare_all_ex_other: %s' % Y_compare_all_ex_other)
    print('Y_all_ex_other: %s' % Y_all_ex_other)
    print('acc_all_ex_other: %s' % acc_ex_other)

    Y_all = sum([len(data_dict.get('Y', [])) for _v1, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict.get('Y_compare', [])) for _v1, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    print('Y_compare_all: %s' % Y_compare_all)
    print('Y_all: %s' % Y_all)
    print('acc_all: %s' % acc)
    if kwargs.get('w_path'):
        print_test_xlsx(raw_data, w_path=kwargs['w_path'])
        print('interface print_test_xlsx successful!!!')


def test_intention_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
    # 意图模型, 统计准确率, 一级, 二级
    print('test_intention_model:')
    raw_data = get_train_test_data(r_path=r_path, **kwargs)
    intention = getIntention()
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            # try:
            # y_intent, y_score = intention.check_intention_by_model(x_temp)
            # y_intent, y_score = intention.check_intention_by_model_union(x_temp)
            y_intent, y_score = intention.check_intention_by_model(x_temp)
            # except:
            #     pass
            # y_intent, y_score = intention.check_intention_by_model_alter(x_temp)
            y = intent_dict[y_intent]
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
            if y != 14:
                # other 的话排除掉， 分子是label == y,分母是 y !=14 的数据
                raw_data[label].setdefault('exclude_acc_fenzi', []).append(label == y)
                raw_data[label].setdefault('exclude_acc_fenmu', []).append(y)
        classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
        raw_data[label]['acc'] = classify_acc
        print('label_num:%s,  label:%s, total:%s, acc_total:%s, acc:%s' % (
            label, num2eng_dict[label], len(raw_data[label]['Y']), sum(raw_data[label]['Y_compare']), classify_acc))
        # print('label_num:%s  label:%s  num:%s acc:%s' % (
        # label, num2eng_dict[label], len(data_dict_temp['X']), classify_acc))
    Y_all_ex_other= sum([len(data_dict.get('exclude_acc_fenmu', [])) for _v1, data_dict in raw_data.items()])
    Y_compare_all_ex_other = sum([sum(data_dict.get('exclude_acc_fenzi', [])) for _v1, data_dict in raw_data.items()])
    acc_ex_other = float(Y_compare_all_ex_other) / Y_all_ex_other if Y_all_ex_other != 0 else 0
    print('Y_compare_all_ex_other: %s' % Y_compare_all_ex_other)
    print('Y_all_ex_other: %s' % Y_all_ex_other)
    print('acc_all_ex_other: %s' % acc_ex_other)

    Y_all = sum([len(data_dict['Y']) for _v1, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict['Y_compare']) for _v1, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    print('Y_compare_all: %s' % Y_compare_all)
    print('Y_all: %s' % Y_all)
    print('acc_all: %s' % acc)
    if kwargs.get('w_path'):
        print_test_xlsx(raw_data, w_path=kwargs['w_path'])
        print('model print_test_xlsx successful!!!')


def final_func_get_3_model_result(raw_data):
    # 得到3个模型的结果
    intention = getIntention()
    for label, data_dict_temp in raw_data.items():
        for index, x_temp in enumerate(data_dict_temp['X']):
            char, pinyin, pos, word_pos, is_use_char, is_use_pinyin, is_use_pos, is_use_word_pos =\
                intention.get_models_result_optimize(x_temp)
            data_dict_temp.setdefault('char_Y', []).append(char)
            data_dict_temp.setdefault('pinyin_Y', []).append(pinyin)
            data_dict_temp.setdefault('pos_Y', []).append(pos)
            data_dict_temp.setdefault('word_pos_Y', []).append(word_pos)
            data_dict_temp.setdefault('is_use_char', []).append(is_use_char)
            data_dict_temp.setdefault('is_use_pinyin', []).append(is_use_pinyin)
            data_dict_temp.setdefault('is_use_pos', []).append(is_use_pos)
            data_dict_temp.setdefault('is_use_word_pos', []).append(is_use_word_pos)
    return raw_data


def test_optimize_weight_model(r_path='train_test_dialog_finally.xlsx', **kwargs):
    # 意图模型, 统计准确率, 一级, 二级 获取最优权重
    print('test_optimize_weight_model:')
    raw_data = get_train_test_data(r_path=r_path, final_func=final_func_get_3_model_result, **kwargs)
    intention = getIntention()
    weights_list = []
    index = 0
    for char_weight in range(1, 10, 1):
        for pinyin_weight in range(1, 10, 1):
            for pos_weight in range(1, 10, 1):
                for threshold in range(0, 10, 1):
                    params = {
                        'char_weight': char_weight,
                        'pinyin_weight': pinyin_weight,
                        'pos_weight': pos_weight,
                        'threshold': threshold
                    }
                    # if char_weight == 1 and pinyin_weight == 1 and pos_weight == 2 and threshold == 3:
                    #     print('aa')
                    step_dict = test_optimize_weight_model_step(raw_data, intention, **params)
                    step_dict.update({'char_weight': char_weight, 'pinyin_weight': pinyin_weight,
                                         'pos_weight': pos_weight, 'threshold': threshold})
                    weights_list.append(step_dict)
                    index += 1
                    if index % 30 == 0:
                        print('index: %s' % index)
        weights_list.sort(key=lambda temp: temp['acc'], reverse=True) # acc 排序
        # weights_list.sort(key=lambda temp: temp['acc_ex_other'], reverse=True)   # acc_ex_other排序
        if len(weights_list) > 5000:
            weights_list = weights_list[:5000]
        print('char_weight进行到%s, len(weight_list):%s' % (char_weight, len(weights_list)))
        print('前20weight：')
        for weights in weights_list[:20]:
            print('acc:%s,  acc_ex_other:%s, len_Y_all_ex_other:%s, len_Y_compare_all_ex_other:%s,'
                  'char:%s,  pinyin:%s, pos:%s, threshold:%s' % (
                weights['acc'], weights['acc_ex_other'], weights['len_Y_all_ex_other'],
                weights['len_Y_compare_all_ex_other'], weights['char_weight'],
                weights['pinyin_weight'], weights['pos_weight'], weights['threshold']))

    print('最终前5000weights')
    txt = open('ai_kefu_test_optimize_weight_model_acc.txt', mode='w')
    # txt = open('test_optimize_weight_model_acc_exclude.txt', mode='w')
    for weights in weights_list:
        txt.write('acc:%s,  acc_ex_other:%s, len_Y_all_ex_other:%s, len_Y_compare_all_ex_other:%s,'
                  'char:%s,  pinyin:%s, pos:%s, threshold:%s\n' % (
                      weights['acc'], weights['acc_ex_other'], weights['len_Y_all_ex_other'],
                      weights['len_Y_compare_all_ex_other'], weights['char_weight'],
                      weights['pinyin_weight'], weights['pos_weight'], weights['threshold']))
        print('acc:%s,  acc_ex_other:%s, len_Y_all_ex_other:%s, len_Y_compare_all_ex_other:%s,'
              'char:%s,  pinyin:%s, pos:%s, threshold:%s' % (
                  weights['acc'], weights['acc_ex_other'], weights['len_Y_all_ex_other'],
                  weights['len_Y_compare_all_ex_other'], weights['char_weight'],
                  weights['pinyin_weight'], weights['pos_weight'], weights['threshold']))


def test_optimize_weight_model_2(r_path='train_test_dialog_finally.xlsx', **kwargs):
    # 意图模型, 统计准确率, 一级, 二级 获取最优权重
    print('test_optimize_weight_model:')
    raw_data = get_train_test_data(r_path=r_path, final_func=final_func_get_3_model_result, **kwargs)
    intention = getIntention()
    weights_list = []
    index = 0
    for char_weight in range(1, 10, 1):
        for pinyin_weight in range(1, 10, 1):
            for pos_weight in range(1, 10, 1):
                for word_pos_weight in range(1, 10, 1):
                # for threshold in range(0, 10, 1):
                    params = {
                        'char_weight': char_weight,
                        'pinyin_weight': pinyin_weight,
                        'pos_weight': pos_weight,
                        'word_pos_weight': word_pos_weight
                        # 'threshold': threshold
                    }
                    # if char_weight == 1 and pinyin_weight == 1 and pos_weight == 2 and threshold == 3:
                    #     print('aa')
                    step_dict = test_optimize_weight_model_step(raw_data, intention, **params)
                    step_dict.update({'char_weight': char_weight, 'pinyin_weight': pinyin_weight,
                                         'pos_weight': pos_weight, 'word_pos_weight': word_pos_weight})
                    weights_list.append(step_dict)
                    index += 1
                    if index % 30 == 0:
                        print('index: %s' % index)
        weights_list.sort(key=lambda temp: temp['acc'], reverse=True)  # acc 排序
        # weights_list.sort(key=lambda temp: temp['acc_ex_other'], reverse=True)   # acc_ex_other排序
        if len(weights_list) > 5000:
            weights_list = weights_list[:5000]
        print('char_weight进行到%s, len(weight_list):%s' % (char_weight, len(weights_list)))
        print('前20weight：')
        for weights in weights_list[:20]:
            print('acc:%s,  acc_ex_other:%s, len_Y_all_ex_other:%s, len_Y_compare_all_ex_other:%s,'
                  'char:%s,  pinyin:%s, pos:%s, word_pos_weight:%s' % (
                weights['acc'], weights['acc_ex_other'], weights['len_Y_all_ex_other'],
                weights['len_Y_compare_all_ex_other'], weights['char_weight'],
                weights['pinyin_weight'], weights['pos_weight'], weights['word_pos_weight']))

    print('最终前5000weights')
    txt = open('ai_kefu_test_optimize_weight_model_acc.txt', mode='w')
    # txt = open('test_optimize_weight_model_acc_exclude.txt', mode='w')
    for weights in weights_list:
        txt.write('acc:%s,  acc_ex_other:%s, len_Y_all_ex_other:%s, len_Y_compare_all_ex_other:%s,'
                  'char:%s,  pinyin:%s, pos:%s, word_pos_weight:%s\n' % (
                      weights['acc'], weights['acc_ex_other'], weights['len_Y_all_ex_other'],
                      weights['len_Y_compare_all_ex_other'], weights['char_weight'],
                      weights['pinyin_weight'], weights['pos_weight'], weights['word_pos_weight']))
        print('acc:%s,  acc_ex_other:%s, len_Y_all_ex_other:%s, len_Y_compare_all_ex_other:%s,'
              'char:%s,  pinyin:%s, pos:%s, word_pos_weight:%s' % (
                  weights['acc'], weights['acc_ex_other'], weights['len_Y_all_ex_other'],
                  weights['len_Y_compare_all_ex_other'], weights['char_weight'],
                  weights['pinyin_weight'], weights['pos_weight'], weights['word_pos_weight']))

def test_optimize_weight_model_step(raw_data, intention, **kwargs):
    # 意图模型, 统计准确率, 一级, 二级
    # print('test_optimize_weight_model_step:')
    for label, data_dict_temp in raw_data.items():
        data_dict_temp.pop('Y', None)
        data_dict_temp.pop('Y_compare', None)
        data_dict_temp.pop('exclude_acc_fenmu', None)
        data_dict_temp.pop('exclude_acc_fenzi', None)
        for index, x_temp in enumerate(data_dict_temp['X']):
            # y_intent, y_score = intention.check_intention_by_model(x_temp)
            # y_intent, y_score = intention.check_intention_by_model_alter(x_temp)
            kwargs['char_result'] = data_dict_temp['char_Y'][index]
            kwargs['pinyin_result'] = data_dict_temp['pinyin_Y'][index]
            kwargs['pos_result'] = data_dict_temp['pos_Y'][index]
            kwargs['word_pos_result'] = data_dict_temp['word_pos_Y'][index]
            kwargs['is_use_char'] = data_dict_temp['is_use_char'][index]
            kwargs['is_use_pinyin'] = data_dict_temp['is_use_pinyin'][index]
            kwargs['is_use_pos'] = data_dict_temp['is_use_pos'][index]
            kwargs['is_use_word_pos'] = data_dict_temp['is_use_word_pos'][index]
            y_intent, y_score = intention.check_intention_by_model_alter_optimize(**kwargs)
            y = intent_dict[y_intent]
            raw_data[label].setdefault('Y', []).append(y)
            raw_data[label].setdefault('Y_compare', []).append(label == y)
            if y != 14:
                # other 的话排除掉， 分子是label == y,分母是 y !=14 的数据
                raw_data[label].setdefault('exclude_acc_fenzi', []).append(label == y)
                raw_data[label].setdefault('exclude_acc_fenmu', []).append(y)
        # classify_acc = float(sum(raw_data[label]['Y_compare'])) / len(data_dict_temp['X'])
        # raw_data[label]['acc'] = classify_acc
        # print('label_num:%s  label:%s  num:%s acc:%s' % (
        # label, num2eng_dict[label], len(data_dict_temp['X']), classify_acc))
    Y_all_ex_other = sum([len(data_dict['exclude_acc_fenmu']) for _v1, data_dict in raw_data.items() if data_dict.get('exclude_acc_fenmu')])
    Y_compare_all_ex_other = sum([sum(data_dict['exclude_acc_fenzi']) for _v1, data_dict in raw_data.items() if data_dict.get('exclude_acc_fenzi')])
    acc_ex_other = float(Y_compare_all_ex_other) / Y_all_ex_other
    # print('Y_compare_all_ex_other: %s' % Y_compare_all_ex_other)
    # print('Y_all_ex_other: %s' % Y_all_ex_other)
    # print('acc_all_ex_other: %s' % acc_ex_other)

    Y_all = sum([len(data_dict['Y']) for _v1, data_dict in raw_data.items()])
    Y_compare_all = sum([sum(data_dict['Y_compare']) for _v1, data_dict in raw_data.items()])
    acc = float(Y_compare_all) / Y_all
    # print('Y_compare_all: %s' % Y_compare_all)
    # print('Y_all: %s' % Y_all)
    # print('acc_all: %s' % acc)
    return {'acc': acc, 'acc_ex_other': acc_ex_other, 'len_Y_all_ex_other': Y_all_ex_other,
            'len_Y_compare_all_ex_other': Y_compare_all_ex_other}



if __name__ == '__main__':
    # r_path = '训练集A_AI测试集.xls'
    # r_path = 'train_test_dialog_finally.xlsx'
    r_path = '意图识别训练验证测试集合.xls'
    # result = get_train_test_data(r_path=r_path, sheet_index=1)
    # result = test_union_model(r_path=r_path, sheet_index=2, model_version=3, w_path='union_test_report.xlsx')
    # result = test_char_model(r_path=r_path, sheet_index=1, model_version=2, w_path='char_test_report.xlsx')
    # test_pinyin_model(r_path=r_path, sheet_index=1, model_version=2, w_path='pinyin_test_report.xlsx')
    # test_pos_char_model(r_path=r_path, sheet_index=2, model_version=2, w_path='pos_char_test_report.xlsx')
    # test_word_pos_model(r_path=r_path, sheet_index=1, model_version=2)
    test_intention_model(r_path=r_path, sheet_index=2, model_version=6, w_path='model_test_report.xlsx')
    # test_intention_interface(r_path=r_path, sheet_index=2, is_service=1, model_version=6,
    #                          w_path='interface_test_report.xlsx')
    # test_optimize_weight_model(r_path=r_path, sheet_index=1, model_version=2)
    # test_optimize_weight_model_2(r_path=r_path, sheet_index=1, model_version=2)
    # test_optimize_weight_service(r_path='train_test_dialog_finally.xlsx')
    print('finish')
