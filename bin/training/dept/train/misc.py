import numpy as np
from keras.callbacks import ModelCheckpoint, Callback


class ModelStepCheckPoint(Callback):
    """
    没2000步存一次
    """

    def __init__(self, filepath, monitor='val_loss', verbose=0, mode='min', period=1000):
        super(ModelStepCheckPoint, self).__init__()
        self.monitor = monitor
        self.verbose = verbose
        self.filepath = filepath
        self.period = period

        self.epoch = 0
        self.step = 0

        assert mode in ['min', 'max']
        if mode == 'min':
            self.monitor_op = np.less
            self.best = np.Inf
        elif mode == 'max':
            self.monitor_op = np.greater
            self.best = -np.Inf

    def on_epoch_begin(self, epoch, logs=None):
        self.epoch = epoch

    def on_batch_begin(self, batch, logs=None):
        self.step = batch

    @property
    def version(self):
        version = str(self.epoch).zfill(2) + '-' + str(self.step).zfill(5)
        return version

    def on_batch_end(self, batch, logs=None):
        if not batch % self.period == 0:
            return

        file_path = self.filepath.format(self.version, logs['loss'])
        current = logs.get(self.monitor)
        if self.monitor_op(current, self.best):
            print('version %s: %s improved from %0.5f to %0.5f, saving model to %s'
                  % (self.version, self.monitor, self.best, current, file_path))
            self.best = current
            self.model.save(file_path, overwrite=True)
        else:
            print('version %05s: %s did not improve' % (self.version, self.monitor))
