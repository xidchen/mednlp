import graphene
from graphene import String, Float
from mednlp.dao.graphql_entity import Entity
from mednlp.dao.graphql_dataloader import EntityLoader

entity_loader = EntityLoader(max_batch_size=100)


class Relation(graphene.ObjectType):
    """
    关系基类
    """
    id = String(description='关系ID')
    relation_type = String(description='关系类型')
    relation_name = String(description='关系名称')
    audit_status = String(description='审核状态')
    from_id = String(description='From实体Id')
    from_obj = graphene.Field(Entity, description='From实体')
    from_name = String(description='From实体名称')
    from_type = String(description='From实体类型')
    to_id = String(description='To实体Id')
    to_obj = graphene.Field(Entity, description='To实体')
    to_name = String(description='To实体名称')
    to_type = String(description='To实体类型')
    relation_score = Float(description='关系系数')

    @staticmethod
    def resolve_from_obj(parent, info):
        """
        解析疾病-症状-临床表现
        :return: 关系类型
        """
        result = None
        if parent.get('from_id'):
            result = entity_loader.load(parent['from_id'])
        return result

    @staticmethod
    def resolve_to_obj(parent, info):
        """
        解析疾病-症状-临床表现
        :return: 关系类型
        """
        result = None
        if parent.get('to_id'):
            result = entity_loader.load(parent['to_id'])
        return result


class PureRelation(Relation):
    """
    纯净版关系类
    """
    pass
