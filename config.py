'''
Created on 14.01.2018

@author: Stefan Rossmann
'''
import json
from ModbusClient import Parity, Stopbits
from warnings import catch_warnings
import threading
from collections import OrderedDict
import copy
import datetime
import ModbusClient, datalogger
import traceback
import  os
import logging


class Config(object):
    '''
    classdocs
    '''
    # Here will be the instance stored.
    __instance = None
    @staticmethod
    def getConfig():
        """ Static access method. """
        if Config.__instance == None:
            Config()
        return Config.__instance.config
    
    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance == None:
            Config()
        return Config.__instance 

    def __init__(self):
        """ Virtually private constructor. """
        if Config.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self
        self.eventcounter = 0
        self.lock = threading.RLock()
        self.pythonswversion = 'error'
        self.webserverversion = 'error'
        self.uploadalldata = False
        self.registerlogfilecounter = 0  # This is a Counter to store the Modbus data in the file (registerlogdataxxx.csv) (to consider to multiplier)
        self.mqttconnectionlost = False
        with open('configuration/config.json') as json_data:
            json_data = json_data.read()
            self.config = json.loads(json_data)
            self.read_version()


    def __geteventcounter(self):
        #if eventcounter = none -> Try to read file
        if self.__eventcounter is None:
            try:
                f = open('count.txt', 'r')
                self.__eventcounter = int(f.read())
                f.close()
            except Exception:
                self.__eventcounter = 0
        return self.__eventcounter

    def __seteventcounter(self, val):
        #Write the value to file
        try:
            self.__eventcounter = val
            f = open('count.txt', 'w+')
            f.write(str(self.__eventcounter))
            f.close()
        except Exception:
            pass

    eventcounter = property(__geteventcounter, __seteventcounter)

    def write_config(self):

        if 'readorder' in self.config:
            for ro in self.config['readorder']:
                del ro['value']
                del ro['oldvalue']

        with open('configuration/config.json', 'w') as f:
            json.dump(self.config, f, indent=2, sort_keys=False)
            f.write("\n")

    def WritePythonSWVersion(self):
        try:
            with open('version.json', 'w') as f:
                data = OrderedDict()
                data['pythonswversion'] = '{0:%Y-%m-%d}'.format(datetime.datetime.now())
                data['webserverversion'] = '{0:%Y-%m-%d}'.format(datetime.datetime.now())
                json.dump(data, f, indent=2)
                f.write("\n")
        except Exception:
            pass

    def read_version(self):
        logging.info('Webserver Read Version (ReadVersion()')
        try:
            with open('version.json') as json_data:
                d = json.load(json_data)
                self.pythonswversion = (d['pythonswversion'])
                self.webserverversion = (d['webserverversion'])

        except Exception:
            self.pythonswversion = 'error'
            self.webserverversion = 'error'

