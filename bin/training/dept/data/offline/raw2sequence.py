import codecs
from bin.training.dept.data.offline.processer import DeptPreProcessor
from bin.training.dept.data.offline.pre_io import DeptPreWriter


class DeptRawMaker(object):
    def __init__(self, raw_path, output_path):
        self.raw_stream = codecs.open(raw_path, 'r', encoding='utf-8')

        self.processor = DeptPreProcessor()
        self.writer = DeptPreWriter(output_path)

    def make(self):
        index = 0
        for count, line in enumerate(self.raw_stream):
            if count % 1000 == 0:
                print('the {}th has started'.format(count))
            # if count < 33000:
            #     continue

            if not self.processor.could_split(line):
                continue
            if not self.processor.could_find_dept():
                continue
            if not self.processor.could_vectorize():
                continue

            result = self.processor.raw2pre()
            self.writer.write_single(index, **result)
            index += 1

        self.writer.close()


def make_dept_data():
    input_path = '/data/home/fangcheng/data/mednlp/dept/entity_clean/entity.txt'
    output_path = '/data/home/fangcheng/data/mednlp/dept/2019_fc'
    data_maker = DeptRawMaker(input_path, output_path)
    data_maker.make()


if __name__ == '__main__':
    make_dept_data()
