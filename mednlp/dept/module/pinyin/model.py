from keras.models import model_from_json


class PinyinModel(object):
    def __init__(self, model_path, version=None):
        self.model_path = model_path
        self.model_version = version
        self.net = None

    def load(self):
        """加载已经存在的模型,其中version为版本号"""
        version = self.model_version
        model_base_path = self.model_path
        model_path = model_base_path + '.' + '%s' + '.arch'
        model_arch = model_path % version
        model_weight_path = model_base_path + '.' + '%s' + '.weight'
        model_weight = model_weight_path % version
        model = model_from_json(open(model_arch).read())
        # model = model_from_json(open(model_arch).read(), {'AttentionLayer': AttentionLayer})
        model.load_weights(model_weight, by_name=True)
        self.net = model
        print('pinyin model has restored!')

    def predict(self, data):
        result = self.net.predict(data)
        return result
