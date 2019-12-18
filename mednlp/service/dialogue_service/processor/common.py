#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
import global_conf
middleware_cfg_path = global_conf.cfg_path

class MiddlewareConfiguration(object):

    """读取middleware.cfg中的配置，采用单例类，文件只读取一次"""

    def __new__(self, *args, **kwargs):
        if not hasattr(self, '_instance'):
            self._instance = super(MiddlewareConfiguration,
                                   self).__new__(self, *args, **kwargs)
            self._instance.__initialize__()
        return self._instance

    def __initialize__(self):
        self.parser = ConfigParser.ConfigParser()
        self.parser.read(middleware_cfg_path)

        # 获取一个配置项
    def get_option(self, section, option):
        if self.parser.has_option(section, option):
            return self.parser.get(section, option)
        return None

        # 获取一个配置的全部配置项
    def get_section(self, section):
        if self.parser.has_section(section):
            return {item[0] :item[1] for item in self.parser.items(section)}
        return None


def get_outer_service_url():
    return MiddlewareConfiguration().get_option('OuterService', 'URL_PATH')

def get_ai_service_url():
    return MiddlewareConfiguration().get_option('AIService', 'URL_PATH')