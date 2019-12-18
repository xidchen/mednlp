from mednlp.dept.common.dictionary import internet_dept_helper
from mednlp.dept.common.result import DeptResults, Department


class SetStrategyManager(object):
    def __init__(self):
        self.strategy_dict = {1: Standard40SetStrategy(),
                              2: Standard45Strategy(),
                              3: InternetSetStrategy(),
                              }

    def get_strategy(self, data_set):
        return self.strategy_dict[data_set]


class SetStrategy(object):
    def execute(self, result, sex=1):
        raise NotImplementedError


class InternetSetStrategy(SetStrategy):
    def __init__(self):
        self.internet_helper = internet_dept_helper

    def execute(self, result, sex=1):
        """
        将45模型输出科室转换成互联网医院标准科室，科室名相同的分数相加
        :param result:
        :param sex:
        :return:
        """
        assert isinstance(result, DeptResults)
        rows = min(37, result.rows)
        internet_result = DeptResults(rows=rows)
        for dept in result:
            internet_name = self.internet_helper.get_internet_from_standard(dept.name)
            if internet_name is None:
                continue

            internet_dept = internet_result.dept_dict.get(internet_name)
            internet_id = self.internet_helper.get_id_from_internet(internet_name)
            if internet_dept is None:
                internet_dept = Department(internet_name, 0, internet_id)
                internet_result.append(internet_dept)
            internet_dept.probability += dept.probability

        internet_result.sort()
        internet_result.normalize_score()
        return internet_result


class Standard40SetStrategy(object):
    def __init__(self):
        self.extra_dept_name = ['生殖与遗传', '手外科', '口腔颌面外科', '肿瘤外科', '关节外科']
        self.sex_weight_mapping = {1: [0, 1], 2: [1, 0]}

    def execute(self, result, sex=1):
        """
        去掉以上额外科室的输出，其中：
        a.手外科和关节外科的得分算到骨科，
        b.肿瘤外科算到肿瘤科
        c.生殖与遗传根据性别算到男科和妇科
        d.口腔颌面外科根据口腔科和骨科的比例瓜分至两科室
        :param result:
        :param sex: 1:女, 2:男
        :return:
        """
        assert isinstance(result, DeptResults)
        result.rows = min(40, result.rows)

        self.merge_score(result, '手外科', '骨科')
        self.merge_score(result, '关节外科', '骨科')
        self.merge_score(result, '肿瘤外科', '肿瘤科')

        sex_weight = self.sex_weight_mapping.get(sex)
        '''性别有可能未知"0"，未知就不操作'''
        if sex_weight is not None:
            self.merge_scores(result, '生殖与遗传', ['男科', '妇科'], sex_weight)
        self.merge_scores(result, '口腔颌面外科', ['骨科', '口腔科'])

        result.sort()
        result.normalize_score()
        return result

    @staticmethod
    def merge_score(result, src_dept_name, dst_dept_name):
        src_dept = result.pop(src_dept_name)
        if src_dept is None:
            return
        dst_dept = result.dept_dict[dst_dept_name]
        dst_dept.probability += src_dept.probability

    @staticmethod
    def merge_scores(result, src_dept_name, dst_dept_names: list, weights: list = None):
        if weights is None:
            '''若weights输入为None，则默认按照result中比例进行分配'''
            weights = []
            for dst_name in dst_dept_names:
                dst_dept = result.dept_dict.get(dst_name)
                if dst_dept is None:
                    return
                weights.append(dst_dept.probability)
            # weights = [result.dept_dict[dst_name].probability for dst_name in dst_dept_names]
            weights = [weight / sum(weights) for weight in weights]
        '''否则就按照输入比例进行分配'''
        assert len(dst_dept_names) == len(weights)
        src_dept = result.pop(src_dept_name)
        if src_dept is None:
            return
        for dst_dept_name, weight in zip(dst_dept_names, weights):
            dst_dept = result.dept_dict[dst_dept_name]
            dst_dept.probability += src_dept.probability * weight


class Standard45Strategy(SetStrategy):
    def execute(self, result, sex=1):
        assert isinstance(result, DeptResults)
        result.rows = min(45, result.rows)
        return result
