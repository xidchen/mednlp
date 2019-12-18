#!/usr/bin/python
#encoding=utf-8


import time
import global_conf 
from ailib.storage.db import DBWrapper
from mednlp.service.base_request_handler import BaseRequestHandler
import mednlp.service.client.ai_client as ai_client

import processor.processor_factory as processor_factory
import json
import configulation as configulation
import active_factory as active_factory
import pdb


class DialogueService(BaseRequestHandler):

    query_object = ''
    ai_server = ai_client.AIClient(global_conf.cfg_path)

    def initialize(self, runtime=None,  **kwargs):
	super(DialogueService, self).initialize(runtime, **kwargs)
	if runtime and 'xwyz_db' in runtime: 
	    self.db = runtime['xwyz_db']
	else:
	    self.db = DBWrapper(global_conf.cfg_path, 'mysql', 'KnowledgeGraphSQLDB', autocommit=True)

    def post(self):
        return self.get()
	# self.asynchronous_get()

    def get(self):
	# self.asynchronous_get()
        return self._get()

    def _get(self):
        #init the base search attribute
        start_time = time.time()*1000
        result = {}
        if not self.request.body:
            result['code'] = 1
            result['message'] = 'No query!'
            self.write_result(result, result['message'], result['code'])
            return
        try:
            input_params = self.get_input_params(self.request.body)
            if input_params.get('input') :
                intention, intention_details = self.get_intention(input_params)
                conf = configulation.Configulation(self.db)
                conf.load_data(input_params, intention)
                entity_dict = self.get_entity_dict(input_params)
                active_factory_in = active_factory.ActiveFactory()
                active_object = active_factory_in.build(intention, entity_dict, input_params, conf, intention_details)
                if intention:
                    active_object.process()
		    return_result = active_object.build_result()
		    result['data'] = return_result
                else:
                    result['code'] = 1
                    result['message'] = 'No aiserver result!'
        except Exception as e:
            result['code'] = 1
	    result['message'] = 'falided!'
            result['except_message'] = 'except: %s' % e
            self.write_result(result, result['message'], result['code'])
            return
        result['qtime'] = time.time()*1000 - start_time
        self.write_result(result)
        return

    def get_intention(self, input_params):
        intention = ''
	intention_details = []
        if 'q' in input_params['input']:
            q = input_params['input']['q']
            params = {'q':q}
	    intention_list = self.get_intention_range(input_params)
  	    intention_list_json = json.dumps(intention_list)
	    params['intention_set'] = intention_list_json
            intention_result = self.ai_server.query(params, self.debug)
            if intention_result and intention_result.get('data'):
                intention_object = intention_result.get('data')
                intention = intention_object['intention']
		if intention_object.get('intentionDetails'):
		    intention_details.append(intention_object['intentionDetails'])
		if intention == 'content':
		    intention = 'keyword'
		    intention_details = ['treatment']
        return intention, intention_details

    def get_intention_range(self, input_params):
	intention_list = []
	if 'organization' in input_params:
	    org_code = str(input_params['organization'])
	    org_sql = """
		SELECT intention 
		FROM ai_union.access_org_intention 
		WHERE org_code='%s' 
		AND intention_status=1
		"""
	    org_sql = org_sql % org_code
	    rows = self.db.get_rows(org_sql)
	    for row in rows:
		if 'intention' in row:
		    intention_list.append(row['intention'])
	return intention_list

    def get_entity_dict(self, input_params):
        entity_map = {'std_department':{'departmentName':'entity_name',
                                    'departmentId': 'entity_id'},
                      'doctor': {'doctorName': 'entity_name',
                                     'doctorId': 'entity_id'},
                      'symptom': {'symptomName': 'entity_name',
                                     'symptomId': 'entity_id'},
                      'disease': {'diseaseName': 'entity_name',
                                     'diseaseId': 'entity_id'},
                      'hospital_department': {'departmentName': 'entity_name',
                                     'departmentId': 'entity_id'},
                      'hospital': {'hospitalName': 'entity_name',
                                     'hospitalId': 'entity_id'},
                      'body_part': {'bodyPartName': 'entity_name',
                                     'bodyPartId': 'entity_id'},
                      'treatment': {'treatmentName': 'entity_name',
                                     'treatmentId': 'entity_id'},
                      'medicine': {'medicineName': 'entity_name',
                                    'medicineId': 'entity_id'},
                      'area': {'city': {'cityName': 'entity_name',
                                    'cityId': 'entity_id'},
		      		'province': {'provinceName': 'entity_name',
		      				'provinceId': 'entity_id'}
				}
                      }

	input_change_params = {'city': 'cityId',
				'province': 'provinceId',
				'hospital': 'hospitalId',
				'doctor': 'doctorId',
				'hospitalName': 'hospitalName',
				'doctorName': 'doctorName',
				'symptomName': 'symptomName',
				'sex': 'sex',
				'age': 'age'
				}
	
        entity_dict = {}
        if 'q' in input_params['input']:
            q = input_params['input']['q']
            params = {'q':q}
            entity_result = self.ai_server.query(params, self.debug, service='entity_extract')
            if entity_result and entity_result.get('data'):
                for entity_obj in entity_result.get('data'):
                    if entity_map.get(entity_obj.get('type')):
                        entity_map_item = entity_map.get(entity_obj.get('type'))
                        for item in entity_map_item:
			    sub_type = entity_obj.get('sub_type')
			    if sub_type and entity_obj.get('type') == 'area':
				if sub_type == item:
				    for sub_item in entity_map_item[sub_type]:
			    	        if sub_item in entity_dict and entity_obj.get(entity_map_item[item][sub_item]):
					    entity_dict[sub_item].append(entity_obj.get(entity_map_item[item][sub_item]))
				        elif entity_obj.get(entity_map_item[item][sub_item]):
					    entity_dict[sub_item] = []
  					    entity_dict[sub_item].append(entity_obj.get(entity_map_item[item][sub_item]))
				continue
                            if item in entity_dict:
                                entity_dict[item].append(entity_obj.get(entity_map_item[item]))
                            else:
                                entity_dict[item] = []
                                entity_dict[item].append(entity_obj.get(entity_map_item[item]))
	for param in input_change_params:
	    if input_params['input'].get(param):
		value = input_params['input'].get(param)
		entity_dict[input_change_params[param]] = []
		entity_dict[input_change_params[param]].append(value)
        return entity_dict


    def get_input_params(self, request=None):
        """
        解析输入的内容
        :param request: 输入的内容
        :return:
        """
        params = {}
        if request:
            params = json.loads(request)
            if params.get('input'):
                input_dict = {}
                for input_item in params.get('input'):
                    input_dict.update(input_item)
                params['input'] = input_dict
        return params

    def get_result(self,intention, entity_dict, input_params, conf):
        intention_object = ''
        final_result = {}
        intention_object = processor_factory.get_intention_instance(intention, entity_dict)
        if intention_object:
            intention_object.set_params(input_params,intention, conf, entity_dict)
            final_result = intention_object.get_intention_result()
        return final_result

if __name__ == '__main__':
    handlers = [(r'/dialogue_service', DialogueService, dict(runtime={}))]
    import ailib.service.base_service as base_service
    base_service.run(handlers)



