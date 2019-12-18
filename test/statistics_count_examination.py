#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import datetime

txtPath = '../logs/'
txtLists = os.listdir(txtPath)

physical_count = 0
examination_count = 0

time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S' )

for filename in txtLists:
    if re.findall('cdss.*.log', filename):
        filepath = os.path.join(txtPath, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            for lines in file:
                match_result = re.search('fl的类型是', lines)
                if match_result:
                    if re.search('status', lines):
                        physical_count += 1
                    else:
                        examination_count += 1

print('截至到统计的时间:%s，\n检查检验解读接口调用总次数为%d次：\n其中基卫云调用%d次，云HIS调用%d次。'%
      (time_now, physical_count+examination_count, physical_count, examination_count))

