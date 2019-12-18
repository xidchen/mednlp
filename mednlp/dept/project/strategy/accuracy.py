from mednlp.dept.common.dictionary import accuracy_helper1, accuracy_helper
from mednlp.dept.common.result import DeptResults


class AccuracyStrategy(object):
    def __init__(self):
        self.first_accuracy_helper = accuracy_helper
        self.second_accuracy_helper = accuracy_helper1

    def execute(self, result):
        assert isinstance(result, DeptResults)
        for i, dept in enumerate(result):
            helper = self.first_accuracy_helper if i == 0 else self.second_accuracy_helper
            dept.accuracy = helper.get_accuracy_from_probability(dept.probability)
        return result
