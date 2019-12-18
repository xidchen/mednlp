#!/usr/bin/python
#encoding=utf-8

import sys
import os
from optparse import OptionParser

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../common'))

import client.tmserver_client
from client.agada_client import AgadaClient


input_file = 'quanke_0612.txt'
max_number = sys.maxint
#host_port_a = 'localhost:7200'
#host_port_b = 'localhost:7206'

def run_test():
    tc_a = client.tmserver_client.TmserverClient(host_port_a)
    tc_b = AgadaClient()
    input = open(input_file, 'r')
    count = 0
    for line in input:
        count = count + 1
        if count > max_number:
            break
        line = line.strip()
        line = line.decode('utf-8')
        classify_result_a = None
        classify_result_b = None
        try:
            classify_result_a = tc_a.query(line)
            classify_result_b = tc_b.query(line)
        except:
            classify_result = None
            classify_result2 = None
            continue
        if classify_result_a or classify_result_b:
            department_a = classify_result_a.get('bestc') if classify_result_a else None
            data = classify_result_b.get('data')
            if data and data[0]:
                department_b = data[0].get('dept')
            if department_a != department_b:
                format = '%s-%s-%s'
                buf = format % (line,department_a,department_b)
                print buf.encode('utf-8')




if __name__=="__main__":
    command = """\npython %s [-c config_file -a host_a -b host_b -n number]""" %sys.argv[0]

    parser = OptionParser(usage=command)
    parser.add_option("-c", "--config", dest="config", help="the config file", metavar="FILE")
    parser.add_option("-a", "--host-a", dest="hosta", help="the a host of tmserver(ip:port)", metavar="String")
    parser.add_option("-b", "--host-b", dest="hostb", help="the b host of tmserver(ip:port)", metavar="String")
    parser.add_option("-n", "--number", dest="number", help="the max limit of record", metavar="INT")
    (options, args) = parser.parse_args()
    
    if options.config:
        cfg_path = options.config
    if options.hosta:
        host_port_a = options.hosta
    if options.hostb:
        host_port_b = options.hostb
    if options.number:
        max_number = int(options.number)
    run_test()            
