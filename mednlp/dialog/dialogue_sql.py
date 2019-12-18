# -*- coding: utf-8 -*-

SQL_CONFIG = {
    'organization': {
        # 根据orgCode获取configId
        'config_id': """
        SELECT
          robc.id,
          robc.hospital_source
        FROM ai_union.r_org_base_config robc, ai_union.r_org_auth roa
        WHERE
          roa.organize_code = '%(org_id)s'
          AND roa.is_deleted = 0
          AND roa.id = robc.org_auth_id
          AND robc.is_deleted = 0
          AND robc.app_status = 1;
        """,
        'hospital_relation': """
        SELECT
            hospital_uuid,
            doctor_source,
            is_map_department
        FROM ai_union.r_org_hospital_rel
        WHERE org_config_id = '%(config_id)s'
          AND is_deleted = 0
        """
    },
    'intention': {
        # 获取意图集合信息
        'intention_set': """
        SELECT
            ris.id,
            ris.intention_set_name,
            ris.is_unified_state,
            ris.is_catch_all_set
        FROM ai_union.r_intention_set ris
        WHERE
          ris.is_deleted = 0
          AND ris.is_open = 1
          AND ris.is_default_set = 0
          AND ris.org_config_id = '%(config_id)s'
        """,
        # 获取非默认意图子集合数据
        'sub_intention_set': """
        SELECT
            roi.intention_set_id,
            ris.intention_set_name,
            ris.is_unified_state,
            roi.id,
            roi.intention_code
        FROM ai_union.r_intention_set ris
        INNER JOIN ai_union.r_org_intention roi
          ON ris.id = roi.intention_set_id
        WHERE
          ris.is_deleted = 0
          AND ris.is_open = 1
          AND ris.is_default_set = 0
          AND ris.org_config_id = '%(config_id)s'
          AND roi.is_deleted = 0
        """,
        'sub_intention_default_set': """
        SELECT
            roi.intention_set_id,
            ris.intention_set_name,
            ris.is_unified_state,
            roi.id,
            roi.intention_code
        FROM ai_union.r_intention_set ris
        INNER JOIN ai_union.r_org_intention roi
          ON ris.id = roi.intention_set_id
        WHERE
          ris.is_deleted = 0
          AND ris.is_open = 1
          AND ris.is_default_set = 1
          AND ris.org_config_id = '%(config_id)s'
          AND roi.is_deleted = 0
          AND roi.intention_code= '%(intention_code)s'
        """
    },
    'card': {
        'base': """
          SELECT
            rc.id card_id,
            rc.card_type type,
            rc.intention_set_id,
            rcc.ai_field,
            rc.card_num
          FROM ai_union.r_card rc
          LEFT JOIN ai_union.r_card_content rcc
            ON rcc.card_id = rc.id
          WHERE
            rc.intention_set_id = '%(intention_set_id)s'
            AND rc.is_deleted = 0
            AND rcc.is_deleted = 0
        """
    },
    'answer': {
        'exception': """
        SELECT
            ra.answer_text,
            ra.answer_type
        FROM ai_union.r_answer ra
        WHERE
          ra.org_config_id = '%(config_id)s'
          AND ra.answer_type in (4,5,6)
          AND ra.is_deleted = 0
        """,
        # 正常文案
        'base': """
        SELECT
          ra.id answer_id,
          ra.answer_text text,
          ra.answer_type type,
          ra.intention_set_id
        FROM ai_union.r_answer ra
        WHERE
          ra.answer_type = 1
          AND ra.intention_set_id = '%(intention_set_id)s'
          AND ra.is_deleted=0
        """
    },
    'out_link': {
        'base': """
        SELECT
          ro.id out_link_id,
          ro.outlink_name name,
          ro.outlink_type type,
          ro.content text,
          ro.action,
          ro.outlink_start_location location,
          ro.biz_id,
          ro.relation,
          ro.intention_set_id
        FROM ai_union.r_outlink ro
        WHERE
          ro.is_deleted=0
          AND ro.intention_set_id = '%(intention_set_id)s'
        """
    },
    'keyword': {
        'base': """
        SELECT
          rk.id keyword_id,
          rk.keyword_start_location location,
          rk.content text,
          rk.ai_field,
          rk.biz_id,
          rk.relation,
          rk.intention_set_id
        FROM ai_union.r_keyword rk
        WHERE
          rk.is_deleted = 0
          AND rk.intention_set_id = '%(intention_set_id)s'
        """
    }
}
