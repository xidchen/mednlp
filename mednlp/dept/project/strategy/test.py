import unittest

import global_conf
from mednlp.dept.project.strategy.sub_dept import SubDeptMapping, SubDeptStrategy
from mednlp.dept.common.result import DeptResults


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.case1 = [['神经外科', 0.565377286, '123'],
                      ['神经内科', 0.4, '321'],
                      ['脑部肿瘤科', 0.2, '111'],
                      ['中医科', 0.2, '000']]

    def test_sub_mapping(self):
        a = u"血液科"
        b = u'耳鼻咽喉科'
        c = u'a'
        sub_dept = SubDeptMapping(global_conf.children_sub_deptment, '儿科')
        sub_name, sub_id = sub_dept.get_sub_dept(a)
        self.assertEqual(sub_name, '小儿血液科')
        self.assertEqual(sub_id, '7f6812c8-cff3-11e1-831f-5cf9dd2e7135')

        sub_name, sub_id = sub_dept.get_sub_dept(b)
        self.assertEqual(sub_name, '小儿耳鼻喉科')
        self.assertEqual(sub_id, '7f683672-cff3-11e1-831f-5cf9dd2e7135')

        children_sub_deptment = sub_dept.get_sub_dept(c)
        self.assertEqual(children_sub_deptment, None)

    def test_common_strategy(self):
        sub_dept = SubDeptMapping(global_conf.chinese_medicine_sub_deptment, '中医科')
        strategy = SubDeptStrategy(sub_dept)

        case = self.case1.copy()
        dept_results = DeptResults.build(case)
        dept = dept_results.dept_dict.get('中医科')
        strategy.execute(dept_results)
        self.assertEqual(dept.sub_dept, {})

        case[1][1] = 0.6
        dept_results = DeptResults.build(case)
        dept = dept_results.dept_dict.get('中医科')
        strategy.execute(dept_results)
        self.assertEqual(dept.sub_dept['sub_dept_name'], '中医神经内科')


if __name__ == '__main__':
    unittest.main()
