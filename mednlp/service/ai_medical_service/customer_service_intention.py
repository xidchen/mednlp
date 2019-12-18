#!/usr/bin/python
# encoding=utf-8


from mednlp.service.ai_medical_service import ai_search_common
from mednlp.service.ai_medical_service import basic_intention


class CustomerServiceIntention(basic_intention.BasicIntention):
    """
    寒暄处理的意图
    """

    def get_dialogue_service_result(self):
        result = {}
        dialogue_response = self.get_diagnose_service_resp()
        if dialogue_response and dialogue_response.get('data'):
            data = dialogue_response['data']
            ai_search_common.customer_build_dialogue_service(data, result)
        return result

    def get_search_result(self):
        result = self.get_dialogue_service_result()
        if result.get('intention'):
            self.ai_result = result
            return

    def data_output(self, return_type=3):
        """
        返回文档格式化输出,1代表驼峰式输出,2代表下划线输出,3代表混合式输出(不处理)
        """
        if return_type == 3:
            return self.ai_result
