import global_conf
from ailib.client.ai_service_client import AIServiceClient

def structuring_diseases(content_input):
    ai_service = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
    parms = {
        'q': content_input,
    }
    structuration_result = ai_service.query(parms, service='entity_extract', method='get')
    data = structuration_result.get("data")
    diseases = set()
    for d in data:
        type_all = d.get("type_all")
        name = d.get("entity_name")
        if "disease" in type_all:
            diseases.add(name)
        if type == "symptom" and len(name) > 2 and name[-2:] == "感染":
            diseases.add(name)
    return diseases


def structuring_symptom_disease(content_input):
    ai_service = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
    parms = {
        'q': content_input,
    }
    structuration_result = ai_service.query(parms, service='entity_extract', method='get')
    data = structuration_result.get("data")
    symptom = set()
    for d in data:
        type = d.get("type")
        name = d.get("entity_name")
        if type == "disease":
            symptom.add(name)
        if type == "symptom":
            symptom.add(name)
    return symptom