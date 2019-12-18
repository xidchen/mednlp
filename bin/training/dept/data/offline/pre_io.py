import os
import codecs
import pandas
import numpy as np

from bin.training.dept.data.offline.csv_writer import CsvWriter


class DeptPreWriter(object):
    def __init__(self, output_path):
        char_file = os.path.join(output_path, 'char.txt')
        pinyin_file = os.path.join(output_path, 'pinyin.txt')
        info_file = os.path.join(output_path, 'info.csv')

        self.char_stream = codecs.open(char_file, 'w')
        self.pinyin_stream = codecs.open(pinyin_file, 'w')
        self.info_writer = CsvWriter(info_file)

    def write_single(self, index, dept=0, char='*' * 100, pinyin='*' * 100, sex=0, age=0):
        char_str = ','.join(char)
        pinyin_str = ','.join(pinyin)
        data_format = '{} {}\n'
        char_line = data_format.format(dept, char_str)
        pinyin_line = data_format.format(dept, pinyin_str)

        content = {'index': index, 'sex': sex, 'age': age, 'dept': dept,
                   'char_length': len(char),
                   'char_begin': self.char_stream.tell(),
                   'pinyin_begin': self.pinyin_stream.tell()}

        self.char_stream.write(char_line)
        self.pinyin_stream.write(pinyin_line)
        content['char_end'] = self.char_stream.tell()
        content['pinyin_end'] = self.pinyin_stream.tell()

        self.info_writer.write_line(content)

    def close(self):
        self.char_stream.close()
        self.pinyin_stream.close()


class DeptPreReader(object):
    def __init__(self, input_path, df=None, d_range=None):
        pinyin_path = os.path.join(input_path, 'pinyin.txt')
        char_path = os.path.join(input_path, 'char.txt')
        self.pinyin_stream = codecs.open(pinyin_path, 'r')
        self.char_stream = codecs.open(char_path, 'r')

        self.df = df if df is not None else self.get_df(input_path)
        self.d_range = d_range if d_range is not None else [0, len(self.df) - 1]

    @property
    def total(self):
        total = 0
        if self.total is not None:
            total = len(self.df)
        return total

    @staticmethod
    def get_df(data_path):
        info_file = os.path.join(data_path, 'info.csv')
        df = pandas.DataFrame(pandas.read_csv(info_file))
        return df

    @staticmethod
    def read_from_line(line):
        y_str, x_str = line.strip().split(' ')
        x = np.array([int(x) for x in x_str.split(',')])
        y = np.array([int(y_str)])
        return x, y

    def _get_single(self, stream, offset):
        stream.seek(offset)
        data = stream.readline()
        x, y = self.read_from_line(data)
        return x, y

    def _get_part(self, stream, start_offset, stop_offset):
        length = stop_offset - start_offset
        stream.seek(start_offset)
        data = stream.read(length)
        sample_list = data.split('\n')

        x_list, y_list = [], []
        for sample in sample_list:
            if not len(sample) > 0:
                continue
            x, y = self.read_from_line(sample)
            x_list.append(x)
            y_list.append(y)
        return x_list, y_list

    def read_single(self, index):
        line = self.df.iloc[index]
        char_x, char_y = self._get_single(self.char_stream, int(line['char_begin']))
        py_x, py_y = self._get_single(self.pinyin_stream, int(line['pinyin_begin']))
        assert (char_y == py_y).sum() == 1
        age = line['age']
        sex = line['sex']
        return char_x, py_x, char_y, age, sex

    def read_part(self, start, stop):
        """
        read sample between [start, stop], both sides are included!
        :param start: included
        :param stop: also included
        :return:
        """
        start_sample = self.df.iloc[start]
        stop_sample = self.df.iloc[stop]
        char_x, char_y = self._get_part(self.char_stream, start_sample['char_begin'], stop_sample['char_end'])
        py_x, py_y = self._get_part(self.pinyin_stream, start_sample['pinyin_begin'], stop_sample['pinyin_end'])
        age = self.df[start:stop]['age']
        sex = self.df[start:stop]['sex']
        return char_x, py_x, char_y, age, sex

    def read_all(self):
        char_x_list, char_y_list = [], []
        py_x_list, py_y_list = [], []
        start_index = 0
        for stop_index in self.d_range[1:]:
            start_sample = self.df.iloc[start_index]
            stop_sample = self.df.iloc[stop_index]
            char_x, char_y = self._get_part(self.char_stream, int(start_sample['char_begin']),
                                            int(stop_sample['char_end']))
            py_x, py_y = self._get_part(self.pinyin_stream, int(start_sample['pinyin_begin']),
                                        int(stop_sample['pinyin_end']))
            char_x_list.extend(char_x)
            char_y_list.extend(char_y)
            py_x_list.extend(py_x)
            py_y_list.extend(py_y)

            start_index = stop_index

        age = self.df['age']
        sex = self.df['sex']
        return char_x_list, py_x_list, char_y_list, age, sex

    # def read_all1(self):
    #     char_x, char_y = self._get_all(self.char_stream)
    #     py_x, py_y = self._get_all(self.pinyin_stream)
    #     # age = self.df['age']
    #     # sex = self.df['sex']
    #     return char_x, py_x, char_y
