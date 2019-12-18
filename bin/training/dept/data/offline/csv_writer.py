import pandas as pd


class CsvWriter(object):
    def __init__(self, output_path, index=0):
        self.output_path = output_path
        self.index = index

    def write_line(self, content):
        assert isinstance(content, dict)
        for key, value in content.items():
            content[key] = [value]
        pd_line = pd.DataFrame.from_dict(content)
        write_header = self.index == 0
        pd_line.to_csv(self.output_path, mode='a', index=False, header=write_header)
        self.index += 1

    def write_lines(self, content):
        assert isinstance(content, dict)
        line_num = 0
        for i, (key, value) in enumerate(content.items()):
            if i == 0:
                line_num = len(value)
                continue
            assert len(value) == line_num
        pd_line = pd.DataFrame.from_dict(content)
        write_header = self.index == 0
        pd_line.to_csv(self.output_path, mode='a', index=False, header=write_header)
        self.index += line_num
