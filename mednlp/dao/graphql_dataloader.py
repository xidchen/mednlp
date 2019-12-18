from promise import Promise
from promise.dataloader import DataLoader
from ailib.client.cloud_solr import CloudSolr
from functools import wraps
from ailib.utils.log import GLLog
import ailib.service.parameter as parameter
from time import time as timer
import global_conf
import traceback
import collections


cloud_solr = CloudSolr(global_conf.cfg_path)
logger = GLLog('graphql_dataloader', log_dir=global_conf.log_dir, level='info').getLogger()

ENTITY_NORMAL_QUERY_FIELD = """
name_s^10 name_eg^5 name_ng^4 name_code_s^10 name_code_ng^4 name_code_eg^5 name_py_s^11 name_py_ng^5 name_py_eg^6
"""

ENTITY_SOLR_QUERY_FIELD = """
name_s^10 relation_set_ss^9 name_eg^8 name_ng^1 
name_code_s^10 name_code_ng^1 name_code_eg^8 
name_py_s^11 name_py_ng^2 name_py_eg^9
"""


class RelationLoader(DataLoader):
    """
    关系数据加载器
    """
    def batch_load_fn(self, keys):
        # Here we return a promise that will result on the
        # corresponding user for each key in keys
        docs = DataQueryUtils.query_relation(ids=keys)
        doc_map = dict([(doc.get('id'), doc) for doc in docs])
        return Promise.resolve([doc_map.get(key, None) for key in keys])


class EntityLoader(DataLoader):
    """
    实体数据加载器
    """
    def batch_load_fn(self, keys):
        from mednlp.dao.graphql_disease import Disease
        _resolve_entity = dict()
        _resolve_entity['disease'] = Disease
        docs = DataQueryUtils.get_entity(id=keys, entity_type=[key for key in _resolve_entity.keys()])
        doc_map = dict([(doc.get('id'), _resolve_entity[doc['entity_type']](**doc)) for doc in docs])
        return Promise.resolve([doc_map.get(key, None) for key in keys])


_entity_field = {
    'common_field': ['id', 'name:name_s', 'entity_type:type_s', 'standard_name:standard_name_s',
                     'standard_audit_status:standard_audit_status_s', 'is_standard:is_standard_s',
                     'audit_status:audit_status_s', 'relation_set:relation_set_ss', 'relation_set_id:relation_set_id_ss',
                     'label_set:label_set_ss', 'is_common:is_common_ss', 'common_weight:common_weight_f'],
    'disease': ['male_rate:male_rate_ss', 'female_rate:female_rate_ss', 'age_scope_1_rate:age_scope_1_rate_ss',
                'age_scope_2_rate:age_scope_2_rate_ss', 'age_scope_3_rate:age_scope_3_rate_ss',
                'age_scope_4_rate:age_scope_4_rate_ss', 'age_scope_5_rate:age_scope_5_rate_ss',
                'age_scope_6_rate:age_scope_6_rate_ss', 'overview:overview_tt', 'clinical_manifestation:clinical_manifestation_tt',
                'diagnosis:diagnosis_tt', 'differential_diagnosis:differential_diagnosis_tt', 'diagnosis:diagnosis_tt',
                'differential_diagnosis:differential_diagnosis_ss', 'treatment:treatment_tt', 'stage:stage_tt',
                'complication:complication_tt', 'follow_up_guidance:follow_up_guidance_tt', 'referral:referral_tt',
                'prevention:prevention_tt', 'health_education:health_education_tt', 'treatment_process:treatment_process_tt',
                'auxiliary_inspection:auxiliary_inspection_tt', 'disease_id:disease_id_ss', 'common_disease_id:common_disease_id_ss',
                'alias_disease_id:alias_disease_id_ss',
                'disease_symptom_clinical_relation:disease_symptom_clinical_relation_ss',
                'disease_physical_examination_clinical_relation:disease_physical_examination_clinical_relation_ss',
                'disease_inspection_filter_relation:disease_inspection_filter_relation_ss',
                'disease_examination_filter_relation:disease_examination_filter_relation_ss',
                'disease_disease_paternity_relation:disease_disease_paternity_relation_ss']
}

_relation_field = {
    'pure_relation': ['id', 'relation_type:relation_type_s', 'relation_name:relation_name_s',
                      'audit_status:audit_status_s', 'from_id:from_id_s', 'from_name:from_name_s',
                      'from_type:from_type_s', 'to_id:to_id_s', 'to_name:to_name_s', 'to_type:to_type_s',
                      'relation_score:relation_score_f']
}


def print_exec_time(fn):
    """
    打印方法的运行时间
    :param fn:
    :return:
    """
    @wraps(fn)
    def measure_time(*args, **kwargs):
        start = timer()
        result = fn(*args, **kwargs)
        duration = timer() - start
        logger.info("函数:{},\t请求耗时：{} ms \t参数:{},{}".format(fn.__name__, round(duration * 1000, 2), args, kwargs))
        return result
    return measure_time


