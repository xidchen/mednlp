#!/usr/bin/python
#encoding=utf-8

import json
from configulation import Configulation
from component.answer import Answer
from component.card import Card
from component.out_link import OutLink
import processor.processor_factory as processor_factory
import pdb


class Active():



    def __init__(self):
	self.answer = Answer()
    	self.card = Card()
    	self.out_link = OutLink()
    	self.intention_object = ''
    	self.fl = set()
    	self.response_data = {}
    	self.intention = ''
    	self.input_params = {}
    	self.intention_details = []

    def build_intention(self, intention, intention_details):
	self.intention = intention
	self.intention_details = intention_details

    def build_input_params(self, input_params):
	self.input_params = input_params

    def build_conf(self, conf):
        self.answer.set_answer_conf(conf.answer)
        self.card.set_card_conf(conf.card)
        self.out_link.set_out_link_conf(conf.out_link)

    def build_fl(self):
        self.fl.update(self.answer.get_fl())
        self.fl.update(self.card.get_fl())
        self.fl.update(self.out_link.get_fl())

    def build_processor(self, intention, entity_dict, input_params, conf, intention_details):
        self.processor_object = processor_factory.get_processor_instance(intention, entity_dict, intention_details, input_params)
        if self.processor_object:
            self.processor_object.set_params(input_params, intention, conf, entity_dict, self.fl)

    def process(self):
        if self.processor_object:
            self.processor_object.get_intention_result()
            self.response_data = self.processor_object.response_data

    def build_result(self):
        result_data = {}
        result_data['intention'] = self.intention
        result_data['answer'] = self.answer.build_obj_result(self.response_data)
        result_data['card'] = self.card.build_obj_result(self.response_data)
        result_data['out_link'] = self.out_link.build_obj_result(self.response_data)
	result_data['interactive_box'] = []
        result_data['isEnd'] = 1
        result_data['isHelp'] = 0
	result_data['dialogue'] = self.input_params
	if self.response_data and self.response_data[0].get('isEnd') == 0:
	    is_sex = self.response_data[0].get('isSex') 			
	    is_age = self.response_data[0].get('isAge')
            symptoms = self.response_data[0].get('symptoms') 
	    if is_sex:
		sex_box={}
     		sex_box['field'] = 'sex'
     		sex_box['type'] = 'single'
                sex_box['content'] = [0,1,2]
                sex_box['conf_id'] = 9998
		result_data['interactive_box'].append(sex_box)
	    if is_age:
		age_box={}
     		age_box['field'] = 'age'
     		age_box['type'] = 'single'
                age_box['conf_id'] = 9997
		result_data['interactive_box'].append(age_box)
	    if symptoms:
		symptom_box = {}
		symptom_box['field'] = 'symptomName'
		symptom_box['content'] = symptoms
     		symptom_box['type'] = 'multiple'
                symptom_box['conf_id'] = 9996
		result_data['interactive_box'].append(symptom_box)
	    result_data['isEnd'] = 0
	if self.input_params.get('mode') == 'loudspeaker_box' and self.intention == 'other':
	    result_data['answer'] = {'text':'很抱歉，小微还在学习中，暂时无法解决您的问题'}
	return result_data
