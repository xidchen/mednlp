#!/usr/bin/python
# -*- coding: utf-8 -*-


class Card():
#    card_type = ''
#    id = ''
#    content = []
#    fl = set()
    field_list = ['conf_id', 'type', 'content']
	
    def __init__(self):	
    	self.card_type = ''
    	self.id = ''
    	self.content = []
    	self.fl = set()

    def set_card_conf(self, card):
        self.id = card.get('id')
        self.card_type = card.get('card_type')
	if card.get('dic_solr_name'):
            self.fl = set(card.get('dic_solr_name').split(','))

    def get_id(self):
	return self.id

    def get_card_type(self):
	return self.card_type

    def get_fl(self):
        return self.fl

    def get_content(self):
        return self.content

    def build_obj_result(self, response_data):
	card_obj = {}
	card_obj['type'] = self.card_type
	card_obj['conf_id'] = self.id
	card_obj['content'] = []
	for data_item in response_data:
            card_dict = {}
            for key,value in data_item.items():
                if key in self.fl and value:
                    card_dict[key] = value
            if card_dict:
                card_obj['content'].append(card_dict)
	return_obj = {}
	for field in self.field_list:
	    if card_obj.get(field):
		return_obj[field] = card_obj.get(field)
        return return_obj
