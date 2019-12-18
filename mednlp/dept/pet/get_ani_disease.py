import csv
import re


def display_data():
    p = re.compile(u'[猪猫粮狗牛鼠蛇蜈蚣兔鸟蜥蜴]')

    input_path = '/home/fangcheng/all_disease.csv'
    in_stream = open(input_path, 'r')
    reader = csv.reader(in_stream)
    for i, line in enumerate(reader):
        if i == 0:
            continue
        if len(p.findall(line[0])) > 0:
            print(line[0])


def read_data():
    data_path = '/home/fangcheng/fc/pet/pet.csv'
    stream = open(data_path, 'r')
    reader = csv.reader(stream)
    data = []
    for i, line in enumerate(reader):
        if i == 0:
            continue
        item = {'label': int(line[0]), 'sentence': line[1]}
        data.append(item)

    stream.close()
    return data
