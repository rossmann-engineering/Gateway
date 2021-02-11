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
        self.ReadInterval = 15
        self.BasicInterval = 900
        self.mqttbroker = list()
        self.HttpServer = 'http://127.0.0.1:8080'
        self.AppId = ''
        self.ProductId = ''
        self.DeviceId = ''
        self.Authorization = ''
        self.MultipleFactor = 1
        self.ModbusCommand = list()
        self.Devices = list()
        self.ReadOrders = list()
        self.lock = threading.RLock()
        self.atcommandlock = threading.RLock()
        self.configmodel = OrderedDict()        #This is the model for thewebserver configuration age
        self.settingsmodel = OrderedDict()  # This is the model for thewebserver configuration age
        self.connected = True;
        self.datetime_disconnected = datetime.datetime(1970, 1, 1)
        self.__eventcounter = None
        self.uploadalldata = False              #This a the Button from the Webserver to send all commands

        self.Pin = '1234'
        self.cloudconnectionlost = False
        self.mqttconnectionlost = False         #Pass the connection Status from mqtt to checkcloudconnectivity
        self.enable3g = 'enabled'


        self.pythonswversion = "1.0.0.0"
        self.webserverversion = "1.0.0.0"
        self.gwserialnumber = "1234"

        self.registerlogfilecounter = 0                      #This is a Counter to store the Modbus data in the file (registerlogdataxxx.csv) (to consider to multiplier)
        self.loggingmultiplier = 1

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

    
    def ReadConfig(self):

        with open('configuration/config.json') as json_data:
            json_data = json_data.read()
            d = json.loads(json_data, object_pairs_hook=OrderedDict)

            self.BasicInterval = (d['basicinterval'])
            self.ReadInterval = (d['readinterval'])
            if ('loggingmultiplier' in d):
                self.loggingmultiplier = (d['loggingmultiplier'])
            if ('mqttbroker' in d):
                self.mqttbroker = (d['mqttbroker'])
            if ('modbuscommand' in d):
                self.ModbusCommand = (d['modbuscommand'])
            if ('devices' in d):
                self.Devices = (d['devices'])
            if ('readorders' in d):
                self.ReadOrders = (d['readorders'])
            

            
    def StoreConfig(self, provisionig=False):
        with open('configuration/config.json') as json_data:
            json_data = json_data.read()
            data = json.loads(json_data, object_pairs_hook=OrderedDict)

        data['mqttbroker'] = (self.mqttbroker)
        data['basicinterval'] = (self.BasicInterval)
        data['readinterval'] = (self.ReadInterval)
        data['loggingmultiplier'] = (self.loggingmultiplier)
        data['modbuscommand'] = (self.ModbusCommand)
        data['devices'] = (self.Devices)
        data['readorders'] = copy.deepcopy(self.ReadOrders)
        for s in range(0, len( data['readorders'])):
            if 'nextwakeup' in data['readorders'][s]:
                del data['readorders'][s]['nextwakeup']
            if 'oldvalue' in data['readorders'][s]:
                del data['readorders'][s]['oldvalue']
            if 'patchValue' in data['readorders'][s]:
                del data['readorders'][s]['patchValue']
            if 'sendValue' in data['readorders'][s]:
                del data['readorders'][s]['sendValue']
            if 'value' in data['readorders'][s]:
                del data['readorders'][s]['value']
        with open('configuration/config.json', 'w') as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")


    def enablereadorder(self, registernumber, enable):
        """This Method searched the ReadOrders for the given Registernumber. This Registernumber will be
        activated if the Parameter "enable" is true, and disabled otherwise
        """
        #Search for the Registernumber
        for s in range(0, len(self.ReadOrders)):
            readorder = dict(self.ReadOrders[s])
            if (('register' in readorder) & ('dataarea' in readorder)):
                if (readorder['address'] == registernumber) and (readorder['dataarea'] == 3):
                    if enable:
                        readorder['active'] = True
                    else:
                        readorder['active'] = False

                self.ReadOrders[s] = readorder



    def ReadVersion(self):
        logging.info('Webserver Read Version (ReadVersion()')
        try:
            with open('version.json') as json_data:
                d = json.load(json_data)
                self.pythonswversion = (d['pythonswversion'])
                self.webserverversion = (d['webserverversion'])

        except Exception:
            self.pythonswversion = 'error'
            self.webserverversion = 'error'

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

