#!/usr/bin/python
#encoding=utf-8

import json
from configulation import Configulation
from active import Active


class ActiveFactory():

    active = Active()

    def build(self, intention, entity_dict, input_params, conf, intention_details):
	self.active = Active()
	self.active.build_intention(intention, intention_details)
	self.active.build_input_params(input_params)
	self.active.build_conf(conf)
        self.active.build_fl()
        self.active.build_processor(intention, entity_dict, input_params, conf, intention_details)
        return self.active
