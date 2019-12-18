#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pymongo
if not sys.version > '3':
    import ConfigParser
else:
    import configparser as ConfigParser


class MongoWrapper:
    args = {'connect_timeout': 'connect_timeout'}

    def __init__(self, cfg_path):
        parser = ConfigParser.ConfigParser()
        parser.read(cfg_path)
        self.section = 'MONGOBD_HEALTH_RECORD'
        self.host = parser.get(self.section, 'HOST')
        self.port = int(parser.get(self.section, 'PORT'))
        self.user = parser.get(self.section, 'USER')
        self.passwd = parser.get(self.section, 'PASS')
        self.client = pymongo.MongoClient(host=self.host, port=self.port)
        self.db = self.client.health_record
        self.mono = self.db.authenticate(self.user, self.passwd)
        print('连接成功')

    def find_medical_order_data(self,orderIds):
        collection = self.db.MedicalOrder
        medical_record = collection.find({'orderId': {'$in': orderIds}})
        return medical_record

    def find_out_patient_data(self,evenIds):
        collection = self.db.OutPatient
        out_patient = collection.find({'medicalEventId': {'$in': evenIds}})
        return out_patient

    def close(self):
        self.client.close()
        self.client = None
