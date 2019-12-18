#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
index_medical_relation.py -- the index tool of medical relation

Author: maogy <maogy@guahao.com>
Create on 2017-07-07 Friday.
"""


import datetime
from base_index import BaseIndex
from ailib.storage.db import DBWrapper
# from config.sql_config import SQL_CONFIG
# import helper
import cdss.global_conf as global_conf
# import Data
# import wylib.index.wy_data as wy_data


class IndexMedicalRelation(BaseIndex):

    index_filename = 'medical_relation.xml'
    core = 'medical_relation'

    def initialise(self, **kwargs):
        self.db = DBWrapper(self.cfg_path, 'mysql', 'AIMySQLDB')

    def get_data(self):
        sql = """
        SELECT
            concat(ri.entity_id_a,'_',ri.entity_id_b,'_',ri.type) relation_id,
            ri.entity_id_a,
            d.name entity_name_a,
            ri.entity_id_b,
            s.name entity_name_b,
            ri.weight,
            ri.type
        FROM ai_medical_knowledge.relation_info ri
        LEFT JOIN ai_medical_knowledge.disease d ON d.id=ri.entity_id_a AND d.state=1
        LEFT JOIN ai_medical_knowledge.symptom s ON s.id=ri.entity_id_b AND s.state=1
        WHERE ri.state=1
        """
        relations = self.db.get_rows(sql)
        return relations

    def process_data(self, docs):
        return docs


if __name__ == "__main__":
    indexer = IndexMedicalRelation(global_conf, dev=True)
    indexer.index()
