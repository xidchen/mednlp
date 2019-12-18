from mednlp.dept.project.strategy import SexStrategy, AgeStrategy, SetStrategyManager, \
    LevelStrategyManager, SubDeptStrategy, AccuracyStrategy
from mednlp.dept.common.result import DeptResults
from mednlp.dept.common.dictionary import sub_pediatrics_helper, sub_chinese_medicine_helper, sub_tumor_helper


class RulesManager(object):
    def __init__(self):
        self.set_strategy_manager = SetStrategyManager()
        self.level_manager = LevelStrategyManager()
        self.sex_strategy = SexStrategy()
        self.age_strategy = AgeStrategy()
        self.accuracy_strategy = AccuracyStrategy()

        self.sub_dept_strategies = [SubDeptStrategy(sub_pediatrics_helper),
                                    SubDeptStrategy(sub_chinese_medicine_helper),
                                    SubDeptStrategy(sub_tumor_helper)]

    def execute(self, result, age, sex, level, mode, data_set, rows):
        assert isinstance(result, DeptResults)
        result.rows = rows
        result = self.set_strategy_manager.get_strategy(data_set).execute(result, sex=sex)
        result = self.sex_strategy.execute(result, sex)
        result = self.age_strategy.execute(result, age)
        result = self.level_manager.get_strategy(level).execute(result, mode)
        for sub_dept_strategy in self.sub_dept_strategies:
            sub_dept_strategy.execute(result)
        result = self.accuracy_strategy.execute(result)
        return result
