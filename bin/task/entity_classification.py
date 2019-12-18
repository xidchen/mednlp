#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: FH <fenghui@guahao.com>
Created on 2019/9/22 21:46

The script for classifying entities.（实体分类）
"""
import argparse
from mednlp.kg.classify_entity import ClassifyEntity


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_source", type=str, help="Input source")
    parser.add_argument("output_source", type=str, help="Output source")
    parser.add_argument("entity_type", type=str, help="Entity type")
    parser.add_argument("-l", "--limit", type=int, help="Limit number")
    parser.add_argument('-d', '--debug', help='Debug mode', dest='debug', action='store_true')
    args = parser.parse_args()
    input_source = args.input_source
    output_source = args.output_source
    entity_type = args.entity_type

    limit_number = -1
    if args.limit:
        limit_number = args.limit

    cl_en = ClassifyEntity(
        input_source=input_source,
        output_source=output_source,
        entity_type=entity_type,
        limit_number=limit_number,
        debug_mode=args.debug
    )
    cl_en.classify_entity()
