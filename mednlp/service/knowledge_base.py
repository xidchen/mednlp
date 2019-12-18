from mednlp.service.base_request_handler import BaseRequestHandler
from mednlp.model.knowledge_base_model import KnowledgeBase
import re
import json

knowledgebase = KnowledgeBase()


class KnowledgeBase(BaseRequestHandler):

    def post(self):
        return self.get()

    def get(self):
        self.asynchronous_get()

    def _get(self):
        result = {}
        result.setdefault('data', [])
        result.setdefault('totalCount', 1)
        query = self.get_argument('disease', '')
        if not query:
            query_str = self.request.body
            try:
                querys = json.loads(query_str, encoding='utf-8')
                query = str(querys.get('disease'))
            except Exception:
                print('data is error')
                return result

        querys = re.split('[,，]', query)
        disease_result = []
        if not query:
            return result
        for disease in querys:
            disease_result.append(knowledgebase.predict(disease))
        if not disease_result:
            return result
        else:
            result['data'] = disease_result
            result['totalCount'] = len(disease_result)
        return result


if __name__ == '__main__':
    handlers = [(r'/knowledge_base', KnowledgeBase, dict(runtime={}))]
    import ailib.service.base_service as base_service

    base_service.run(handlers)
