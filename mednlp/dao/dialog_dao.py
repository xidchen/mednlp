#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dialog_dao.py -- the dao of dialog service

Author: maogy <maogy@guahao.com>
Create on 2018-10-01 Monday.
"""


def load_dialog_conf(db, organization):
    """
    从配置数据库加载指定机构的配置.
    """
    intention_sql = """
    SELECT
        aoi.id,
        aoi.intention,
        aoi.is_diy_config is_custom,
        aoi.answer_tips answer
    FROM ai_union.access_org_intention aoi
    WHERE aoi.intention_status=1 AND aoi.org_code='%(org_id)s'
    """
    rows = db.get_rows(intention_sql % {'org_id': organization})
    conf_intentions = set()
    conf = {}
    intention_dict = {}
    for row in row_to_str(rows):
        if not row['intention']:
            continue
        intention_dict[row['id']] = row['intention']
        intention_conf = conf.setdefault(row['intention'], {})
        if row['is_custom'] == 1:
            conf_intentions.add(str(row['id']))
            intention_conf['is_custom'] = row['is_custom']
        #conf_intentions.add(str(row['id']))
        #intention_conf['is_custom'] = row['is_custom']
            answer_conf = intention_conf.setdefault('answer', {})
            answer_conf['text'] = row['answer']
            answer_conf['conf_id'] = row['id'] 
    if not conf_intentions:
        return conf
    biz_id = set([str(b_id) for b_id in intention_dict.keys()])
    print('conf intention:' + str(conf_intentions))
    card_conf = load_card_conf(db, conf_intentions)
    for intention_id, card_conf_item in card_conf.items():
        intention_name = intention_dict[intention_id]
        conf[intention_name]['card'] = card_conf_item
        biz_id.add(str(card_conf_item['conf_id']))
    out_link_conf = load_out_link_conf(db, conf_intentions)
    for intention_id, out_link_conf_intention in out_link_conf.items():
        intention_name = intention_dict[intention_id]
        conf[intention_name]['out_link'] = out_link_conf_intention
        for out_link_conf_item in out_link_conf_intention['conf']:
            biz_id.add(str(out_link_conf_item['conf_id']))
    biz_conf = load_biz_dic(db, biz_id)
    item_dict = {'answer': ['answerTips', 'answerUrl'],
                 'card': ['cardUrl', 'cardContent'],
                 'out_link': ['button']}
    for intention_conf in conf.values():
        for item_name, biz_fields in item_dict.items():
            item_confs = intention_conf.get(item_name)
            if not item_confs:
                continue
            if item_name == 'out_link':
                item_confs = item_confs['conf']
            else:
                item_confs = [item_confs]
            for item_conf in item_confs:
                if not item_conf:
                    continue
                conf_id = item_conf.get('conf_id')
                if not conf_id:
                    continue
                biz_value = biz_conf.get(conf_id)
                if not biz_value:
                    continue
                for field in biz_fields:
                    biz = biz_value.get(field)
                    if biz:
                        item_conf.setdefault('biz_conf',biz).update(biz)
    return conf

def load_biz_dic(db, biz_id):
    """
    加载业务及关键词配置.
    """
    biz_sql = """
    SELECT
    	aoi.id AS biz_id,
    	abdr.rel_type,
	ad.dic_solr_name name          
    FROM                                                       
      ai_union.access_card_info aci                            
    INNER JOIN                                                  
      ai_union.access_org_intention aoi ON aoi.id = aci.intention_id
    INNER JOIN                                                  
      ai_union.access_biz_dic_rel abdr ON aci.id = abdr.biz_id 
    INNER JOIN
      ai_union.access_dic ad ON ad.id = abdr.dic_id            
    WHERE  aoi.id in %(biz)s 
    UNION
    SELECT
    	aoi.id AS biz_id,
    	abdr.rel_type,
	ad.dic_solr_name name 
    FROM
        ai_union.access_org_intention aoi
    INNER JOIN
        ai_union.access_url acu ON acu.intention_id = aoi.id
    INNER JOIN
        ai_union.access_biz_dic_rel abdr ON acu.id = abdr.biz_id
    INNER JOIN
        ai_union.access_dic ad ON ad.id = abdr.dic_id
        WHERE  aoi.id in %(biz)s 
    UNION
    SELECT
    	aoi.id AS biz_id,
    	abdr.rel_type,
	ad.dic_solr_name name 
	FROM
      ai_union.access_org_intention aoi
    INNER JOIN
      ai_union.access_biz_dic_rel abdr ON aoi.id = abdr.biz_id 
    INNER JOIN
      ai_union.access_dic ad ON ad.id = abdr.dic_id
     WHERE  aoi.id in %(biz)s 
	UNION
    SELECT
    	aoi.id AS biz_id,
    	abdr.rel_type,
	ad.dic_solr_name name  
    FROM
      ai_union.access_button_info abi
    INNER JOIN
      ai_union.access_org_intention aoi ON aoi.id = abi.intention_id
    INNER JOIN
      ai_union.access_biz_dic_rel abdr ON abi.id = abdr.biz_id 
    INNER JOIN
      ai_union.access_dic ad ON ad.id = abdr.dic_id
     WHERE  aoi.id in %(biz)s
    """
    rows = db.get_rows(biz_sql % {'biz': "(%s)" % ",".join(biz_id)})
    conf = {}
    for row in row_to_str(rows):
        biz_conf = conf.setdefault(row['biz_id'], {})
        dic_name = biz_conf.setdefault(row['rel_type'], set())
        dic_name.add(row['name'])
    return conf

        
def load_card_conf(db, intention_id):
    """
    加载卡片配置.
    """
    card_sql = """
    SELECT
        aci.card_type,
        aci.id,
        aci.intention_id
    FROM ai_union.access_card_info aci
    WHERE aci.intention_id in %(intention)s
    """
    rows = db.get_rows(
        card_sql % {'intention': "(%s)" % ",".join(intention_id)})
    conf = {}
    for row in row_to_str(rows):
        card_conf = conf.setdefault(row['intention_id'], {})
        card_conf['type'] = row['card_type']
        card_conf['conf_id'] = row['id']
    return conf


def load_out_link_conf(db, intention_id):
    """
    加载按钮配置.
    返回值->{intention:{'conf':[{'conf_id'}], 'is_db':1是,0否}}
    """
    out_link_sql = """
    SELECT
        abi.id,
        abi.intention_id
    FROM ai_union.access_button_info abi
    WHERE abi.intention_id in %(intention)s
    """
    rows = db.get_rows(
        out_link_sql % {'intention': "(%s)" % ",".join(intention_id)})
    conf = {}
    for row in row_to_str(rows):
        out_link_conf = conf.setdefault(row['intention_id'], {})
        out_link_list = out_link_conf.setdefault('conf', [])
        out_link_item = {'conf_id': row['id']}
        out_link_list.append(out_link_item)
        out_link_conf['is_db'] = 1
    return conf

def row_to_str(rows):
    rows_str = []
    for row in rows:
        item_dict = {}
        for key,value in row.items():
            if isinstance(value, bytes):
                item_dict[key] = str(value, encoding='utf-8')
            else:
                item_dict[key] = value
        rows_str.append(item_dict)
    return rows_str

if __name__ == '__main__':
    from ailib.storage.db import DBWrapper
    import global_conf
    database = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB', autocommit=True)
    result = load_dialog_conf(database, '123')
    print(result)
    print('aa')
