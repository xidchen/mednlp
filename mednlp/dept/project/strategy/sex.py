from mednlp.dept.common.result import DeptResults


class SexStrategy(object):
    def __init__(self):
        self.female_dept_names = ['妇科', '产科', '妇产科']
        self.male_dept_names = ['男科']
        self.sex_opposite_dept_mapping = {1: self.male_dept_names, 2: self.female_dept_names}

    def execute(self, result, sex=1):
        """
        1.男不入妇科：男性病人不应该到妇科、产科和妇产科，这几类分诊概率设置成0
        2.女不入男科：女性病人不应该到男科，男科分诊概率设置成0
        :param result:
        :param sex: 1:女, 2:男
        :return:
        """
        assert isinstance(result, DeptResults)
        opposite_dept_names = self.sex_opposite_dept_mapping.get(sex)
        if opposite_dept_names is None:
            return result
        for dept_name in opposite_dept_names:
            self.clear_score(result, dept_name)
        result.sort()
        result.normalize_score()
        return result

    @staticmethod
    def clear_score(result, dept_name):
        dept = result.dept_dict.get(dept_name)
        if dept is not None:
            dept.probability = 0
