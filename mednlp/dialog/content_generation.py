#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
content_generation.py -- the interface of content generation

Author: maogy <maogy@guahao.com>
Create on 2019-01-13 Sunday.
"""

import traceback
import json
import global_conf
from ailib.utils.exception import AIServiceException
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.dialog.cg_constant import logger
from mednlp.dialog.generator.hospital_search_generator import HospitalSearchGenerator
from mednlp.dialog.generator.department_classify import DepartmentClassifyInteractiveGenerator, DepartmentClassify
from mednlp.dialog.generator.department_search import DepartmentSearchGenerator
from mednlp.dialog.generator.sentence_similar_generator import SentenceSimilarGenerator
from mednlp.dialog.generator.baike_search_generator import BaikeSearchGenerator
from mednlp.dialog.generator.post_search_generator import PostSearchGenerator
from mednlp.dialog.generator.greeting_generator import GreetingGenerator
from mednlp.dialog.generator.doctor_search_generator import DoctorSearchGenerator
from mednlp.dialog.generator.previous_diagnose_generator import PreviousDiagnoseGenerator
from mednlp.dialog.generator.question_answer_search_generator import QuestionAnswerGenerator
from mednlp.dialog.generator.recommend_question_generator import RecommendQuestionGenerator
import pdb


generators = {
    'hospital_search': HospitalSearchGenerator(global_conf.cfg_path),
    'department_classify_interactive': DepartmentClassifyInteractiveGenerator(
        global_conf.cfg_path),
    'department_search': DepartmentSearchGenerator(global_conf.cfg_path),
    'sentence_similar': SentenceSimilarGenerator(global_conf.cfg_path),
    'baike_search': BaikeSearchGenerator(global_conf.cfg_path),
    'post_search': PostSearchGenerator(global_conf.cfg_path),
    'greeting': GreetingGenerator(global_conf.cfg_path),
    'doctor_search': DoctorSearchGenerator(global_conf.cfg_path),
    'department_classify': DepartmentClassify(global_conf.cfg_path),
    'previous_diagnose': PreviousDiagnoseGenerator(global_conf.cfg_path),
    'question_answer': QuestionAnswerGenerator(global_conf.cfg_path),
    'recommend_question': RecommendQuestionGenerator(global_conf.cfg_path)
}


class ContentGeneration(BaseRequestHandler):

    not_none_field = ['source', 'generator', 'method']

    def initialize(self, runtime=None, **kwargs):
        super(ContentGeneration, self).initialize(runtime, **kwargs)

    def post(self):
        self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self, **kwargs):
        result = {}
        try:
            if self.request.body:
                input_obj = json.loads(self.request.body)
                self.check_parameter(input_obj)
                generator = generators[input_obj.get('generator')]
                method = input_obj.get('method')
                parameters = input_obj.get('parameter', {})
                if 'fl' in parameters:
                    if '*' in parameters['fl']:
                        parameters['fl'] = generator.get_output_field()
                    else:
                        parameters['fl'] = parameters['fl']
                data = result.setdefault('data', {})
                if method == 'generate':
                    data.update(self.generate(generator, parameters))
                elif method == 'check':
                    data.update(self.check(generator))
        except AIServiceException as ai_err:
            raise ai_err
        except Exception:
            logger.error(traceback.format_exc())
            raise AIServiceException(self.request.body)
        return result

    def check(self, generator):
        result = {'code': generator.get_name(),
                  'input_field': generator.get_input_field(),
                  'output_field': generator.get_output_field()}
        return result

    def generate(self, generator, parameters):
        return generator.generate(parameters)

    def check_parameter(self, parameters):
        for field in self.not_none_field:
            if field not in parameters:
                raise AIServiceException(field)
        if parameters.get('generator') not in generators:
            raise AIServiceException(parameters.get('generator'))


if __name__ == '__main__':
    handlers = [(r'/content_generation', ContentGeneration)]
    import ailib.service.base_service as base_service
    base_service.run(handlers)
