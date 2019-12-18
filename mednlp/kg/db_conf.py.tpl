#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
db_conf.py -- the db field conf

Author: maogy <maogy@guahao.com>
Create on 2019-02-12 Tuesday.
"""


disease = {
    'relation': {
        '${DISEASE_DISEASE_PATERNITY_RELATION}': 'disease_disease_paternity_relation',
        '${DISEASE_SYMPTOM_CLINICAL_RELATION}': 'disease_symptom_clinical_relation',
        '${DISEASE_PHYSICAL_EXAMINATION_CLINICAL_RELATION}': 'disease_physical_examination_clinical_relation',
        '${DISEASE_INSPECTION_FILTER_RELATION}': 'disease_inspection_filter_relation',
        '${DISEASE_EXAMINATION_FILTER_RELATION}': 'disease_examination_filter_relation',
        '${COMMON_PREPARATION_DISEASE_INDICATION_RELATION}': 'common_preparation_disease_indication_relation',
        '${COMMON_PREPARATION_DISEASE_CONTRAINDICATION_RELATION}': 'common_preparation_disease_contraindication_relation'
    },
    'label': {
        '${DISEASE_LABEL_DISEASE_ID}': 'disease_id',
        '${DISEASE_LABEL_DISEASE_ALIAS}': 'alias_disease_id',
        '${DISEASE_LABEL_DISEASE_COMMON_NAME}': 'common_disease_id'
    },
    'attribute': {
        '${DISEASE_ATT_CRITICAL}': 'is_critical',
        '${DISEASE_ATT_IMPOSSIBLE_PART}': 'impossible_part',
        '${DISEASE_ATT_MALE_RATE}': 'male_rate',
        '${DISEASE_ATT_FEMALE_RATE}': 'female_rate',
        '${DISEASE_ATT_AGE_SCOPE_1_RATE}': 'age_scope_1_rate',
        '${DISEASE_ATT_AGE_SCOPE_2_RATE}': 'age_scope_2_rate',
        '${DISEASE_ATT_AGE_SCOPE_3_RATE}': 'age_scope_3_rate',
        '${DISEASE_ATT_AGE_SCOPE_4_RATE}': 'age_scope_4_rate',
        '${DISEASE_ATT_AGE_SCOPE_5_RATE}': 'age_scope_5_rate',
        '${DISEASE_ATT_AGE_SCOPE_6_RATE}': 'age_scope_6_rate',
        '${DISEASE_ATT_COMMON_WEIGHT}': 'common_weight'
    }
}

inspection = {
    'relation': {
        '${DISEASE_INSPECTION_FILTER_RELATION}': 'disease_inspection_filter_relation'
    },
    'attribute': {
        '${INSP_ATTR_UNIT}': 'unit',
        '${INSP_ATTR_SHORT_NAME}': 'short_name',
        '${INSP_ATTR_CRITERION_NAME}': 'criterion_name',
        '${INSP_ATTR_RAISE}': 'raise_explanation',
        '${INSP_ATTR_DOWN}': 'down_explanation',
        '${INSP_ATTR_OBVIOUS_RAISE}': 'obvious_raise_explanation',
        '${INSP_ATTR_OBVIOUS_DOWN}': 'obvious_down_explanation',
        '${INSP_ATTR_NEGATIVE}': 'negative_explanation',
        '${INSP_ATTR_POSITIVE}': 'positive_explanation',
        '${INSP_ATTR_SUSPICIOUS_POSITIVE}': 'suspicious_positive_explanation',
        '${INSP_ATTR_MODERATE_POSITIVE}': 'moderate_positive_explanation',
        '${INSP_ATTR_STRONG_POSITIVE}': 'strong_positive_explanation',
        '${INSP_ATTR_STANDARD_VALUE}': 'standard_value_explanation',
        '${INSP_ATTR_ACCELERATE}': 'accelerate_explanation',
        '${INSP_ATTR_SLOWER}': 'slower_explanation',
        '${INSP_ATTR_RAISE_ADVICE}': 'raise_advice',
        '${INSP_ATTR_DOWN_ADVICE}': 'down_advice',
        '${INSP_ATTR_OBVIOUS_RAISE_ADVICE}': 'obvious_raise_advice',
        '${INSP_ATTR_OBVIOUS_DOWN_ADVICE}': 'obvious_down_advice',
        '${INSP_ATTR_NEGATIVE_ADVICE}': 'negative_advice',
        '${INSP_ATTR_POSITIVE_ADVICE}': 'positive_advice',
        '${INSP_ATTR_SUSPICIOUS_POSITIVE_ADVICE}': 'suspicious_positive_advice',
        '${INSP_ATTR_MODERATE_POSITIVE_ADVICE}': 'moderate_positive_advice',
        '${INSP_ATTR_STRONG_POSITIVE_ADVICE}': 'strong_positive_advice',
        '${INSP_ATTR_STANDARD_VALUE_ADVICE}': 'standard_value_advice',
        '${INSP_ATTR_ACCELERATE_ADVICE}': 'accelerate_advice',
        '${INSP_ATTR_SLOWER_ADVICE}': 'slower_advice',
        '${INSP_ATTR_NORMAL}': 'normal_explanation'
    },

}

examination = {
    'relation': {
        '${DISEASE_EXAMINATION_FILTER_RELATION}': 'disease_examination_filter_relation'
    },
    'attribute': {

    },

}

physical_examination = {
    'relation': {
        '${DISEASE_PHYSICAL_EXAMINATION_CLINICAL_RELATION}': 'disease_physical_examination_clinical_relation'
    },
    'attribute': {
        '${PHY_EXAM_ATTR_UNIT}': 'unit',
        '${PHY_EXAM_ATTR_LOW_WEIGHT}': 'low_weight_explanation',
        '${PHY_EXAM_ATTR_OVER_WEIGHT}': 'over_weight_explanation',
        '${PHY_EXAM_ATTR_FAT_WEIGHT}': 'fat_weight_explanation',
        '${PHY_EXAM_ATTR_ACCELERATE}': 'accelerate_explanation',
        '${PHY_EXAM_ATTR_SLOWER}': 'slower_explanation',
        '${PHY_EXAM_ATTR_RAISE}': 'raise_explanation',
        '${PHY_EXAM_ATTR_DOWN}': 'down_explanation',
        '${PHY_EXAM_ATTR_LOW_WEIGHT_ADVICE}': 'low_weight_advice',
        '${PHY_EXAM_ATTR_OVER_WEIGHT_ADVICE}': 'over_weight_advice',
        '${PHY_EXAM_ATTR_FAT_WEIGHT_ADVICE}': 'fat_weight_advice',
        '${PHY_EXAM_ATTR_ACCELERATE_ADVICE}': 'accelerate_advice',
        '${PHY_EXAM_ATTR_SLOWER_ADVICE}': 'slower_advice',
        '${PHY_EXAM_ATTR_RAISE_ADVICE}': 'raise_advice',
        '${PHY_EXAM_ATTR_DOWN_ADVICE}': 'down_advice',
        '${PHY_EXAM_ATTR_NORMAL}': 'normal_explanation'
    }
}

prescribing_behavior = {
    'label': {
        '${PRESCRIBE_ID}': 'sku_id'
    }
}

common_preparation = {
    'relation': {
        '${COMMON_PREPARATION_DISEASE_INDICATION_RELATION}': 'common_preparation_disease_indication_relation',
        '${COMMON_PREPARATION_DISEASE_CONTRAINDICATION_RELATION}': 'common_preparation_disease_contraindication_relation'
    },
    'label': {
        '${MEDICINE_ID}': 'med_id'
    }
}

medicine = {
    'relation': {
        '${COMMON_PREPARATION_MEDICINE_RELATION}': 'common_preparation_medicine_relation'
    },
    'attribute': {
        '${MED_ATT_DOSAGE}': 'dosage',
        '${MED_ATT_DOSAGE_UNIT}': 'dosage_unit',
        '${MED_ATT_DOSAGING_FREQIEMCY}': 'dosing_frequency',
        '${MED_ATT_ADM_ROUTE}': 'administration_route',
        '${MED_ATT_ADM_DURATION}': 'administration_duration',
        '${MED_ATT_ADM_DURATION_UNIT}': 'administration_duration_unit',
        '${MED_ATT_PACKAGE_QUANTITY}': 'package_quantity',
        '${MED_ATT_PACKAGE_UNIT}': 'package_unit'
    }
}

standard_department = {
    'label': {

    },
    'attribute': {

    },
    'relation': {
        '${DEPARTMENT_SYMPTOM_COMMON_RELATION}': 'department_symptom_common_relation'
    }
}

symptom = {
    'label': {
        # '${SYMPTOM_ID}': 'symptom_id',
        # '${SYMPTOM_RULE_ID}': 'symptom_id'
    },
    'attribute': {
        '${SYMPTOM_ATTR_IS_COMMON}': 'is_common',
        '${SYMPTOM_ATTR_COMMON_WEIGHT}': 'common_weight'
    },
    'relation': {
        '${DISEASE_SYMPTOM_CLINICAL_RELATION}': 'disease_symptom_clinical_relation',
        '${SYMPTOM_BODY_PART_RELATION}': 'symptom_body_part_relation',
        '${DEPARTMENT_SYMPTOM_COMMON_RELATION}': 'department_symptom_common_relation'
    }
}

tcm_disease = {
    'label': {

    },
    'attribute': {
        '${TCM_DISEASE_ATT_MALE_RATE}': 'male_rate',
        '${TCM_DISEASE_ATT_FEMALE_RATE}': 'female_rate'
    },
    'relation': {
        '${DISEASE_SYNDROME_TCM_RELATION}': 'disease_syndrome_tcm_relation'
    }
}

tcm_syndrome = {
    'label': {

    },
    'attribute': {

    },
    'relation': {
        '${DISEASE_SYNDROME_TCM_RELATION}': 'disease_syndrome_tcm_relation'
    }
}

tcm_prescription = {
    'label': {

    },
    'attribute': {
        '${TCM_PRESCRIPTION_ATTR_CRITERION_NAME}': 'criterion_name',
    },
    'relation': {

    }
}

disease_syndrome = {
    'label': {

    },
    'attribute': {
        '${DISEASE_SYNDROME_ATTR_CRITERION_NAME}': 'criterion_name',
    },
    'relation': {
        '${DISEASE_SYNDROME_DISEASE_RELATION}': 'disease_syndrome_disease_relation',
        '${DISEASE_SYNDROME_SYNDROME_RELATION}': 'disease_syndrome_syndrome_relation'
    }
}

treatment_plan = {
    'relation': {
        '${TREATMENT_PLAN_DISEASE_RELATION}': 'treatment_plan_disease_relation',
        '${TREATMENT_PLAN_DISEASE_ACCOMPANY_RELATION}': 'treatment_plan_disease_accompany_relation',
        '${TREATMENT_PLAN_COMMON_PREPARATION_RELATION}': 'treatment_plan_common_preparation_relation'
    }
}

human_body = {
    'relation': {
        '${SYMPTOM_BODY_PART_RELATION}': 'symptom_body_part_relation'
    }
}

medicine_atc_dir = {
    'label': {

    },
    'attribute': {
        '${MEDICINE_ATC_DIR_ATTR_DIR_LEVEL}': 'dir_level'
    },
    'relation': {

    }
}

db_conf = {
    'disease': disease,
    'inspection': inspection,
    'examination': examination,
    'physical_examination': physical_examination,
    'prescribing_behavior': prescribing_behavior,
    'common_preparation': common_preparation,
    'medicine': medicine,
    'human_body': human_body,
    'standard_department': standard_department,
    'medicine_atc_dir': medicine_atc_dir,
    'tcm_disease': tcm_disease,
    'tcm_syndrome': tcm_syndrome,
    'tcm_prescription': tcm_prescription,
    'disease_syndrome': disease_syndrome,
    'treatment_plan': treatment_plan,
    'symptom': symptom
}

entity_type_dict = {
    '${ENTITY_DISEASE_TYPE}': 'disease',
    '${ENTITY_INSPECTION_TYPE}': 'inspection',
    '${ENTITY_HOSPITAL_TYPE}': 'hospital',
    '${ENTITY_PHYSICAL_EXAMINATION_TYPE}': 'physical_examination',
    '${ENTITY_PRESCRIBE_TYPE}': 'prescribing_behavior',
    '${ENTITY_COMMON_MEDICINE_TYPE}': 'common_preparation',
    '${ENTITY_MEDICINE_TYPE}': 'medicine',
    '${ENTITY_TREATMENT_TYPE}': 'treatment',
    '${ENTITY_HUMAN_BODY_TYPE}': 'human_body',
    '${ENTITY_STANDARD_DEPARTMENT_TYPE}': 'standard_department',
    '${ENTITY_EXAMINATION_TYPE}': 'examination',
    '${ENTITY_CROWD_TYPE}': 'crowd',
    '${ENTITY_MEDICINE_COMPOSITION_TYPE}': 'drug_composition',
    '${ENTITY_MANUFACTURER_TYPE}': 'manufacturer',
    '${ENTITY_MEDICINE_MANUFACTURER_TYPE}': 'drug_manufacturer',
    '${ENTITY_DRUG_PRODUCT_TYPE}': 'drug_product',
    '${ENTITY_DOSAGE_FORM_TYPE}': 'dosage_form',
    '${ENTITY_MEDICINE_ATC_DIR_TYPE}': 'medicine_atc_dir',
    '${ENTITY_TCM_DISEASE_TYPE}': 'tcm_disease',
    '${ENTITY_TCM_SYNDROME_TYPE}': 'tcm_syndrome',
    '${ENTITY_TCM_PRESCRIPTION_TYPE}': 'tcm_prescription',
    '${ENTITY_TCM_DRUG_TYPE}': 'tcm_drug',
    '${ENTITY_DISEASE_SYNDROME_TYPE}': 'disease_syndrome',
    '${ENTITY_TREATMENT_PLAN_TYPE}': 'treatment_plan',
    '${ENTITY_ALLERGIC_TYPE}': 'allergic',
    '${ENTITY_SYMPTOM_TYPE}': 'symptom'
}


medical_knowledge = {
    'disease_type': {
        '2': ['${LABEL_ORIGINAL_TCM_DISEASE}']
    }
}


entity_label_dict = {
    'past_medical_history': '${ENTITY_PAST_MEDICAL_HISTORY_TYPE}',
    'family_history': '${ENTITY_FAMILY_HISTORY_TYPE}',
    'surgical_history': '${ENTITY_SURGICAL_HISTORY_TYPE}',
    'trauma_history': '${ENTITY_TRAUMA_HISTORY_TYPE}',
    'allergy_history': '${ENTITY_ALLERGEY_HISTORY_TYPE}',
}

