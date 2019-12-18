#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sql_config.py -- of sql standardized_entity_name

Author: raogj <raogj@raogj.com>
Create on 2019-08-08.
"""

SQL_SEN = {
    'standard_name': {
        'standard_name_select': """
        SELECT 
            e.entity_name entity_name, 
            e.entity_type entity_type, 
            se.entity_name standard_name
        FROM 
            ai_union.entity e
        INNER JOIN ai_union.standard_entity se 
            ON e.standard_uuid=se.entity_uuid
        WHERE 
            e.is_delete=0 
            AND e.audit_status<>99
            AND ( e.entity_type='disease' OR e.entity_type='zsyr0fqA')
        """,
        'context_select': """
        SELECT 
            etd.context_id, 
            etd.context
        FROM 
            ai_opendata.wy_zny_examination_text_df etd
            LEFT JOIN ai_opendata.wy_zny_examination_to_entity_df eted
            ON etd.context_id=eted.context_id
        WHERE 
            etd.is_processed_id='0'
           AND eted.context_id IS NULL 
        """,
        'entity_insert': """
        INSERT INTO
            ai_opendata.wy_zny_examination_to_entity_df
        VALUES
        """,
        'status_update': """
        UPDATE  
            ai_opendata.wy_zny_examination_text_df
        SET 
            (is_processed_id, processed_time) = ('{status}', now())
        WHERE context_id IN
        """,
        'end_tag_delete': """
        DELETE  FROM
            ai_opendata.wy_zny_examination_to_entity_df
        WHERE
            context_id='end-tag'
        """
    }
}
