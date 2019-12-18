import numpy as np
from mednlp.dept.utils.vectors import Char2vector
import global_conf
from mednlp.dept.pet.get_ani_disease import read_data
from keras.preprocessing.sequence import pad_sequences
from keras.models import Model, load_model
from keras.layers import Input, Bidirectional, LSTM, Dense
from keras.layers.embeddings import Embedding
from keras.callbacks import ModelCheckpoint
from keras.utils.np_utils import to_categorical


class PetPreProcessor(object):
    def __init__(self):
        self.vector_helper = Char2vector(global_conf.char_vocab_dict_path)

    def raw2pre(self, raw):
        vector = self.vector_helper.get_vector(raw[:100])
        return vector

    @staticmethod
    def pre2train(pre):
        vector = np.array([int(v) for v in pre])
        vectors = vector[np.newaxis, :]
        vectors = pad_sequences(vectors, maxlen=100)
        return vectors


def generate_vector():
    data = read_data()
    output_path = '/home/fangcheng/fc/pet/pet_vector.txt'
    vector_helper = Char2vector(global_conf.char_vocab_dict_path)
    line = '{},{}'
    out_stream = open(output_path, 'w')
    for item in data:
        vector = vector_helper.get_vector(item['sentence'][:100])
        vector_str = ' '.join(vector)
        label_str = str(item['label'])
        line_data = line.format(label_str, vector_str)

        out_stream.write(line_data + '\r\n')
    out_stream.close()


class HumanPetData(object):
    def __init__(self, data_path):
        self.in_stream = open(data_path, 'r')

    def close(self):
        self.in_stream.close()

    def get_data(self):
        labels, vectors = [], []
        for line in self.in_stream.readlines():
            label, vector = line.split(',')
            vector = np.array([int(v) for v in vector.split(' ')])
            labels.append(int(label))
            vectors.append(vector)
        vectors = pad_sequences(vectors, maxlen=100)
        labels = to_categorical(np.array(labels) - 1, num_classes=2)
        samples = len(labels)
        shuffle_indices = np.random.permutation(np.arange(samples))
        labels = np.array(labels)[shuffle_indices]
        vectors = np.array(vectors)[shuffle_indices]
        labels_t = labels[:int(samples * 0.9)]
        vectors_t = vectors[:int(samples * 0.9)]
        labels_v = labels[int(samples * 0.9):]
        vectors_v = vectors[int(samples * 0.9):]
        return vectors_t, labels_t, vectors_v, labels_v


class Trainer(object):
    def __init__(self):
        pre_data_path = '/home/fangcheng/fc/pet/pet_vector.txt'
        self.data = HumanPetData(pre_data_path)
        self.model = HumanPetModel()

    def train(self):
        save_file_name = '/home/fangcheng/fc/pet/model-e{epoch:03d}-l{loss:.3f}.h5'
        checkpoint = ModelCheckpoint(filepath=save_file_name,
                                     monitor='val_categorical_accuracy',
                                     mode='auto',
                                     save_best_only='True')

        xt, yt, xv, yv = self.data.get_data()
        self.model.fit(xt, yt, xv, yv, [checkpoint])


class ModelWorker(object):
    def __init__(self):
        self.processor = PetPreProcessor()

    def pre(self, sentence):
        pre = self.processor.raw2pre(sentence)
        train_data = self.processor.pre2train(pre)
        return train_data

    @staticmethod
    def execute(model, data):
        result = model.predict(data)[0]
        return result[0]


class HumanPetModel(object):
    def __init__(self, model_path=None):
        if model_path is None:
            self.net = self.build_net()
        else:
            self.net = load_model(model_path)

    @staticmethod
    def build_net():
        char_input = Input(shape=(100,))
        char_embedding = Embedding(8000, 32)(char_input)

        lstm1 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True))(char_embedding)
        lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(lstm1)
        out = Dense(2, activation='softmax')(lstm2)
        model = Model(input=char_input, outputs=out)
        model.compile(loss="categorical_crossentropy", metrics=["categorical_accuracy"], optimizer="adam")
        return model

    def predict(self, data):
        return self.net.predict(data)

    def fit(self, xt, yt, xv, yv, callbacks):
        self.net.fit(xt, yt, batch_size=32, epochs=20, validation_data=(xv, yv), callbacks=callbacks)


def tet():
    model_path = '/home/fangcheng/fc/pet/model-e011-l0.038.h5'
    model = HumanPetModel(model_path)
    worker = ModelWorker()

    sentences = ['我被我的狗咬了',
                 '我的狗被我咬了',
                 '我的猫得了猫廯，好难受',
                 '最近发烧39度，你看我牛逼不？',
                 '我家猪猪越吃越胖',
                 '我家的狗狗，3个多月了，昨天称了下刚好10斤，怎么那么瘦啊'
                 ]
    for s in sentences:
        data = worker.pre(s)
        result = worker.execute(model, data)
        print(result)


if __name__ == '__main__':
    # train()
    tet()
