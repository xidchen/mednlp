#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
conf.py -- the configure of kg

Author: maogy <maogy@guahao.com>
Create on 2019-02-11 Monday.
"""


disease_conf = {
    'relation': {
        'disease_disease_paternity_relation': {'type': '_ss'},
        'disease_symptom_clinical_relation': {'type': '_ss'},
        'disease_physical_examination_clinical_relation': {'type': '_ss'},
        'disease_inspection_filter_relation': {'type': '_ss'},
        'disease_examination_filter_relation': {'type': '_ss'},
        'common_preparation_disease_indication_relation': {'type': '_ss'},
        'common_preparation_disease_contraindication_relation': {'type': '_ss'}
    },
    'label': {
        'disease_id': {'type': '_s'},
        'alias_disease_id': {'type': '_s'},
        'common_disease_id': {'type': '_s'}
    },
    'attribute': {
        'is_critical': {'type': '_s'},
        'impossible_part': {'type': '_s'},
        'male_rate': {'type': '_f'},
        'female_rate': {'type': '_f'},
        'age_scope_1_rate': {'type': '_f'},
        'age_scope_2_rate': {'type': '_f'},
        'age_scope_3_rate': {'type': '_f'},
        'age_scope_4_rate': {'type': '_f'},
        'age_scope_5_rate': {'type': '_f'},
        'age_scope_6_rate': {'type': '_f'},
        'common_weight': {'type': '_f'}
    }
}

physical_examination_conf = {
    'relation': {
        'disease_physical_examination_clinical_relation': {'type': '_ss'},
    },
    'attribute': {
        'unit': {'type': '_s'},
        'low_weight_explanation': {'type': '_s'},
        'over_weight_explanation': {'type': '_s'},
        'fat_weight_explanation': {'type': '_s'},
        'severe_fat_explanation': {'type': '_s'},
        'accelerate_explanation': {'type': '_s'},
        'slower_explanation': {'type': '_s'},
        'raise_explanation': {'type': '_s'},
        'down_explanation': {'type': '_s'},
        'low_weight_advice': {'type': '_s'},
        'over_weight_advice': {'type': '_s'},
        'fat_weight_advice': {'type': '_s'},
        'severe_fat_advice': {'type': '_s'},
        'accelerate_advice': {'type': '_s'},
        'slower_advice': {'type': '_s'},
        'raise_advice': {'type': '_s'},
        'down_advice': {'type': '_s'},
        'normal_explanation': {'type': '_s'}
    }
}

inspection_conf = {
    'relation': {
        'disease_inspection_filter_relation': {'type': '_ss'},
    },
    'attribute': {
        'unit': {'type': '_s'},
        'short_name': {'type': '_s'},
        'criterion_name': {'type': '_s'},
        'raise_explanation': {'type': '_s'},
        'down_explanation': {'type': '_s'},
        'obvious_raise_explanation': {'type': '_s'},
        'obvious_down_explanation': {'type': '_s'},
        'negative_explanation': {'type': '_s'},
        'positive_explanation': {'type': '_s'},
        'suspicious_positive_explanation': {'type': '_s'},
        'moderate_positive_explanation': {'type': '_s'},
        'strong_positive_explanation': {'type': '_s'},
        'standard_value_explanation': {'type': '_s'},
        'accelerate_explanation': {'type': '_s'},
        'slower_explanation': {'type': '_s'},
        'raise_advice': {'type': '_s'},
        'down_advice': {'type': '_s'},
        'obvious_raise_advice': {'type': '_s'},
        'obvious_down_advice': {'type': '_s'},
        'negative_advice': {'type': '_s'},
        'positive_advice': {'type': '_s'},
        'suspicious_positive_advice': {'type': '_s'},
        'moderate_positive_advice': {'type': '_s'},
        'strong_positive_advice': {'type': '_s'},
        'standard_value_advice': {'type': '_s'},
        'accelerate_advice': {'type': '_s'},
        'slower_advice': {'type': '_s'},
        'normal_explanation': {'type': '_s'}
    }
}

examination_conf = {
    'relation': {
        'disease_examination_filter_relation': {'type': '_ss'},
    },
    'attribute': {

    }
}

prescribing_behavior_conf = {
        'label': {
            'sku_id': {'type': '_s'}
        }
}

common_preparation = {
        'relation': {
            'common_preparation_disease_indication_relation': {'type': '_ss'},
            'common_preparation_disease_contraindication_relation': {'type': '_ss'}
        },
        'label': {
            'med_id': {'type': '_s'}
        }
}

medicine_conf = {
    'relation': {
        'common_preparation_medicine_relation': {'type': '_ss'}
    },
    'attribute': {
        'supplier': {'type': '_ss'},
        'dosage': {'type': '_s'},
        'dosage_unit': {'type': '_s'},
        'dosing_frequency': {'type': '_s'},
        'administration_route': {'type': '_s'},
        'administration_duration': {'type': '_s'},
        'administration_duration_unit': {'type': '_s'},
        'package_quantity': {'type': '_s'},
        'package_unit': {'type': '_s'}
    }
}

standard_department_conf = {
    'label': {

    },
    'attribute': {

    },
    'relation': {
        'department_symptom_common_relation': {'type': '_ss'}
    }
}

symptom_conf = {
    'lable': {
        'symptom_id': {'type': '_s'}
    },
    'attribute': {
        'is_common': {'type': '_s'},
        'common_weight': {'type': '_f'}
    },
    'relation': {
        'disease_symptom_clinical_relation': {'type': '_ss'},
        'symptom_body_part_relation': {'type': '_ss'},
        'department_symptom_common_relation': {'type': '_ss'}
    }
}

tcm_disease_conf = {
    'label': {

    },
    'attribute': {
        'male_rate': {'type': '_f'},
        'female_rate': {'type': '_f'}
    },
    'relation': {
        'disease_syndrome_tcm_relation': {'type': '_ss'}
    }
}

tcm_syndrome_conf = {
    'label': {

    },
    'attribute': {

    },
    'relation': {
        'disease_syndrome_tcm_relation': {'type': '_ss'}
    }
}

tcm_prescription_conf = {
    'label': {

    },
    'attribute': {
        'criterion_name': {'type': '_s'},
    },
    'relation': {

    }
}

disease_syndrome_conf = {
    'label': {

    },
    'attribute': {
        'criterion_name': {'type': '_s'},
    },
    'relation': {
        'disease_syndrome_disease_relation': {'type': '_ss'},
        'disease_syndrome_syndrome_relation': {'type': '_ss'}
    }
}

treatment_plan_conf = {
    'relation': {
        'treatment_plan_disease_relation': {'type': '_ss'},
        'treatment_plan_disease_accompany_relation': {'type': '_ss'},
        'treatment_plan_common_preparation_relation': {'type': '_ss'}
    }
}

human_body_conf = {
    'relation': {
        'symptom_body_part_relation': {'type': '_ss'}
    }
}

medicine_atc_dir_conf = {
    'label': {

    },
    'attribute': {
        'dir_level': {'type': '_s'},
    },
    'relation': {

    }
}

optional_conf = {
    'type_name': {'type': '_s'},
    'audit_status': {'type': '_i'},
    'is_standard': {'type': '_i'},
    'standard_audit_status': {'type': '_i'},
    'relations': {'type': '_t'},
    'attributes': {'type': '_t'},
    'attribute_name_map': {'type': '_t'},
    'relation_name_map': {'type': '_t'}
}

kg_conf = {
    'entity':{
        'disease': disease_conf,
        'physical_examination': physical_examination_conf,
        'inspection': inspection_conf,
        'examination': examination_conf,
        'medicine': medicine_conf,
        'human_body': human_body_conf,
        'standard_department': standard_department_conf,
        'common_preparation': common_preparation,
        'prescribing_behavior': prescribing_behavior_conf,
        'medicine_atc_dir': medicine_atc_dir_conf,
        'tcm_disease': tcm_disease_conf,
        'tcm_syndrome': tcm_syndrome_conf,
        'tcm_prescription': tcm_prescription_conf,
        'disease_syndrome': disease_syndrome_conf,
        'treatment_plan': treatment_plan_conf,
        'symptom': symptom_conf
    }
}


