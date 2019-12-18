exam_status = {
    "H": "raise",
    "L": "down",
    "↑": "raise",
    "↑↑": "obvious_raise",
    "↓": "down",
    "↓↓": "obvious_down",
    "-": "negative",
    "+": "positive",
    "++": "moderate_positive",
    "+++": "strong_positive",
    "++++": "strong_positive",
    "1+": "positive",
    "2+": "moderate_positive",
    "3+": "strong_positive",
    "4+": "strong_positive",
    "±": "suspicious_positive",
    "阳性": "positive",
    "可疑阳性": "suspicious_positive",
    "中度阳性": "moderate_positive",
    "强阳性": "strong_positive",
    "阴性": "negative",
    "升高": "raise",
    "上升": "raise",
    "明显升高": "obvious_raise",
    "降低": "down",
    "下降": "down",
    "明显降低": "obvious_down",
    "-1": "suspicious_positive",
    "0": "negative",
    "1": "positive",
    "2": "moderate_positive",
    "3": "strong_positive",
    "4": "strong_positive",
    "5": "strong_positive",
    "体重偏低": "low_weight",
    "超重": "over_weight",
    "肥胖": "fat_weight",
    "增快": "accelerate",
    "减慢": "slower"
}

en_cn_match = {
    "blood_pressure": {
        "cn_name": "血压",
        "pr": "脉率",
        "sbp_level": "左侧收缩压",
        "dbp_level": "左侧舒张压",
        "right_sbp_level": "右侧收缩压",
        "right_dbp_level": "右侧舒张压"
    },
    "blood_sugar": {
        "cn_name": "血糖",
        "cholesterin": "总胆固醇",
        "triglyceride": "甘油三酯",
        "cldl": "血清低密度脂蛋白胆固醇",
        "chdl": "血清高密度脂蛋白胆固醇"
    },
    "garea_bmi": {
        "cn_name": "BMI",
        "bmi": "bmi值"
    },
    "garea_temperature": {
        "cn_name": "体温",
        "temperature": "体温"
    },
    "garea_urine": {
        "cn_name": "尿常规",
        "alb": "尿微量白蛋白",
        "pro": "尿蛋白质",
        "glu": "尿糖",
        "ket": "尿酮体",
        "blo": "尿潜血",
        "leu": "尿白细胞",
        "nit": "尿亚硝酸盐",
        "ubg": "尿胆原",
        "ph": "尿PH值",
        "sg": "尿比重",
        "bil": "尿胆红素",
        "asc": "尿抗坏血酸"
    },
    "inorganic_matter": {
        "cn_name": "无机物质",
        "k": "钾离子",
        "na": "钠离子"
    },
    "liver_function": {
        "cn_name": "肝功能",
        "alt": "谷丙转氨酶",
        "ast": "谷草转氨酶",
        "tbil": "总胆红素",
        "dbil": "直接胆红素"
    },
    "protein": {
        "cn_name": "蛋白质",
        "alb": "白蛋白"
    },
    "renal_function": {
        "cn_name": "肾功能",
        "cre": "肌酐",
        "urea": "尿素"
    },
    "healthexam_garea": {
        "cn_name": "体检其它",
        "breathRate": "呼吸频率",
        "leftVision": " 左眼视力 ",
        "rightVision": "右眼视力",
        "heartRate": "心率",
        "gluHemoglobin": "糖化血红蛋白"
    }
}

en_to_cn_status = {
    "normal": "正常",
    "negative": "阴性",
    "suspicious_positive": "可疑阳性",
    "positive": "阳性",
    "moderate_positive": "中度阳性",
    "strong_positive": "强阳性",
    "raise": "升高",
    "obvious_raise": "明显升高",
    "down": "降低",
    "obvious_down": "明显降低",
    "low_weight": "体重偏低",
    "over_weight": "超重",
    "fat_weight": "肥胖",
    "accelerate": "增快",
    "slower": "减慢"
}

rule_item = ['肾功能|肌酐', '肝功能|结合胆红素', '肝功能|总胆红素', '血生化|空腹血糖']
physical_exam = ['体温', '呼吸频率', '脉率', '心率', '收缩压', '舒张压', 'BMI', '体温', '视力']
