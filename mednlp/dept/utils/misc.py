from mednlp.dept.common.result import Department
from mednlp.dept.utils.vectors import Dept2Vector, SubDept2Vector


class DeptDictionary(object):
    def __init__(self, dept_helper: Dept2Vector, *sub_dept_helpers):
        self.dept_helper = dept_helper
        for sub_dept_helper in sub_dept_helpers:
            assert isinstance(sub_dept_helper, SubDept2Vector)
        self.sub_dept_helpers = {sdh.parent_name: sdh for sdh in sub_dept_helpers}

        self.dictionary = {}
        self.sub_dictionary = {}

        self.arrange_dictionary()

    def arrange_dictionary(self):
        for dept_name in self.dept_helper.name2id.keys():
            dept_id = self.dept_helper.get_id_from_name(dept_name)
            dept = Department(dept_name, probability=0, dept_id=dept_id)
            self.dictionary[dept_name] = dept

        for dept_name, sub_helper in self.sub_dept_helpers.items():
            for sub_dept_name in sub_helper.child2id.keys():
                dept_id = self.dept_helper.get_id_from_name(dept_name)
                dept = Department(dept_name, probability=0, dept_id=dept_id)

                sub_dept_id = sub_helper.get_id_from_child(sub_dept_name)
                dept.add_sub_dept(sub_dept_name, sub_dept_id)
                self.sub_dictionary[sub_dept_name] = dept

    def get_department_by_name(self, dept_name: str) -> Department:
        department = self.dictionary.get(dept_name) or self.sub_dictionary.get(dept_name)
        if department is None:
            raise ValueError('could not find {} in standard dictionary'.format(dept_name))
        department = department.copy()
        return department

    def get_dept_pair_by_sub_name(self, sub_dept_name: str) -> tuple:
        """
        输入子科室名，获取主科室的组合。
        如，输入小儿呼吸内科，则返回儿科和呼吸内科
        :param sub_dept_name:
        :return:
        """
        department = self.sub_dictionary.get(sub_dept_name)
        if department is None:
            raise ValueError('could not find {} in standard dictionary'.format(sub_dept_name))
        sub_dept_helper = self.sub_dept_helpers[department.name]
        by_dept_name = sub_dept_helper.get_dept_from_child(sub_dept_name)
        parent_name = sub_dept_helper.parent_name
        main_department = self.get_department_by_name(parent_name)
        by_department = self.get_department_by_name(by_dept_name)
        return main_department, by_department
