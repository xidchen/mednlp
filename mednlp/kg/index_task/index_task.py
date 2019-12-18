#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
index_task.py -- the index task

Author: maogy <maogy@guahao.com>
Create on 2019-03-05 Tuesday.
"""


import sys
from optparse import OptionParser
from .index_entity import IndexEntity
from .index_cloud_entity import IndexCloudEntity
from .index_graphql_entity import IndexGraphQlEntity
from .index_graphql_relation import IndexGraphQlRelation
from .index_rule import IndexRuleCondition

import global_conf


if __name__ == "__main__":

    command = """
    python %s [options]
    """ % sys.argv[0]

    cfg_path = global_conf.cfg_path

    parser = OptionParser(usage=command)
    parser.add_option("-s", "--service", dest="service",
                      help="the service to index", metavar="string")
    parser.add_option("-t", "--seconds", dest="seconds",
                      help="the pre seconds read", metavar="INT")
    parser.add_option("-i", "--ids", dest="ids",
                      help="the id to add", metavar="string")
    (options, args) = parser.parse_args()

    service_dict = {
        'cloud_entity': IndexCloudEntity,
        'graphql_entity': IndexGraphQlEntity,
        'graphql_relation': IndexGraphQlRelation,
        'rule_condition': IndexRuleCondition,
        'entity': IndexEntity
    }
    params = {}
    if options.seconds:
        params['seconds'] = options.seconds
    if options.ids:
        params['ids'] = options.ids
    if options.service:
        i = service_dict[options.service](global_conf, **params)
        i.index()
