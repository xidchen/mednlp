from mednlp.dept.common.dictionary import medicine_helper, dept_dictionary
from mednlp.dept.common.result import DeptResults, Department, ResultHelper
from ailib.client.ai_service_client import AIServiceClient
import global_conf


class MedicineLookUpStrategy(object):
    def __init__(self):
        self.ai_server = AIServiceClient(global_conf.cfg_path, 'AIService')
        self.medicine_helper = medicine_helper

        self.dept_dictionary = dept_dictionary

    def _build_department_result(self, dept_score: dict):
        dept_result = DeptResults()
        for dept_name, score in dept_score.items():
            if dept_name in self.dept_dictionary.dictionary:
                dept = self.dept_dictionary.get_department_by_name(dept_name)
                dept.probability = score
                dept_result.add(dept)

            elif dept_name in self.dept_dictionary.sub_dictionary:
                dept1, dept2 = self.dept_dictionary.get_dept_pair_by_sub_name(dept_name)
                dept1.probability = score * 0.5
                dept2.probability = score * 0.5
                dept_result.add(dept1)
                dept_result.add(dept2)

        dept_result.normalize_score()
        return dept_result

    def execute(self, query: str) -> DeptResults:
        """
        主诉中可能带有药品名，抽取药品名称，并映射到对应科室
        :param query:
        :return:
        """
        params = {'q': query}
        extract_results = self.ai_server.query(params, 'entity_extract')['data']
        medicine_results = list(filter(lambda x: x['type'] == 'medicine', extract_results))

        '''根据字典加权求和'''
        results = []
        for medicine_result in medicine_results:
            medicine = medicine_result['entity_name']
            dept_score = self.medicine_helper.get_dept_score_by_medicine(medicine)

            if dept_score is None:
                continue
            dept_result = self._build_department_result(dept_score)
            results.append(dept_result)

        results_num = len(results)
        if results_num == 0:
            dept_results = DeptResults()
        else:
            weights = [1 / len(results), ] * len(results)
            dept_results = ResultHelper.merge(results, weights)
        return dept_results

    @staticmethod
    def merge_with_ai_result(medicine_results: DeptResults, ai_results: DeptResults):
        weights = [0.4, 0.6]
        results = [medicine_results, ai_results]
        final_results = ResultHelper.merge(results, weights)
        final_results.normalize_score()
        final_results.sort()
        return final_results
