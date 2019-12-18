#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
aiserver_client.py -- the client of aiserver

Author: geeq <geeq@guahao.com>
Create on 2018-03-15 Monday.
"""

import sys
import os
import urllib
import json
import pdb

default_cfg_path = os.path.join(os.path.dirname(__file__), '../../../../etc/cdss.cfg')


if not sys.version > '3':
    import urllib2
else:
    import urllib.request as urllib2
    import urllib.parse as urllib

if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser

class AIClient():
    _instance = None

    def __init__(self, global_conf=None):
        self.__parser = ConfigParser.ConfigParser()
        self.cfg_path = default_cfg_path
        if global_conf and hasattr(global_conf, 'cfg_path'):
            self.cfg_path = global_conf.cfg_path
        print(self.cfg_path)
        self.__parser.read(self.cfg_path)
        self.host = self.__parser.get('AIService', 'IP')
        self.port = int(self.__parser.get('AIService', 'PORT'))

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __query(self, url, params, **kwargs):
        url = url + urllib.urlencode(params)
        if kwargs.get('debug'):
            print('AIServer URL:', url)
            sys.stdout.flush()
        try:
            s = urllib2.urlopen(url, timeout=3).read()
        except Exception:
            print('AIServer time out, the url is %s' % url)
            s = '{}'
        return json.loads(s)

    def __query_post(self, url, params, **kwargs):
        if kwargs.get('debug'):
            print('AIServer URL:', url)
            print('AIServer Data:', params)
            sys.stdout.flush()
        data = params['data']
        if isinstance(data, str):
            data = bytes(data, encoding = "utf8")
        request = urllib2.Request(url=url, data=data)
        try:
            s = urllib2.urlopen(request, timeout=3).read()
        except Exception:
            print('AIServer time out, the url is %s' % url)
            s = '[]'
        return json.loads(s)

    def query(self, params, debug=False, **kwargs):
        service = kwargs.get('service', 'dialogue_analysis')
        baseurl = 'http://%s:%s/%s?' % (self.host, self.port, service)
        # params['q'] = params['q'].encode('utf8')
        # url = baseurl + urllib.urlencode(params)
        # params['input'] = params['input'].decode('utf-8')
        if kwargs.get('method') == 'post':
            return self.__query_post(baseurl, params, debug=debug)
        else:
            return self.__query(baseurl, params, debug=debug)
