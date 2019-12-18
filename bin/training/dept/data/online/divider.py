class Divider(object):
    def divide(self, *args, **kwargs):
        raise NotImplementedError


class PercentageDivider(Divider):
    def __init__(self, start=0.0, division=None, data_set=None):
        division = division if division is not None else [0.7, 0.15, 0.15]
        assert len(division) == 3 and sum(division) == 1
        data_set = data_set if data_set is not None else ['train', 'validation', 'test']

        self.start = start
        self.data_set = data_set
        self.division = division

    def divide(self):
        result = {}
        start = self.start
        for data_set, length in zip(self.data_set, self.division):
            data_range = self._get_range(start, length)
            result[data_set] = data_range
            start = start + length
        return result

    @staticmethod
    def _get_range(start, length):
        stop = start + length
        if stop <= 1:
            data_range = [[start, stop]]
        else:
            stop = stop - 1
            data_range = [[start, 1.0], [0.0, stop]]
        return data_range


def test_dis():
    divider = PercentageDivider(start=0.15, division=[0.1, 0.1, 0.8])
    result = divider.divide()
    print(result)


if __name__ == '__main__':
    test_dis()
