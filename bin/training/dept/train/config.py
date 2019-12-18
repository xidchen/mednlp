import os


class DeptConfig(object):
    def __init__(self):
        """

        """
        '''path related'''
        self.RESOURCE_PATH = '/data/home/fangcheng/fc/dept/resource'
        self.BRANCH_NAME = 'b-lstm'
        self.BRANCH_PATH = os.path.join(self.RESOURCE_PATH, self.BRANCH_NAME)
        if not os.path.exists(self.BRANCH_PATH):
            os.mkdir(self.BRANCH_PATH)
        self.DATA_PATH = '/data/home/fangcheng/data/mednlp/dept/2019_fc'

        '''training related'''
        self.CRITERION = "categorical_crossentropy"
        self.METRIC = ["categorical_accuracy"]
        self.OPTIMIZER = "adam"

        self.CLASSES = 45
        self.BATCH_SIZE = 512
        self.EPOCHS = 3

        self.CHAR_NUM = 100
        self.PINYIN_NUM = 100
        self.CHAR_DICT_SIZE = 8000
        self.PINYIN_DICT_SIZE = 500
