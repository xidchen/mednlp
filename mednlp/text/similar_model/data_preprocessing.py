# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from mednlp.kg.drgs.obtain_train_data import SQLDataCombine, SimilarDataTranslate
from mednlp.text.similar_model.model_predict import ModelPredict

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

DC_Model = SQLDataCombine()
DW_model = SimilarDataTranslate()


model_dir = '/data/mednlp/models/consistency_model/'
PD_Model = ModelPredict(model_dir)


class DataDeal(SimilarDataTranslate):

    def __init__(self):
        super(DataDeal, self).__init__()

    def data_obtain(self, inputfile, outputfile, nums, data_dir):
        sentence_list = self.get_data_init(inputfile, nums)
        self.merge_data_label(sentence_list, outputfile, data_dir)

    def get_data_init(self, inputfile, nums):
        sentence_list = []
        k = 0
        with open(inputfile, 'r', encoding='utf-8') as reader:
            for line in reader:
                k += 1
                if k <= nums:
                    sentence_list.append(line.strip('\n'))
                else:
                    break
        return sentence_list

def data_obtain_and_predict(sql_list, label_name, column_list, filename, data_dir):
    '''
    获取sql数据库中关于某种疾病的数据合并需要的列
    :param sql_list: [sql_code1, sql_code2,...]
    :param label_name: str
    :param column_list:[colname1, colname2,...]
    :return:
    '''
    #
    data_list = DC_Model.data_combine(sql_list, column_list, label_name)
    outputfile_name = 'consistency_data_' + filename + '.txt'
    DW_model.merge_data_label(data_list, outputfile_name, data_dir)
    logging.info('The data has been obtained!')
    output_file_pred = filename + '_predict.txt'
    outputfile = os.path.join(data_dir, output_file_pred)
    inputfile = os.path.join(data_dir, outputfile_name)
    logging.info('Model Predict')
    PD_Model.batch_predict_write(inputfile, outputfile)
    logging.info('Finished!')

if __name__ == '__main__':
    from mednlp.text.similar_model.sql_disease import sql_list, disease_list

    data_dir = '/data/yinwd_data/silimar_data/predict_set/'
    label_name = 'disease_name'
    column_list = ['chief_complaint', 'medical_history']

    for index, sql in enumerate(sql_list):
        dis_name = disease_list[index]
        data_obtain_and_predict([sql], label_name, column_list, dis_name, data_dir)


