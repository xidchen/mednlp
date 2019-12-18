#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
db_conf.py -- the db field conf

Author: maogy <maogy@guahao.com>
Create on 2019-02-12 Tuesday.
"""


disease = {
    'relation': {
        '958c3f47-8787-11e9-bb66-f48e38c4c9f4': 'disease_disease_paternity_relation',
        '958c72bb-8787-11e9-bb66-f48e38c4c9f4': 'disease_symptom_clinical_relation',
        '32cbebf1-77fd-4b1e-b355-c2e6519a4c38': 'disease_physical_examination_clinical_relation',
        '95f3df89-8787-11e9-bb66-f48e38c4c9f4': 'disease_inspection_filter_relation',
        '95f36782-8787-11e9-bb66-f48e38c4c9f4': 'disease_examination_filter_relation',
        '23ac616c-8ecf-47ab-b91f-e900916b1ea0': 'common_preparation_disease_indication_relation',
        'f45b6353-dc5c-4ba5-859b-0dd7927251d3': 'common_preparation_disease_contraindication_relation'
    },
    'label': {
        'pkCizO3q': 'disease_id',
        'sLPj2EzJ': 'alias_disease_id',
        'JpAFSSYS': 'common_disease_id'
    },
    'attribute': {
        'a7f53eb3b9fa447a9dc049700c95346e': 'is_critical',
        'f733f23c43944862a00c9724663c460c': 'impossible_part',
        '478d28ccc84a4464bfdffdcc9ed5b7dd': 'male_rate',
        '94d4f6c8528041098b76d364cb16a6a5': 'female_rate',
        'a1563648219442f2b3427fddbdd1184b': 'age_scope_1_rate',
        '6e1adcd206f04c0f9f2ab14b63394722': 'age_scope_2_rate',
        '4351ff96654d4430a61e1188eab6a47b': 'age_scope_3_rate',
        '590000d71b7b43bcac502c67533dddae': 'age_scope_4_rate',
        '22a444a3ac8e472a8ee60a4bede1fdda': 'age_scope_5_rate',
        'fd9b7bfd89f3487a90e2edac8f77dd87': 'age_scope_6_rate',
        'cc28c3c92ed14cbfa5d22ad7212592f9': 'common_weight'
    }
}

inspection = {
    'relation': {
        '95f3df89-8787-11e9-bb66-f48e38c4c9f4': 'disease_inspection_filter_relation'
    },
    'attribute': {
        'ed97a05dbf5c4c17a303951ed1f73338': 'unit',
        'fac3681f86794a70833d2dc9c2b58bfb': 'short_name',
        '1112ce89d18842ba80b87b214cce20db': 'criterion_name',
        '3bc21eb502b240f8ac3c300c1747a3fe': 'raise_explanation',
        'a510af37b90f4bd8b72866500f3eb8f0': 'down_explanation',
        '6bf1715243914a20a54b3035576be0a5': 'obvious_raise_explanation',
        'b6d0fdd796f04ae2b7f3134968ce776a': 'obvious_down_explanation',
        '8f0f04350a6a4a868f581f3a740bfbbf': 'negative_explanation',
        '57ae925c86f04312b8a9993e401baea3': 'positive_explanation',
        '185a4dd133804faa9f95281ca5427a47': 'suspicious_positive_explanation',
        'fae5d3343eb74b5385b1d57fccbbe2b3': 'moderate_positive_explanation',
        '012084fa730f4190b040b9ce66e2c8d2': 'strong_positive_explanation',
        '0ade8c9ed6fb48099a455287cc4fe988': 'standard_value_explanation',
        'c14bfee0247f4ff3a80ce8caf08338f9': 'accelerate_explanation',
        '9cfb190045424262bc349f2e4b3bb4f4': 'slower_explanation',
        '0bc06d7627ca47f3bb210fe501883a96': 'raise_advice',
        'fe736cf5e7df4750a55e4d7b4f5b572c': 'down_advice',
        '92e25aef28e64055a130484327bed351': 'obvious_raise_advice',
        '48768e1e3de3409294d4e7c4e92ad75f': 'obvious_down_advice',
        'bc5e8e53c7d747869d5b1541bdda6f96': 'negative_advice',
        '55a0fa115f7d4382aff8ecf96a09e0e5': 'positive_advice',
        '76dc006d7c3c4a9c9f6a577782e9d5e1': 'suspicious_positive_advice',
        '30897f2b817f4dbfb867d63b8b1911fa': 'moderate_positive_advice',
        '1fbb58cbbeb548e59cdf01054f74af75': 'strong_positive_advice',
        '0ade8c9ed6fb48099a455287cc4fe988': 'standard_value_advice',
        '8dcfacea994e469bae27c6eb5ad07516': 'accelerate_advice',
        'ddb199ef7ae64cd28447acff074a6489': 'slower_advice',
        '767edc54040e4f3ca6a10f6c535dfc92': 'normal_explanation'
    },

}

examination = {
    'relation': {
        '95f36782-8787-11e9-bb66-f48e38c4c9f4': 'disease_examination_filter_relation'
    },
    'attribute': {

    },

}

physical_examination = {
    'relation': {
        '32cbebf1-77fd-4b1e-b355-c2e6519a4c38': 'disease_physical_examination_clinical_relation'
    },
    'attribute': {
        'f33dc4b41b5043f9826b04b3087e64bf': 'unit',
        'f987e57c333e42df9b29266c8881b145': 'low_weight_explanation',
        '6996b24ec031430aae6ff8cf4283e2da': 'over_weight_explanation',
        '420a892a39024a01a4ff4e4a92384fb9': 'fat_weight_explanation',
        '7b539cc55ed04428a9236967a739c622': 'accelerate_explanation',
        'f0830d13b5a94b748424293e66db057e': 'slower_explanation',
        '45404bd94a0247ae8ee86255189cbbff': 'raise_explanation',
        '6548fb0d464f4281b74ac1ea7fdb135b': 'down_explanation',
        '3fe79fba65b646dfadebaa7393f20a50': 'low_weight_advice',
        'b2d70008c57a408983849e0130db2fa1': 'over_weight_advice',
        '561f1e2f125640608361ee83de8f5e22': 'fat_weight_advice',
        '68a2d0eeb8b74d86b77420d765fd2dd7': 'accelerate_advice',
        '4f4b0912ec89473d90739ecd0c46cfa3': 'slower_advice',
        '2ab619b1187940e8837d0daceab4e20d': 'raise_advice',
        'bdf572363a0d4036b117c813459779be': 'down_advice',
        'd835c22d25014ba888d90845275017e4': 'normal_explanation'
    }
}

prescribing_behavior = {
    'label': {
        'f1j6zT94': 'sku_id'
    }
}

common_preparation = {
    'relation': {
        '23ac616c-8ecf-47ab-b91f-e900916b1ea0': 'common_preparation_disease_indication_relation',
        'f45b6353-dc5c-4ba5-859b-0dd7927251d3': 'common_preparation_disease_contraindication_relation'
    },
    'label': {
        'lXuVwc4Z': 'med_id'
    }
}

medicine = {
    'relation': {
        'a1a0a010-86c8-11e9-bfde-c81f66c0f33f': 'common_preparation_medicine_relation'
    },
    'attribute': {
        'baa30c9694cf424e886457558cb6deb5': 'dosage',
        'fc3260585bbf46fd83a928efcda1fc34': 'dosage_unit',
        'b2833099c1a84f9fad54e699f32d54d3': 'dosing_frequency',
        'd1e3c3980c6b489cbb2db28a3d736176': 'administration_route',
        '68d3d5ee6eb146caadf40a95331217af': 'administration_duration',
        'dea94264b2ac4f20ad6d90f653782f74': 'administration_duration_unit',
        '2a043e8eed154534b1e590be2ff86cdb': 'package_quantity',
        '67e3a9ef60434a338eddbeb05855bfe7': 'package_unit'
    }
}

standard_department = {
    'label': {

    },
    'attribute': {

    },
    'relation': {
        '645f6e88-8733-11e9-bfde-c81f66c0f33f': 'department_symptom_common_relation'
    }
}

symptom = {
    'label': {
        # 'pkCizO3q': 'symptom_id',
        # '2tq7CO74': 'symptom_id'
    },
    'attribute': {
        '3ca6f899501c4c3492f96acc73149769': 'is_common',
        '7da4316b6cee4f50873395c17e74645d': 'common_weight'
    },
    'relation': {
        '958c72bb-8787-11e9-bb66-f48e38c4c9f4': 'disease_symptom_clinical_relation',
        'c40622b2-3ad0-4097-85b7-b00aa1e16dc9': 'symptom_body_part_relation',
        '645f6e88-8733-11e9-bfde-c81f66c0f33f': 'department_symptom_common_relation'
    }
}

tcm_disease = {
    'label': {

    },
    'attribute': {
        '552b63b865d84ec5b3daa6bb2a37fb3a': 'male_rate',
        '4a7688c2d0f54869ae991b34fb4c0f1a': 'female_rate'
    },
    'relation': {
        '80948d4e-8e78-11e9-bfde-c81f66c0f33f': 'disease_syndrome_tcm_relation'
    }
}

tcm_syndrome = {
    'label': {

    },
    'attribute': {

    },
    'relation': {
        '80948d4e-8e78-11e9-bfde-c81f66c0f33f': 'disease_syndrome_tcm_relation'
    }
}

tcm_prescription = {
    'label': {

    },
    'attribute': {
        'dbd9271338354045b1122dec4f8e8c56': 'criterion_name',
    },
    'relation': {

    }
}

disease_syndrome = {
    'label': {

    },
    'attribute': {
        '01a51d2cc9a54a75af9a0d525b03f796': 'criterion_name',
    },
    'relation': {
        '78ce81a7-8e78-11e9-bfde-c81f66c0f33f': 'disease_syndrome_disease_relation',
        'ccaabd7f-8d81-11e9-bfde-c81f66c0f33f': 'disease_syndrome_syndrome_relation'
    }
}

treatment_plan = {
    'relation': {
        '12ab3671-a24e-11e9-95b0-2aaa81e8f50d': 'treatment_plan_disease_relation',
        '27ffb1de-a24e-11e9-95b0-2aaa81e8f50d': 'treatment_plan_disease_accompany_relation',
        '1727453e-8ce5-11e9-bb66-f48e38c4c9f4': 'treatment_plan_common_preparation_relation'
    }
}

human_body = {
    'relation': {
        'c40622b2-3ad0-4097-85b7-b00aa1e16dc9': 'symptom_body_part_relation'
    }
}

medicine_atc_dir = {
    'label': {

    },
    'attribute': {
        '7d1cce8c7a65474194fc8dab58729f3c': 'dir_level'
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
    'disease': 'disease',
    'oFw6zran': 'inspection',
    'VCIqE8AF': 'hospital',
    'PrN1tM6l': 'physical_examination',
    '3Lminu2l': 'prescribing_behavior',
    'HFxsdcy5': 'common_preparation',
    'xMLx7PGr': 'medicine',
    'dJS9RSy0': 'treatment',
    'FVB1BY33': 'human_body',
    '7DfztjJp': 'standard_department',
    '2yfCNEoM': 'examination',
    'BHp3nQrx': 'crowd',
    'ut5qXpHw': 'drug_composition',
    'uRFEEzuK': 'manufacturer',
    'VyymUitz': 'drug_manufacturer',
    'lmEBBpOn': 'drug_product',
    '6nrOGwhM': 'dosage_form',
    'ijiV7c49': 'medicine_atc_dir',
    'QWG2qTZV': 'tcm_disease',
    'BDWcvnje': 'tcm_syndrome',
    'wNhB8eJU': 'tcm_prescription',
    'MDO1neXW': 'tcm_drug',
    'HTsetDmR': 'disease_syndrome',
    'vFx947TJ': 'treatment_plan',
    'yTYJux56': 'allergic',
    'zsyr0fqA': 'symptom'
}


medical_knowledge = {
    'disease_type': {
        '2': ['l7lZ3rIY']
    }
}


entity_label_dict = {
    'past_medical_history': 'Euu2suB5',
    'family_history': 'I8aSO0Th',
    'surgical_history': '6L10t3eQ',
    'trauma_history': 'twkSCE9S',
    'allergy_history': '8D6ivDzp',
}

