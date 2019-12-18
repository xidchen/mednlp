#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
post.py -- the poster

Author: maogy <maogy@guahao.com>
Create on 2019-02-11 Monday.
"""


import os
import sys
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser
from optparse import OptionParser
import global_conf

cfg_path = global_conf.cfg_path

if __name__=="__main__":
    command = """
    python %s solr_core post_file
    """ %sys.argv[0]
    base_dir = os.path.dirname(__file__)
    post_file = base_dir + '/post.sh'
    parser = ConfigParser.ConfigParser()
    parser.read(cfg_path)
    solr_host = parser.get('SolrPost', 'IP')
    solr_port = parser.get('SolrPost', 'PORT')
    dir_path = os.path.dirname(__file__)
    command = post_file + ' %s:%s %s %s' % (solr_host, solr_port ,sys.argv[1],  sys.argv[2])
    print(command)
    os.system(command)

