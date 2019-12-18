#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse
import xml.dom.minidom
import re
import glob
import pandas as pd
import json
import os

class InsepectionRange(object):

    def  __init__(self, disease):
        self.disease = disease
        super(InsepectionRange, self).__init__()

    def xml_parse(self):
        file_route = '/ssddata/cdss/bl/gssdermyy/' + self.disease + '/*/*/LIS/lisinfo.xml'
        # fs = glob.glob('/ssddata/cdss/bl/gssdermyy/肺腺癌/*/*/LIS/lisinfo.xml')
        files = glob.glob(file_route) # 搜索目录下所有的lisinfo.xml文件
        colunames = ['TestName', 'ItemName', 'enName', 'Unit', 'ReferenceValue']

        output_file = open('inspection_valuerange.txt', 'w', encoding='utf-8')

        for file in files:
            ## 每一个文件生成一个大的dataframe，最后组合在一起
            f_disease = re.sub('/.*', '',re.search('gssdermyy.*LIS',file).group().replace('gssdermyy/', ''))
            file_id = re.search('\d+?/LIS', file).group().replace('/LIS', '')
            DOMTree = xml.dom.minidom.parse(file)
            collection = DOMTree.documentElement
            TestModels = collection.getElementsByTagName("TestModel")

            for TestModel in TestModels:
                inspection_df_one = pd.DataFrame(columns=colunames)
                TestName = TestModel.getElementsByTagName('TestName')[0]  #在xml解析树的外层
                if TestName.childNodes: ## 当检查项目为空时，跳过
                    testname = TestName.childNodes[0].data  # 获取检查类的名称（血常规等综合）
                    # print("TestName: %s" % TestName.childNodes[0].data)

                    ItemNames = TestModel.getElementsByTagName('ItemName')[0:]
                    # for ItemName in ItemNames:
                    #     print("ItemName: %s" % ItemName.childNodes[0].data)
                    enNames = TestModel.getElementsByTagName('enName')[0:]  # 在xml解析树的内层
                    Units = TestModel.getElementsByTagName('Unit')[0:]
                    ReferenceValues = TestModel.getElementsByTagName('ReferenceValue')[0:]
                    # 对应字典
                    data_result = {'ItemName': ItemNames,
                                    'enName': enNames,
                                    'Unit': Units,
                                    'ReferenceValue': ReferenceValues
                                   }
                    for item_ins in colunames[1:]:
                        col_data = []
                        xml_data = data_result.get(item_ins)
                        for value_data in xml_data:
                            if value_data.childNodes: # 非空才能提取内容，否则记为''
                                value_result = value_data.childNodes[0].data
                            else:
                                value_result = ''
                            col_data.append(value_result)

                        inspection_df_one['TestName'] = [testname]*len(col_data)
                        inspection_df_one[item_ins] = col_data

                for i in range(inspection_df_one.shape[0]):
                    data_r = inspection_df_one.iloc[i,].tolist()
                    if data_r:
                        print('%s 疾病,第 %d 条'%(f_disease, i))
                        data_w = "\t".join([str(x) for x in data_r])
                        output_file.write(data_w + '\n')
        output_file.close()


    def get_range_dict(self):
        if not os.path.isfile("inspection_valuerange.txt"):
            self.xml_parse()

        inspection_value_dict = {}
        inspection_value = open("inspection_valuerange.txt", 'r', encoding='utf-8')
        inspection_value_file = open("inspection_valuerange_dict2.txt", 'w', encoding='utf-8')
        unit_file = open("unit.txt", 'w', encoding='utf-8')
        unit_list = []
        for line in inspection_value:
            if line:
                line_sp =  re.split('\t', line.strip())
                item_cn = line_sp[1]
                item_en = line_sp[2]
                item_range = line_sp[-1]
                unit = line_sp[-2]

                if unit not in unit_list:
                    unit_file.write(unit + ' \n')
                    unit_list.append(unit)

                if re.findall('\d-\d', item_range):
                   range_sp = re.split('-',item_range)
                   if len(range_sp) == 2:
                        value_low, value_up = range_sp
                        inspection_value_dict[item_cn] = [value_low, value_up]
                        inspection_value_dict[item_en] = [value_low, value_up]

        ner_result_dict = json.dumps(inspection_value_dict, ensure_ascii=False, indent=1)
        inspection_value_file.write(ner_result_dict)
        inspection_value_file.close()

if __name__ == '__main__':
    model = InsepectionRange('*')
    # model.xml_parse()
    model.get_range_dict()