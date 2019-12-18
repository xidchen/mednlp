#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
base_generator.py -- the base of generator

Author: maogy <maogy@guahao.com>
Create on 2019-01-13 Sunday.
"""


class BaseGenerator(object):

    name = 'base_generator'
    input_field = []
    output_field = []

    def __init__(self, **kwargs):
        pass

    def get_name(self):
        return self.name

    def get_input_field(self):
        return self.input_field

    def get_output_field(self):
        return self.output_field

    def generate(self, input_obj, **kwargs):
        pass

