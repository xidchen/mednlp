import global_conf
import configparser
from mednlp.dept.pet.rule import RuleWorker
from mednlp.dept.pet.model import ModelWorker, HumanPetModel


class HumanPetWorker(object):
    def __init__(self):
        self.rule_worker = RuleWorker()
        self.model_worker = ModelWorker()

        parser = configparser.ConfigParser()
        parser.read(global_conf.cfg_path)
        model_path = parser.get('HUMAN_OR_PET_MODEL', 'path')
        # model_path = '/home/fangcheng/fc/pet/model-e011-l0.038.h5'
        self.model = HumanPetModel(model_path)

    def execute(self, sentence) -> dict:
        human_score = 0
        animal_exist = self.rule_worker.contain_animal_word(sentence)
        if not animal_exist:
            human_score = 1
        else:
            rule_result = self.rule_worker.contain_white_word(sentence)
            human_score += rule_result * 0.4

            temp_data = self.model_worker.pre(sentence)
            model_result = self.model_worker.execute(self.model, temp_data)
            human_score += model_result * 0.5

        is_human = human_score > 0.45
        subject = 'human' if is_human else 'pet'
        pet_score = 1 - human_score
        result = {'subject': subject, 'score': pet_score}
        return result


# def tet():
# from mednlp.dept.pet.get_ani_disease import read_data
# import numpy as np

#     manager = HumanPetWorker()
#     samples = read_data()
#     cm = np.zeros((2, 2))
#     for sample in samples:
#         pred = manager.execute(sample['sentence'])
#         print(pred, end=' ')
#         print(sample)
#         cm[1 - int(pred)][sample['label'] - 1] += 1
#     print(cm)


def tet1():
    manager = HumanPetWorker()
    sentences = ['我被我的狗咬了',
                 '我的狗被我咬了',
                 '我的猫得了猫廯，好难受',
                 '最近发烧39度，你看我牛逼不？',
                 '我家猪猪越吃越胖',
                 '我家的猫猫，3年了，上个月死了，怎么这么黄啊',
                 '感冒咳嗽流鼻涕'
                 ]
    for s in sentences:
        result = manager.execute(s)
        print(result)


if __name__ == '__main__':
    tet1()
