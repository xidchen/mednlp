#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
update.py -- the update module for dict or other

Author: maogy
Create on 2017-12-25 Monday.
"""


import sys
import os
import datetime
from ailib.utils.log import GLLog
import ailib.utils.ioutil as ioutil
from ailib.utils.ioutil import SimpleFileLock
from ailib.storage.db import DBWrapper
from mednlp.dao.sql_box import SQLS
import global_conf

class FileUpdate(object):

    def __init__(self, **kwargs):
        """
        初始化.
        参数:
        db->数据库实例.
        logger->日志实例.
        """
        self.logger = kwargs.pop('logger', GLLog('updater').getLogger())
        if kwargs.get('db'):
            self.db = kwargs.pop('db')
        else:
            self.db = DBWrapper(global_conf.cfg_path, 'mysql', 'AIMySQLDB',
                                logger=self.logger)

    def update(self, section, file_type, out_dir, **kwargs):
        """
        更新文件.
        参数:
        file_type->需要更新的文件类型.
        out_dir->文件输出目录.
        file_name->更新文件文件名,可空,默认为'file_type'+'.dic'
        format->输出文件的行格式,可空,默认为'%s\t%s\n'.
        """
        
        dic_path = os.path.join(out_dir, kwargs.get('file_name',
                                                    file_type + '.dic'))
        # print('---dic_path---', dic_path)
        lock = SimpleFileLock(dic_path)
        handler = kwargs.get('handler')
        try:
            lock.lock(600)
            sql = SQLS[section][file_type]
            rows = self.db.get_rows(sql)
            today = datetime.date.today().strftime("%Y-%m-%d")
            tmp_dict_file = '%s.%s' % (dic_path, today)
            out_file = open(tmp_dict_file, 'w')
            line_format = kwargs.pop('format', '%s\t%s\n')
            for row in rows:
                if not row.get('id') or not row.get('name'):
                    continue
                if handler:
                    result = handler(row)
                    if result:
                        for res in result:
                            res_name = res['name'] if isinstance(res['name'], str) else res['name'].encode('utf-8')
                            res_id = res['id'] if isinstance(res['id'], str) else res['id'].encode('utf-8')
                            out_file.write(line_format % (res_name, res_id))
                            #out_file.write(line_format % (str(row['name'], encoding='utf-8'), str(row['id'], encoding='utf-8')))
                    continue
                row_name = row['name'] if isinstance(row['name'], str) else row['name'].encode('utf-8')
                row_id = row['id'] if isinstance(row['id'], str) else str(row['id'])#.encode('utf-8')
                out_file.write(line_format % (row_name, row_id))
                # print(row_name, row_id)
                #out_file.write(line_format % (str(row['name'], encoding='utf-8'), str(row['id'], encoding='utf-8')))
            out_file.close()
            ioutil.file_replace(tmp_dict_file, dic_path)
        finally:
            lock.unlock()

        dic_filter = kwargs.get('dic_filter', '')
        if dic_filter:
            dic_filter(verbose=False)
