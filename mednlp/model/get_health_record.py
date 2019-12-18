
from global_conf import cfg_path
from mednlp.model.mongodb import MongoWrapper

mongodb = MongoWrapper(cfg_path)

#为减少频繁查询mongodb数据库，一次性获取一段时间内的健康单数据
#建立order_no到主诉和现病史的映射关系
def get_health_record_data(orderIds):
    medical_record = mongodb.find_medical_order_data(orderIds)
    medicalEventIds = []
    id_map = {}
    for r in medical_record:
        medicalEventId = r.get('medicalEventId')
        medicalEventId = medicalEventId
        id_map[r.get('medicalEventId')] = r.get('orderId')
        medicalEventIds.append(medicalEventId)
    out_patient = mongodb.find_out_patient_data(medicalEventIds)
    res = {}
    for order_id in orderIds:
        res[order_id] = []
    for r in out_patient:
        event_id = r.get('medicalEventId')
        chief_complaint = r.get('chiefComplaint','主诉缺失')
        present_illness = r.get('presentIllness','现病史缺失')
        order_id = id_map.get(event_id)
        if order_id:
            res[order_id].append(chief_complaint)
            res[order_id].append(present_illness)

    return res

# 根据order_no和主诉，现病史映射关系，去填充consult_info信息
def add_health_record_to_consult_info(res,consult_info):
    #consult_info.update({'chiefComplaint': 'do not have heath_record', 'presentIllness': 'do not have heath_record'})
    order_no = consult_info.get('order_no')
    if res.get(order_no):
        chief_complaint = res.get(order_no)[0]
        present_illness = res.get(order_no)[1]
        add_dict = {'chiefComplaint': chief_complaint, 'presentIllness': present_illness}
        consult_info.update(add_dict)
    return consult_info


#['grohqp7el5190214023109810','0ubpwl0nun190214021739562','hhb7ry747b190214054441780']