#!/usr/bin/python
#encoding=utf-8
 


import sys
import os
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../common'))

from client.agada_client import AgadaClient


input_file = 'traindata.txt'
max_number = sys.maxint
host_port_b = 'localhost:7206'

def run_test():
    tc_b = AgadaClient(host_port_b)
    input = open(input_file, 'r')
    count = 0
    mis_count = 0 
    for line in input:
        count = count + 1
        if count > max_number:
            break
        if count % 100 == 0:
            print '%s finished!' % count
            print '%s mis_count' % mis_count
        line = str(line.strip())
        line_items = line.split('\t')
        if len(line_items) < 4:
            continue
        dept = line_items[3]
        line = line.decode('utf-8')
        classify_result_b = None
        try:
            classify_result_b = tc_b.query(line)
        except:
            classify_result2 = None
            continue
        if classify_result_b:
            data = classify_result_b.get('data')
            department_b = ''
            if data and data[0]:
                department_b = data[0].get('dept')
                b = str(department_b)
            if dept != b:
                mis_count += 1
                format = '%s-%s'
                buf = format % (line,department_b)
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
