from mednlp.dept.common.dictionary import disease_helper
from mednlp.dept.common.result import DeptResults, Department


class DiseaseLookUpStrategy(object):
    def __init__(self):
        self.disease_helper = disease_helper

    def execute(self, disease) -> DeptResults:
        dept_name = self.disease_helper.get_dept_from_disease(disease)
        dept_result = DeptResults()
        if dept_name is not None:
            dept_id = self.disease_helper.get_id_from_dept(dept_name)
            department = Department(dept_name, 0.7, dept_id)
            dept_result.append(department)
        return dept_result
