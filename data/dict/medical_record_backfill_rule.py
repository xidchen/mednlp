#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-08-03 Saturday
@Desc:	全科V2.0 症状回填规则
"""

from functools import partial


def is_all_have(actual, expect):
    """ 判断expect中是否包含所有的actual

    :actual: 实际输入，字典形式
    :expect: 期望输入包含的
    :returns:

    """
    for exp in expect.split('|'):
        if exp not in actual:
            return False
        if not actual[exp]:
            return False
    return True


rule_templates = {
    'rule1': (
        ('患者{病程}前{诱因}出现{程度}{症状}', partial(is_all_have, expect="病程|诱因|程度|症状")),
        ('患者{病程}前{诱因}出现{症状}', partial(is_all_have, expect="病程|诱因|症状")),
        ('患者{病程}前出现{程度}{症状}', partial(is_all_have, expect="病程|程度|症状")),
        ('患者{病程}前出现{症状}', partial(is_all_have, expect="病程|症状")),
        ('患者{诱因}出现{程度}{症状}', partial(is_all_have, expect="诱因|程度|症状")),
        ('患者{诱因}出现{症状}', partial(is_all_have, expect="诱因|症状")),
        ('患者出现{程度}{症状}', partial(is_all_have, expect="程度|症状")),
        ('患者出现{症状}', partial(is_all_have, expect="症状"))
    ),
    'rule2': (
        ('患者{病程}内{诱因}出现{程度}{症状}', partial(is_all_have, expect="病程|诱因|程度|症状")),
        ('患者{病程}内{诱因}出现{症状}', partial(is_all_have, expect="病程|诱因|症状")),
        ('患者{诱因}出现{程度}{症状}', partial(is_all_have, expect="诱因|程度|症状")),
        ('患者{诱因}出现{症状}', partial(is_all_have, expect="诱因|症状")),
        ('患者{病程}内出现{程度}{症状}', partial(is_all_have, expect="病程|程度|症状")),
        ('患者{病程}内出现{症状}', partial(is_all_have, expect="病程|症状")),
        ('患者{诱因}出现{程度}{症状}', partial(is_all_have, expect="诱因|程度|症状")),
        ('患者{诱因}出现{症状}', partial(is_all_have, expect="诱因|症状"))
    ),
    'rule3': (
        ('患者{病程}前{诱因}出现{程度}{具体症状}', partial(is_all_have, expect="病程|诱因|程度|具体症状")),
        ('患者{病程}前{诱因}出现{具体症状}', partial(is_all_have, expect="病程|诱因|具体症状")),
        ('患者{病程}前出现{程度}{具体症状}', partial(is_all_have, expect="病程|程度|具体症状")),
        ('患者{病程}前出现{具体症状}', partial(is_all_have, expect="病程|具体症状")),
        ('患者{诱因}出现{程度}{具体症状}', partial(is_all_have, expect="诱因|程度|具体症状")),
        ('患者{诱因}出现{具体症状}', partial(is_all_have, expect="诱因|具体症状")),
        ('患者出现{程度}{具体症状}', partial(is_all_have, expect="程度|具体症状")),
        ('患者出现{具体症状}', partial(is_all_have, expect="具体症状")),
        ('患者{病程}前{诱因}出现{程度}{症状}', partial(is_all_have, expect="病程|诱因|程度|症状")),
        ('患者{病程}前{诱因}出现{症状}', partial(is_all_have, expect="病程|诱因|症状")),
        ('患者{病程}前出现{程度}{症状}', partial(is_all_have, expect="病程|程度|症状")),
        ('患者{病程}前出现{症状}', partial(is_all_have, expect="病程|症状")),
        ('患者{诱因}出现{程度}{症状}', partial(is_all_have, expect="诱因|程度|症状")),
        ('患者{诱因}出现{症状}', partial(is_all_have, expect="诱因|症状")),
        ('患者出现{程度}{症状}', partial(is_all_have, expect="程度|症状")),
        ('患者出现{症状}', partial(is_all_have, expect="症状"))
    ),
    'rule_buwz': (
        ('具体部位不详', lambda x: x.get('部位') == '不详'),
        ('部位是{部位}', partial(is_all_have, expect="部位"))
    ),
    'rule_qita': (
        ('其他：{其他：}', partial(is_all_have, expect="其他：")),
    ),
    'rule_xyvi': (
        ('为{性质}', partial(is_all_have, expect="性质")),
    ),
    'rule_fazotedm': (
        ('呈{发作特点}', partial(is_all_have, expect="发作特点")),
    ),
    'rule_hrjxynsu': (
        ('', lambda x: x.get('缓解因素', '') == '无'),
        ('{缓解因素}可缓解', partial(is_all_have, expect="缓解因素")),
    ),
    'rule_jwvsynsu': (
        ('', lambda x: x.get('加重因素', '') == '无'),
        ('{加重因素}加重', partial(is_all_have, expect="加重因素")),
    ),
    'rule_bjsvvgvd': (
        ('伴随症状不详', lambda x: x.get('伴随症状') == '不详'),
        ('伴随{伴随症状}', partial(is_all_have, expect="伴随症状")),
    ),
    'rule_yitmnztiwen': (
        ('一天内体温波动幅度：{一天内体温波动幅度}', partial(is_all_have, expect="一天内体温波动幅度")),
    ),
    'rule_tiwf': (
        ('体温：{体温}', partial(is_all_have, expect="体温")),
    ),
    'rule_zvgktiwf': (
        ('最高体温：{最高体温}', partial(is_all_have, expect="最高体温")),
    ),
    'rule_ynse': (
        ('音色：{音色}', partial(is_all_have, expect="音色")),
    ),
    'rule_titl': (
        ('体态：{体态}', partial(is_all_have, expect="体态")),
    ),
    'rule_tivszgjw': (
        ('体重增加：{体重增加}', partial(is_all_have, expect="体重增加")),
    ),
    'rule_tivsxwjd': (
        ('体重下降：{体重下降}', partial(is_all_have, expect="体重下降")),
    ),
    'rule_bcxmxyui': (
        ('表现形式：{表现形式}', partial(is_all_have, expect="表现形式")),
    ),
    'rule_dabmyjse': (
        ('为{大便颜色}', partial(is_all_have, expect="大便颜色")),
    ),
    'rule_dabmxyvd': (
        ('大便性状：{大便性状}', partial(is_all_have, expect="大便性状")),
    ),
    'rule_plbmpnci': (
        ('排便频次：{排便频次}', partial(is_all_have, expect="排便频次")),
    ),
    'rule_yjse': (
        ('为{颜色}', partial(is_all_have, expect="颜色")),
    ),
    'rule_qiwz': (
        ('气味：{气味}', partial(is_all_have, expect="气味")),
    ),
    'rule_ncyeyjse': (
        ('为{尿液颜色}', partial(is_all_have, expect="尿液颜色")),
    ),
    'rule_ncld': (
        ('尿量：{尿量}', partial(is_all_have, expect="尿量")),
    ),
    'rule_plncpnci': (
        ('排尿频次：{排尿频次}', partial(is_all_have, expect="排尿频次")),
    ),
    'rule_fhuebuwz': (
        ('无放射痛', lambda x: x.get('放射部位') == '无'),
        ('放射部位：{放射部位}', partial(is_all_have, expect="放射部位")),
    ),
    'rule_fhuebuwz_tgts': (
        ('无放射痛', lambda x: x.get('放射部位') == '无'),
        ('疼痛放射到{放射部位}', partial(is_all_have, expect="放射部位")),
    ),
    'rule_mzcifazouijm': (
        ('每次发作时间：{每次发作时间}', partial(is_all_have, expect="每次发作时间")),
    ),
    'rule_pnci': (
        ('频次：{频次}', partial(is_all_have, expect="频次")),
    ),
    'rule_zvzkiuxmbuwz': (
        ('最早出现部位：{最早出现部位}', partial(is_all_have, expect="最早出现部位")),
    ),
    'rule_uild': (
        ('食量：{食量}', partial(is_all_have, expect="食量")),
    ),
    'rule_xtthvi': (
        ('血糖值：{血糖值}', partial(is_all_have, expect="血糖值")),
    ),
    'rule_jutibuwz': (
        ('具体部位：{具体部位}', partial(is_all_have, expect="具体部位")),
    ),
    'rule_bldlyiwz': (
        ('白带异味：{白带异味}', partial(is_all_have, expect="白带异味")),
    ),
    'rule_zvgkxtya': (
        ('最高血压：{最高血压}', partial(is_all_have, expect="最高血压")),
    ),
    'rule_buwzlzbx': (
        ('部位类别：{部位类别}', partial(is_all_have, expect="部位类别")),
    ),
    'rule_zvgkubsoya': (
        ('最高收缩压：{最高收缩压}', partial(is_all_have, expect="最高收缩压")),
    ),
    'rule_zvgkuuvhya': (
        ('最高舒张压：{最高舒张压}', partial(is_all_have, expect="最高舒张压")),
    ),
    'rule_jutivgvd': (
        ('具体表现为{具体症状}', partial(is_all_have, expect="具体症状")),
    ),
    'rule_jwvsuijm': (
        ('加重{加重时间(非必填)}', partial(is_all_have, expect="加重时间(非必填)")),
    ),
    'rule_zvgkxtthvi': (
        ('最高血糖值：{最高血糖值}', partial(is_all_have, expect="最高血糖值")),
    ),
}

symptom_backfill_rule = {
    'common': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_fhuebuwz', 'rule_zvzkiuxmbuwz', 'rule_jutibuwz', 'rule_xyvi',
               'rule_yjse', 'rule_fazotedm', 'rule_qita', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '腹痛': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_xyvi', 'rule_fazotedm', 'rule_fhuebuwz_tgts', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '发热': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_yitmnztiwen', 'rule_tiwf', 'rule_zvgktiwf', 'rule_bjsvvgvd'],
    '咳嗽': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_ynse', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '排尿困难、尿潴留': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_bjsvvgvd'],
    '体重增加': ['rule2', 'rule_jwvsuijm', 'rule_titl', 'rule_tivszgjw', 'rule_bjsvvgvd'],
    '体重下降': ['rule2', 'rule_jwvsuijm', 'rule_tivsxwjd', 'rule_bjsvvgvd'],
    '尿失禁': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_bjsvvgvd'],
    '恶心': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '腹泻': ['rule1', 'rule_jwvsuijm', 'rule_dabmyjse', 'rule_dabmxyvd', 'rule_plbmpnci', 'rule_bjsvvgvd'],
    '便秘': ['rule1', 'rule_jwvsuijm', 'rule_bcxmxyui', 'rule_plbmpnci', 'rule_bjsvvgvd'],
    '咽痛': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_xyvi', 'rule_fazotedm', 'rule_bjsvvgvd'],
    '肉眼血尿': ['rule1', 'rule_jwvsuijm', 'rule_yjse', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_bjsvvgvd'],
    '口臭': ['rule1', 'rule_jwvsuijm', 'rule_qiwz', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '烧心': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '月经异常': ['rule1', 'rule_jwvsuijm', 'rule_jutivgvd', 'rule_bjsvvgvd'],
    '尿频尿急尿痛': ['rule3', 'rule_jwvsuijm', 'rule_jutivgvd', 'rule_ncyeyjse', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_ncld', 'rule_plncpnci', 'rule_bjsvvgvd'],
    '腹胀': ['rule1', 'rule_jwvsuijm', 'rule_xyvi', 'rule_fazotedm', 'rule_bjsvvgvd'],
    '胸痛': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_fhuebuwz', 'rule_xyvi', 'rule_fazotedm', 'rule_mzcifazouijm', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '腰背痛': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_xyvi', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '咯血': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_bjsvvgvd'],
    '失眠': ['rule1', 'rule_jwvsuijm', 'rule_bcxmxyui', 'rule_pnci', 'rule_bjsvvgvd'],
    '水肿': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_zvzkiuxmbuwz', 'rule_xyvi', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '头痛': ['rule1', 'rule_jwvsuijm', 'rule_buwz', 'rule_xyvi', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '头晕': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_bjsvvgvd'],
    '疲劳': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_hrjxynsu', 'rule_bjsvvgvd'],
    '咽部异物感': ['rule1', 'rule_jwvsuijm', 'rule_xyvi', 'rule_fazotedm', 'rule_bjsvvgvd'],
    '心悸': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '便血': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_bjsvvgvd'],
    '食欲不振': ['rule1', 'rule_jwvsuijm', 'rule_uild', 'rule_bjsvvgvd'],
    '血糖升高': ['rule1', 'rule_jwvsuijm', 'rule_zvgkxtthvi', 'rule_fazotedm', 'rule_xtthvi', 'rule_bjsvvgvd'],
    '血糖降低': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_xtthvi', 'rule_bjsvvgvd'],
    '反酸': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_bjsvvgvd'],
    '吞咽困难': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_bjsvvgvd'],
    '皮肤瘙痒': ['rule1', 'rule_jwvsuijm', 'rule_xyvi', 'rule_fazotedm', 'rule_bjsvvgvd'],
    '血压升高': ['rule1', 'rule_jwvsuijm', 'rule_fazotedm', 'rule_zvgkubsoya', 'rule_zvgkuuvhya', 'rule_zvgkxtya', 'rule_bjsvvgvd'],
    '关节痛': ['rule1', 'rule_jwvsuijm', 'rule_buwzlzbx', 'rule_jutibuwz', 'rule_xyvi', 'rule_fazotedm', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
    '白带异常': ['rule1', 'rule_jwvsuijm', 'rule_xyvi', 'rule_bldlyiwz', 'rule_bjsvvgvd'],
    '呼吸不畅（胸闷、气喘、喘憋）': ['rule3', 'rule_xyvi', 'rule_fazotedm', 'rule_bcxmxyui', 'rule_mzcifazouijm', 'rule_hrjxynsu', 'rule_jwvsynsu', 'rule_bjsvvgvd'],
}
