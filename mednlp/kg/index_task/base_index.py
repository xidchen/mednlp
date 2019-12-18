#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
base_index.py -- the base class of index builder

Author: maogy <maogy@guahao.com>
Create on 2017-02-20 Monday.
"""


import os
import sys
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser
from optparse import OptionParser
import traceback
import formatter
from ailib.utils.log import GLLog


class BaseIndex(object):
    """
    索引构建基类.
    需指定类属性:index_filename,core
    需重载方法:get_data,process_data
    可选重载方法:initialise
    """

    # 索引文件文件名定义,通常用于全量重建,
    index_filename = None
    # 该索引类对应的solr的core,通常每个类需要单独指定
    core = 'core'

    output_type = 'xml'
    solr_operate = 'add'
    dest_dir = None
    cfg_path = ''
    filename = None
    dev_mode = False
    service_mode = False
    inc_sec = 0
    inc_ids = set()
    is_page = False
    page_status = 1
    for_canal = False

    def __init__(self, gconf, **kwargs):
        """
        构造函数.
        参数:
        output_type->索引输出方式,目前支持值:xml
        solr_operate->索引的solr操作,目前支持值:add,delete等
        dest_dir->索引文件目标输出目录
        dev->是否开发模式,开发模式覆盖cfg文件的输出文件配置
        """
        self.logger = GLLog('index_service',
                            log_dir=gconf.log_dir).getLogger()
        self.cfg_path = gconf.cfg_path
        self.parse_cfg()
        self.output = None
        if kwargs.get('dev'):
            self.dev_mode = kwargs['dev']
            self.dest_dir = None
            self.filename = None
            self.parse_args()
        if kwargs.get('output_type'):
            self.output_type = kwargs['output_type']
        if kwargs.get('solr_operate'):
            self.solr_operate = kwargs['solr_operate']
        if kwargs.get('dest_dir'):
            self.dest_dir = kwargs['dest_dir']
        if kwargs.get('seconds'):
            self.inc_sec = int(kwargs['seconds'])
        if kwargs.get('ids'):
            self.inc_ids = set(kwargs['ids'].split(','))
        if kwargs.get('for_canal'):
            self.for_canal = kwargs['for_canal']
        if self.inc_sec or self.inc_ids:
            self.filename = None
            if not self.dev_mode:
                self.dest_dir = self.incremental_dir
        if kwargs.get('service'):
            self.service_mode = kwargs['service']
            self.filename = None
            self.dest_dir = self.incremental_dir
        self.initialise(**kwargs)

    def parse_cfg(self):
        """
        cfg文件(middleware.cfg)解析.
        解析配置->Index:FULL_DIR,INCREMENTAL_DIR
        Solr:PORT,IP
        """
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.cfg_path)
        section = 'Index'
        if self.config.has_option(section, 'FULL_DIR'):
            self.full_dir = self.config.get(section, 'FULL_DIR')
            self.full_dir = self.full_dir + '/' + self.core
            self.dest_dir = self.full_dir
            self.filename = self.index_filename
        if self.config.has_option(section, 'INCREMENTAL_DIR'):
            self.incremental_dir = self.config.get(section, 'INCREMENTAL_DIR')
            self.incremental_dir = self.incremental_dir + '/' + self.core
        section = 'SolrPost' if self.config.has_section('SolrPost') else 'Solr'
        if self.config.has_option(section, 'PORT'):
            self.solr_port = self.config.get(section, 'PORT')
        if self.config.has_option(section, 'IP'):
            self.solr_ip = self.config.get(section, 'IP')

    def parse_args(self):
        """
        解析脚本命令行参数.
        """
        command = """
        python %s [options]
        """ % sys.argv[0]
        parser = OptionParser(usage=command)
        parser.add_option("-c", "--config", dest="config",
                          help="the config file", metavar="FILE")
        parser.add_option("-g", "--debug", dest="debug", default=False,
                          help="run in debug mode", action="store_true")
        parser.add_option("-t", "--seconds", dest="seconds",
                          help="the pre seconds read", metavar="INT")
        parser.add_option("-i", "--ids", dest="ids",
                          help="the id to add", metavar="string")
        parser.add_option("-d", "--directory", dest="directory",
                          help="directory store index file", metavar="FILE")
        (options, args) = parser.parse_args()
        if options.config:
            self.cfg_path = options.config
        if options.directory:
            self.dest_dir = options.directory
        if options.seconds:
            self.inc_sec = int(options.seconds)
        if options.ids:
            self.inc_ids = set(options.ids.split(','))
        if options.debug:
            self.debug = True

    def initialise(self, **kwargs):
        """
        子类可重载的初始化函数(可选).
        """
        pass

    def get_data(self, ids=None):
        """
        获取数据的方法,子类必须重载实现.
        参数:不定.
        返回值:一个原始数据的字典列表.
        结构为:[{field1:value1,field2:value2,..},..]
        """
        pass

    def process_data(self, data):
        """
        处理原始数据,构建索引文档.
        参数:
        data->必传参数,为get_data方法的返回值.
        结构为:[{field1:value1,field2:value2,..},..]
        返回值:
        适用于solr相应core的索引文档(doc),也为字典列表格式.
        具体结构为:[{field1:value1,field2:value2,..},..]
        """
        pass

    def data_output(self, docs, close=True):
        """
        索引文档格式化输出.
        目前实现的有xml方式的输出,由构造函数的output_type参数指定输出方式.
        参数:
        docs->构建完成的索引文档,具体结构:[{field1:value1,field2:value2,..},..].
        close->本次输出结束后是否关闭输出,主要用于分页构建的输出,默认True.
        """
        if self.output_type == 'xml':
            if self.output is None or self.service_mode:
                self.output = formatter.SolrXMLBuilder(self.dest_dir,
                                                       self.solr_operate,
                                                       self.filename)
        self.output.append(docs)
        if close:
            self.output.close()
            if self.filename:
                self.commit_xml()

    def commit_xml(self):
        """
        xml方式索引输出的索引文件提交.
        """
        base_dir = os.path.dirname(__file__)
        post_file = base_dir + '/./post.sh'
        xml_file = self.dest_dir + '/' + self.filename
        command = post_file + ' %s:%s %s %s' % (self.solr_ip, self.solr_port,
                                                self.core, xml_file)
        print(command)
        os.system(command)

    def check_runtime(self):
        """
        检查运行环境是否正确,比如:数据库连接等.
        返回值->正确返回0,错误返回非零,1表述数据库连接异常.
        """
        if hasattr(self, 'db'):
            if self.db.is_close():
                return 1
        return 0

    def merge_data(self, data, message):
        return data

    def get_data_pre(self, **kwargs):
        pass

    def index(self, **kwargs):
        """
        索引构建流程控制.
        流程:get_data->process_data->data_output.
        可选参数:
        ids->增量id,逗号分隔的字符串.
        message->需要合并的消息(常用于实时通道),由merge_data处理,get_data_pre也
        会有一些简单处理.
        """
        try:
            self.__index(**kwargs)
        except Exception:
            self.logger.error(traceback.format_exc())

    def __index(self, **kwargs):
        """
        索引构建流程控制.
        流程:get_data->process_data->data_output.
        可选参数:
        ids->增量id,逗号分隔的字符串.
        message->需要合并的消息(常用于实时通道),由merge_data处理,get_data_pre也
        会有一些简单处理.
        """
        self.get_data_pre(**kwargs)
        data = None
        while(self.page_status):
            try:
                data = self.get_data()
            except Exception:
                self.logger.error(traceback.format_exc())
                if self.check_runtime():
                    self.initialise()
                    data = self.get_data()
                else:
                    return
            if kwargs.get('message') and not self.for_canal:
                data = self.merge_data(data, kwargs['message'])
            docs = self.process_data(data)
            if self.is_page and self.page_status:
                self.data_output(docs, close=False)
            else:
                self.data_output(docs)
            if not self.is_page:
                break
        if hasattr(self, 'db') and not self.service_mode:
            self.db.close()
