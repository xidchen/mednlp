import graphene
from graphene import List, String
from mednlp.dao.graphql_entity import Entity
from mednlp.dao.graphql_relation import PureRelation
from mednlp.dao.graphql_dataloader import DataQueryUtils, RelationLoader

relation_loader = RelationLoader(max_batch_size=100)


class Disease(graphene.ObjectType):
    """
    疾病
    """
    class Meta:
        interfaces = (Entity, )
    # 属性信息
    male_rate = List(String, description='男性发病率')
    female_rate = List(String, description='女性发病率')
    age_scope_1_rate = List(String, description='年龄范围1发病率')
    age_scope_2_rate = List(String, description='年龄范围2发病率')
    age_scope_3_rate = List(String, description='年龄范围3发病率')
    age_scope_4_rate = List(String, description='年龄范围4发病率')
    age_scope_5_rate = List(String, description='年龄范围5发病率')
    age_scope_6_rate = List(String, description='年龄范围6发病率')
    overview = List(String, description='疾病概述')
    clinical_manifestation = List(String, description='临床表现')
    diagnosis = List(String, description='诊断')
    differential_diagnosis = List(String, description='鉴别诊断')
    treatment = List(String, description='治疗')
    stage = List(String, description='分层分级')
    complication = List(String, description='并发症')
    follow_up_guidance = List(String, description='随访指导')
    referral = List(String, description='转诊')
    prevention = List(String, description='预防')
    health_education = List(String, description='健康教育')
    treatment_process = List(String, description='疾病管理流程')
    auxiliary_inspection = List(String, description='辅助检查')

    # 标签信息
    disease_id = List(String, description='基础疾病库第一优先级标准词ID')
    common_disease_id = List(String)
    alias_disease_id = List(String)

    # 关系信息
    disease_symptom_clinical_relation = List(PureRelation, description='疾病-症状-临床表现')
    disease_physical_examination_clinical_relation = List(PureRelation, description='疾病-体征-临床表现')
    disease_inspection_filter_relation = List(PureRelation, description='疾病-检验-筛查检验')
    disease_examination_filter_relation = List(PureRelation, description='疾病-检查-筛查检查')
    disease_disease_paternity_relation = List(PureRelation, description='疾病-疾病-父子关系')

    @staticmethod
    def resolve_disease_symptom_clinical_relation(parent, info):
        """
        解析疾病-症状-临床表现
        :return: 关系类型
        """
        result = []
        if getattr(parent, info.field_name):
            for e_id in getattr(parent, info.field_name):
                result.append(relation_loader.load(e_id))
        return result

    @staticmethod
    def resolve_disease_physical_examination_clinical_relation(parent, info):
        """
        解析疾病-体征-临床表现
        :return: 关系类型
        """
        result = []
        if getattr(parent, info.field_name):
            result = relation_loader.load_many(getattr(parent, info.field_name))
        return result

    @staticmethod
    def resolve_disease_inspection_filter_relation(parent, info):
        """
        解析疾病-检验-筛查检查
        :return: 关系类型
        """
        result = []
        if getattr(parent, info.field_name):
            result = relation_loader.load_many(getattr(parent, info.field_name))
        return result

    @staticmethod
    def resolve_disease_examination_filter_relation(parent, info):
        """
        解析疾病-检查-筛查检查
        :return: 关系类型
        """
        result = []
        if getattr(parent, info.field_name):
            result = relation_loader.load_many(getattr(parent, info.field_name))
        return result

    @staticmethod
    def resolve_disease_disease_paternity_relation(parent, info):
        """
        解析疾病-疾病-父子关系
        :return: 关系类型
        """
        result = []
        if getattr(parent, info.field_name):
            result = relation_loader.load_many(getattr(parent, info.field_name))
        return result
