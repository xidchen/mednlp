#bronchitis
sql1 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name = '支气管炎'
    and LENGTH(medical_history)>20
    AND chief_complaint != '便民开药'
	AND chief_complaint NOT LIKE '%复诊%'
	AND chief_complaint NOT LIKE '%治疗%'
	AND chief_complaint NOT LIKE '%开药%'
	AND chief_complaint NOT LIKE '%肾%'
	AND chief_complaint NOT LIKE '%腹部%'
    AND medical_history != '无特殊不适'
    limit 100,100
    """
# lung_cancer
sql2 = """
select (case disease_name when '肺癌' then '肺癌' else '肺癌' end) as disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name LIKE '%肺癌%'
	AND medical_history LIKE '%肺%'
	and LENGTH(medical_history)>2
	AND chief_complaint != '便民开药'
	AND medical_history != '无特殊不适'
	limit 100,100
"""
# gastric_cancer
sql3 = """
select (case disease_name when '胃癌' then '胃癌' else '胃癌' end) as disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
where disease_name LIKE '%胃癌%'
and medical_history LIKE '%胃%'
and LENGTH(medical_history)>20
AND chief_complaint != '便民开药'
AND medical_history != '无特殊不适'
limit 100,100
"""
# appendicitis
sql4 = """
    select (case disease_name when '阑尾炎' then '阑尾炎' else '阑尾炎' end) as disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name like '%阑尾炎%'
    and LENGTH(medical_history)>2
    AND chief_complaint != '便民开药'
    AND medical_history != '无特殊不适'
    AND chief_complaint LIKE '%腹%'
    AND chief_complaint != '健康体检'
    AND chief_complaint NOT LIKE '%复诊%'
    limit 100
    """
# AURI
sql5 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name = '急性上呼吸道感染'
    and LENGTH(medical_history)>2
    AND chief_complaint != '便民开药'
    AND medical_history != '无特殊不适'
    AND chief_complaint != '健康体检'
    AND chief_complaint NOT LIKE '%复诊%'
    limit 100, 100
    """

#bronchopneumonia(支气管肺炎)
sql6 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '支气管肺炎'
	and LENGTH(medical_history)>2
	AND chief_complaint != '便民开药'
	AND medical_history != '无特殊不适'
	AND chief_complaint != '健康体检'
	AND medical_history  LIKE '%肺炎%'
	limit 100, 100
"""
# hypertension
sql7 = """
    select (case disease_name when '高血压' then '高血压' else '高血压' end) as disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name like '%高血压%'
    and LENGTH(medical_history)>2
    AND chief_complaint != '便民开药'
    AND medical_history LIKE '%血压%'
    AND chief_complaint NOT LIKE '%开药%'
    AND chief_complaint NOT LIKE '%复诊%'
    limit 100
    """
# CHD
sql8 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '冠状动脉粥样硬化性心脏病'
	and LENGTH(medical_history)>20
	and LENGTH(chief_complaint)>20
	AND chief_complaint != '阵发性胸痛天，加重天'
	AND chief_complaint not LIKE '%牙%'
	AND medical_history != '无特殊不适'
	AND chief_complaint != '健康体检'
	AND chief_complaint != '见特殊病历记录'
	AND medical_history LIKE '%心电图%'
	limit 100, 100
	"""
# CG
sql9 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name = '慢性胃炎'
    and LENGTH(medical_history)>20
    AND medical_history != '无特殊不适'
	AND chief_complaint LIKE '%胃%'
    limit 100
    """

# GC
sql10 = """
    select (case disease_name when '胃CA' then '胃癌' else '胃癌' end) as disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name = '胃Ca'
    and LENGTH(medical_history)>2
    AND LENGTH(chief_complaint)>2
    AND chief_complaint != '便民开药'
    AND medical_history != '无特殊不适'
	AND chief_complaint != '健康体检'
	AND chief_complaint != '见特殊病历记录'
	AND medical_history  LIKE '%胃%'
    limit 100, 100
    """
# spondylosis
sql11 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
    where disease_name = '颈椎病'
    and LENGTH(medical_history)>2
    AND chief_complaint != '便民开药'
    AND medical_history != '无特殊不适'
	AND chief_complaint != '健康体检'
	AND chief_complaint != '见特殊病历记录'
	AND chief_complaint NOT LIKE '%开药%'
	AND chief_complaint NOT LIKE '%复诊%'
    limit 100, 100
    """
# periodontitis
sql12 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '慢性牙周炎'
	and LENGTH(medical_history)>2
	AND chief_complaint != '便民开药'
	AND medical_history != '无特殊不适'
	AND chief_complaint != '健康体检'
	AND chief_complaint != '见特殊病历记录'
	AND chief_complaint NOT LIKE '%开药%'
	AND chief_complaint NOT LIKE '%复诊%'
	AND chief_complaint NOT LIKE '%要求%'
	limit 100, 100
	"""

#cerebral infarction
sql13 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '脑梗死'
	and LENGTH(medical_history)>2
	AND chief_complaint != '便民开药'
	AND medical_history != '无特殊不适'
	AND chief_complaint != '健康体检'
	AND medical_history  LIKE '%脑梗%'
	limit 100, 100
"""

#acute cerebrovascular disease(ACD)
sql14 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '急性脑血管病'
	and LENGTH(medical_history)>2
	AND chief_complaint NOT LIKE '%开药%'
	AND chief_complaint NOT LIKE '%购买%'
	AND chief_complaint NOT LIKE '%要求%'
	AND chief_complaint not like '%健康%'
	AND medical_history like '%急性脑血%'
	limit 100
"""

#myoma of uterus(MOU)
sql15 = """
    select disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '子宫肌瘤'
	and LENGTH(medical_history)>2
	AND chief_complaint NOT LIKE '%开药%'
	AND chief_complaint NOT LIKE '%购买%'
	AND chief_complaint NOT LIKE '%要求%'
	AND chief_complaint not like '%健康%'
	limit 100, 100
"""
#esophagus cancer
sql16 = """
    select (case disease_name when '食管CA' then '食管癌' else '食管癌' end) as disease_name, chief_complaint, medical_history FROM medical_data.medical_record_data
	where disease_name = '食管CA'
	and LENGTH(medical_history)>2
	AND chief_complaint NOT LIKE '%开药%'
	AND chief_complaint NOT LIKE '%购买%'
	AND chief_complaint NOT LIKE '%要求%'
	AND medical_history like '%食管%'
	limit 100, 100
"""

sql_list = [sql1, sql2, sql3, sql4, sql5, sql6, sql7, sql8,
            sql9, sql10, sql11, sql12, sql13, sql14, sql15, sql16]

disease_list = ['bronchitis', 'lung_cancer', 'gastric_cancer', 'appendicitis', 'AURI', 'bronchopneumonia',
                'hypertension', 'CHD', 'CG', 'GC', 'spondylosis', 'periodontitis', 'cerebral_infarction',
                'ACD', 'MOU', 'esophagus_cancer']