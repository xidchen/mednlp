#!/usr/bin/python
#encoding=utf-8

import json
import pdb

class Configulation():


    answer_sql = """
    SELECT
      aoi.id, 
      aoi.answer_tips,
      GROUP_CONCAT(ad.dic_solr_name) AS dic_solr_name
    FROM
      ai_union.access_org_intention aoi
    LEFT JOIN
      ai_union.access_biz_dic_rel abdr ON aoi.id = abdr.biz_id and abdr.rel_type in ('answerTips')
    LEFT JOIN
      ai_union.access_dic ad ON ad.id = abdr.dic_id
    WHERE 1=1
      AND aoi.org_code = '%(org_id)s' AND aoi.intention = '%(intention)s'
    GROUP BY aoi.id
    """
    answer_url_sql = """
    SELECT 
    acu.id AS id,
    GROUP_CONCAT(ad.dic_solr_name) AS dic_solr_name
    FROM
    	ai_union.access_org_intention aoi
    INNER JOIN
    	ai_union.access_url acu ON acu.intention_id = aoi.id
    INNER JOIN
    	ai_union.access_biz_dic_rel abdr ON acu.id = abdr.biz_id
    INNER JOIN
    	ai_union.access_dic ad ON ad.id = abdr.dic_id
    WHERE
        aoi.org_code = '%(org_id)s'
	AND aoi.intention = '%(intention)s'
	AND abdr.rel_type = 'answerUrl'
    GROUP BY acu.id
    """
    card_sql = """
    SELECT 
      aci.card_type,
      aci.id,
      GROUP_CONCAT(ad.dic_solr_name) AS dic_solr_name
    FROM
      ai_union.access_card_info aci
    LEFT JOIN
      ai_union.access_org_intention aoi ON aoi.id = aci.intention_id
    LEFT JOIN
      ai_union.access_biz_dic_rel abdr ON aci.id = abdr.biz_id and abdr.rel_type in ('cardUrl', 'cardContent')
    LEFT JOIN
      ai_union.access_dic ad ON ad.id = abdr.dic_id
    WHERE 1=1
      AND aoi.org_code = '%(org_id)s' AND aoi.intention = '%(intention)s'
    GROUP BY aci.id
    """
    out_link_sql="""
    SELECT 
      abi.id,
      GROUP_CONCAT(ad.dic_solr_name) AS dic_solr_name
    FROM
      ai_union.access_button_info abi
    LEFT JOIN
      ai_union.access_org_intention aoi ON aoi.id = abi.intention_id
    LEFT JOIN
      ai_union.access_biz_dic_rel abdr ON abi.id = abdr.biz_id and abdr.rel_type='button' 
    LEFT JOIN
      ai_union.access_dic ad ON ad.id = abdr.dic_id
    WHERE 1=1
      AND aoi.org_code = '%(org_id)s' AND aoi.intention = '%(intention)s'
    GROUP BY abi.id  
    """


    def __init__(self, db):
        self.db = db
    	self.out_link = []
    	self.card = {}
    	self.answer = {}
	

    def load_data(self, input_params, intention):
        intention = intention
        org_id =  input_params.get('organization')

        card_sql = self.card_sql % {'intention': intention, 'org_id': org_id}
        card_rows = self.db.get_rows(card_sql)
	if card_rows:
	    self.card = card_rows[0]

        out_link_sql = self.out_link_sql % {'intention': intention, 'org_id': org_id}
        out_link_rows = self.db.get_rows(out_link_sql)
        if out_link_rows:
            self.out_link = out_link_rows
	
        answer_sql = self.answer_sql % {'intention': intention, 'org_id': org_id}
        answer_rows = self.db.get_rows(answer_sql)
	answer_url_sql = self.answer_url_sql % {'intention': intention, 'org_id': org_id}
	answer_url_rows = self.db.get_rows(answer_url_sql)
        if answer_rows:
	    self.answer['keyword_params'] = answer_rows[0]
	if answer_url_rows:
            self.answer['url_params'] = answer_url_rows

