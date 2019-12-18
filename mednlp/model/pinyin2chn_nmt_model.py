# -*- coding: utf-8 -*-
from ailib.model.base_model import BaseModel
from mednlp.model.nmt_model.nmt_model import NMTmodel
from mednlp.utils.utils import unicode_python_2_3
import sys
import numpy as np


class pinyin2chnNMT(BaseModel):
    def initialize(self, model_version=1, **kwargs):
        self.model_version = model_version
        self.src_vocab_file = kwargs.get('src_vocab_file')
        self.tgt_vocab_file = kwargs.get('tgt_vocab_file')
        self.special_name_list = [x.strip() for x in open(kwargs.get('name_file')).readlines()]
        self.load_model()
        self.threshold = 0.98

    def load_model(self):
        # load LSTM model
        self.model = NMTmodel(self.model_path, self.src_vocab_file, self.tgt_vocab_file)
        self.model.build()

    def predict(self, query, sex=1, age=-1, type=1):
        input_pinyin = query[0]
        input_text = [c for c in unicode_python_2_3(query[1])]
        output_text, score = self.model.predict(input_pinyin)
        if not sys.version > '3':
            output_text = output_text.split(' ')
        else:
            output_text = output_text.decode().split(' ')
        score = [float(s) for s in score.split(' ')]
        final_text = self.get_final_str(input_text, output_text, score)
        if not sys.version > '3':
            final_text = unicode(final_text)
        else:
            final_text = final_text
        has_error = self.check_error(input_text, final_text)

        return has_error, final_text

    def get_final_str(self, input_text, output_text, score):
        final_text = []
        err_positions = []
        if len(input_text) <= len(output_text):
            for i in range(len(input_text)):
                if (score[i] < self.threshold or output_text[i] == u'<unk>' or
                        output_text[i] == u'！' or output_text[i] == u'？'):
                    final_text.append(input_text[i])
                else:
                    final_text.append(output_text[i])
                    if input_text[i] != output_text[i]:
                        err_positions.append(i)
        else:
            for i in range(len(output_text)):
                if (score[i] < self.threshold or output_text[i] == u'<unk>' or
                        output_text[i] == u'！' or output_text[i] == u'？'):
                    final_text.append(input_text[i])
                else:
                    final_text.append(output_text[i])
                    if input_text[i] != output_text[i]:
                        err_positions.append(i)
            final_text.extend(input_text[len(output_text):])
        err_groups = self.group_errors(np.asarray(err_positions))
        final_text = self.search_for_names(input_text, final_text, err_groups)
        final_text = ''.join(final_text)
        return final_text

    @staticmethod
    def group_errors(error_groups):
        continous_indices = [i for i, df in enumerate(np.diff(error_groups)) if df != 1]
        continous_indices = np.hstack([-1, continous_indices, len(error_groups) - 1])
        continous_indices = np.vstack([continous_indices[:-1] + 1, continous_indices[1:]]).T
        return continous_indices.astype(np.int32).tolist()

    def search_for_names(self, input_text, final_text, err_groups):
        input_text = ''.join(input_text)
        for err_group in err_groups:
            start_idx, end_idx = err_group
            err_text = input_text[start_idx: end_idx + 1]
            for special_name in self.special_name_list:
                if err_text in special_name and special_name in input_text and input_text.index(special_name[0]) <= start_idx and input_text.index(special_name[-1]) >= end_idx:
                    final_text[input_text.index(special_name[0]):input_text.index(special_name[-1])+1] = special_name
        return final_text

    @staticmethod
    def check_error(raw_query, corrected_query):
        has_error = 0
        for raw, correct in zip(raw_query, corrected_query):
            if raw != correct:
                has_error = 1
                break
        return has_error


if __name__=='__main__':
    import global_conf
    pinyin2chn_nmt = pinyin2chnNMT(cfg_path=global_conf.cfg_path,
                                   model_section='PINYIN2CHN_MODEL',
                                   src_vocab_file=global_conf.chinese_correct_src_vocab_file,
                                   tgt_vocab_file=global_conf.chinese_correct_tgt_vocab_file)

    query = ['wo tou teng', '我头疼']
    result = pinyin2chn_nmt.predict(query)
    print(result)