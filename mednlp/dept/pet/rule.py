import re
import numpy as np
from mednlp.dept.pet.get_ani_disease import read_data


class RuleWorker(object):
    def __init__(self):
        white_list = ['鼠疫', '鼠药', '杀鼠剂', '鼠咬', '鼠乳病', '鼠伤', '鼠型', '鼠标',
                      '猪布', '猪肉', '猪带', '猪囊', '猪流感', '猪霍乱', '猪链球菌',
                      '牵牛花', '牛肉', '牛痘', '牛皮癣', '牛皮病癣', '疯牛病', '牛疥疮', '牛布', '牛牙症',
                      '狗咬', '狗抓',
                      '鸟啄', '鸟疫', '鸟病', '鸟热', '鸟氨酸', '鸟嘌呤', '鸟脚',
                      '蛇咬', '蛇毒', '蛇皮癣', '蛇缠腰', '蛇果疮',
                      '猫抓', '猫叫综合征', '猫廯',
                      '蜈蚣咬', '蜈蚣螫', '蜈蚣蜇',
                      '兔唇', '兔热病', '兔眼',
                      '蜥蝎毒液中毒',
                      '鱼鳞病', ]
        self.white_conditions = [re.compile('.*' + white + '.*') for white in white_list]
        self.ani_con = re.compile(u'[猪猫粮狗牛鼠蛇蜈蚣兔鸟蜥蜴]')

    def contain_animal_word(self, sentence):
        animal_exist = self.ani_con.findall(sentence)
        return len(animal_exist) > 0

    def contain_white_word(self, sentence):
        result = 0
        for whi_con in self.white_conditions:
            temp = whi_con.match(sentence)
            if temp is not None:
                result = 1
                break
        return result


def tet():
    samples = read_data()
    cm = np.zeros((2, 2))
    rule_worker = RuleWorker()
    for sample in samples:
        pred = rule_worker.contain_white_word(sample['sentence'])
        print(pred, end=' ')
        print(sample)
        cm[pred - 1][sample['label'] - 1] += 1
    print(cm)


if __name__ == '__main__':
    # s = '牛跑完步发红正常吗'
    # print(execute(s))
    tet()
