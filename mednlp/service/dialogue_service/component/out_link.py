#!/usr/bin/python
# -*- coding: utf-8 -*-


class OutLink():


    def __init__(self):
	self.out_link_obj_list = []
	self.fl = set()

    def get_fl(self):
        return self.fl

    def set_out_link_conf(self, out_link_rows):
	for link in out_link_rows:
	    if link:
		link_obj = OutLinkObj()
		link_obj.set_out_link_conf(link)
		self.out_link_obj_list.append(link_obj)
        	if link.get('dic_solr_name'):
            	    self.fl = set(link.get('dic_solr_name').split(','))

    def build_obj_result(self, response_data=[]):
	return_obj = []
	for out_link_obj in self.out_link_obj_list:
	    json_obj = out_link_obj.build_obj_result(response_data)
	    if json_obj:
		return_obj.append(json_obj)
	return return_obj
	

class OutLinkObj():

    id = ''
    parameter = []
    fl = set()
    field_list = ['conf_id', 'parameter']


    def set_out_link_conf(self, out_link):
        self.id = out_link.get('id')
	if out_link.get('dic_solr_name'):
            self.fl = set(out_link.get('dic_solr_name').split(','))

    def get_id(self):
	return self.id

    def get_parameter(self):
	return self.parameter

    def get_fl(self):
        return self.fl

    def build_obj_result(self, response_data=[]):
        out_link_obj = {}
        out_link_obj['conf_id'] = self.id
        out_link_obj['parameter'] = []
        for data_item in response_data:
            out_link_dict = {}
            for key,value in data_item.items():
                if key in self.fl and value:
                    out_link_dict[key] = value
            if out_link_dict:
                out_link_obj['parameter'].append(out_link_dict)
	return_obj = {}
	for field in self.field_list:
	    if out_link_obj.get(field):
		return_obj[field] = out_link_obj.get(field)
        return return_obj
