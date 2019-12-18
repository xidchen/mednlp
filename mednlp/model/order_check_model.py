# -*- coding: utf-8 -*-
import re
import json
import pymongo
import global_conf
from mednlp.model.get_health_record import get_health_record_data
from ailib.client.ai_service_client import AIServiceClient
from mednlp.model.AESCipher import AESCipher
from mednlp.model.structuring_disease import structuring_diseases,structuring_symptom_disease

client_search_service = AIServiceClient(global_conf.cfg_path, 'SearchService')

# 411
def name_idf(consult_info):
    f = open(global_conf.dict_path + 'family_names.txt', encoding='UTF-8')
    lines = f.readlines()
    familyNames = []
    for l in lines:
        l = l.rstrip('\n')
        familyNames.append(l)
    name_encrypt = consult_info.get('patient_name_encrypt', '')
    print('name_encrypt:', name_encrypt)
    if name_encrypt != '':
        # 进行姓名AES解密
        iv = 'greenlineguahaow'
        key = 'xfzyl39df#($)p6j'
        aes = AESCipher(iv, key)
        name = aes.decrypt(name_encrypt)
        print('name:', name)
        t = re.match('^[\u4E00-\u9FA5]{2,5}$', name)
        if t and len(name) <= 5:
            # 姓氏字典不全，造成漏查，还是用汉字匹配
            # if name[0] in familyNames or name[0:2] in familyNames:
            return True
        return False
    return True

# 412
def sex_idf(consult_info):
    male_dept = ('男科')
    femal_dept = ('妇科', '产科', '妇产科')
    patient_sex = consult_info.get('patient_sex', '')
    hosp_dept_name = consult_info.get('standard_parent_name', '')
    if hosp_dept_name:
        if patient_sex == 1 and hosp_dept_name in femal_dept:
            return False
        if patient_sex == 2 and hosp_dept_name in male_dept:
            return False
    return True

# 413
def age_idf(consult_info):
    age = consult_info.get('patient_age', -1)
    hosp_dept_name = consult_info.get('standard_parent_name', '')
    if hosp_dept_name:
        if age == -1:
            return True
        if age > 16 and hosp_dept_name in ('儿科'):
            return False
    return True

# 421
def disease_idf(consult_info):
    age = consult_info.get('patient_age', -1)
    disease = consult_info.get("disease_name")
    standard_parent_name = consult_info.get('standard_parent_name', '')
    department_norm_name = consult_info.get('department_norm_name', '')
    if standard_parent_name == "全科医疗科":
        return True
    if standard_parent_name == "其他":
        return True
    if not disease:
        return True
    if disease == 'undefined':
        return True
    if disease == '尚未确诊':
        return True
    if not standard_parent_name and not department_norm_name:
        return True
    diseaseList = re.split('[/、，\\\]', disease)
    params = {"name": diseaseList,
              "ef": ["id", "disease_id"],
              "start": 0
              }
    # 这里传入的时候将dict转化为json形式
    ai_content = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
    entity_contnet = ai_content.query(params=json.dumps(params, ensure_ascii=False),
                                      service="entity_service", method='post')
    data = entity_contnet.get('data')
    diseases = []
    entity = data.get("entity")
    for e in entity:
        disease_id = e.get("disease_id")
        if disease_id == None:
            diseases = diseases
        else:
            diseases.append(disease_id)
    if len(diseases) == 0:
        return True
    param = {"disease": diseases, 'fl': 'std_department'}
    response = client_search_service.query(param, 'disease_service', method='get')
    if response['code'] == 0:
        resp_disease = response.get('disease')
        depts = []
        for rds in resp_disease:
            if 'std_department' in rds:
                rd = rds['std_department']
                for r in rd:
                    dep = r.split('|')[1]
                    depts.append(dep)
        if depts:
            if standard_parent_name == "儿科" and age < 16:
                return True
            if "重症医学" in depts and standard_parent_name == "内科":
                return True
            if "急诊科" in depts and standard_parent_name == "内科":
                return True
            if "普通内科" in depts and standard_parent_name == "内科":
                return True
            if "普外科" in depts and standard_parent_name == "外科":
                return True
            if "骨科" in depts and standard_parent_name == "外科":
                return True
            if standard_parent_name not in depts and department_norm_name not in depts:
                print("错误原因({}/{})医生科室不在疾病科室列表{}中".format(standard_parent_name, department_norm_name, depts))
                return False
    return True


