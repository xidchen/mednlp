from mednlp.dept.common.result import DeptResults
from mednlp.dept.utils.vectors import SubDept2Vector


class SubDeptStrategy(object):
    def __init__(self, sub_dept_map):
        assert isinstance(sub_dept_map, SubDept2Vector)
        self.sub_dept_helper = sub_dept_map

    @staticmethod
    def get_rest_highest_dept(dept_results, object_dept):
        if len(dept_results) == 0:
            return None
        dept_results.sort(reverse=True)
        results_copy = dept_results.dept_list.copy()  # 浅拷贝，不增加内存
        results_copy.remove(object_dept)
        if len(results_copy) == 0:
            return None
        rest_highest_dept = results_copy[0]
        return rest_highest_dept

    def execute(self, dept_results):
        """
        根据模型预测结果，给定科室是目标科室的科室，增加子科室和子科室id
        老策略：
        a. 若第一可信是主科室，则尝试和第二可信匹配形成子科室
        b. 若其余科室为主科室，则尝试和第一可信匹配形成子科室
        等价于：
        预测为主科室的结果，与其余科室置信最高的结果尝试匹配，形成子科室
        :param dept_results: 模型预测结果
        :return: 返回目标科室部分已增加已增加目标科室下面的二级科室和id的结果,类型list
        """
        assert isinstance(dept_results, DeptResults)
        chief_dept_name = self.sub_dept_helper.parent_name
        department = dept_results.dept_dict.get(chief_dept_name)
        if department is None:
            return
        rest_highest_dept = self.get_rest_highest_dept(dept_results, department)
        if rest_highest_dept is None:
            return

        sub_dept_name = self.sub_dept_helper.get_child_from_dept(rest_highest_dept.name)
        if sub_dept_name is not None:
            sub_dept_id = self.sub_dept_helper.get_id_from_child(sub_dept_name)
            department.add_sub_dept(sub_dept_name, sub_dept_id)


class PediatricsStrategy(SubDeptStrategy):
    def __init__(self, sub_dept_map):
        super(PediatricsStrategy, self).__init__(sub_dept_map)
        assert self.sub_dept_helper.parent_name is '儿科'

    def execute(self, dept_results):
        """
        儿科特殊需求，以提高儿科分诊的准确率
        若主科室为儿科，子科室为小儿呼吸科，则直接提供小儿呼吸科，不要子科室
        :param dept_results:
        :return:
        """
        assert isinstance(dept_results, DeptResults)
        chief_dept_name = self.sub_dept_helper.parent_name
        department = dept_results.dept_dict.get(chief_dept_name)
        rest_highest_dept = self.get_rest_highest_dept(dept_results, department)

        sub_dept_name = self.sub_dept_helper.get_child_from_dept(rest_highest_dept.name)
        if sub_dept_name is not None:
            sub_dept_id = self.sub_dept_helper.get_id_from_child(sub_dept_name)
            department.name = sub_dept_name
            department.id = sub_dept_id
