#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
chinese_medicine_sub_deptment.py -- 若出现中医科室若出现第一个位置，替换为中医的二级科室，若出现在其他位置，则出现中医科室和其他科室

Author: caoxg <caoxg@guahao.com>
Create on 2018-08-16 星期三.
"""


import codecs
import global_conf


class ChineseMedicineSubDeptment():
    def __init__(self, sub_deptment_path=global_conf.chinese_medicine_sub_deptment):
        self.sub_deptment_path = sub_deptment_path
        self.parent_children_dept, self.children_dept_id = self.load_sub_dept()

    def load_sub_dept(self):
        """
        生成标准科室和中医二级科室之间的对应关系
        :return: 返回标准科室和中医对应科室的对应关系，以及中医对应科室和科室id的对应关系
        """
        sub_dept_data = codecs.open(self.sub_deptment_path, 'r', encoding='utf-8')
        parent_children_dept = {}
        children_dept_id = {}
        for line in sub_dept_data:
            lines = line.strip().split('=')
            parent_children_dept[lines[0]] = lines[1]
            children_dept_id[lines[1]] = lines[2]
        return parent_children_dept, children_dept_id

    def get_sub_dept(self, deptment):
        """
        给定标准科室，给出中医对应的二级科室下
        :param score:标准科室
        :return: 中医下面对应的二级科室和科室id
        """
        if self.parent_children_dept.get(deptment):
            sub_dept = self.parent_children_dept.get(deptment)
            sub_dept_id = self.children_dept_id.get(sub_dept)
            return [sub_dept, sub_dept_id]
        else:
            return

    def get_list_sub_dept(self, depts):
        """
        根据模型预测结果，给科室是中医的科室，增加子科室和子科室id
        :param depts: 模型预测结果
        :param rows: 取模型预测结果的前几个结果
        :return: 返回中医部分已增加已增加儿科下面的二级科室和id的结果，类型list
        """
        data = []
        for id, line in enumerate(depts):
            if id==0:
                sub_deptment_result = self.get_sub_dept(depts[1][0].decode('utf-8'))
            else:
                sub_deptment_result = self.get_sub_dept(depts[0][0].decode('utf-8'))
            if line[0] == '中医科' and sub_deptment_result:
                line.extend(sub_deptment_result)
                data.append(line)
            else:
                data.append(line)
        return data

    def get_dict_sub_dept(self, depts, rows=1):
        """
        根据模型预测结果，给科室是中医的科室，增加子科室和子科室id
        :param depts: 模型预测结果
        :param rows: 取模型预测结果的前几个结果
        :return: 返回儿科部分已增加已增加儿科下面的二级科室和id的结果，类型dict
        """
        data = []
        for line in depts[0:rows]:
            if len(line) == 6:
                data.append({'dept_name': line[0], 'score': line[1], 'dept_id': line[2], 'accuracy': line[3],
                             'sub_dept_name': line[4], 'sub_dept_id': line[5]})
            else:
                data.append({'dept_name': line[0], 'score': line[1], 'dept_id': line[2], 'accuracy': line[3]})
        return data


if __name__ == '__main__':
    depts = [
        ['\xe8\x82\xbe\xe5\x86\x85\xe7\xa7\x91', 0.26388648609992077, '7f67a158-cff3-11e1-831f-5cf9dd2e7135', '89.36%']
        , ['\xe6\xb3\x8c\xe5\xb0\xbf\xe5\xa4\x96\xe7\xa7\x91', 0.13326719749827845,
           '7f67c9e4-cff3-11e1-831f-5cf9dd2e7135',
           '86.74%'],
        ['\xe4\xb8\xad\xe5\x8c\xbb\xe7\xa7\x91', 0.057117327837661047, '7f68c1d2-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'], ['\xe5\xa6\x87\xe7\xa7\x91', 0.053520661856896981, '7f67f3d8-cff3-11e1-831f-5cf9dd2e7135',
                     '86.39%'], ['\xe9\xaa\xa8\xe7\xa7\x91', 0.048683311718350039,
                                 '7f67dd62-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe7\x94\xb7\xe7\xa7\x91', 0.043350602243175905, '7f691af6-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe6\x99\xae\xe5\xa4\x96\xe7\xa7\x91', 0.036462190074383109, '7f67c1f6-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'], ['\xe6\xb6\x88\xe5\x8c\x96\xe5\x86\x85\xe7\xa7\x91', 0.036437813000735196,
                     '7f66b590-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe5\x86\x85\xe5\x88\x86\xe6\xb3\x8c\xe7\xa7\x91', 0.027219630131439142,
         '7f67af54-cff3-11e1-831f-5cf9dd2e7135', '86.39%'], ['\xe6\x99\xae\xe9\x80\x9a\xe5\x86\x85\xe7\xa7\x91',

                                                             0.026845436265173266,
                                                             '7f67aca2-cff3-11e1-831f-5cf9dd2e7135',
                                                             '86.39%'], ['\xe8\x82\xbf\xe7\x98\xa4\xe7\xa7\x91',
                                                                         0.026648720233389225,
                                                                         '7f689446-cff3-11e1-831f-5cf9dd2e7135',
                                                                         '86.39%'],
        ['\xe7\xa5\x9e\xe7\xbb\x8f\xe5\x86\x85\xe7\xa7\x91', 0.021797913288668012,
         '7f67994c-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe5\xbf\x83\xe8\xa1\x80\xe7\xae\xa1\xe5\x86\x85\xe7\xa7\x91', 0.019536584257580973,
         '7f64f016-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe7\x9a\xae\xe8\x82\xa4\xe7\xa7\x91', 0.01851018013996332, '7f688f14-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe7\xa5\x9e\xe7\xbb\x8f\xe5\xa4\x96\xe7\xa7\x91', 0.017669327379067516,
         '7f67bf44-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe5\x84\xbf\xe7\xa7\x91', 0.013637232798550405, '7f6802e2-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe8\x84\x8a\xe6\x9f\xb1\xe5\xa4\x96\xe7\xa7\x91', 0.012091843552488164,
         '7f67df9c-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe8\x80\xb3\xe9\xbc\xbb\xe5\x92\xbd\xe5\x96\x89\xe7\xa7\x91', 0.011871840879855475,
         '7f686908-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe9\xa3\x8e\xe6\xb9\xbf\xe5\x85\x8d\xe7\x96\xab\xe7\xa7\x91', 0.011119321504071156,
         '7f67a716-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe4\xb9\xb3\xe8\x85\xba\xe5\xa4\x96\xe7\xa7\x91', 0.01001644647999083,
         '7f67d2ea-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe5\x8f\xa3\xe8\x85\x94\xe7\xa7\x91', 0.0095484017543808943, '7f687074-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'], ['\xe8\x82\x9d\xe8\x83\x86\xe5\xa4\x96\xe7\xa7\x91', 0.0095207665345860438,
                     '7f67c4a8-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe8\x83\xb8\xe5\xa4\x96\xe7\xa7\x91', 0.0094095097811881089, '7f67b9f4-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe7\x9c\xbc\xe7\xa7\x91', 0.0090701956136634912, '7f6848ce-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe6\x95\xb4\xe5\xbd\xa2\xe5\xa4\x96\xe7\xa7\x91', 0.0081212240724533938,
         '7f67d02e-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe5\x91\xbc\xe5\x90\xb8\xe5\x86\x85\xe7\xa7\x91', 0.007587377742501851,
         '7f65d238-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe8\x82\x9b\xe8\x82\xa0\xe5\xa4\x96\xe7\xa7\x91', 0.0075721222983604029,
         '7f67c764-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe7\x96\xbc\xe7\x97\x9b\xe7\xa7\x91', 0.0070324905022630937, '7f68b552-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe6\x84\x9f\xe6\x9f\x93\xe7\xa7\x91', 0.0063901601225869135, '7f67a9d2-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe7\xb2\xbe\xe7\xa5\x9e\xe7\xa7\x91', 0.006087497498324955, '7f6908f4-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'], ['\xe8\xa1\x80\xe7\xae\xa1\xe5\xa4\x96\xe7\xa7\x91', 0.0060667707503358256,
                     '7f67cc8c-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe5\xbf\x83\xe7\x90\x86\xe7\xa7\x91', 0.0047082543238328202, '7f690674-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'], ['\xe5\xbf\x83\xe8\xa1\x80\xe7\xae\xa1\xe5\xa4\x96\xe7\xa7\x91', 0.0040427794972742069,
                     '7f67bc9c-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe8\xa1\x80\xe6\xb6\xb2\xe7\xa7\x91', 0.0038475562939774021, '7f67a450-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe5\xba\xb7\xe5\xa4\x8d\xe7\xa7\x91', 0.0034448316146485783, '7f6912fe-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe4\xba\xa7\xe7\xa7\x91', 0.0032991362914987486, '7f67f8c4-cff3-11e1-831f-5cf9dd2e7135', '86.39%'],
        ['\xe6\x80\xa7\xe7\x97\x85\xe7\xa7\x91', 0.0020509709788005515, '7f6891bc-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe6\x80\xa5\xe8\xaf\x8a\xe7\xa7\x91', 0.0016151206493955055, '7f691d80-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'],
        ['\xe7\x83\xa7\xe4\xbc\xa4\xe7\xa7\x91', 0.00053771873206767836, '7f67d81c-cff3-11e1-831f-5cf9dd2e7135',
         '86.39%'], ['\xe6\x96\xb0\xe7\x94\x9f\xe5\x84\xbf\xe7\xa7\x91', 0.00035704770822077254,
                     '7f6843d8-cff3-11e1-831f-5cf9dd2e7135', '86.39%']]
    a = "乳腺外科".decode('utf-8')
    b = '呼吸内科'.decode('utf-8')
    c = 'a'.decode('utf-8')
    sub_dept = ChineseMedicineSubDeptment()
    print sub_dept
    children_sub_deptment = sub_dept.get_sub_dept(a)
    print sub_dept.get_list_sub_dept(depts)
    print sub_dept.get_dict_sub_dept(sub_dept.get_list_sub_dept(depts),40)
    if children_sub_deptment:
        print children_sub_deptment[0]
        print children_sub_deptment[1]
    children_sub_deptment = sub_dept.get_sub_dept(b)
    if children_sub_deptment:
        print children_sub_deptment[0]
        print children_sub_deptment[1]

    children_sub_deptment = sub_dept.get_sub_dept(c)
    if children_sub_deptment:
        print children_sub_deptment[0]
        print children_sub_deptment[1]