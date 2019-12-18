#!/usr/bin/python
#coding=utf-8

import os
import logging
import logging.handlers
import stat

class Log:
    def __init__(self, log_file, name):
        if os.path.exists(log_file):
            log_handler = logging.FileHandler(log_file)
        else:
            log_handler = logging.FileHandler(log_file)
            os.chmod(log_file, stat.S_IRWXU)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        log_handler.setFormatter(formatter)

        self.logger = logging.getLogger(name)
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.INFO)
       
    def getLogger(self):
        return self.logger 




class GLLog:
    def __init__(self, name, log_file=None, show_thread=False ):
        base_dir = os.path.dirname(__file__) + '/../../'
        if not log_file:
            log_file = base_dir + 'logs/' + name + '.log'
        self.logger = logging.getLogger(name)  
        self.logger.setLevel(logging.INFO)
        # 输出到控制台
        ch = logging.StreamHandler()
        # 输出到文件
        fh = logging.handlers.TimedRotatingFileHandler(log_file, 'midnight', 1)
        time_name_str = '%(asctime)s %(name)s' 
        level_message_str = '%(levelname)s:%(message)s'
        threadName_str = ' '
        if show_thread:
            threadName_str = ' %(threadName)s '
        format_str = time_name_str + threadName_str + level_message_str
        formatter = logging.Formatter(format_str)
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
        
    def getLogger(self):
        return self.logger 
