#!/usr/bin/env python
import time

import paho.mqtt.client as mqtt
import datalogger
import config as cfg
import requests
import database
import traceback
import datetime
import logging


class Clients(object):
    '''
    classdocs
    '''
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Clients.__instance == None:
            Clients()
        return Clients.__instance

    def __init__(self):
        """ Virtually private constructor. """

        if Clients.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Clients.__instance = self
        logging.info('Thread MQTT started')
        config = cfg.Config.getInstance()
        config.mqttconnectionlost = True
        self.clients = list()


        # Contains the client instance (instance) and the server id (serverid)
        self.client = dict()
        loopcounter = 0
        for t in config.mqttbroker:
            self.clients.append(dict())
            mqttbroker = dict(t)
            self.clients[loopcounter]['instance'] = mqtt.Client('client' + str(loopcounter))
            self.clients[loopcounter]['instance'].max_queued_messages_set(1)
            self.clients[loopcounter]['instance'].on_connect = self.on_connect
            self.clients[loopcounter]['instance'].on_disconnect = self.on_disconnect
            self.clients[loopcounter]['instance'].on_publish = self.on_publish
            #self.clients[loopcounter]['instance'].username_pw_set(mqttbroker['accesstoken'], '')
            while (not internet_on()):
                config.mqttconnectionlost = True
                datalogger.logData('MQTT-Client - Wait for Internet connection available')
                time.sleep(2)
            try:
                if 'username' in mqttbroker and 'password' in mqttbroker:
                    self.clients[loopcounter]['instance'].username_pw_set(mqttbroker['username'], mqttbroker['password'])
                self.clients[loopcounter]['instance'].connect(mqttbroker['address'], int(mqttbroker['port']), 6000)
                logging.info('Initialize MQTT Client to Broker ' + str(mqttbroker['address'])+', Port: ' +  str(mqttbroker['port']))
                time.sleep(2)

                self.clients[loopcounter]['instance'].loop_start()
                time.sleep(5)

                self.clients[loopcounter]['serverid'] = mqttbroker['serverid']
                self.clients[loopcounter]['mid'] = 0

                logging.info('Added MQTT Client at initialization to List')
                db_conn = database.connect("eh.db")
                database.create_tables(db_conn)
                loopcounter = loopcounter + 1
            except:
                logging.error('Exception connecting to MQTT-Broker: ' + str(traceback.format_exc()))



    def on_connect(self, client, userdata, flags, rc):
        cfg.mqttconnectionlost = False

        #client.subscribe('v1/devices/me/telemetry/#')


        #DataLogger.logData('Connected to MQTT-Broker with Status code ' + str(rc))
        pass
    def on_disconnect(self, client, userdata, flags, rc):
        logging.info('Disconnected from MQTT-Broker')

        pass



    def on_publish(self, client, userdata, mid):

        #DataLogger.logData('Publish successfully acknowledged mid: ' + str(mid))
        self.client['mid'] = mid


def internet_on():
    url = 'http://www.google.com/'
    timeout = 2

    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False



def publish_message(serverid, topic, payload):
    config = cfg.Config.getInstance()
    try:

        logging.info('Store Message to Database, ServerID ' + str(serverid) + ' Message: ' + payload)
        if (len(payload) > 5):
            db_conn = database.connect("eh.db")
            database.add_message_queue(db_conn, datetime.datetime.now(), serverid, topic, payload)
    except:
        logging.error('Exception storing data in Database: ' + str(traceback.format_exc()))


    try:
        # check message queue for entries
        db_conn = database.connect("eh.db")
        datatosend = database.get_message_queue(db_conn, serverid)
        if (len(datatosend) > 5):
            for t in Clients.getInstance().clients:
                datalogger.logData('Message Queue exceeded max. size, trying to reconnect')
                #config.mqttconnectionlost = True
                client = dict(t)
                client['instance'].reconnect()
        if datatosend:
            cancelSend= False      #Cancel send messages if one Message failed
            for element in datatosend:
                if cancelSend:
                    break
                if not internet_on():
                    datalogger.logData('MQTT-Client - Wait for Internet connection available')
                    config.mqttconnectionlost = True
                    break
                logging.info('Message from Queue restored ' + str(element))

                for t in Clients.getInstance().clients:
                    client = dict(t)
                    if (client['serverid'] == serverid):

                        response = client['instance'].publish(element['topic'], element['payload'],  qos=1)
                        logging.info('Message Published to MQTT Broker ' + str(element['payload']) + " topic: " + str(element['topic']) + " Server-Response: " + str(response.rc) + "mid: " + str(response.mid))
                        time.sleep(1)
                        if (response.rc == 0):
                            for x in range(6):
                                if  response.is_published():
                                    datalogger.logData('Message Deleted from queue ' + str(
                                        element['payload']) + " topic: " + str(
                                        element['topic']) + " Server-Response: " + str(response.rc) + "mid: " + str(
                                        response.mid))

                                    datalogger.logMQTTRegisterData('MQTT send Payload to Serverid ' + str(serverid) + " Topic: " + str(element['topic']) + " Payload: " + str(element['payload']))
                                    config.mqttconnectionlost = False
                                    database.delete_message_queue(db_conn, element['rowid'])
                                    break
                                else:
                                    time.sleep(2)   #was 0.5 26.02.2020
                            if (x >= 5):
                                cancelSend = True
                                break


                            pass

                        else:
                            cancelSend = True
                            break


    except:
        datalogger.logData('Exception Restoring MQTT Messages  ' + str(traceback.format_exc()))

