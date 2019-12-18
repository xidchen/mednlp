import random
import numpy as np

from bin.training.dept.data.offline.pre_io import DeptPreReader
from bin.training.dept.data.offline.processer import DeptPreProcessor
from bin.training.dept.train.config import DeptConfig


class DeptDataSet(object):
    def __init__(self, data_path, df=None):
        self.reader = DeptPreReader(data_path, df)
        self.processor = DeptPreProcessor()
        self.config = DeptConfig()

        self.total = len(self.reader.df)

    def __len__(self):
        return self.total

    def get_all(self):
        """
        内存不足以吃下所有数据，该方法不支持
        :return:
        """
        char_x, py_x, dept, age, sex = self.reader.read_all()
        # char_x, py_x, dept = self.reader.read_all1()
        char, pinyin, dept = self.processor.pre2train(char_x, py_x, dept)
        return [char, pinyin], dept

    def get_single_by_random(self):
        batch_size = self.config.BATCH_SIZE
        part_size = 128
        part = 0
        while (part + 1) * batch_size * part_size < self.total:
            part_start = part * batch_size * part_size
            part_stop = (part + 1) * batch_size * part_size
            char_x, py_x, dept, age, sex = self.reader.read_part(part_start, part_stop)
            # TODO: do some shuffle
            char, pinyin, dept = self.processor.pre2train(char_x, py_x, dept)
            for i in range(part_size):
                batch_start = i * batch_size
                batch_stop = (i + 1) * batch_size
                yield char[batch_start:batch_stop], pinyin[batch_start:batch_stop], dept[batch_start:batch_stop]
            part += 1


def tet_reader():
    data_path = '/data/home/fangcheng/data/mednlp/dept/2019_fc'
    reader = DeptDataSet(data_path)
    (char, pinyin), dept = reader.get_all()
    print(char.shape)


if __name__ == '__main__':
    tet_reader()
