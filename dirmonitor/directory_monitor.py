#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
directory_monitor.py -- the dir monitor

Author: maogy <maogy@guahao.com>
Create on 2019-03-05 Tuesday.
"""


import pyinotify
import sys
import os
import logging
import fcntl
import signal
import time
import traceback
import subprocess
from optparse import OptionParser 
from daemon import Daemon
from log import Log


logger = None
class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, corename, solrpath, sleep, monitor):
        self.sleep = sleep
        self.monitor = monitor
        self.work_dic = {}
        post_file = os.path.join(solrpath, 'mednlp/kg/index_task/post.py')
        self.post_sh = 'python %s %s' % (post_file, corename)
        logger.info('post:'+self.post_sh)
        logger.info("starting monitor.....")
    def process_IN_CREATE(self, event):
        if event.name in self.work_dic:
            return
        self.work_dic[event.name] = 1

    def process_IN_CLOSE_WRITE(self, event):
        if event.name in self.work_dic and self.work_dic[event.name] == 1:
            self.work_dic[event.name] = 2
            logger.info("new file found: %s" % os.path.join(event.path, event.name))
            if self.monitor == None or event.name.endswith(self.monitor.split('.')[1]):
                logger.info("handle file %s" % os.path.join(event.path, event.name))
                try:
                    logger.info(self.post_sh + " " + os.path.join(event.path, event.name))
                    result = subprocess.Popen(self.post_sh + " " + os.path.join(event.path, event.name), 
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    logger.info("stdout output: %s", result.stdout.read())
                    logger.info("stderr output: %s", result.stderr.read())
                except Exception as e:
                    logger.info("handle file failed:%s" % traceback.format_exc())
                try:
                    os.remove(os.path.join(event.path, event.name))
                except Exception as e:
                    logger.info("handle file failed:%s" % traceback.format_exc())

                del self.work_dic[event.name]
                if self.sleep != None:
                    time.sleep(int(self.sleep))       

def RunMonitor(directory, corename, solrpath, sleep, monitor):
    if os.path.isfile(directory):
        print("monitored directory is required")
        sys.exit(1) 

    if not os.path.exists(directory):
        print("directory:%s not exist" % directory)
        sys.exit(1)

    wm = pyinotify.WatchManager()
    wm.add_watch(directory, pyinotify.ALL_EVENTS, rec = True)

    notifier = pyinotify.Notifier(wm, EventHandler(corename, solrpath, sleep, monitor))
    notifier.loop()

class MyDaemon(Daemon):
    def __init__(self, pidfile, directory, corename, solrpath, sleep, monitor):
        Daemon.__init__(self, pidfile)
        self.directory = directory
        self.corename = corename
        self.sleep = sleep
        self.monitor = monitor
        self.solrpath = solrpath

    def run(self):
        RunMonitor(self.directory, self.corename, self.solrpath, self.sleep, self.monitor)

def StopDaemon(signum, e):
        logger.info("received signal: %d at %s" %(signum, e))
        sys.exit(1)

def convert_path(path):
    return path.replace('/', '_')

if __name__ == "__main__":
    command = "python %s -r directory -f process_file [-s sleep] [-m monitor] [-d]" %sys.argv[0]
    parser = OptionParser(usage=command)

    parser.add_option("-r", "--directory", dest="directory", help="the monitor directory path", metavar="DIR")
    parser.add_option("-c", "--core", dest="corename", help="the solr core name to post to", metavar="STRING")
    parser.add_option("-s", "--sleep", dest="sleep", help="the time of sleep after excute the another program", metavar="INT")
    parser.add_option("-m", "--monitor", dest="monitor", help="the special file want to monitor", metavar="STRING")
    parser.add_option("-d", "--daemon", dest="daemon", action="store_true", help="run in daemon")
    # parser.add_option("-p", "--path", dest="solrpath", help="the solr path", metavar="STRING")
    (options, args) = parser.parse_args()
    
    # #give the default solr deploy address
    # if not options.solrpath or options.solrpath == '':
    #     options.solrpath = '/lxops/glsearch_solr'
    #run the daemon process
    if options.corename and options.directory:
        directory_path = convert_path(options.directory)
        base_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),'../')
        log_dir = os.path.join(base_dir, 'logs/dirmonitor_%s.log')
        print(log_dir)
        logfile = log_dir % options.corename
        logger = Log(logfile, 'dirmonitor').getLogger()
        if options.daemon:
            daemon = MyDaemon("/tmp/dirmonitor.%s.pid" % directory_path,
                              os.path.realpath(options.directory),
                              options.corename, base_dir, options.sleep,
                              options.monitor)
            signal.signal(signal.SIGTERM, StopDaemon)
            daemon.start()
        else:
            RunMonitor(options.directory, options.corename, base_dir, options.sleep, options.monitor) 
    else:
        parser.print_help()
        sys.exit(0)
