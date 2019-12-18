#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
dept_classify.py -- the service of dept_classify

Author: maogy <maogy@guahao.com>
Create on 2017-06-19 星期一.
"""

import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.dept_classify_merge_model import MergeModel, MedicalRecordModel
from mednlp.dept.project.strategy.sub_dept import SubDeptStrategy
from mednlp.dept.utils.vectors import SubDept2Vector
from mednlp.dept.utils.accuracy import Score2Accuracy
from mednlp.dept.utils.rules import dept_filter_error, DiseaseDept, TransInspection
from mednlp.dept.common.result import DeptResults
from mednlp.dept.project.strategy.level import LevelStrategyManager

mergemodel = MergeModel(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_MODEL')
medicalrecordmodel = MedicalRecordModel(cfg_path=global_conf.cfg_path, model_section='DEPT_CLASSIFY_MODEL')
children_sub_deptment = SubDept2Vector(global_conf.children_sub_deptment, '儿科')
chinese_medicine_sub_deptment = SubDept2Vector(global_conf.chinese_medicine_sub_deptment, '中医科')
tumour_sub_deptment = SubDept2Vector(global_conf.tumour_sub_deptment, '肿瘤科')
score2accuracy = Score2Accuracy(global_conf.accuracy_second_path)
disease_dept = DiseaseDept()
transinspection = TransInspection()


class DeptClassify(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.write_result(self._get())

    def _get(self):
        query = self.get_q_argument('', limit=2000)
        rows = self.get_argument('rows', 1)
        sex = self.get_argument('sex', 0)
        age = self.get_argument('age', -1)
        level = self.get_argument('level', 1)
        mode = self.get_argument('mode', 1)
        dept_set = self.get_argument('dept_set', 1)
        disease = self.get_argument('disease', '')
        sex = dept_filter_error(sex, 0)
        age = dept_filter_error(age, -1)
        level = dept_filter_error(level, 1)
        mode = dept_filter_error(mode, 1)
        dept_set = dept_filter_error(dept_set, 1)
        rows = dept_filter_error(rows, 1)
        result = {}
        query = transinspection.transform_inspection_data(query)
        if dept_set == 2:
            rows = min(45, rows)
        elif dept_set == 3:
            rows = min(37, rows)
        else:
            rows = min(40, rows)
        disease_depts = disease_dept.predict(disease)
        if disease and disease_depts:
            depts = disease_depts
        else:
            query = query + disease
            if not query:
                return result
            if mode == 2:
                depts = medicalrecordmodel.predict(query, sex=sex, age=age, level=level, dept_set=dept_set)
            else:
                depts = mergemodel.predict(query, sex=sex, age=age, level=level, dept_set=dept_set)

        dept_results = DeptResults.build(depts, rows)
        LevelStrategyManager().get_strategy(level).execute(dept_results, mode)
        mergemodel.add_accuracy2(dept_results)
        SubDeptStrategy(children_sub_deptment).execute(dept_results)
        SubDeptStrategy(chinese_medicine_sub_deptment).execute(dept_results)
        SubDeptStrategy(tumour_sub_deptment).execute(dept_results)
        score2accuracy.add_accuracy_to_result(dept_results)
        fc_result = {'data': dept_results.serialize(),
                     'totalCount': max(1, dept_results.rows)}

        # data = result.setdefault('data', [])
        # # if dept_set == 1:
        # # depts = get_origin_dept(depts, sex)
        # if level == 2 and depts and depts[0][1] < 0.2:
        #     depts = []
        # if mode == 2:
        #     if level == 3 and depts and depts[0][1] < 0.6:
        #         depts = []
        # else:
        #     if level == 3 and depts and depts[0][1] < 0.4:
        #         depts = []
        # if level == 4 and depts:
        #     if (depts[0][1] >= 0.4) or (depts[0][1] + depts[1][1] >= 0.7):
        #         if max(depts[0][1], depts[1][1]) > 2 * (min(depts[0][1], depts[1][1])):
        #             rows = 1
        #         else:
        #             rows = 2
        #     else:
        #         depts = []
        # if not depts:
        #     data.append({'dept_name': 'unknow'})
        #     result['totalCount'] = 1
        #     return result
        # depts = mergemodel.add_accuracy(depts)
        # if len(depts) > 1:
        #     # depts[1][3] = score2accuracy.get_accuracy(depts[1][1])
        #     depts = score2accuracy.get_accuracy_list(depts)
        #     children_depts = children_sub_deptment.get_list_sub_dept(depts)
        #     medicine_depts = chinese_medicine_sub_deptment.get_list_sub_dept(children_depts)
        #     tumour_depts = tumour_sub_deptment.get_list_sub_dept(medicine_depts)
        #     data.extend(chinese_medicine_sub_deptment.get_dict_sub_dept(tumour_depts, rows=rows))
        # else:
        #     data.extend(chinese_medicine_sub_deptment.get_dict_sub_dept(depts, rows=rows))
        # result['totalCount'] = rows
        # return result
        return fc_result


if __name__ == '__main__':
    handlers = [(r'/dept_classify', DeptClassify, dict(runtime={}))]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
