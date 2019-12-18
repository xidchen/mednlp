#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ai_generator.py -- the base generator of ai service

Author: maogy <maogy@guahao.com>
Create on 2019-01-13 Sunday.
"""


from ailib.client.ai_service_client import AIServiceClient
from .base_generator import BaseGenerator


class AIGenerator(BaseGenerator):

    def __init__(self, cfg_path, **kwargs):
        self.ac = AIServiceClient(cfg_path, 'AIService')
        self.plat_sc = AIServiceClient(cfg_path, 'SEARCH_PLATFORM_SOLR')