# 422
def online_case_idf(consult_info):
    f = open(global_conf.dict_path + "offline_disease_case.txt")
    offlineDiseaseCases = []
    for line in f.readlines():
        line = line.rstrip("\n")
        offlineDiseaseCases = offlineDiseaseCases + line.split("、")
    f.close()
    disease = consult_info.get('disease_name', '')
    if not disease:
        return True
    else:
        if disease in offlineDiseaseCases:
            print("{}只能线下就诊，不适合网络诊疗".format(disease))
            return False
        else:
            return True


# 432
def uncivilized_word_idf(consult_info):
    # 不文明用语需要整理成一个文档，然后读取成list
    f = open(global_conf.dict_path + 'uncivilized_words.txt', encoding='UTF-8')
    lines = f.readlines()
    uncivilized_words = []
    for i in lines:
        i = i.rstrip('\n')
        uncivilized_words.append(i)

    reply = consult_info.get('doctor_reply_list', '')
    wordList = ''
    if reply:
        for r in reply:
            wordList += r
        w = re.findall("|".join(uncivilized_words), wordList)
        if w:
            return False
    return True


# 441
def chief_complaint_have_idf(consult_info):
    chief_complaint = consult_info.get("chiefComplaint")
    print("chief_complaint:",chief_complaint)
    if chief_complaint == '主诉缺失':
        #print(chief_complaint)
        return False
    return True


# 442
def chief_complaint_brief_idf(consult_info):
    chief_complaint = consult_info.get("chiefComplaint")
    if chief_complaint:
        if len(chief_complaint) > 20:
            return False
    return True


#443
def chief_complaint_loss_importance(consult_info):
    chief_complaint = consult_info.get("chiefComplaint")
    #print(chief_complaint)
    if chief_complaint == '三伏贴末伏复诊':
        return True
    if chief_complaint == '主诉缺失':
        return True
    if chief_complaint and chief_complaint != 1:
        num = (re.findall('\d+', chief_complaint) + re.findall('半年', chief_complaint) + re.findall('半月', chief_complaint))
        if not num:
            return False
        # 把主诉结构化后发现不包含疾病和症状信息
        if not structuring_symptom_disease(chief_complaint):
            return False
    return True


# 447
#注意presentIllness出现：上呼吸道感染等大类疾病的准确率
def chief_complaint_compaire_disease(consult_info):
    chief_complaint = consult_info.get("chiefComplaint")
    present_illness = consult_info.get("presentIllness")
    if chief_complaint and present_illness:
        if chief_complaint == '主诉缺失':
            return True
        if present_illness == '现病史缺失':
            return True
        str_diseases = structuring_symptom_disease(chief_complaint)
        str_illness = structuring_symptom_disease(present_illness)
        print("主诉中疾病症状:",str_diseases)
        print("present_illness",str_illness)
        if not str_illness.intersection(str_diseases):
            return False
    return True


# entity_extract?q="既往体检有甲状腺结节2年	"

