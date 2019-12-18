import configparser

from mednlp.dept.module.c_py.worker import CharPinyinWorker
from mednlp.dept.module.cnn.worker import CNNWorker
# from mednlp.dept.module.c_py.model import CharPinyinModel
# from mednlp.dept.module.cnn.model import CNNModel
from mednlp.dept.common.result import ResultHelper
from onnet.arch.models.tf_serving.model import TFServeModel


class AdviceManager(object):
    def __init__(self, cfg_path):
        parser = configparser.ConfigParser()
        parser.read(cfg_path)

        serving_ip = parser.get('TFServing', 'IP')
        serving_port = parser.get('TFServing', 'PORT')
        part_url = parser.get('TFServing', 'BASE_URL')
        base_url = 'http://' + serving_ip + ':' + serving_port + '/' + part_url

        c_py_url = parser.get('DEPT_CLASSIFY_CHAR_PINYIN_MODEL', 'url')
        c_py_url = base_url + '/' + c_py_url
        self.c_py_model = TFServeModel(c_py_url)
        cnn_url = parser.get('DEPT_CLASSIFY_TEXTCNN_MODEL', 'url')
        cnn_url = base_url + '/' + cnn_url
        self.cnn_model = TFServeModel(cnn_url)

        # c_py_path = parser.get('DEPT_CLASSIFY_CHAR_PINYIN_MODEL', 'path')
        # self.c_py_model1 = CharPinyinModel(c_py_path, 0)
        # self.c_py_model1.load()
        # cnn_path = parser.get('DEPT_CLASSIFY_TEXTCNN_MODEL', 'path')
        # self.cnn_model1 = CNNModel(cnn_path, 1)
        # self.cnn_model1.load()

        self.c_py_worker = CharPinyinWorker()
        self.cnn_worker = CNNWorker()

    def execute(self, query):
        cpy_data = self.c_py_worker.pre(query)
        cpy_model_results = self.c_py_worker.execute(cpy_data, self.c_py_model)
        cpy_results = self.c_py_worker.post(cpy_model_results)

        cnn_data = self.cnn_worker.pre(query)
        cnn_model_results = self.cnn_worker.execute(cnn_data, self.cnn_model)
        cnn_results = self.cnn_worker.post(cnn_model_results)

        results = [cnn_results, cpy_results]
        weights = [0.4, 0.6]
        merge_result = ResultHelper.merge(results, weights)
        merge_result.sort()
        return merge_result