def send_mqtt_data(disconnected = False, connected = False):
    config = cfg.Config.getInstance()
    logging.info('Sending MQTT-Data...')
    for s in config.mqttbroker:
        for u in config.Devices:
            mqttbroker = dict(s)
            logging.info('Sending MQTT-Data to serverid' + str(mqttbroker['serverid']))
            payload = '{"ts":' + str(int(datetime_to_unix_timestamp(datetime.datetime.now())))
            if 'identifier' in u:
                payload = payload + ',' + ' "identifier": "' + u['identifier'] + '"'
            if 'uid' in u:
                payload = payload + ',' + ' "uid": : "' + u['uid'] + '"'
            else:
                payload = payload + ',' + ' "type": "' + 'Modbus' + '"'
            if 'ipaddress' in u:
                payload = payload + ',' + ' "localaddress": "' + u['ipaddress'] + '"'
            if 'port' in u:
                payload = payload + ',' + ' "localport": ' + str(u['port'])
            if 'unitidentifier' in u:
                payload = payload + ',' + ' "slaveid": ' + str(u['unitidentifier'])

            payload = payload + ', "sampledata":{'


            # This is the Message we send if the Modbus Device is not connected
            if (disconnected):
                payload = payload + '"Modbus Connected":0'

            # This is the Message we send if the Modbus Device is connected
            if (connected):
                payload = payload + '"Modbus Connected":1'

            if (not connected and not disconnected):
                config.lock.acquire()
                #Send Readorders
                try:
                    read_order_count = 0
                    for t in config.ReadOrders:
                        readOrder = dict(t)
                        active = (readOrder['active'] == True)
                        if 'serverid' in readOrder:
                            serverids = readOrder['serverid']
                        else:
                            serverids = [1];
                        if (('sendValue' in readOrder) and (mqttbroker['serverid'] in serverids)):
                            sendValue = (readOrder['sendValue'] == True)
                        else:
                            sendValue = False

                        if active & sendValue & (readOrder['transportid'] == u['transportid']):
                            if read_order_count > 0:
                                payload = payload + ','
                            payload = payload + '"' + str(readOrder['name']) + '":' + str(readOrder['value'])
                            read_order_count = read_order_count + 1
                except Exception:
                    logging.error('Exception send_mqtt_data to MQTT-Broker: ' + str(traceback.format_exc()))
                finally:
                    config.lock.release()

            payload = payload + '}}'
            if (read_order_count > 0):
                publish_message(mqttbroker['serverid'], mqttbroker['publishtopic'], payload)


def datetime_to_unix_timestamp(dt):
    return (dt - datetime.datetime(1970,1,1)).total_seconds() * 1000


if __name__ == "__main__":
    #config = Config.Config.getInstance()
    #config.ReadConfig()
    client = mqtt.Client('client')
    client.connect('mqtt-dashboard.com', 1883, 6000)
    #send_mqtt_data()
    #dt = datetime.datetime(2016,1,1,12,0,0)
    #print (int(datetime_to_unix_timestamp(dt)))
    #execute_write_order('{"method":"Non-Saving Load","params":{"Non-Saving Load":50}}')