# 451
def drug_indication_idf(consult_info):
    ai_content = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
    drug = []
    indications = []
    disease = consult_info.get('disease_name')
    if not disease:
        return True
    if disease == 'undefined':
        return True
    diseaseList = re.split('[/、，\\\]', disease)
    drug_info = consult_info.get('prescription_drug_detail', '')
    if not drug_info:
        return True
    else:
        for d in drug_info:
            common_name = d.split('|')[1]
            drug.append(common_name)
        if not drug:
            return True
        else:
            params = {"name": drug,
                      "status": 0,
                      "ef": ["id", "name", "common_preparation_disease_indication_relation"]
                      }
            # 这里传入的时候将dict转化为json形式
            entity_contnet = ai_content.query(params=json.dumps(params, ensure_ascii=False),
                                              service="entity_service", method='post')
            if entity_contnet.get('code') == 0:
                data = entity_contnet.get('data')
                entity = data.get("entity")
                disease_id = []
                for e in entity:
                    de = e.get("common_preparation_disease_indication_relation")
                    if de != None:
                        disease_id = disease_id + de
                if not disease_id:
                    return True
                else:
                    pa = {"id": list(disease_id),
                          "status": 0,
                          "ef": ["name"]
                          }
                    entity_c = ai_content.query(params=json.dumps(pa, ensure_ascii=False),
                                                service="entity_service", method='post')
                    da = entity_c.get('data')
                    en = da.get("entity")
                    for e in en:
                        indications.append(e.get("name"))
    SameDisease = [d for d in diseaseList if d in indications]
    if len(SameDisease) == 0:
        print("确诊疾病 {} 没有在药品{}适应症列表 {} 中".format(disease, drug, indications))
        return False
    else:
        return True

# 461
def medical_threapy_logic_idf(consult_info):
    prescription_drug_detail = consult_info.get('prescription_drug_detail', '')
    sex = consult_info.get('patient_sex', '')
    age = consult_info.get('patient_age', -1)
    if not prescription_drug_detail:
        return True
    all_method = []
    specila_method = '阴道给药'
    for d in prescription_drug_detail:
        drugId = d.split('|')[0]
        param = {'drug': drugId, 'fl': 'take_method_name'}
        response = client_search_service.query(param, 'prescription_plat_drug', method='get')
        if response['code'] == 0:
            data = response.get('data')
            for d in data:
                take_method = d.get('take_method_name', '')
                if type(take_method) == str:
                    all_method.append(take_method)
                else:
                    all_method = all_method + take_method
    # print('所以药品给药方法:',all_method)
    if sex == 2 and age < 16 and specila_method in all_method:
        print("给未成年女性给药途径{}里有{},不合规".format(all_method, specila_method))
        return False
    else:
        return True


# 461
def medical_sex_logic_idf(consult_info):
    disease = consult_info.get("disease_name")
    sex = consult_info.get('patient_sex', '')
    if not disease:
        return True
    params = {"name": [disease],
              "ef": ["id", "disease_id"]
              }
    # 这里传入的时候将dict转化为json形式
    ai_content = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
    entity_contnet = ai_content.query(params=json.dumps(params, ensure_ascii=False),
                                      service="entity_service", method='post')
    if entity_contnet.get('code') == 0:
        data = entity_contnet.get('data')
        diseases = []
        entity = data.get("entity")
        for e in entity:
            disease_id = e.get("disease_id")
            if disease_id == None:
                diseases = diseases
            else:
                diseases.append(disease_id)
        if len(diseases) == 0:
            return True
        param = {"disease": diseases, 'fl': 'std_department'}
        response = client_search_service.query(param, 'disease_service', method='get')
        if response['code'] == 0:
            resp_disease = response.get('disease')
            depts = []
            for rds in resp_disease:
                if 'std_department' in rds:
                    rd = rds['std_department']
                    for r in rd:
                        dep = r.split('|')[1]
                        depts.append(dep)
            if depts:
                if sex == 1 and ('妇科' or '产科' or '妇产科') in depts and '男科' not in depts:
                    print("病人为男性诊出病：{} 是女性病".format(disease))
                    return False
                if sex == 2 and '男科' in depts and ('妇科' or '产科' or '妇产科') not in depts:
                    print("病人为女性诊出病：{} 是男性疾病".format(disease))
                    return False
    return True

# group 461
def medical_logic_idf(consult_info):
    threapy_logic = medical_threapy_logic_idf(consult_info)
    sex_logic = medical_sex_logic_idf(consult_info)
    return threapy_logic and sex_logic


#新规则
#2.1首问语规范
def first_reply_idf(consult_info):
    doctor_reply_list = consult_info.get('doctor_reply_list','')
    if doctor_reply_list:
        first_reply = doctor_reply_list[0]
        regex = '你好|您好'
        res = re.findall(regex,first_reply)
        if len(res) == 0:
            return False
    return True

