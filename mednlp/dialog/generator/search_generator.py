#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
search_generator.py -- the search class of generation

Author: maogy <maogy@guahao.com>
Create on 2019-01-13 Sunday.
"""


from ailib.client.ai_service_client import AIServiceClient
from .base_generator import BaseGenerator


class SearchGenerator(BaseGenerator):

    def __init__(self, cfg_path, **kwargs):
        self.sc = AIServiceClient(cfg_path, 'SearchService')
        self.plat_sc = AIServiceClient(cfg_path, 'SEARCH_PLATFORM_SOLR')
        
