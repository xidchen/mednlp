# ！/usr/bin/env python
# -*- coding：utf-8 -*-

"""
@Author:chaipf
@Email:	chaipf@guahao.com
@Date:	2019-08-11 Sunday
@Desc:	中医真证型训练程序
"""

import os
import sys
import codecs
from optparse import OptionParser
import tensorflow as tf
from keras.layers.embeddings import Embedding
from keras.layers import Input, Dense, Bidirectional
from keras.layers import LSTM
from keras.layers import concatenate
from keras.models import Model
from keras.utils.np_utils import to_categorical
from keras.preprocessing.sequence import pad_sequences
import keras.backend.tensorflow_backend as ktf
from base_trainer import BaseTrainer
from mednlp.text.vector import Char2vector, Dept2Vector
import global_conf


def get_session(gpu_fraction=1):
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_fraction, allow_growth=True)
    return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


ktf.set_session(get_session())


class TCMSyndromeCharModel(BaseTrainer):
    def __init__(self, file_number=2970861):
        super(TCMSyndromeCharModel, self).__init__(model_name='tcm_syndrome_diagnose')
        self.file_number = file_number
        self.classes = 21
        self.epoch_num = 100
        self.char_num = 6000
        self.disease_num = 10
        self.seq_num = 600
        self.char2vector = Char2vector(dept_classify_dict_path=global_conf.dept_classify_char_dict_path)
        syndrome2vector = Dept2Vector(global_conf.tcm_syndrome_path)
        self.syndrome_to_id = syndrome2vector.name2index
        disease2vector = Dept2Vector(global_conf.tcm_disease_path)
        self.disease_to_id = disease2vector.name2index

    def origin_model(self):
        """  """
        disease_input = Input(shape=(self.seq_num,))
        symptom_input = Input(shape=(self.seq_num,))
        disease_embedding = Embedding(self.disease_num, 4)(disease_input)
        symptom_embedding = Embedding(self.char_num, 16)(symptom_input)
        embedding = concatenate([disease_embedding, symptom_embedding])

        # lstm1 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True))(embedding)
        # lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(lstm1)
        lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(embedding)
        out = Dense(self.classes, activation='sigmoid')(lstm2)
        model = Model(input=[disease_input, symptom_input], outputs=out)

        return model

    def make_train_input(self, file_name):
        diseases, symptoms, syndromes = [], [], []
        y = []
        with codecs.open(file_name, 'r', 'utf-8') as f:
            for line in f.readlines():
                items = line.strip().split('\t')
                diseases.append([self.disease_to_id[items[3]]])
                symptoms.append(self.char2vector.get_char_vector(items[4]))
                # syndromes.append([items[0]])
                syndromes.append([self.syndrome_to_id[i] for i in items[0].split(',')])
                # y.append(sum(to_categorical([self.syndrome_to_id[i] for i in items[0].split(',')], num_classes=self.classes)))

        from sklearn.preprocessing import MultiLabelBinarizer
        multilabel_binarizer = MultiLabelBinarizer()
        multilabel_binarizer.fit(syndromes)
        y = multilabel_binarizer.transform(syndromes)

        x1 = pad_sequences(symptoms, maxlen=self.seq_num)
        x0 = pad_sequences(diseases, maxlen=self.seq_num)
        # y = to_categorical(syndromes, num_classes=self.classes)
        train_num = int(len(syndromes) * 0.9)

        train_x1 = x1[:train_num]
        train_x0 = x0[:train_num]
        train_y = y[:train_num]
        valid_x1 = x1[train_num:]
        valid_x0 = x0[train_num:]
        valid_y = y[train_num:]

        return ([train_x0, train_x1], train_y), ([valid_x0, valid_x1], valid_y)

    def train_model(self, data_file_path, ratio=0.9):
        (train_x, train_y), (valid_x, valid_y) = self.make_train_input(data_file_path)
        model = self.origin_model()
        from keras.optimizers import SGD
        sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(loss="binary_crossentropy", metrics=["binary_accuracy"], optimizer=sgd)
        model.fit(train_x, train_y, validation_data=(valid_x, valid_y), batch_size=512, epochs=self.epoch_num,
                  verbose=1, callbacks=[self.model_checkpoint])
        return model

    def save_model(self, model, version=835):
        """
        :param model: 需要保存的模型
        :param version: 模型保存版本
        :return: 无
        """
        model_arch = '%s.%s.arch' % (self.model_name, version)
        model_weight = '%s.%s.weight' % (self.model_name, version)
        model_arch_path = os.path.join('.', model_arch)
        model_weight_path = os.path.join('.', model_weight)

        # 保存神经网络的结构与训练好的参数
        json_string = model.to_json()
        open(model_arch_path, 'w').write(json_string)
        model.save_weights(model_weight_path)


if __name__ == '__main__':
    command = '\npython %s [-t trainfile -v version]' % sys.argv[0]
    parser = OptionParser(usage=command)
    parser.add_option('-v', dest='version', help='the version of model')
    parser.add_option('--trainfile', dest='trainfile', help='the trainfile of train')
    (options, args) = parser.parse_args()

    tscm = TCMSyndromeCharModel()
    model = tscm.train_model(options.trainfile)
    tscm.save_model(model, version=options.version)
