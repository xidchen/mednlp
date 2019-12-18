import numpy as np
from keras.models import model_from_json


class CharPinyinModel(object):
    def __init__(self, model_path, version=None):
        """
        初始化模型，加载相关字典文件
        """
        self.model_path = model_path
        self.model_version = version
        self.net = None

    def load(self):
        """
        加载模型
        """
        model_base_name = '{}.{}'.format(self.model_path, self.model_version)
        model_arch_name = '{}.arch'.format(model_base_name)
        model_weight_name = '{}.weight'.format(model_base_name)
        model = model_from_json(open(model_arch_name).read())
        model.load_weights(model_weight_name, by_name=True)
        self.net = model
        print('char-pinyin union model has restored!')

    def predict(self, char: np.ndarray, pinyin: np.ndarray):
        dept_values = self.net.predict([char, pinyin])

        return dept_values
