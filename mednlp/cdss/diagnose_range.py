# -*- coding: utf-8 -*-
"""
@Author: chaipf
@Email: chaipf@guahao.com
@Date: 20190422
@Desc: 诊断范围优化 http://confluence.guahao-inc.com/pages/viewpage.action?pageId=37697951
"""

import csv
import codecs
import global_conf
from functools import reduce


MERGE_MAP_NAME = {
    '支气管哮喘': '哮喘',
    # '急性化脓性胆管炎': '急性化脓性梗阻性胆管炎',
    # '新生儿肺透明膜病': '新生儿呼吸窘迫综合征',
    '慢性中耳炎': '慢性化脓性中耳炎',
    '手皮真菌病': '手癣',
    # '上呼吸道感染': '急性上呼吸道感染',
    '绿脓杆菌性肺炎': '肺炎',
    '肺炎球菌性肺炎': '肺炎',
    '葡萄球菌性肺炎': '肺炎',
    '非典型性肺炎': '肺炎',
    '肾病综合征伴微小病变型肾小球肾炎': '肾病综合征',
    '膜性肾病': '肾病综合征',
    '乳房纤维囊性乳腺病': '乳腺增生',
    '乳腺囊性增生病(慢性囊性乳腺炎)': '乳腺增生',
    # '急性肾衰竭伴有肾小管坏死': '急性肾衰竭',     # 急性肾衰竭先不做
    '莱姆病': None,
    # '便血': None,
    # '腹泻': None,
    '阴道出血': None,
    '瘢痕': None,
    '失眠': None,
    # '消瘦': None,
    '乳头溢液': None,
    # '耳鸣': None,
    '天花': None,
    '单纯红细胞再生障碍性贫血': None,
    '产间尿潴留': None,
    '新生儿窒息 NOS': None,
    '新生儿肺炎 NOS': None,
    '新生儿败血症 NOS': None,
    '新生儿出血病': None,
    '新生儿ABO溶血性贫血': None,
    '新生儿高胆红素血症': None,
    '新生儿黄疸 NOS': None,
    '新生儿失血性贫血': None,
    '新生儿糖尿病': None,
    '新生儿惊厥': None,
    '单胎活产': None,
}


def trans_map():
    """将映射表中名字转化为id"""
    all_diseases = {}
    with codecs.open(global_conf.disease_id_name_path, 'r', 'utf-8') as f:
        for items in csv.reader(f):
            if len(items) == 2:
                all_diseases[items[1]] = items[0]
    maps = {}
    for k, v in MERGE_MAP_NAME.items():
        ori_id = all_diseases.get(k)
        now_id = all_diseases.get(v)
        if not ori_id:
            print("not find" + str(k))
        maps[ori_id] = now_id
    return maps


MERGE_MAP = trans_map()

def merge_diagnose_range(all_diseases):
    if len(all_diseases) == 0:
        return all_diseases
    disease_score_map = {}
    for disease in all_diseases:
        disease_score_map[disease['disease_id']] = disease['score']

    for ori, now in MERGE_MAP.items():
        ori_score = disease_score_map.get(ori, 0)
        now_score = disease_score_map.get(now, 0)
        if now:
            disease_score_map[now] = ori_score + now_score
        if ori in disease_score_map:
            del disease_score_map[ori]

    disease_list = []
    for disease, score in disease_score_map.items():
        disease_list.append({'disease_id': disease, 'score': score})

    # 重新归一化
    sum_score = reduce(lambda x, y: x + y['score'], disease_list, 0)
    if sum_score == 0:
        sum_score = 1e-9
    for disease in disease_list:
        disease['score'] /= sum_score

    # 重新排序
    sorted_diseases = sorted(disease_list, key=lambda x: x['score'], reverse=True)
    return sorted_diseases
