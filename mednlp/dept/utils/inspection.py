import global_conf
from ailib.client.ai_service_client import AIServiceClient


class TransInspection(object):

    def __init__(self):
        self.aisc = AIServiceClient(global_conf.cfg_path, 'AIService')

    def transform_inspection_data(self, content):
        """
        :param content: 要请求的内容
        :return:把检查检验的数值改为升高和降低
        """
        try:
            entity_result = self.aisc.query({'q': content, 'type': 'physical,examination', 'property': 'value'},
                                            'entity_extract')
        except:
            return content
        if not entity_result.get('data'):
            return content

        entities = {}
        for entity in entity_result.get('data'):
            if entity.get('type') in ('examination', 'physical') and entity.get('property'):
                if entity.get('property').get('value_status'):
                    entities[entity.get('entity_text')] = entity.get('entity_name') + entity.get('property'). \
                        get('value_status')
        for org_text, rep_text in entities.items():
            content = content.replace(org_text, rep_text)
        return content
