#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import torch
from tqdm import tqdm
import numpy as np
from sklearn import metrics
import global_conf
import torch.nn.functional as F
from ailib.client.ai_service_client import AIServiceClient
from pytorch_pretrained_bert.modeling import BertForSequenceClassification
from pytorch_pretrained_bert.tokenization import BertTokenizer
from mednlp.text.similar_model.classify_model import \
    convert_examples_to_features, SimilarProcessor, convert_single_example_to_feature, InputExample
from torch.utils.data import TensorDataset, DataLoader, SequentialSampler

AIService_Model = AIServiceClient(global_conf.cfg_path, 'AIService')

class SimilarProcessorNew(SimilarProcessor):

    def __init__(self):
        super(SimilarProcessorNew, self).__init__()

    def get_data(self, data_dir_file):
        """See base class."""
        return self._create_examples(
            self._read_tsv(data_dir_file), "pred_data")


class ModelPredict(SimilarProcessorNew):

    def __init__(self, model_dir):
        super(ModelPredict, self).__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_dir = model_dir
        self.max_seq_length = 512
        self.label_list = self.get_labels()
        self.tokenizer = BertTokenizer.from_pretrained(self.model_dir)
        self.model = BertForSequenceClassification.from_pretrained(self.model_dir,
                                                                   num_labels=len(self.label_list))
        self.model.to(self.device)

    def batch_predict_write(self, inputfile, outputfile):
        '''模型测试
        inputfile: 输入文本
        outputfile: 输出文本
        '''
        Output_Data = open(outputfile, 'w', encoding='utf-8')
        test_examples = SimilarProcessorNew().get_data(inputfile)
        test_features = convert_examples_to_features(
            test_examples, self.label_list, self.max_seq_length, self.tokenizer)
        all_input_ids = torch.tensor([f.input_ids for f in test_features], dtype=torch.long)
        all_input_mask = torch.tensor([f.input_mask for f in test_features], dtype=torch.long)
        all_segment_ids = torch.tensor([f.segment_ids for f in test_features], dtype=torch.long)
        all_label_ids = torch.tensor([f.label_id for f in test_features], dtype=torch.long)
        test_data = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_label_ids)

        # print(all_label_ids)
        # Run prediction for full data
        test_sampler = SequentialSampler(test_data)
        test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=8)

        self.model.eval()
        predict = np.zeros((0,), dtype=np.int32)
        gt = np.zeros((0,), dtype=np.int32)
        probability_similar = np.zeros((0,), dtype=np.float64)
        for input_ids, input_mask, segment_ids, label_ids in test_dataloader:
            input_ids = input_ids.to(self.device)
            input_mask = input_mask.to(self.device)
            segment_ids = segment_ids.to(self.device)

            with torch.no_grad():
                logits = self.model(input_ids, segment_ids, input_mask)
                pred = logits.max(1)[1]
                predict = np.hstack((predict, pred.cpu().numpy()))
                gt = np.hstack((gt, label_ids.cpu().numpy()))
                probability = F.softmax(logits ,dim=1)
                probability_similar = np.hstack((probability_similar, probability.cpu().numpy()))
        # print(predict)
        Classification_report = metrics.classification_report(y_true=gt, y_pred=predict, labels=[0, 1],
                                                              target_names=['不相似', '相似'])
        print('Classification_report', Classification_report)
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

    def predict_sample_similar(self, text_a, text_b):
        '''
        给出预测概率
        :param text_a: 输入句子
        :param text_b: 句子b
        :return: 输出预测值和预测概率
        '''
        guid = 1
        example = InputExample(guid, text_a, text_b)
        feature = convert_single_example_to_feature(example, self.max_seq_length, self.tokenizer)
        input_ids = torch.tensor(feature.input_ids, dtype=torch.long).unsqueeze(0)
        input_mask = torch.tensor(feature.input_mask, dtype=torch.long).unsqueeze(0)
        segment_ids = torch.tensor(feature.segment_ids, dtype=torch.long).unsqueeze(0)
        # print(input_ids.size(), input_mask.size(), segment_ids.size())
        self.model.eval()
        input_ids = input_ids.to(self.device)
        input_mask = input_mask.to(self.device)
        segment_ids = segment_ids.to(self.device)
        with torch.no_grad():
            logits = self.model(input_ids, segment_ids, input_mask)
            pred = logits.max(1)[1]
            probability = F.softmax(logits, dim=1)[0]
        return pred.cpu().numpy(), probability.cpu().numpy()


