import graphene
from graphene import String, List, Float


class Entity(graphene.Interface):
    """
    实体基类
    """
    # 通用基础信息
    id = String(description='实体ID')
    name = String(description='实体名称')
    standard_name = String(description='标准名称')
    is_standard = String(description='是否标准词')
    standard_audit_status = String(description='本体审核状态')
    entity_type = String(description='实体类型')
    audit_status = String(description='实体审核状态')
    relation_set = List(String, description='别名集合')
    relation_set_id = List(String, description='别名ID集合')
    label_set = List(String, description='标签集合')
    # 通用属性
    is_common = String(description='是否常见实体')
    common_weight = Float(description='常见搜索指数')

