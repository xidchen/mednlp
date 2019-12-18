# -*- coding: utf-8 -*-

from ailib.client.cloud_solr import CloudSolr
import mednlp.text.pinyin as pinyin
import hashlib
import json
import global_conf

def rule_condition_prefilter(cloud_client: CloudSolr, org_code: str, rule_group: str, question_codes: dict, **kwargs) -> (dict, dict):
    """
    根据条件对需要出发的规则进行预过滤
    :param org_code: 机构ID
    :param rule_group: 规则组名称
    :param question_codes: 全局问题code和答案
    :param kwargs: 可扩展参数
    :param kwargs: 可扩展参数
    :return: {'rule_id':{'name':'123', 'code':'123'}},{'rule_id':{'name':'123', 'code':'123', 'case_set':['1']}}
    """
    map_result = {}
    not_map_result = {}
    fq_dict = {
        'organize_code_s': org_code,
        'rule_group_ss': rule_group
    }
    if 'rule_entities' in kwargs:
        fq_dict['rule_entity_ss'] = ' and '.join(kwargs['rule_entities'])
    code_set = set()
    fl = ['rule_code:rule_code_s', 'rule_id:rule_id_s', 'rule_entity:rule_entity_ss', 'question_total:question_total_i']

    for key, values in question_codes.items():
        for value in values:
            value = str(value)
            code_set.add('question_{}_{}_i'.format(key, hashlib.md5(value.encode(encoding='utf8')).hexdigest()))
    fl.append('match_total:sum({})'.format(','.join(['if(exists({}), field({}), 0)'.format(code, code) for code in code_set])))
    fl.append('is_else_case:is_else_case_s')
    fl.append('next_node_type:next_node_type_s')
    fl.append('rule_name:rule_name_s')
    fl.append('rule_case_id:rule_case_id_s')
    param = {
        'timeout': 0.3,
        'fl': ','.join(fl),
        'fq_list': ['gad_condition_s:1 OR is_else_case_s:1 OR '+' OR '.join([code + ':1' for code in code_set])],
        'rows': 100,
        'group': {
            'groupField': 'rule_code_s',
            'groupLimit': 100
        }
    }
    if code_set:
        groups = []
        for i in range(0, 3):
            groups_tem, search_again = single_query(cloud_client=cloud_client, fq_dict=fq_dict, param=param, start=i*100)
            groups.extend(groups_tem)
            if not search_again:
                break
        if groups:
            for group in groups:
                for data in group.get('result', []):
                    if data.get('match_total') == data.get('question_total') and data.get('next_node_type', '') == '3':
                        map_result[data.get('rule_id')] = {
                            'code': data.get('rule_code'),
                            'name': data.get('rule_name'),
                        }
                    else:
                        not_map_result.setdefault(data.get('rule_id'), {})['code'] = data.get('rule_code')
                        not_map_result.setdefault(data.get('rule_id'), {})['name'] = data.get('rule_name')
                        not_map_result.setdefault(data.get('rule_id'), {}).setdefault('case_set', []).append(
                            data.get('rule_case_id'))
            for key in map_result.keys():
                if key in not_map_result:
                    del not_map_result[key]

    return map_result, not_map_result


def single_query(cloud_client: CloudSolr, fq_dict: dict, param: dict, start:int =0)->dict:
    """
    根据条件查询一次solr
    :param fq_dict: solr过滤条件
    :param param: solr普通参数
    :param start: 开始的数据条数
    :return:
    """
    result = {}
    groups = []
    search_again = False
    param['start'] = start
    try:
        result = cloud_client.solr_search('*:*', 'ai_rule_condition_prefilter', fq_dict, **param)
    except Exception:
        param['fq_dict'] = fq_dict
        traceback.print_exc()
        print('预过滤规则失败，参数：{}'.format(json.dumps(param, ensure_ascii=False)))
    if result and result['code'] == 200:
        group_values = result.get('groupResult', {}).get('values', [])
        if group_values:
            groups = group_values[0].get('values', [])
            total = group_values[0].get('ngroups', -1)
            if (start+1) * 100 < total:
                search_again = True
    return groups, search_again



if __name__ == '__main__':
    cloud_client = CloudSolr(global_conf.cfg_path)
    question_codes = {
        'tizheng2':['体位2', '面容2', '苗条'],
        'sex':['男']
    }
    result = rule_condition_prefilter(cloud_client, org_code='b07d3a56ae654ab5971dc7ab8c07a6d5', rule_group='多case测试', question_codes=question_codes)
    print(result)
