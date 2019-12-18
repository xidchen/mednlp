from keras.models import Model
from keras.layers import Input, Bidirectional, LSTM, Dense
from keras.layers.embeddings import Embedding
from keras.layers import concatenate


class DeptClsNet(object):
    def __init__(self, config):
        self.char_size = config.CHAR_DICT_SIZE
        self.pinyin_size = config.PINYIN_DICT_SIZE
        self.classes = config.CLASSES

    def build_net(self):
        char_input = Input(shape=(100,))
        pinyin_input = Input(shape=(100,))
        char_embedding = Embedding(self.char_size, 32)(char_input)
        pinyin_embedding = Embedding(self.pinyin_size, 16)(pinyin_input)
        embedding = concatenate([char_embedding, pinyin_embedding])

        lstm1 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02, return_sequences=True))(embedding)
        lstm2 = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.02))(lstm1)
        out = Dense(self.classes, activation='softmax')(lstm2)
        model = Model(input=[char_input, pinyin_input], outputs=out)
        return model

