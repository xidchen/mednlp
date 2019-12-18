#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
sql_config.py -- some sql

Author: maogy
Create on 2016-12-19 Monday.
"""

SQLS = {
    'mmseg': {
        'disease': """
        SELECT
            d.disease_uuid id,
            d.disease_name name
        FROM medical_kg.disease d
        WHERE d.is_deleted=0 AND d.sort_code=0
        UNION SELECT
            da.disease_uuid id,
            da.alias name
        FROM medical_kg.disease_alias da
        JOIN medical_kg.disease d ON d.disease_uuid=da.disease_uuid
        WHERE d.is_deleted=0 AND d.sort_code=0
        """,
        'disease_all': """
        SELECT
            d.id,
            d.name
        FROM medical_knowledge.disease d
        WHERE d.state=1 AND d.sort_code=0
        UNION
        SELECT
            da.disease_uuid id,
            da.alias name
        FROM medical_knowledge.disease_alias da
        INNER JOIN medical_knowledge.disease d ON d.id=da.disease_uuid
        """,
        'symptom': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.symptom s
        WHERE s.is_deleted=0
        """,
        'symptom_wy': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.symptom s
        WHERE s.is_deleted=0 AND s.`source`=1
        """,
        'symptom_all': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.symptom s
            ON s.symptom_uuid=ri.entity_id_b AND ri.relation_type=3000 AND s.is_deleted=0
        WHERE ri.relation_type=3000 AND ri.is_deleted=0
        GROUP BY ri.entity_id_b
        """,
        'synonym': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.symptom s ON s.symptom_uuid=ri.entity_id_b AND s.is_deleted=0
        WHERE ri.relation_type=9001 AND ri.is_deleted=0 
        UNION
        SELECT
            bp.body_part_uuid id,
            bp.body_part_name name
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.body_part bp ON bp.body_part_uuid=ri.entity_id_b AND bp.is_deleted=0
        WHERE ri.relation_type=9002 AND ri.is_deleted=0

        """,
        'body_part': """
        SELECT
            bp.body_part_uuid id,
            bp.body_part_name name
        FROM medical_kg.body_part bp
        WHERE bp.is_deleted=0
        """,
        'doctor': """
        SELECT
            eb.ID id,
            eb.NAME name
        FROM HRS_STD.EXPERT_BASIC eb
        WHERE eb.STATE=0 AND eb.SWITCH_STATE=0
        """,
        'std_department': """
        SELECT
            sd.id id,
            sd.name name
        FROM hrs_std.std_department sd
        where sd.state=0
        UNION 
        SELECT
            sda.std_dept_id id,
            sda.std_dept_alias name
        FROM hrs_std.std_department_alias sda
        """,
        'hospital_department': """
        SELECT
            hdb.id id,
            hdb.name
        FROM hrs_std.hosp_dept_basic hdb
        WHERE hdb.name LIKE '%科' OR hdb.name LIKE '%门诊'
            OR hdb.name LIKE '%中心'
        GROUP BY hdb.name
        HAVING count(hdb.id) > 1
        """,
        'hospital': """
        SELECT
            hb.ID id,
            hb.NAME name
        FROM HRS_STD.HOSPITAL_BASIC hb
        WHERE hb.STATE=0 AND hb.SWITCH_STATE=0
        UNION
        SELECT
            ha.hospital_id id,
            ha.alias name
        FROM hrs_std.hospital_alias ha
        INNER JOIN hrs_std.hospital_basic hb on hb.id=ha.hospital_id
            AND hb.STATE=0 AND hb.SWITCH_STATE=0
        UNION
        SELECT 
            hb.ID id,
            hb.short_name name
        FROM HRS_STD.HOSPITAL_BASIC hb
        WHERE hb.STATE=0 AND hb.SWITCH_STATE=0 AND hb.short_name <> ''
        """,
        'treatment': """
        SELECT
            treatment.id id,
            treatment.name name
        FROM medical_knowledge.treatment as treatment
        WHERE treatment.state = 1 
        """,

        'medicine': """
        SELECT
            common_preparation.id id,
            common_preparation.name name
        FROM medicine.common_preparation as common_preparation
        """,

        'area': """
        SELECT
            area_info.id id,
            area_info.area_name name
        FROM hrs_std.area_info as area_info
        UNION
        SELECT
            999999 id,
            '全国' name
        """
        # 'disease': """
        # SELECT
        #     d.disease_uuid id,
        #     d.disease_name name
        # FROM medical_kg.disease d
        # WHERE d.is_deleted=0 AND d.sort_code=0
        # UNION SELECT
        #     da.disease_uuid id,
        #     da.alias name
        # FROM medical_kg.disease_alias da
        # JOIN medical_kg.disease d ON d.disease_uuid=da.disease_uuid
        # WHERE d.is_deleted=0 AND d.sort_code=0
        # """,
        # 'symptom': """
        # SELECT
        #     s.symptom_uuid id,
        #     s.symptom_name name
        # FROM medical_kg.symptom s
        # WHERE s.is_deleted=0
        # """,
        # 'symptom_wy': """
        # SELECT
        #     s.symptom_uuid id,
        #     s.symptom_name name
        # FROM medical_kg.symptom s
        # WHERE s.is_deleted=0 AND s.`source`=1
        # """,
        # 'symptom_all': """
        # SELECT
        #     s.symptom_uuid id,
        #     s.symptom_name name
        # FROM medical_kg.relation_info ri
        # INNER JOIN medical_kg.symptom s
        #     ON s.symptom_uuid=ri.entity_id_b AND ri.relation_type=3000 AND s.is_deleted=0
        # WHERE ri.relation_type=3000 AND ri.is_deleted=0
        # GROUP BY ri.entity_id_b
        # """,
        # 'symptom_synonym_group': """
        # SELECT
        #     GROUP_CONCAT(DISTINCT ri.entity_id_a) id,
        #     s.name
        # FROM ai_medical_knowledge.relation_info ri
        # INNER JOIN ai_medical_knowledge.symptom s
        #     ON s.id=ri.entity_id_b AND ri.`type`=3000 AND ri.state=1
        # WHERE ri.`type`=3000 AND ri.state=1
        # GROUP BY ri.entity_id_b
        # """,
        # 'body_part': """
        # SELECT
        #     bp.body_part_uuid id,
        #     bp.body_part_name name
        # FROM medical_kg.body_part bp
        # WHERE bp.is_deleted=0
        # """,
    },
    # 'synonym': {
    #     'symptom': """
    #     SELECT
    #         ri.entity_id_a group_id,
    #         ri.entity_id_b synonym_id
    #     FROM medical_kg.relation_info ri
    #     WHERE ri.relation_type=3000 AND ri.is_deleted=0 AND ri.entity_id_a IS NOT NULL
    #         AND ri.entity_id_b IS NOT NULL
    #     """,
    #     'synonym': """
    #     SELECT
    #         ri.entity_id_a group_id,
    #         ri.entity_id_b synonym_id
    #     FROM medical_kg.relation_info ri
    #     WHERE ri.is_deleted=0 AND ri.relation_type=9000
    #     """,
    #     'wy_symptom': """
    #     SELECT
    #         ri.entity_id_a group_id,
    #         ri.entity_id_b synonym_id
    #     FROM medical_kg.relation_info ri
    #     WHERE ri.relation_type=9001 AND ri.is_deleted=0
    #     """,
    #     'wy_symptom_name': """
    #     SELECT
    #         ri.entity_id_a group_id,
    #         s.symptom_name synonym_id
    #     FROM medical_kg.relation_info ri
    #     INNER JOIN medical_kg.symptom s ON s.symptom_uuid=ri.entity_id_b AND s.is_deleted=0
    #     WHERE ri.relation_type=9001 AND ri.is_deleted=0
    #     """
    # },
    'synonym': {
        'symptom': """
        SELECT
            ri.entity_id_a name,
            ri.entity_id_b id
        FROM medical_kg.relation_info ri
        WHERE ri.relation_type=3000 AND ri.is_deleted=0 AND ri.entity_id_a IS NOT NULL
            AND ri.entity_id_b IS NOT NULL
        """,
        'synonym': """
        SELECT
            ri.entity_id_a name,
            ri.entity_id_b id
        FROM medical_kg.relation_info ri
        WHERE ri.is_deleted=0 AND ri.relation_type=9000
        """,
        'wy_symptom': """
        SELECT
            ri.entity_id_a name,
            ri.entity_id_b id
        FROM medical_kg.relation_info ri
        WHERE ri.relation_type=9001 AND ri.is_deleted=0
        """,
        'wy_symptom_name': """
        SELECT
            ri.entity_id_a name,
            s.symptom_name id
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.symptom s ON s.symptom_uuid=ri.entity_id_b AND s.is_deleted=0
        WHERE ri.relation_type=9001 AND ri.is_deleted=0
        UNION
        SELECT
            ri.entity_id_a name,
            bp.body_part_name id
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.body_part bp ON bp.body_part_uuid=ri.entity_id_b AND bp.is_deleted=0
        WHERE ri.relation_type=9002 AND ri.is_deleted=0
        """
    }, 
    'file_update': {
        'disease': """
        SELECT
            d.disease_uuid id,
            d.disease_name name
        FROM medical_kg.disease d
        WHERE d.is_deleted=0 AND d.sort_code=0
        UNION SELECT
            da.disease_uuid id,
            da.alias name
        FROM medical_kg.disease_alias da
        JOIN medical_kg.disease d ON d.disease_uuid=da.disease_uuid
        WHERE d.is_deleted=0 AND d.sort_code=0
        """,
        'symptom': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.symptom s
        WHERE s.is_deleted=0
        """,
        'symptom_wy': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.symptom s
        WHERE s.is_deleted=0 AND s.`source`=1
        """,
        'symptom_all': """
        SELECT
            s.symptom_uuid id,
            s.symptom_name name
        FROM medical_kg.relation_info ri
        INNER JOIN medical_kg.symptom s
            ON s.symptom_uuid=ri.entity_id_b AND ri.relation_type=3000 AND s.is_deleted=0
        WHERE ri.relation_type=3000 AND ri.is_deleted=0
        GROUP BY ri.entity_id_b
        """,
        'symptom_synonym_group': """
        SELECT
            GROUP_CONCAT(DISTINCT ri.entity_id_a) id,
            s.name
        FROM ai_medical_knowledge.relation_info ri
        INNER JOIN ai_medical_knowledge.symptom s
            ON s.id=ri.entity_id_b AND ri.`type`=3000 AND ri.state=1
        WHERE ri.`type`=3000 AND ri.state=1
        GROUP BY ri.entity_id_b
        """,
        'body_part': """
        SELECT
            bp.body_part_uuid id,
            bp.body_part_name name
        FROM medical_kg.body_part bp
        WHERE bp.is_deleted=0
        """,
    },

    'mmseg_kg': {
        "disease":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'disease'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        "symptom_wy":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'zsyr0fqA'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        "body_part":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'FVB1BY33'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        "std_department":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = '7DfztjJp'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        "hospital_department":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'c70sXkL0'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        "treatment":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'dJS9RSy0'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        # "medicine":"""
        # SELECT a.entity_uuid id, a.entity_name name FROM ai_union.entity a
        # INNER JOIN
        # (SELECT entity_uuid FROM ai_union.entity_label
        # WHERE label_type = 'HDfAgluJ' AND entity_type='lmEBBpOn' AND is_deleted = 0) b
        # ON a.entity_uuid = b.entity_uuid
        # """, #利用线上的medicine更新字典
        # "hospital":"""
        # SELECT a.entity_uuid id, a.entity_name name FROM ai_union.entity a
        # INNER JOIN
        # (SELECT entity_uuid FROM ai_union.entity_label
        # WHERE label_type = 'HDfAgluJ' AND entity_type='VCIqE8AF' AND is_deleted = 0) b
        # ON a.entity_uuid = b.entity_uuid
        # """,  #利用线上的hospital更新字典
        "examination":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'oFw6zran'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        "physical":"""
        SELECT
            a.entity_uuid id,
            a.entity_name name
        FROM
            ai_union.entity a
        INNER JOIN (
            SELECT
                entity_uuid
            FROM
                ai_union.entity_label
            WHERE
                label_type = 'HDfAgluJ'
            AND entity_type = 'PrN1tM6l'
            AND is_deleted = 0
        ) b ON a.entity_uuid = b.entity_uuid
        """,
        'doctor': """
        SELECT
            eb.ID id,
            eb.NAME name
        FROM HRS_STD.EXPERT_BASIC eb
        WHERE eb.STATE=0 AND eb.SWITCH_STATE=0
        """,
        'area': """
        SELECT
            area_info.id id,
            area_info.area_name name
        FROM hrs_std.area_info as area_info
        UNION
        SELECT
            999999 id,
            '全国' name
        """,
        'medicine': """
        SELECT
            common_preparation.id id,
            common_preparation.name name
        FROM medicine.common_preparation as common_preparation
        """,
        'hospital': """
        SELECT
            hb.ID id,
            hb.NAME name
        FROM HRS_STD.HOSPITAL_BASIC hb
        WHERE hb.STATE=0 AND hb.SWITCH_STATE=0
        UNION
        SELECT
            ha.hospital_id id,
            ha.alias name
        FROM hrs_std.hospital_alias ha
        INNER JOIN hrs_std.hospital_basic hb on hb.id=ha.hospital_id
            AND hb.STATE=0 AND hb.SWITCH_STATE=0
        UNION
        SELECT
            hb.ID id,
            hb.short_name name
        FROM HRS_STD.HOSPITAL_BASIC hb
        WHERE hb.STATE=0 AND hb.SWITCH_STATE=0 AND hb.short_name <> ''
        """
    }
}
