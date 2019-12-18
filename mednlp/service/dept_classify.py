import global_conf
from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.dept.utils.inspection import TransInspection
from mednlp.dept.project.strategy.disease import DiseaseLookUpStrategy
from mednlp.dept.project.strategy.medicine import MedicineLookUpStrategy
from mednlp.dept.common.result import DeptResults
from mednlp.dept.project.manager.case import CaseManager
from mednlp.dept.project.manager.advice import AdviceManager
from mednlp.dept.project.manager.rules import RulesManager
from ailib.utils.exception import AIServiceException

mode_manager_mapping = {1: AdviceManager(global_conf.cfg_path),
                        2: CaseManager(global_conf.cfg_path)}
rules_manager = RulesManager()
inspection_helper = TransInspection()
medicine_manager = MedicineLookUpStrategy()


class DeptClassify(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        parameters = self.input()
        result = self.execute(parameters)
        return result

    def input(self):
        exception = AIServiceException()
        try:
            query = self.get_q_argument('', limit=2000)
            rows = self.get_int_argument('rows', 1)
            sex = self.get_int_argument('sex', 0)
            age = self.get_int_argument('age', -1)
            level = self.get_int_argument('level', 1)
            mode = self.get_int_argument('mode', 1)
            dept_set = self.get_int_argument('dept_set', 1)
            disease = self.get_argument('disease', '')
            medicine = self.get_argument('medicine', '')
        except Exception as e:
            exception.message = str(e.args)
            raise exception

        if len(disease) > 0 and len(medicine) > 0:
            exception.message = "参数disease和medicine不可同时存在"
            raise exception
        if len(disease) == 0 and len(medicine) == 0 and len(query) <= 0:
            exception.message = "参数q、disease、medicine不可同时为空"
            raise exception
        if sex not in [0, 1, 2]:
            exception.message = "参数sex必须是0、1、或者2"
            raise exception
        if level not in [1, 2, 3, 4]:
            exception.message = "参数level必须是1、2、3或者4"
            raise exception
        if mode not in [1, 2]:
            exception.message = "参数mode必须是1或者2"
            raise exception
        if dept_set not in [1, 2, 3]:
            exception.message = "参数dept_set必须是1、2或者3"
            raise exception

        parameters = {'query': query,
                      'rows': rows,
                      'sex': sex,
                      'age': age,
                      'level': level,
                      'mode': mode,
                      'dept_set': dept_set,
                      'disease': disease,
                      'medicine': medicine}
        return parameters

    @staticmethod
    def execute(parameters):
        exception = AIServiceException()
        exception.code = 2

        try:
            dept_results = DeptResults()
            query = inspection_helper.transform_inspection_data(parameters['query'])
            if parameters['disease']:
                disease_strategy = DiseaseLookUpStrategy()
                dept_results = disease_strategy.execute(parameters['disease'])
            elif parameters['medicine']:
                dept_results = medicine_manager.execute(parameters['medicine'])

            if len(dept_results) == 0 and len(query) > 0:
                manager = mode_manager_mapping[parameters['mode']]
                ai_results = manager.execute(query)

                medicine_results = medicine_manager.execute(query)
                dept_results = medicine_manager.merge_with_ai_result(medicine_results, ai_results)

            dept_results = rules_manager.execute(dept_results, parameters['age'],
                                                 parameters['sex'], parameters['level'],
                                                 parameters['mode'], parameters['dept_set'], parameters['rows'])

            result = {'data': dept_results.serialize(),
                      'totalCount': max(1, min(dept_results.rows, len(dept_results))),
                      }
        except Exception as e:
            exception.message = e.args
            raise exception

        return result


if __name__ == '__main__':
    handlers = [(r'/dept_classify', DeptClassify, dict(runtime={}))]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
