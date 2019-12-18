# -*- coding: utf-8 -*-

from ailib.model.base_model import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
import global_conf
import pandas as pd
import numpy as np
import codecs
import json
from mednlp.utils.file_operation import get_disease_name


class DiagnoseReliabilityClassifier(BaseModel):
    ''' 判别诊断结果可靠性 '''

    def initialize(self, moder_version=1, **kwargs):
        self.w = 0.7
        self.accuracy = 0.9
        self.load_dict(global_conf.disease_classify_dict_path)
        self.moder_version = moder_version

        model_base_path = self.model_path
        model_path = model_base_path + "." + str(self.moder_version) + '.m'
        self.load_model(model_path)

    def load_model(self, model_path):
        self.classifier = joblib.load(model_path)

    def load_dict(self, dictPath):
        allDiseases = {}
        with codecs.open(dictPath, 'r', 'utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('\t')
                if len(items) == 2:
                    allDiseases[items[0]] = items[1]
        self.allDiseases = allDiseases

        self.id_name = get_disease_name()

    def calc_accuracy(self, diseases):
        # 格式化输入的数据为模型可用
        X = []
        for disease in diseases[:5]:
            diseaseId = disease['disease_id']
            name = self.id_name[diseaseId]
            label = self.allDiseases.get(name)
            score = disease['score']
            X.append(label)
            X.append(score)
        if len(X) < 10:
            for _ in range(int(5 - len(X) / 2)):
                X.append(-1)
                X.append(0)

        # 预测诊断结果可靠性
        predictProba = self.classifier.predict_proba(np.array(X).reshape((1, -1)))
        confidence = 0
        try:
            confidence = predictProba[0][1]
        except Exception:
            pass

        if confidence >= self.w:
            # 是否确诊置信度大于阈值，增加top1结果的accuracy值。公式为：
            # 是否确诊准确率 + (1 - 是否确诊准确率) * ((当前是否确诊置信度 - 阈值) / (1 - 阈值))
            # 当是否确诊置信度为1时，accuracy值为1
            # 当是否确诊置信度等于阈值时，accuracy值为是否确诊准确率
            top1Accuracy = self.accuracy + (1 - self.accuracy) * (confidence - self.w) / (1 - self.w)
            otherAccuracy = 1 - top1Accuracy
        else:
            # 是否确诊置信度小于阈值，降低top1结果的accuracy值
            top1Accuracy = self.accuracy * (confidence / self.w)
            otherAccuracy = min(1 - top1Accuracy, top1Accuracy)

        otherScoreSum = sum(X[3::2])
        for i, desease in enumerate(diseases):
            if i == 0:
                diseases[i]['accuracy'] = round(top1Accuracy, 4)
            else:
                diseases[i]['accuracy'] = round(otherAccuracy * diseases[i]['score'] / otherScoreSum, 4)

        return diseases

    def fit(self, X, Y):
        self.classifier = RandomForestClassifier(n_jobs=-1, random_state=27, n_estimators=170)
        self.classifier.fit(X, Y)

    def predict(self, X):
        prob = self.classifier.predict_proba(X)
        return np.array([1 if p[1] > self.w else 0 for p in prob])

    def test(self, testX, testY):
        predictions = self.predict(testX)
        self._show_test_summary(predictions, testY)

    def _show_test_summary(self, predictions, testY, dataLength=0):
        if dataLength == 0:
            dataLength = len(predictions)
        print(pd.crosstab(testY, predictions, rownames=['actual'], colnames=['preds']))
        print('覆盖率：{0:.2%}'.format(sum(predictions) / dataLength))
        print('准确率：{0:.2%}'.format(np.array(testY).dot(predictions) / sum(predictions)))

    def dump_model(self, dumpName="is_confirmed_rfc.m"):
        joblib.dump(self.classifier, dumpName)


if __name__ == '__main__':
    strDiseases = ''' [
    {
      "disease_id": "40763",
      "score": 0.9901504429,
      "accuracy": 0.9915,
      "disease_name": "胃恶性肿瘤",
      "entity_id": "40763",
      "entity_name": "胃恶性肿瘤"
    },
    {
      "disease_id": "41729",
      "score": 0.0030320858,
      "accuracy": 0.0028,
      "disease_name": "胃溃疡",
      "entity_id": "41729",
      "entity_name": "胃溃疡"
    },
    {
      "disease_id": "6af282f3-31e1-11e6-804e-848f69fd6b70",
      "score": 0.0021747046,
      "accuracy": 0.0018,
      "disease_name": "胃十二指肠溃疡[消化性溃疡]",
      "entity_id": "6af282f3-31e1-11e6-804e-848f69fd6b70",
      "entity_name": "胃十二指肠溃疡[消化性溃疡]"
    },
    {
      "disease_id": "41727",
      "score": 0.0019811413,
      "accuracy": 0.0017,
      "disease_name": "慢性胃炎",
      "entity_id": "41727",
      "entity_name": "慢性胃炎"
    },
    {
      "disease_id": "42167",
      "score": 0.0011521968,
      "accuracy": 0.001,
      "disease_name": "贲门恶性肿瘤",
      "entity_id": "42167",
      "entity_name": "贲门恶性肿瘤"
    },
    {
      "disease_id": "ba55567a-31df-11e6-804e-848f69fd6b70",
      "score": 0.0006280021,
      "accuracy": 0.0005,
      "disease_name": "肝原位癌",
      "entity_id": "ba55567a-31df-11e6-804e-848f69fd6b70",
      "entity_name": "肝原位癌"
    },
    {
      "disease_id": "41740",
      "score": 0.0003394381,
      "accuracy": 0.0003,
      "disease_name": "胃息肉",
      "entity_id": "41740",
      "entity_name": "胃息肉"
    },
    {
      "disease_id": "7f1700b4-31df-11e6-804e-848f69fd6b70",
      "score": 0.0002979389,
      "accuracy": 0.0002,
      "disease_name": "直肠壶腹恶性肿瘤",
      "entity_id": "7f1700b4-31df-11e6-804e-848f69fd6b70",
      "entity_name": "直肠壶腹恶性肿瘤"
    },
    {
      "disease_id": "41831",
      "score": 0.0001262448,
      "accuracy": 0.0001,
      "disease_name": "肝硬化",
      "entity_id": "41831",
      "entity_name": "肝硬化"
    },
    {
      "disease_id": "64406562-8643-11e7-b11b-1866da8f1f23",
      "score": 0.0001178046,
      "accuracy": 0.0001,
      "disease_name": "急性上呼吸道感染",
      "entity_id": "64406562-8643-11e7-b11b-1866da8f1f23",
      "entity_name": "急性上呼吸道感染"
    }
  ]
'''
    diseases = json.loads(strDiseases)
    dr = DiagnoseReliabilityClassifier(cfg_path=global_conf.cfg_path, model_section='DIAGNOSE_RELIABILITY_MODEL')
    dr.load_model('/home/chaipf/work/mednlp/data/dict/is_confirmed_rfc.m')
    print(dr.calc_accuracy(diseases))
