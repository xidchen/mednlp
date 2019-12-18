import os
from .net import DeptClsNet


class DeptClsModel(object):
    def __init__(self, config):
        self.net = DeptClsNet(config).build_net()
        self.config = config

    def load(self):
        in_path = self.config.BRANCH_PATH
        # arch_path = os.path.join(in_path, 'dept.arch')
        weight_path = os.path.join(in_path, 'dept.weight')
        self.net.load_weights(weight_path)

    def save(self):
        out_path = self.config.BRANCH_PATH
        weight_path = os.path.join(out_path, 'dept.weight')
        self.net.save_weights(weight_path)

        arch_path = os.path.join(out_path, 'dept.arch')
        json_string = self.net.to_json()
        open(arch_path, 'w').write(json_string)

    def predict(self, char, pinyin):
        self.net.predict([char, pinyin])

    def fit(self, data, callbacks=None):
        callbacks = callbacks if callbacks is not None else []
        criterion = self.config.CRITERION
        metric = self.config.METRIC
        optimizer = self.config.OPTIMIZER
        self.net.compile(loss=criterion, metrics=metric, optimizer=optimizer)

        epoch = self.config.EPOCHS
        bs = self.config.BATCH_SIZE

        train_x, train_y = data.train()
        valid_x, valid_y = data.valid()
        self.net.fit(train_x, train_y,
                     batch_size=bs, epochs=epoch,
                     validation_data=(valid_x, valid_y),
                     callbacks=callbacks)

        # steps_per_epoch = int(len(data.train_reader) / self.config.BATCH_SIZE)
        # valid_steps = int(len(data.valid_reader) / self.config.BATCH_SIZE)

        # self.net.fit_generator(data.train_gen(), steps_per_epoch=steps_per_epoch,
        #                        epochs=epoch, max_q_size=10,
        #                        validation_data=data.valid_gen(), validation_steps=valid_steps,
        #                        callbacks=callbacks)
