from mednlp.dept.common.result import DeptResults


class AgeStrategy(object):
    def __init__(self):
        self.baby_threshold = 2
        self.child_threshold = 14
        self.adult_threshold = 16
        self.days_per_year = 365

    def execute(self, result, age):
        """
        1.老不如儿科：若一人年龄大于16岁，则儿科分诊概率为0
        2.少必入儿科（待变动，如新生儿科细分）：若一人年龄小于14岁，则概率强行设置成最大概率的1.2倍
        :param result:
        :param age:
        :return:
        """
        assert isinstance(result, DeptResults)

        pediatrics = result.dept_dict.get('儿科')
        if pediatrics is None:
            return result

        if age > self.adult_threshold * self.days_per_year:
            pediatrics.probability = 0
        elif 0 <= age < self.child_threshold * self.days_per_year:
            ratio = 1.2
            result.sort()
            top_dept = result.first()
            pediatrics.probability = top_dept.probability * ratio

        result.sort()
        result.normalize_score()
        return result