# 6.4
def drug_taboo_idf(consult_info):
    ai_content = AIServiceClient(cfg_path=global_conf.cfg_path, service='AIService')
    drug = []
    taboos = []
    disease = consult_info.get('disease_name')
    if not disease:
        return True
    drug_info = consult_info.get('prescription_drug_detail', '')
    if not drug_info:
        return True
    else:
        for d in drug_info:
            common_name = d.split('|')[1]
            drug.append(common_name)
        if not drug:
            return True
        # 一个处方中药品不能多余5个
        elif len(drug) > 5:
            return False
        else:
            params = {"name": drug,
                      "status": 0,
                      "ef": ["id", "name", "common_preparation_disease_contraindication_relation"]
                      }
            # 这里传入的时候将dict转化为json形式
            entity_contnet = ai_content.query(params=json.dumps(params, ensure_ascii=False),
                                              service="entity_service", method='post')
            if entity_contnet.get('code') == 0:
                data = entity_contnet.get('data')
                entity = data.get("entity")
                disease_id = []
                for e in entity:
                    de = e.get("common_preparation_disease_contraindication_relation")
                    if de != None:
                        disease_id = disease_id + de
                if not disease_id:
                    return True
                else:
                    pa = {"id": list(disease_id),
                          "status": 0,
                          "ef": ["name"]
                          }
                    entity_c = ai_content.query(params=json.dumps(pa, ensure_ascii=False),
                                                service="entity_service", method='post')
                    da = entity_c.get('data')
                    en = da.get("entity")
                    for e in en:
                        taboos.append(e.get("name"))
    if disease in taboos:
        print("患者疾病{}在药品{}禁忌症列表中{}".format(disease, drug, taboos))
        return False
    else:
        return True

# 6.6
def antibiotic_idf(consult_info):
    f = open(global_conf.dict_path + 'antibiotic.txt', encoding='gbk')
    lines = f.readlines()
    level1_anti = lines[0].strip('\n').split(',')
    level2_anti = lines[1].strip('\n').split(',')
    technical_title = consult_info.get('technical_title','')
    drug_info = consult_info.get('prescription_drug_detail', '')
    drug = []
    # print(drug_info)
    if drug_info:
        for d in drug_info:
            common_name = d.split('|')[1]
            drug.append(common_name)
        if drug:
            anti_drug_1 = [i for i in drug if i in level1_anti]
            anti_drug_2 = [i for i in drug if i in level2_anti]
            if technical_title:
                if len(anti_drug_1) != 0 and len(anti_drug_2) == 0:
                    regex = '主治|主任|专家'
                    res = re.findall(regex,technical_title)
                    if len(res) == 0:
                        print('医生级别为"{}"，开的药品中有{}是限制级抗生素，越级开药'.format(technical_title,anti_drug_1))
                        return False
                    else:
                        return True
                elif len(anti_drug_2) != 0:
                    regex = '主任|专家'
                    res = re.findall(regex, technical_title)
                    if len(res) == 0:
                        print('医生级别为"{}"，开的药品中有{}是特殊级抗生素，越级开药'.format(technical_title, anti_drug_2))
                        return False
                    else:
                        return True
    return True

# 6.7

#7.1结束语规范
def end_reply_idf(consult_info):
    finish_type = consult_info.get('finish_type','')
    doctor_reply_list = consult_info.get('doctor_reply_list', '')
    if doctor_reply_list:
        end_reply = doctor_reply_list[-1]
        if finish_type == 1:
            regex = '你好，本次问诊即将结束，如有问题可再次发起问诊，祝您身体健康|由于你长时间没有回复，我将结束本次问诊，如有问题可再次发起问诊，祝你身体健康，再见'
            res = re.findall(regex,end_reply)
            if len(res) == 0:
                return False
    return True

if __name__ == '__main__':
    consult_info = {}
    consult_info['order_no'] = '2172344500601222230'
    consult_info['patient_sex'] = 2
    print(sex_idf)
    print(age_idf)
    print(disease_idf)