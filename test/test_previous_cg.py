#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试预问诊
"""
import json
import global_conf
from mednlp.dialog.generator.previous_diagnose_generator import PreviousDiagnoseGenerator

control = PreviousDiagnoseGenerator(global_conf.cfg_path)


def test(symptom):
    # query = symptom_dict[symptom]
    # print(symptom)

    if not symptom.get('age'):
        symptom['age'] = -1
    if not symptom.get('sex'):
        symptom['sex'] = -1
    result = control.generate(symptom)
    print(result['chief_complaint'])
    print(result['medical_history'])


general = {
    'symptom': '血尿',
    'time': ['2天'],
    'reason': ['不清楚'],
    'accompany_symptom': ['发热', '皮下出血'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解']
}

发热 = {
    'symptom': '发热',
    'time': ['2天'],
    'reason': ['因受凉后'],
    'symptom_property': ['39.5℃'],
    'frequency': ['间断发热'],
    'property_added': ['一天内体温波动＞1.2℃'],
    'accompany_symptom': ['疲劳', '胸痛'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解']
}

咳嗽 = {
    'symptom': '咳嗽',
    'time': ['2天'],
    'reason': ['因受凉后'],
    # 'symptom_property': ['39.5℃'],
    'frequency': ['持续性咳嗽'],
    'accompany_symptom': ['咳痰', '胸痛'],
    'accompany_symptom_property': ['咳粉红丝痰'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解']
}

血压升高 = {
    'time': ['2天'],
    'reason': ['因劳累'],
    'symptom': '血压升高',
    'sbp': ['收缩压：130mmHg'],
    'dbp': ['舒张压：80mmHg'],
    'symptom_property': ['阵发性血压升高'],
    'accompany_symptom': ['恶心', '发热', '反酸'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解']
}

血糖升高 = {
    'time': ['2天'],
    'reason': ['因劳累'],
    'symptom': '血糖升高',
    'property_added': ['血糖值为：22mmol/L'],
    'symptom_property': ['空腹血糖'],
    'accompany_symptom': ['恶心', '发热', '反酸'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解']
}

腹痛 = {
    'symptom': '腹痛',
    'time': ['2天'],
    'reason': ['因不洁饮食'],
    'degree': ['轻度'],
    'body_part': ['上腹部'],
    'frequency': ['持续性疼痛'],
    'symptom_property': ['针刺样痛'],
    'accompany_symptom': ['发热', '皮下出血'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解'],
    'menstruation_last_time': ['末次月经：2019-4-5'],
    'menstruation_interval_time': ['28-30天']
}

# 头晕@|time|前@|reason|@出现|symptom|，@呈|symptom_property|，@|property_added|，@伴随|accompany_symptom|。@|medicine_detail|，@症状|medicine_effect|

头晕 = {
    'symptom': '头晕',
    'time': ['2天'],
    'reason': ['因长时间未进食'],
    'frequency': ['间断性头晕'],
    'symptom_property': ['运动不稳感'],
    'property_added': ['每次头痛持续数秒钟'],
    'accompany_symptom': ['发热', '皮下出血'],
    'medicine_detail': ['阿司匹林口服'],
    'medicine_effect': ['没有缓解']
}

疲劳 = {
    "time": ['2天'],
    "reason": ['因心理压力大'],
    "symptom": "疲劳",
    "property_added": ['充分休息后可以缓解'],
    "accompany_symptom": ['头痛', '咽痛'],
    "medicine_detail": ['阿司匹林口服'],
    "medicine_effect": ['没有缓解']
}

便秘 = {
    "time": ['2天'],
    "reason": ['不清楚'],
    "symptom": "便秘",
    "property_added": ['排便为粪球或硬粪'],
    "accompany_symptom": ['腹痛', '腹胀'],
    "frequency": ['平时0-2天排便一次'],
    "frequency_added": ['每次排便需要5分钟-10分钟'],
    "medicine_detail": ['阿司匹林口服'],
    "medicine_effect": ['没有缓解']
}

恶心 = {
    "time": ["2天"],
    "reason": ["饱餐后"],
    "symptom": "恶心",
    "symptom_property": ["非喷射状呕吐"],
    "property_added": ["呕吐物为血性"],
    "accompany_symptom": ["腹泻", "头晕", "头痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

水肿 = {
    "time": ["2天"],
    "reason": ["因久坐"],
    "symptom": "水肿",
    "body_part": ["全身"],
    "property_added": ["按压水肿处再松开手指，凹陷后数秒-1分钟平复"],
    "first_body_part": ["最早从眼睑、颜面部开始"],
    # "first_body_part": ["不清楚"],
    # "description": ["水肿处皮温凉、呈紫色"],
    "accompany_symptom": ["呼吸困难", "心慌", "少尿"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

口腔溃疡 = {
    "time": ["2天"],
    "reason": ["因烫伤"],
    "symptom": "口腔溃疡",
    "body_part": ["舌部"],
    "property_added": ["有＜3处溃疡"],
    "description": ["溃疡深而大"],
    "accompany_symptom": ["口腔疱疹", "发热"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

呕血 = {
    "time": ["2天"],
    "reason": [],
    "symptom": "呕血",
    "frequency": ["反复性"],
    "symptom_property": ["暗红色"],
    "frequency_added": ["一天呕血＜3次"],
    "quantity": ["每次呕血量少（少于1纸杯）"],
    "accompany_symptom": ["疲劳", "胸痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

心慌 = {
    "time": ["2天"],
    "reason": ["因着凉"],
    "symptom": "心慌",
    "property_added": ["脉搏＜60次/分"],
    "accompany_symptom": ["口腔疱疹", "发热"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

眼睛红痛 = {
    "time": ["2天"],
    "reason": ["眼部外伤后"],
    "symptom": "眼睛红痛",
    # "property_added": ["不清楚"],
    "property_added": ["起初一只眼睛发病，之后双眼发病"],
    "accompany_symptom": ["畏光", "流泪"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

体重下降 = {
    "time": ["2月"],
    "reason": ["因睡眠障碍"],
    "symptom": "体重下降",
    # "quantity": ["否"],
    "quantity": ["3kg"],
    "accompany_symptom": ["乏力", "怕冷"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}
体重减轻 = {
    "time": ["2月"],
    "reason": ["因睡眠障碍"],
    "symptom": "体重减轻",
    # "quantity": ["否"],
    "quantity": ["3kg"],
    "accompany_symptom": ["乏力", "怕冷"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

# 体重升高、体重上升、
体重上升 = {
    "time": ["2月"],
    "reason": ["因活动量减少"],
    "symptom": "体重上升",
    # "quantity": ["否"],
    "quantity": ["3kg"],
    "accompany_symptom": ["怕冷", "睡睡"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

腹泻 = {
    "time": ["2月"],
    "reason": ["因着凉"],
    "symptom": "腹泻",
    "symptom_property": ["果酱样便"],
    "property_added": ["一天排便＞6次"],
    "accompany_symptom": ["畏寒", "发热"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

头痛 = {
    "time": ["2月"],
    "reason": [""],
    "degree": ["轻度"],
    "symptom": "头痛",
    "body_part": ["眼眶"],
    "frequency": ["间断头痛"],
    "symptom_property": ["针刺样痛"],
    "frequency_added": ["每次头痛持续数秒钟"],
    "accompany_symptom": ["头晕", "发热"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

头晕 = {
    "time": ["2月"],
    "reason": ["因长时间未进食"],
    "symptom": "头晕",
    "frequency": ["间断性头晕"],
    "symptom_property": ["运动不稳感"],
    "frequency_added": ["每次头晕持续数秒钟"],
    "accompany_symptom": ["头晕、发热"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

鼻塞 = {
    "time": ["2天"],
    "reason": ["因接触花粉、粉尘"],
    "symptom": "鼻塞",
    "frequency": ["间歇性鼻塞"],
    "symptom_property": ["单侧鼻塞"],
    "accompany_symptom": ["头晕、头痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

咽痛 = {
    "time": ["2天"],
    "reason": ["因咽部烫伤"],
    "degree": ["轻度"],
    "symptom": "咽痛",
    "body_part": ["双侧"],
    "accompany_symptom": ["流涕、咽干"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

白带异常 = {
    "time": ["2月"],
    "reason": ["月经前一周"],
    "symptom": "白带异常",
    # "symptom_property": ["凝乳状或豆样渣白带"],
    "symptom_property": ["无时间规律"],
    "property_added": ["白带有异味"],
    "accompany_symptom": ["尿频、尿痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}
胸痛 = {
    "time": ["2天"],
    "reason": ["外伤后"],
    "degree": ["轻度"],
    "symptom": "胸痛",
    "body_part": ["左侧胸部"],
    "frequency": ["间断性胸痛"],
    "symptom_property": ["锐痛"],
    "property_added": ["疼痛持续数秒钟"],
    "accompany_symptom": ["发热、咳嗽"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

耳痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "degree": ["轻度"],
    "symptom": "耳痛",
    "body_part": ["右侧耳部"],
    "frequency": ["持续性耳痛"],
    "symptom_property": ["钝痛"],
    "accompany_symptom": ["耳闷、耳胀"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

腿痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "degree": ["轻度"],
    "symptom": "腿痛",
    "body_part": ["小腿前侧"],
    "accompany_symptom": ["发热、腰痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

膝部疼痛 = {
    "time": ["2天"],
    "reason": ["因剧烈运动"],
    "degree": ["轻度"],
    "symptom": "膝部疼痛",
    "body_part": ["左侧膝部"],
    "accompany_symptom": ["膝关节肿胀、膝关节僵硬"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

颈部疼痛 = {
    "time": ["2天"],
    "reason": ["因长期低头"],
    "degree": ["轻度"],
    "symptom": "颈部疼痛",
    "property_added": ["颈部活动后疼痛缓解"],
    "accompany_symptom": ["手指麻木、手部疼痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

肩部疼痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "degree": ["轻度"],
    "symptom": "肩部疼痛",
    "body_part": ["肩峰处"],
    "frequency": ["持续性疼痛"],
    "symptom_property": ["钝痛"],
    "accompany_symptom": ["腹痛、胸痛"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

便血 = {
    "time": ["2天"],
    "reason": [],
    "symptom": "便血",
    "frequency": ["间断性便血"],
    "symptom_property": ["暗红色"],
    "property_added": ["黏液样便"],
    "accompany_symptom": ["恶心、呕吐"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

咯血 = {
    "time": ["2天"],
    "reason": ["因劳累"],
    "symptom": "咯血",
    "symptom_property": ["暗红色"],
    "accompany_symptom": ["咳痰、发热"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

呼吸困难 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "symptom": "呼吸困难",
    "frequency": ['阵发性'],
    "description": ['吸气的时候感觉费力'],
    "accompany_symptom": ['胸痛、心悸'],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

失眠 = {
    "time": ["2天"],
    "reason": ["因负性生活事件"],
    "symptom": "失眠",
    "property_added": ["以入睡困难为主"],
    "frequency_added": ['每周失眠＜3次'],
    "description": ['在主要的睡眠时段失眠'],
    "accompany_symptom": ['咳嗽、胸痛'],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

足部疼痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "symptom": "足部疼痛",
    "body_part": ['足底部'],
    "symptom_property": ["胀痛"],
    "accompany_symptom": ['足关节僵硬、步行困难'],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}


踝部疼痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "symptom": "踝部疼痛",
    "body_part": ['踝部前侧'],
    "symptom_property": ["胀痛"],
    "accompany_symptom": ['踝关节僵硬、步行困难'],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

髋部疼痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "symptom": "髋部疼痛",
    "body_part": ["左髋部"],
    "frequency": ["阵发性疼痛"],
    "accompany_symptom": ["下肢活动受限、步行困难"],
    "accompany_symptom_property": ["下肢不能向外分开"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

臀部疼痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "symptom": "臀部疼痛",
    "body_part": ["臀部外上区、臀部外下区"],
    "symptom_property": ['酸痛'],
    "accompany_symptom": ["下肢活动受限、大便障碍"],
    "accompany_symptom_property": ["下肢不能向外分开"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

消化不良 = {
    "time": ["2天"],
    "reason": ["进食辛辣刺激食物后"],
    "symptom": "消化不良",
    "symptom_property": ['餐后饱胀、早饱感、上腹痛、上腹灼烧感'],
    "property_added": ["餐前有症状，餐后加重"],
    "accompany_symptom": ["恶心、发热、反酸"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

腰痛 = {
    "time": ["2天"],
    "reason": ["因外伤"],
    "symptom": "腰痛",
    "degree": ["轻度"],
    "body_part": ["右侧腰部"],
    "symptom_property": ['隐痛'],
    "accompany_symptom": ["发热、少尿"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

吞咽困难 = {
    "time": ["2天"],
    "reason": ["颈部手术后"],
    "symptom": "吞咽困难",
    "frequency": ["间歇性吞咽困难"],
    "accompany_symptom": ["声嘶", "呛咳", "呃逆"],
    "medicine_detail": ["阿司匹林口服"],
    "medicine_effect": ["没有缓解"]
}

asa = {
    'symptom': '腹痛',
    'sex': 1,
    'age': 9125
}
if __name__ == '__main__':
    test(失眠)

