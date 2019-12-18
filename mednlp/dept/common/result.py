# from mednlp.dept.common.dictionary import dept_helper


class Department(object):
    def __init__(self, name, probability, dept_id=None):
        self.id = dept_id
        self.name = name
        self.probability = probability
        self.accuracy = 0

        self.sub_dept = {}

    def add_sub_dept(self, sub_name, sub_id):
        self.sub_dept['sub_dept_name'] = sub_name
        self.sub_dept['sub_dept_id'] = sub_id

    def serialize(self):
        content = {'dept_name': self.name,
                   'score': self.probability,
                   'dept_id': self.id,
                   'accuracy': self.accuracy, }
        content.update(self.sub_dept)
        return content

    def __str__(self):
        return str(self.__dict__)

    def copy(self):
        dept_copy = Department(self.name, self.probability, self.id)
        dept_copy.accuracy = self.accuracy
        dept_copy.sub_dept = self.sub_dept
        return dept_copy


class DeptResults(object):
    def __init__(self, rows=5):
        self.dept_list = []
        self.dept_dict = {}
        self.rows = rows

    @staticmethod
    def build(dept_list, rows=5):
        results = DeptResults(rows=rows)
        for name, prob, dept_id in dept_list:
            dept = Department(name, prob, dept_id=dept_id)
            results.dept_list.append(dept)
            results.dept_dict[dept.name] = dept
        return results

    def append(self, dept):
        assert isinstance(dept, Department)
        self.dept_list.append(dept)
        self.dept_dict[dept.name] = dept

    def add(self, dept):
        assert isinstance(dept, Department)
        if dept.name not in self.dept_dict:
            self.append(dept.copy())
        else:
            ori_dept = self.dept_dict.get(dept.name)
            ori_dept.probability += dept.probability

    def pop(self, dept_name):
        dept = self.dept_dict.pop(dept_name, None)
        if dept is not None:
            self.dept_list.remove(dept)
        return dept

    def normalize_score(self):
        sum_score = sum([dept.probability for dept in self.dept_list])
        for dept in self.dept_list:
            dept.probability = dept.probability / sum_score

    def sort(self, reverse=True):
        self.dept_list.sort(key=lambda x: x.probability, reverse=reverse)

    def first(self):
        return self.dept_list[0]

    def serialize(self):
        self.sort()
        if self.rows == 0 or len(self) == 0:
            return [{'dept_name': 'unknow'}]  # woca, mysterious spell

        content = []
        for i in range(min(self.rows, len(self))):
            dept = self.dept_list[i]
            content.append(dept.serialize())
        return content

    def __len__(self):
        return len(self.dept_list)

    def __iter__(self):
        return self.dept_list.__iter__()

    def __getitem__(self, item):
        return self.dept_list.__getitem__(item)

    def __add__(self, other):
        dept_result = self.__class__()
        for dept in self:
            dept_result.add(dept)
        for dept in other:
            dept_result.add(dept)
        return dept_result

    def __mul__(self, other):
        dept_result = self.__class__()
        if isinstance(other, (float, int)):
            for dept in self:
                dept_copy = dept.copy()
                dept_copy.probability *= other
                dept_result.append(dept_copy)
        else:
            raise NotImplementedError
        return dept_result


class ResultHelper(object):
    # @staticmethod
    # def add_dept_id(result: DeptResults):
    #     assert isinstance(result, DeptResults)
    #
    #     for dept in result:
    #         dept_id = dept_helper.get_id_from_name(dept.name)
    #         dept_id = dept_id if dept_id is not None else ''
    #         dept.id = dept_id

    @staticmethod
    def merge(results: list, weights: list) -> DeptResults:
        assert len(results) == len(weights)
        dept_result = DeptResults()
        temp_results = [result * weight for result, weight in zip(results, weights)]
        for temp_result in temp_results:
            dept_result = dept_result + temp_result

        # import numpy as np
        # dept_names = set()
        # for result in results:
        #     assert isinstance(result, DeptResults)
        #     dept_names.update(set([dept.name for dept in result]))
        #
        # for dept_name in dept_names:
        #     same_dept = [result.dept_dict.get(dept_name) for result in results]
        #     dept_prob = [dept.probability if dept is not None else 0 for dept in same_dept]
        #     merge_prob = (np.array(dept_prob) * np.array(weights)).sum()
        #     new_dept = Department(dept_name, merge_prob)
        #     dept_result.append(new_dept)
        return dept_result
