#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
diagnose_service_dao.py -- the dao of diagnose service

Author: maogy <maogy@guahao.com>
Create on 2017-11-06 Monday.
"""


import global_conf
from ailib.utils.log import GLLog
from ailib.client.ai_service_client import AIServiceClient


class DiagnoseServiceDao(object):
    """
    the dao of diagnose service.
    """

    def __init__(self, **kwargs):
        self.service = 'diagnose_service'
        self.debug = kwargs.get('debug', False)
        self.log_level = 'info'
        if self.debug:
            self.log_level = 'debug'
        self.logger = GLLog('ds_dao', log_dir=global_conf.log_dir,
                            level=self.log_level).getLogger()
        self.logger.debug('ds dao debug mode:%s' % self.debug)
        self.ds = AIServiceClient(global_conf.cfg_path, 'AIService',
                                  debug=self.debug)

    def diagnose(self, medical_record, rows=10, fl='disease_name'):
        """
        根据病历获取诊断结果.
        """
        params = {'rows': rows, 'fl': fl}
        params.update(medical_record)
        response = self.ds.query(params, self.service)
        self.ds.clear_url()
        code = response.get('code')
        if code:
            return None
        if response['totalCount'] > 300:
            return None
        return response['data']
        