class ModelOptimize(object):

    def __init__(self, text_a, text_b):
        self.text_a = text_a
        self.text_b = text_b

        super(ModelOptimize, self).__init__()

    def sentence_len_compare(self):
        len_a = len(self.text_a)
        len_b = len(self.text_b)
        if  len_b*0.8 <= len_a <= len_b*1.2:
            weight_len = 1
        elif len_b*0.6 <= len_a <= len_b*1.4:
            weight_len = 0.8
        elif len_b*0.4 <= len_a <= len_b*1.6:
            weight_len = 0.6
        elif len_b*0.2 <= len_a <= len_b*1.8:
            weight_len = 0.4
        else:
            weight_len = 0.2
        return  weight_len

    def entity_num_compare(self):
        '''
        当实体个数不同加权重（一般text_b是标准的病例），当输入句子和标准病历的实体数量重叠越多权重越大，而且输入句子不能有过多的非标准病历的实体。
        :return: entity_weight的概率
        '''
        entity_a = self._get_entityword(AIService_Model.query({'q': self.text_a}, 'entity_extract'))
        entity_b = self._get_entityword(AIService_Model.query({'q': self.text_b}, 'entity_extract'))
        len_a = len(entity_a)
        len_b = len(entity_b)
        join_ab = len(entity_a & entity_b)
        # print(entity_a, entity_b, join_ab)
        if join_ab >= len_a*0.8 and join_ab >= len_b*0.8:
            entity_weight = 1
        elif join_ab >= len_a*0.6 and join_ab >= len_b*0.6:
            entity_weight = 0.75
        elif join_ab >= len_a*0.4 and join_ab >= len_b*0.4:
            entity_weight = 0.5
        elif join_ab >= len_a*0.2 and join_ab >= len_b*0.2:
            entity_weight = 0.25
        else:
            entity_weight = 0
        return entity_weight

    def _get_entityword(self, entity_result):
        entity_word = []
        entity_list = entity_result.get('data')
        if entity_list:
            for edict in entity_list:
                etype = edict.get('type')
                eword = edict.get('entity_name')
                if etype in ['symptom', 'disease', 'treatment', 'physical', 'examination', 'medicine']:
                    entity_word.append(eword)
        return set(entity_word)


def pred_probability(text_a, text_b, model_pred):
    pred, probability = model_pred.predict_sample_similar(text_a, text_b)
    prob0 = probability[1]
    prob1 = ModelOptimize(text_a, text_b).sentence_len_compare()
    prob2 = ModelOptimize(text_a, text_b).entity_num_compare()
    result = 0.6 * prob0 + 0.1 * prob1 + 0.3 * prob2
    # print('概率Model',prob0, '概率句子长度', prob1, '概率实体数量', prob2)
    return round(result, 4)

def pred_exit_probability(text_a, text_b, prob0):
    prob1 = ModelOptimize(text_a, text_b).sentence_len_compare()
    prob2 = ModelOptimize(text_a, text_b).entity_num_compare()
    result = 0.6 * float(prob0) + 0.1 * prob1 + 0.3 * prob2
    # print('概率Model',prob0, '概率句子长度', prob1, '概率实体数量', prob2)
    return round(result, 4)

if __name__ == '__main__':
    data_dir = '/data/yinwd_data/silimar_data/'
    model_dir = '/data/yinwd_data/consistency_model_20190509/'
    inputfile = os.path.join(data_dir, 'test.tsv')
    outputfile = os.path.join(data_dir, 'test_predict.txt')
    # write_result_predict(inputfile, outputfile, model_dir, max_seq_length)
    model_pred = ModelPredict(model_dir)
    # model_pred.batch_predict_write(inputfile, outputfile)
    sentence1 = '咳嗽3天。3天前无明显诱因下咳嗽，阵咳，喉中有痰，不易咯出。'
    sentence2 = '咳嗽3天。3天前无明显诱因下咳嗽，阵咳，喉中有痰，不易咯出。'
    pred, probability = model_pred.predict_sample_similar(sentence1, sentence2)
    print(pred, probability)
    result = pred_probability(sentence1, sentence2, model_pred)
    print(result)