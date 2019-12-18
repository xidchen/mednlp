import os
import codecs
from bin.training.dept.data.offline.processer import DeptPreProcessor
# from bin.training.dept.data.offline.clean.duplicate import QuerySetter


from bin.training.dept.data.offline.clean.entity import EntityFilter
# from bin.training.dept.data.offline.clean.model import ModelJudge


class DeptRawMaker(object):
    def __init__(self, raw_path, output_path):
        self.raw_stream = codecs.open(raw_path, 'r', encoding='utf-8')

        self.processor = DeptPreProcessor()
        # self.query_setter = QuerySetter()
        self.entity_filter = EntityFilter()
        # self.judge = ModelJudge()
        no_entity_path = os.path.join(output_path, 'no_entity.txt')
        entity_path = os.path.join(output_path, 'entity.txt')
        self.no_e_stream = open(no_entity_path, 'w')
        self.e_stream = open(entity_path, 'w')

    def make(self):
        for count, line in enumerate(self.raw_stream):
            if count % 1000 == 0:
                print('the {}th has started'.format(count))
            # if count < 33000:
            #     continue

            if not self.processor.could_split(line):
                continue
            if not self.processor.could_find_dept():
                continue
            query = self.processor.splits[0]
            # dept = self.processor.splits[3]

            # self.query_setter.need_to_reserve(query)
            # self.judge.need_to_reserve(query, dept)
            if not self.entity_filter.need_to_reserve(query):
                print(line)
                self.no_e_stream.write(line)
            else:
                self.e_stream.write(line)

        self.no_e_stream.close()
        self.e_stream.close()


def make_dept_data():
    input_path = '/data/home/fangcheng/data/mednlp/dept/entity_clean/no_duplicate.txt'
    output_path = '/data/home/fangcheng/data/mednlp/dept/entity_clea'
    data_maker = DeptRawMaker(input_path, output_path)
    data_maker.make()


if __name__ == '__main__':
    make_dept_data()
