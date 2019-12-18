import graphene
from graphene import Schema, List, String, Int
from mednlp.dao.graphql_disease import Disease
from mednlp.dao.graphql_entity import Entity
from mednlp.dao.graphql_middleware import GraphQlMiddleWare
from mednlp.dao.graphql_dataloader import DataQueryUtils
import json


class Query(graphene.ObjectType):
    diseases = List(Disease,
                    q=String(default_value='*:*', description='模糊查询字段'),
                    id=List(String, description='疾病ID列表'),
                    name=List(String, description='疾病名称列表'),
                    match_alias=Int(description='开启别名匹配'),
                    label=List(String, description='业务标签列表'),
                    audit_status=List(String, description='实体审核状态'),
                    sex=Int(description='性别过滤字段'),
                    exclude_name=List(String, description='排除实体名称列表'),
                    entity_type=List(String, default_value=['disease'], description='实体类型列表'),
                    label_order=List(String, description='业务标签排序列表'),
                    is_standard=String(description='查询指定实体标准词状态的数据'),
                    is_common=String(description='查询指定实体常见状态的数据'),
                    start=Int(default_value=0, description='起始行数'),
                    rows=Int(default_value=10, description='页大小')
                    )

    @staticmethod
    def resolve_diseases(parent, info, **kwargs):
        docs = DataQueryUtils.get_entity(parent=parent, info=info, **kwargs)
        result = []
        for doc in docs:
            result.append(Disease(**doc))
        return result


if __name__ == '__main__':
    schema = Schema(query=Query, auto_camelcase=False)
    x = schema.get_type_map()
    query_str = """
    { 
        diseases(q:"*:*" start:0 rows: 20  sex:0 label_order:["pkCizO3q", "JpAFSSYS"]){ 
            id 
            name
            male_rate
            female_rate
            standard_name
            is_standard
            entity_type
            audit_status
            is_common
            common_weight
            male_rate
            overview
            disease_id
            disease_symptom_clinical_relation{
                id
                relation_name
                to_obj{
                    id
                    name
                }
                to_name
            }
        }    
    }
    """
    response = schema.execute(query_str)
    print(json.dumps(response.data, ensure_ascii=False))
    pass

