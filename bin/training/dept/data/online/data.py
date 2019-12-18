import os
import pandas
import numpy as np

from .dataset import DeptDataSet
from .divider import PercentageDivider


class DeptData(object):
    def __init__(self, config):
        self.config = config
        info_file = os.path.join(config.DATA_PATH, 'info.csv')
        self.df = pandas.DataFrame(pandas.read_csv(info_file))

        self.data = {}
        self.distribute()
        # self.distribute1()

    def distribute(self):
        total = len(self.df)
        divider = PercentageDivider(start=0, division=[0.9, 0.05, 0.05])
        div_result = divider.divide()
        for phase, data_ranges in div_result.items():
            dfs = []
            for data_range in data_ranges:
                start_index = round(data_range[0] * total)
                stop_index = round(data_range[1] * total)
                df_part = self.df[start_index:stop_index]
                dfs.append(df_part)
            df = pandas.concat(dfs)
            data_set = DeptDataSet(self.config.DATA_PATH, df)
            self.data[phase] = data_set

    def distribute1(self):
        self.data['train'] = DeptDataSet(self.config.DATA_PATH)

    def train(self):
        return self.data['train'].get_all()

    def valid(self):
        return self.data['validation'].get_all()
