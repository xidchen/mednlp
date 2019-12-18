#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
formatter.py -- format module for index

Author: maogy <maogy@guahao.com>
Create on 2016-11-26 Saturday.
"""

import sys
import string
import ailib.utils.ioutil as ioutil
if not sys.version > '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')

## 定义全局变量
if sys.version > '3':
    basestring = str
else:
    basestring = (str, unicode)


class SolrXMLFormatter:
    def __init__(self, data):
        self.data = data

    def format(self, pp='\t\t', sp='\n'):
        data = self.data
        buf = []
        if 'pop' in data:
            boost_score = data['pop']
            buf.append('%s<doc boost="%s">%s' % ('\t', boost_score, sp))
        else:
            buf.append('%s<doc>%s' % ('\t', sp))
        for key in data:
            value = data[key]
            if value is not None:
                if (isinstance(value, list) or isinstance(value, set)
                    or isinstance(value, dict)):
                    for v in value:
                        if isinstance(v, basestring):
                            v = cdata(v)
                        buf.append('%s<field name="%s">%s</field>%s' % (
                            pp, key, v, sp))
                else:
                    if isinstance(value, basestring):
                        value = cdata(value)
                    buf.append('%s<field name="%s">%s</field>%s' % (pp, key,
                                                                    value, sp))
        buf.append('%s</doc>%s' % ('\t', sp))
        return ''.join(buf)


def cdata(s):
    """
    字符串进行CDATA包装.
    """
    if isinstance(s, basestring):
        if not sys.version > '3':
            if isinstance(s, unicode):
                s = s.encode('utf-8')
        s = remove_control_characters(s)
        return '<![CDATA[%s]]>' % s
    elif isinstance(s, (set, list, tuple)):
        new_s = []
        for item in s:
            new_s.append('<![CDATA[%s]]>' % item)
        return new_s

CONTROL_CHARS = ''


def remove_control_characters(s, ignore_chars=None):
    """
    去掉控制字符.
    参数:
    s->需要处理的字符串,需要str类型,unicode需要先编码.
    ignore_chars->需要忽略的控制字符.
    返回值->去掉控制字符后的字符串.
    """
    if ignore_chars is None:
        ignore_chars = '\r\n'
    global CONTROL_CHARS
    if len(CONTROL_CHARS) == 0:
        for i in range(127, 127+32, 1):
            c = chr(i)
            if c not in ignore_chars:
                CONTROL_CHARS += c
    return s.translate(str.maketrans(CONTROL_CHARS,
                                     ' ' * len(CONTROL_CHARS)))


class SolrXMLBuilder(object):
    """
    构建XML格式的Solr索引.
    """

    def __init__(self, dest_dir, operate='add', filename=None):
        """
        实例化XML构建器.
        参数:
        dest_dir->目标xml文件目录,如为空则输出到标准输出.
        operate->对Solr索引的操作:add,delete,update等,默认为:add.
        """
        self.operate = operate
        self.dest_dir = dest_dir
        self.filename = filename
        output_filename = ioutil.get_file_handler(dest_dir, operate,
                                                  filename)
        if output_filename:
            self.filehandle = open(output_filename, mode='w')
        else:
            self.filehandle = sys.stdout
        ioutil.dump('<update>\n', self.filehandle)

    def append(self, docs, **kwargs):
        """
        增加索引文档.
        参数:
        docs->需要索引的文档列表.如文档中solr_delete字段值为True或非空则删除该主
        键.
        **Kwargs->其它参数.
        """
        for doc in docs:
            if not doc:
                continue
            if doc.get('solr_delete'):
                if doc.get('id'):
                    ioutil.dump('<delete><id>%s</id></delete>\n' % doc['id'],
                                self.filehandle)
                continue
            xmlformatter = SolrXMLFormatter(doc)
            ioutil.dump('<%s>\n' % self.operate, self.filehandle)
            ioutil.dump(xmlformatter.format(), self.filehandle)
            ioutil.dump('</%s>\n' % self.operate, self.filehandle)

    def close(self):
        """
        XML构建器清理.
        """
        ioutil.dump('</update>\n', self.filehandle)
        ioutil.close_file_handler(self.filehandle)
