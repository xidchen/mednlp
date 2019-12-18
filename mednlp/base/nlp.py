#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nlp.py -- the base class of NLP

Author: maogy <maogy@guahao.com>
Create on 2019-02-11 Monday.
"""


from ailib.utils.log import GLLog
import global_conf


class BaseNLP(object):
    """
    The base class for mednlp.
    """

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.log_level = 'info'
        if self.debug:
            self.log_level = 'debug'
        self.logger = kwargs.get('logger')
        if not self.logger:
            self.logger = GLLog('base_nlp', log_dir=global_conf.log_dir,
                                level=self.log_level).getLogger()
        self.logger.debug('base nlp init finished!')
        self.cfg_path = global_conf.cfg_path
