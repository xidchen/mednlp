#/!usr/bin/env python
# -*- coding: utf-8 -*-
import os
import torch
from tqdm import tqdm
import numpy as np
from sklearn import metrics

from pytorch_pretrained_bert.modeling import BertForSequenceClassification
from pytorch_pretrained_bert.tokenization import BertTokenizer
from mednlp.text.similar_model.classify_model import convert_examples_to_features, SimilarProcessor
from torch.utils.data import TensorDataset, DataLoader, SequentialSampler
class SimilarProcessorNew(SimilarProcessor):

    def __init__(self):
        super(SimilarProcessorNew, self).__init__()

    def get_data(self, data_dir_file):
        """See base class."""
        return self._create_examples(
            self._read_tsv(data_dir_file), "pred_data")


def write_result_predict(inputfile, outputfile, model_dir, max_seq_length):
    '''模型测试
    Args:
    model: 模型
	processor: 数据读取方法
	args: 参数表
	label_list: 所有可能类别
	tokenizer: 分词方法
	device
    '''
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    label_list = SimilarProcessorNew().get_labels()
    tokenizer = BertTokenizer.from_pretrained(model_dir)
    model = BertForSequenceClassification.from_pretrained(model_dir, num_labels=len(label_list))
    model.to(device)
    Output_Data = open(outputfile, 'w', encoding='utf-8')
    test_examples = SimilarProcessorNew().get_data(inputfile)
    test_features = convert_examples_to_features(
        test_examples, label_list, max_seq_length, tokenizer)
    all_input_ids = torch.tensor([f.input_ids for f in test_features], dtype=torch.long)
    all_input_mask = torch.tensor([f.input_mask for f in test_features], dtype=torch.long)
    all_segment_ids = torch.tensor([f.segment_ids for f in test_features], dtype=torch.long)
    all_label_ids = torch.tensor([f.label_id for f in test_features], dtype=torch.long)
    test_data = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_label_ids)
    # Run prediction for full data
    test_sampler = SequentialSampler(test_data)
    test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=8)

    model.eval()
    predict = np.zeros((0,), dtype=np.int32)
    probability_similar = np.zeros((0,), dtype=np.float64)
    for input_ids, input_mask, segment_ids, label_ids in test_dataloader:
        input_ids = input_ids.to(device)
        input_mask = input_mask.to(device)
        segment_ids = segment_ids.to(device)

        with torch.no_grad():
            logits = model(input_ids, segment_ids, input_mask)
            pred = logits.max(1)[1]
            predict = np.hstack((predict, pred.cpu().numpy()))
            probability = torch.nn.Softmax()(logits)[:, 1]
            probability_similar = np.hstack((probability_similar, probability.cpu().numpy()))

    # assert len(predict) == len(test_examples)
    sentence_list = open(inputfile, 'r', encoding='utf-8').readlines()
    for index, pred in enumerate(sentence_list):
        line = pred.strip('\n')
        if index < len(predict):
            new_line = line + '\t' + str(predict[index]) \
                       + '\t' + str(round(probability_similar[index], 4))
        else:
            new_line = line + '\t' + '0'
        Output_Data.write(new_line + '\n')

    Output_Data.close()


if __name__ == '__main__':
    data_dir = '/data/yinwd_data/silimar_data/'
    model_dir = '/data/yinwd_data/similar_model_dir/'
    inputfile = os.path.join(data_dir, 'dev.tsv')
    max_seq_length = 512
    outputfile = os.path.join(data_dir, 'dev_predict.txt')
    write_result_predict(inputfile, outputfile, model_dir, max_seq_length)