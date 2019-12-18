#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
underwriting_rule.py -- the rule of underwriting

"""

from .utils import average


class UnderwritingRule:

    def __init__(self):
        self.disease = ''
        self.disease_list = ['高血压', '子宫肌瘤', '乙肝', '宫颈炎', '肾结石']

    def decide(self, query):
        """
        给出结果：除外，拒保，返回人工，EM
        :param: query: dict, 格式:
        {sex:, age:, exam_result, systolic_pressure:, diastolic_pressure:}
        :return: result: dict, 格式:
        {conclusion:, description:, em_value:}
        """
        do_exclusion = 0
        do_refusal = 0
        em_value = 0
        exclusion = []
        refusal = []
        missing_material = []
        return_manual = 0

        exam_result = query.get('exam_result', '')
        systolic_pressure = query.get('systolic_pressure', {})
        diastolic_pressure = query.get('diastolic_pressure', {})
        hypertension_property = query.get('hypertension_property', 0)
        has_hypertension_history = query.get('has_hypertension_history', 0)
        has_drug_control = query.get('has_drug_control', 0)
        total_cholesterol = query.get('total_cholesterol', 4)
        triglyceride = query.get('triglyceride', 1)
        physique_risk = query.get('physique_risk', 0)
        smoking_risk = query.get('smoking_risk', 0)
        hbsag = query.get('hbsag', '')
        hbcab = query.get('hbcab', '')
        sgot = query.get('sgot', 20)
        sgpt = query.get('sgpt', 20)

        cholesterol_risk = 0 if 2.9 <= total_cholesterol <= 6.1 else 1
        triglyceride_risk = 0 if 0.4 <= triglyceride <= 1.6 else 1

        self.disease = '高血压'
        if self.disease in self.disease_list:
            current_systolic_pressure = average(systolic_pressure['3m'])
            current_diastolic_pressure = average(diastolic_pressure['3m'])
            former_systolic_pressure = average(systolic_pressure['3m to 1y'])
            former_diastolic_pressure = average(diastolic_pressure['3m to 1y'])
            if not current_systolic_pressure and not current_diastolic_pressure:
                missing_material.append('血压')
            if current_systolic_pressure > former_systolic_pressure:
                average_systolic_pressure = current_systolic_pressure
            else:
                average_systolic_pressure = (current_systolic_pressure
                                             + former_systolic_pressure) / 2
            if current_diastolic_pressure > former_diastolic_pressure:
                average_diastolic_pressure = current_diastolic_pressure
            else:
                average_diastolic_pressure = (current_diastolic_pressure
                                              + former_diastolic_pressure) / 2
            cardiovascular_risk_factor_number = sum(
                [cholesterol_risk, triglyceride_risk,
                 physique_risk, smoking_risk])
            if hypertension_property == 2:
                do_refusal = 1
                if self.disease not in refusal:
                    refusal.append(self.disease)
            else:
                if average_systolic_pressure >= 160 or (
                        average_diastolic_pressure >= 100):
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)
                elif average_systolic_pressure >= 140 or (
                        average_diastolic_pressure >= 90):
                    if cardiovascular_risk_factor_number >= 3:
                        do_refusal = 1
                        if self.disease not in refusal:
                            refusal.append(self.disease)
            if has_hypertension_history or has_drug_control:
                do_exclusion = 1
                if self.disease not in exclusion:
                    exclusion.append(self.disease)
            if has_drug_control and not former_systolic_pressure and (
                    not former_diastolic_pressure):
                do_exclusion = 1
                if self.disease not in exclusion:
                    exclusion.append(self.disease)
                if average_systolic_pressure <= 140 and (
                        average_diastolic_pressure <= 90):
                    em_value += 50
                elif 140 < average_systolic_pressure <= 150 and (
                        average_diastolic_pressure <= 95) or (
                        average_systolic_pressure <= 150) and (
                        90 < average_diastolic_pressure <= 95):
                    em_value += 100
                elif 150 < average_systolic_pressure or (
                        95 < average_diastolic_pressure):
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)
            if cardiovascular_risk_factor_number == 3:
                em_value += 50
                do_exclusion = 1
                if self.disease not in exclusion:
                    exclusion.append(self.disease)
            elif cardiovascular_risk_factor_number > 3:
                em_value += 100
                do_refusal = 1
                if self.disease not in refusal:
                    refusal.append(self.disease)

        self.disease = '子宫肌瘤'
        if self.disease in self.disease_list:
            for word in ['子宫纤维瘤', '子宫切除术', '子宫内膜增生']:
                if word in exam_result:
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
            for word in ['子宫内膜癌', '腺癌', '乳突癌', '透明细胞癌', '乳突内膜样癌']:
                if word in exam_result:
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)

        self.disease = '乙肝'
        if self.disease in self.disease_list:
            if hbsag == '+':
                for word in ['中毒肝炎', '重度肝炎', '肝纤维化', '肝硬化', '肝癌']:
                    if word in exam_result:
                        do_refusal = 1
                        if self.disease not in refusal:
                            refusal.append(self.disease)
                if sgot <= 40 and sgpt <= 40 and hbcab == '+':
                    em_value += 50
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
                if 40 < sgot <= 120 or 40 < sgpt <= 120:
                    em_value += 75
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
                elif sgot > 120 or sgpt > 120:
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)
            if hbsag == '-':
                if 40 < sgot <= 80 or 40 < sgpt <= 80:
                    em_value += 25
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
                if 80 < sgot <= 96 or 80 < sgpt <= 96:
                    em_value += 50
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
                if 96 < sgot <= 120 or 96 < sgpt <= 120:
                    em_value += 75
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
                if sgot > 120 or sgpt > 120:
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)
            for word in ['HCV', 'HDV', 'HIV', 'AFP升高', '甲胎蛋白', '糖尿病']:
                if word in exam_result:
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)

        self.disease = '宫颈炎'
        if self.disease in self.disease_list:
            for word in ['宫颈炎']:
                if word in exam_result:
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)

        self.disease = '肾结石'
        if self.disease in self.disease_list:
            for word in ['肾结石', '高血压']:
                if word in exam_result:
                    do_exclusion = 1
                    if self.disease not in exclusion:
                        exclusion.append(self.disease)
            for word in ['肾功能受损']:
                if word in exam_result:
                    do_refusal = 1
                    if self.disease not in refusal:
                        refusal.append(self.disease)

        if em_value >= 100:
            do_refusal = 1
        if do_refusal:
            do_exclusion = 0
        if not (do_exclusion or do_refusal or em_value):
            return_manual = 1

        exclusion = '|'.join(exclusion)
        refusal = '|'.join(refusal)
        missing_material = '|'.join(missing_material)
        if missing_material:
            do_refusal = 0
            return_manual = 0

        conclusion = ''
        description = ''
        if do_exclusion:
            conclusion = 'C'
            description = exclusion
        if do_refusal:
            conclusion = 'H'
            description = refusal
        if return_manual:
            conclusion = 'A'
            description = '返回人工'
        if missing_material:
            conclusion = 'D'
            description = missing_material

        result = {'conclusion': conclusion,
                  'description': description,
                  'em_value': em_value}

        return result


if __name__ == "__main__":
    pass
