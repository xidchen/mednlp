from mednlp.service.entity_extract import Entity_Extract


class EntityFilter(object):
    def __init__(self):
        self.extractor = Entity_Extract()
        self.reserve_type = ['symptom', 'disease', 'hospital_department', 'std_department',
                             'body_part', 'treatment', 'medicine', 'crowd',
                             'examination', 'physical', 'medical_word']

        self.reserve_words = ['月经', '大便', '小便', '心理辅导']
        self.uncare_words = ['医生', '病情']

    def need_to_reserve(self, query):
        reserve = False
        for word in self.uncare_words:
            query.replace(word, '')

        entities = self.extractor.result_filter(query, type_list=[], property_list=[])
        for entity in entities:
            if entity['type'] in self.reserve_type:
                reserve = True
                break

        for reserve_word in self.reserve_words:
            if reserve_word in query:
                reserve = True
                break
        return reserve
