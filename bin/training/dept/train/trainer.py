import os

from bin.training.dept.train.model import DeptClsModel
from bin.training.dept.data.online.data import DeptData
from bin.training.dept.train.config import DeptConfig
from bin.training.dept.train.misc import ModelStepCheckPoint, ModelCheckpoint


class Trainer(object):
    def __init__(self, config):
        self.config = config
        self.data = DeptData(config)  # 用于生成训练、验证、测试的数据类
        self.model = DeptClsModel(config)

        # 其他工具，如
        # 1.用于评估结果的评估工具类
        # 2.用于记录的日志工具类
        # 3.用于更改学习策略的工具类

    def build_checkpointer(self):
        model_dir = self.config.BRANCH_PATH
        model_name = 'model-e{}-l{}.h5'
        model_path = os.path.join(model_dir, model_name)
        step_cp = ModelStepCheckPoint(filepath=model_path,
                                      monitor='categorical_accuracy',
                                      mode='max',
                                      period=1000)
        model_name = 'model-e{epoch:03d}-l{loss:.3f}.h5'
        model_path = os.path.join(model_dir, model_name)
        epoch_cp = ModelCheckpoint(filepath=model_path,
                                   monitor='val_categorical_accuracy',
                                   mode='auto',
                                   save_best_only='True')
        return [step_cp, epoch_cp]

    def train(self):
        callbacks = []
        checkpoints = self.build_checkpointer()
        callbacks.extend(checkpoints)
        self.model.fit(self.data, callbacks)


def train():
    config = DeptConfig()
    # data = DeptData(config)
    # for d in data.train():
    #     print(d)
    trainer = Trainer(config)
    trainer.train()


if __name__ == '__main__':
    train()