class DataQueryUtils:

    @staticmethod
    @print_exec_time
    def get_entity(**kwargs):
        """
        获取实体数据
        :param kwargs:
        :return:
        """
        query = DataQueryUtils.deal_parameter(kwargs.get('q', '*:*'))
        if query != '*:*':
            query = parameter.escape_solr(query)
        param = {
            'q': query,
            'start': kwargs.get('start', 0),
            'rows': kwargs.get('rows', 10),
            'qf': ENTITY_SOLR_QUERY_FIELD if kwargs.get('match_alias') == 1 else ENTITY_NORMAL_QUERY_FIELD,
            'fl': '*'
        }
        fq = {}
        fq_list = param.setdefault('fq_list', [])
        if kwargs.get('id'):
            if kwargs.get('match_alias') == 1:
                fq['relation_set_id_ss'] = ' OR '.join(kwargs.get('id'))
            else:
                fq['id'] = ' OR '.join(kwargs.get('id'))
        escape_names = []
        if kwargs.get('name'):
            escape_names = DataQueryUtils.deal_parameter(kwargs['name'])
            escape_names = parameter.escape_solr_list(escape_names)
            if kwargs.get('match_alias') == 1:
                fq['relation_set_ss'] = ' OR '.join(escape_names)
                escape_names.clear()
            else:
                fq['name_s'] = ' OR '.join(escape_names)

        if kwargs.get('exclude_name'):
            exclude_name = DataQueryUtils.deal_parameter(kwargs['exclude_name'])
            exclude_name = parameter.escape_solr_list(exclude_name)
            exclude_name = ['-'+name for name in exclude_name]
            if escape_names:
                exclude_name.extend(escape_names)
            fq['name_s'] = '(' + ' '.join(exclude_name) + ')'

        if kwargs.get('entity_type'):
            fq['type_s'] = '(' + ' '.join(kwargs['entity_type']) + ')'
        if kwargs.get('audit_status'):
            fq['audit_status_s'] = '(' + ' '.join(kwargs['audit_status']) + ')'
        if kwargs.get('is_standard'):
            fq['is_standard_s'] = kwargs['is_standard']
            fq['standard_audit_status_s'] = 1
        if kwargs.get('is_common') == '1':
            fq['is_common_ss'] = '是'
        if kwargs.get('label'):
            fq['label_set_ss'] = '(' + ' '.join(kwargs['label']) + ')'
        if kwargs.get('label_intersection'):
            fq['label_set_ss'] = '(' + ' AND '.join(kwargs['label_intersection']) + ')'
        if kwargs.get('sex'):
            sex = kwargs.get('sex')
            sex_field = ''
            if sex == 1:
                sex_field = 'male_rate'
            elif sex == 2:
                sex_field = 'female_rate'
            fq['-'+sex_field+'_ss'] = 0
        label_field = kwargs.get('label_field')
        ef = []
        if label_field:
            ef.extend(['_' + f+'_label_s' for f in label_field])
        ef.extend(_entity_field['common_field'])
        for entity_type in kwargs.get('entity_type', []):
            ef.extend(_entity_field.get(entity_type, []))
        param['fl'] = ','.join(ef)
        param['bf'] = 'name_length_i'
        param['sort'] = collections.OrderedDict()
        if query == '*:*':  # 设置默认查询根据词频排序
            param['sort']['common_weight_f'] = 'desc'
            param['sort']['name_length_i'] = 'desc'
            name_score = '0'
        else:
            param['sort']['name_length_i'] = 'desc'
            param['sort']['common_weight_f'] = 'desc'
            name_score = 'field(name_length_i)'
        if kwargs.get('label_order'):  # 根据label_order设置打分规则
            bf = []
            for index, label_item in enumerate(kwargs.get('label_order')[::-1]):
                bf.append('if(exists(_%s_label_s),%d,0)' % (label_item, (index + 1) * 100))
            if bf:
                param['bf'] = 'sum(max(%s),%s,if(exists(common_weight_f),1,0))' % (','.join(bf), name_score)
                param['sort']['score'] = 'desc'
                param['sort'].move_to_end('score', last=False)

        res = {}
        try:
            res = cloud_solr.solr_search(param['q'], interface='ai_graphql_entity', fq_dict=fq, **param)
        except:
            traceback.print_exc()
            logger.info("请求实体数据异常,{}".format(traceback.format_exc()))
        if res and res['code'] == 200:
            docs = res['data']
        else:
            docs = []
        return docs

    @staticmethod
    @print_exec_time
    def query_relation(**kwargs):
        """
        获取关系数据
        :param kwargs:
        :return:
        """
        docs = []
        if kwargs.get('ids'):
            param = {
                'rows': len(kwargs.get('ids')),
                'fl': ','.join(_relation_field['pure_relation'])
            }
            if kwargs.get('to_name'):
                param['filter'] = ['to_name_s:(%s)'%(','.join(kwargs.get('to_name')))]
            fq = {'id': ' OR '.join(kwargs.get('ids'))}
            res = {}
            try:
                res = cloud_solr.solr_search('*:*', interface='ai_graphql_relation', fq_dict=fq, **param)
            except:
                traceback.print_exc()
                logger.info("请求关系异常,{}".format(traceback.format_exc()))
            if res and res['code'] == 200:
                docs = res['data']
        return docs

    @staticmethod
    def deal_parameter(parameters):
        """
        根据传入类型处理字符串前后空格
        :param parameters: 字符或列表类型值
        :return: 处理后的入参
        """
        if isinstance(parameters, str):
            parameters = parameters.strip()
        elif isinstance(parameters, list):
            for index in range(len(parameters)):
                if isinstance(parameters[index], str):
                    parameters[index] = parameters[index].strip()
        return parameters


