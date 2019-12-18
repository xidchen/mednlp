"""
接口输入level策略，包括高覆盖、普通、高准确和倩儿高准确四种
"""


class LevelStrategyManager(object):
    def __init__(self):
        self.strategy_dict = {1: HighCoverage(),
                              2: Recommend(),
                              3: HighPrecision(),
                              4: Top2HighPrecision()}

    def get_strategy(self, level):
        return self.strategy_dict[level]


class LevelStrategy(object):
    def execute(self, result, mode):
        raise NotImplementedError


class HighCoverage(LevelStrategy):
    def execute(self, result, mode):
        return result


class Recommend(LevelStrategy):
    def execute(self, result, mode):
        if len(result) < 1:
            return result

        threshold = 0.2
        if result.first().probability < threshold:
            result.rows = 0
        return result


class HighPrecision(LevelStrategy):
    def execute(self, result, mode):
        if len(result) < 1:
            return result

        threshold = 0.6 if mode == 2 else 0.4
        if result.first().probability < threshold:
            result.rows = 0
        return result


class Top2HighPrecision(LevelStrategy):
    def execute(self, result, mode):
        if len(result) < 2:
            return result

        top_score, second_score = result[0].probability, result[1].probability
        top_high = top_score > 0.4
        top_two_high = top_score + second_score >= 0.7
        if top_high or top_two_high:
            higher = max(top_score, second_score)
            lower = min(top_score, second_score)
            result.rows = 1 if higher > 2 * lower else 2
        else:
            result.rows = 0
        return result
