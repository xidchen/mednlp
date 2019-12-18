from bin.training.dept.data.offline.pre_io import DeptPreReader
from bin.training.dept.data.offline.processer import DeptPreProcessor


class CheckData(object):
    def __init__(self, input_path):
        self.reader = DeptPreReader(input_path)
        self.processor = DeptPreProcessor()

    def check(self):
        df = self.reader.df
        self.reader.df = df[(df['dept'] == 43)]
        for i in range(0, 100):
            data = self.reader.read_single(index=i)
            char_x, py_x, char_y, age, sex = data
            # if len(char_x) != len(py_x):
            #     print('the {}th not equal: {}/{}'.format(i, len(char_x), len(py_x)))

            char, pinyin, dept = self.processor.check(char_x, py_x, char_y[0])
            print(dept)
            print(''.join(char))
            print(''.join(pinyin))
            print()

    def check1(self):
        char_x, py_x, char_y, age, sex = self.reader.read_all()
        print(len(char_x))

    def check_df(self):
        df = self.reader.df
        # for i in range(1, 20):
        #     min_length = i * 5
        #     max_length = (i + 1) * 5
        #     part_df = df[(df['char_length'] > min_length) & (df['char_length'] < max_length)]
        #     print('length: {}-{} has {} samples'.format(min_length, max_length, len(part_df)))

        for i in range(46):
            dept = self.processor.lawyer.get_dept(i, reverse=True)
            part_df = df[(df['dept'] == i)]
            print('dept {} has {} samples'.format(dept, len(part_df)))


def check():
    input_path = '/data/home/fangcheng/data/mednlp/dept/0924_df'
    checker = CheckData(input_path)
    checker.check_df()


if __name__ == '__main__':
    check()
