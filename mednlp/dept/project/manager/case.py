import configparser

# from mednlp.dept.module.char.model import CharModel
# from mednlp.dept.module.pinyin.model import PinyinModel
from mednlp.dept.module.char.worker import CharWorker
from mednlp.dept.module.pinyin.worker import PinyinWorker
from mednlp.dept.common.result import ResultHelper
from onnet.arch.models.tf_serving.model import TFServeModel


class CaseManager(object):
    def __init__(self, cfg_path):
        parser = configparser.ConfigParser()
        parser.read(cfg_path)

        serving_ip = parser.get('TFServing', 'IP')
        serving_port = parser.get('TFServing', 'PORT')
        part_url = parser.get('TFServing', 'BASE_URL')
        base_url = 'http://' + serving_ip + ':' + serving_port + '/' + part_url

        char_url = parser.get('DEPT_CLASSIFY_MODEL', 'url')
        char_url = base_url + '/' + char_url
        self.char_model = TFServeModel(char_url)
        pinyin_url = parser.get('DEPT_CLASSIFY_PINYIN_MODEL', 'url')
        pinyin_url = base_url + '/' + pinyin_url
        self.pinyin_model = TFServeModel(pinyin_url)
        #
        # char_path = parser.get('DEPT_CLASSIFY_MODEL', 'path')
        # self.char_model1 = CharModel(char_path, 102)
        # self.char_model1.load()
        # pinyin_path = parser.get('DEPT_CLASSIFY_PINYIN_MODEL', 'path')
        # self.pinyin_model1 = PinyinModel(pinyin_path, 102)
        # self.pinyin_model1.load()

        self.char_worker = CharWorker()
        self.pinyin_worker = PinyinWorker()

    def execute(self, query):
        char_data = self.char_worker.pre(query)
        char_model_results = self.char_worker.execute(char_data, self.char_model)
        char_results = self.char_worker.post(char_model_results)

        py_data = self.pinyin_worker.pre(query)
        py_model_results = self.pinyin_worker.execute(py_data, self.pinyin_model)
        py_results = self.pinyin_worker.post(py_model_results)

        results = [py_results, char_results]
        weights = [0.4, 0.6]
        merge_result = ResultHelper.merge(results, weights)
        merge_result.sort()
        return merge_result
