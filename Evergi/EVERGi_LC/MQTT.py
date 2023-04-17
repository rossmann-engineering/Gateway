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
import json
import ModbusClient
import ssl
import math
import opc_ua
import asyncio
import Evergi.EVERGi_LC
from Evergi.DT_EVERGi import DT_EVERGI


class Clients(object):
    """
    classdocs
    """
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Clients.__instance is None:
            Clients()
        return Clients.__instance

    def __init__(self):
        """ Virtually private constructor. """

        if Clients.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Clients.__instance = self
        logging.info('Thread MQTT started')
        self.clients = list()

        # Contains the client instance (instance) and the server id (serverid)
        self.client = dict()
        loopcounter = 0
        self.clients.append(dict())
        self.clients[loopcounter]['instance'] = mqtt.Client('client' + str(loopcounter))
        self.clients[loopcounter]['instance'].max_queued_messages_set(1)
        self.clients[loopcounter]['instance'].on_connect = self.on_connect
        self.clients[loopcounter]['instance'].on_disconnect = self.on_disconnect
        self.clients[loopcounter]['instance'].on_message = self.on_message
        self.clients[loopcounter]['instance'].on_publish = self.on_publish

        self.clients[loopcounter]['instance'].tls_set(certfile=None,
                       keyfile=None,
                       cert_reqs=ssl.CERT_NONE)


        username = "PLC-test"
        password = "eyJ0eXAiOiJKV1QiLCJhbGciOiJlZDI1NTE5LW5rZXkifQ.eyJqdGkiOiJSRjVMSExJNlBaQUdPVlY0NFZPQk5LM1RDUkozT0RNWVJDTjNNWkRDVTNHVEdWVzJIVkNBIiwiaWF0IjoxNjcxNDQxMDkxLCJpc3MiOiJBQ1VFS0o3V1RMNkZFNzJBVDNQUVMzUkpONDdORzZRMlFJVjNDRE5OQ0pUSEhNWDZPREZZQlBSNyIsIm5hbWUiOiJQTEMtdGVzdCIsInN1YiI6IlVCV09FR1ZJTU82V0NENFY0TFlIUldTREszV0xPQVpRVDVYVUxXQ0lCVEdURERBS0c2TFFHSVlMIiwibmF0cyI6eyJwdWIiOnsiYWxsb3ciOlsiRVZFUkdpRVZTYy5QTEMtdGVzdC5wbGMyc2MiLCJFVkVSR2lFVlNjLlBMQy10ZXN0LnBsYzJzYzJwbGMiXX0sInN1YiI6eyJhbGxvdyI6WyJFVkVSR2lFVlNjLlBMQy10ZXN0LnBsYzJzYzJwbGMiLCJFVkVSR2lFVlNjLlBMQy10ZXN0LnNjMnBsYyJdfSwic3VicyI6LTEsImRhdGEiOi0xLCJwYXlsb2FkIjotMSwiYmVhcmVyX3Rva2VuIjp0cnVlLCJ0eXBlIjoidXNlciIsInZlcnNpb24iOjJ9fQ.A-xts8060ftcFhWDv-TPoRb8R6lxvjFL9lE1K61jPAxyGe_7UjHp_e8bixILzoJ97fLNbVqG1SGmnKJW5GBzDA"
        self.clients[loopcounter]['instance'].username_pw_set(username, password)


        while not internet_on():
            logging.info('MQTT-Client - Wait for Internet connection available')
            time.sleep(2)
        try:


            self.clients[loopcounter]['instance'].connect('nats.evergi.be', 8883, 6000)
            logging.info('Initialize MQTT Client to Broker nats.evergi.be at Por 8883')
            time.sleep(2)

            self.clients[loopcounter]['instance'].loop_start()
            time.sleep(5)

            self.clients[loopcounter]['mid'] = 0

            logging.info('Added MQTT Client at initialization to List')
        except:
            logging.error('Exception connecting to MQTT-Broker: ' + str(traceback.format_exc()))

    def on_connect(self, client, userdata, flags, rc):
        """ connect to mqtt """
        client.subscribe('EVERGiEVSc/PLC-test/sc2plc')
        #client.subscribe('v1/devices/me/attributes')
        pass

    def on_disconnect(self, client, userdata, rc):
        """ disconnect from mqtt """
        logging.info('Disconnected from MQTT-Broker')

        pass

    def on_message(self, client, userdata, msg):
        """ receive message from mqtt Broker """

        logging.info('Message Received from MQTT Broker ' + str(msg.payload))


    def on_publish(self, client, userdata, mid):
        """ on prublish callback funtion  """

        # DataLogger.logData('Publish successfully acknowledged mid: ' + str(mid))
        self.client['mid'] = mid


def internet_on():
    """
    Ping google.com to verify if the internet connection is available
    :return: true or false
    """
    url = 'http://www.google.com/'
    timeout = 2

    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False


def validate_json(message):
    """
    Validate if the message is a JSON format (Function JSON.loads throws an exception if the message is no valid json)
    :param message: Message to validate
    :return: True if valid JSON Message
    """
    try:
        jsonmessage = json.loads(message)
    except ValueError as e:
        return False

    return True


def publish_message(serverid, topic, payload):
    """
    publish message to MQTT-Broker
    :param serverid: Server ID the Message refers to
    :param topic: Topic
    :param payload: message publish to topic
    """

    try:

        logging.info('Store Message to Database, ServerID ' + str(serverid) + ' Message: ' + payload)
        if len(payload) > 5:
            dt_evergi = DT_EVERGI.getInstance()
            db_conn = database.connect("eh.db", '')
            database.add_message_queue(db_conn, datetime.datetime.now(), serverid, topic, payload)
    except:
        logging.error('Exception storing data in Database: ' + str(traceback.format_exc()))

    try:
        # check message queue for entries
        db_conn = database.connect("eh.db", '')
        datatosend = database.get_message_queue(db_conn, serverid)
        if len(datatosend) > 5:
            for t in Clients.getInstance().clients:
                logging.info('Message Queue exceeded max. size, trying to reconnect')
                client = dict(t)
                client['instance'].reconnect()
        if datatosend:
            cancelSend = False  # Cancel send messages if one Message failed
            for element in datatosend:
                if cancelSend:
                    break
                if not internet_on():
                    logging.info('MQTT-Client - Wait for Internet connection available')
                    cfg.Config.getInstance().mqttconnectionlost = True
                    break
                logging.info('Message from Queue restored ' + str(element))
                for t in Clients.getInstance().clients:
                    client = dict(t)

                    if not validate_json(element['payload']):
                        logging.info('Message is no valid JSON (deleted): ' + str(element['payload']))
                        database.delete_message_queue(db_conn, element['rowid'])
                        break
                    response = client['instance'].publish(element['topic'], element['payload'], qos=1)
                    logging.info('Message Published to MQTT Broker ' + str(element['payload']) + " topic: " + str(
                        element['topic']) + " Server-Response: " + str(response.rc) + "mid: " + str(response.mid))
                    time.sleep(1)
                    if response.rc == 0:
                        for x in range(6):
                            if response.is_published():
                                logging.info('Message Deleted from queue ' + str(
                                    element['payload']) + " topic: " + str(
                                    element['topic']) + " Server-Response: " + str(response.rc) + "mid: " + str(
                                    response.mid))

                                datalogger.logMQTTRegisterData(
                                    'MQTT send Payload to Serverid ' + str(serverid) + " Topic: " + str(
                                        element['topic']) + " Payload: " + str(element['payload']))
                                database.delete_message_queue(db_conn, element['rowid'])
                                break
                            else:
                                time.sleep(2)  # was 0.5 26.02.2020
                        if x >= 5:
                            cancelSend = True
                            break
                        pass
                    else:
                        cancelSend = True
                        break


    except:
        logging.error('Exception Restoring MQTT Messages  ' + str(traceback.format_exc()))


def send_mqtt_data():
    """
    send mqtt data
    """
    logging.info('Sending MQTT-Data...')
    dt_evergi = DT_EVERGI.getInstance()
    db_conn = database.connect("eh.db", '')


    payload = '{"Time":' + str(int(datetime_to_unix_timestamp(datetime.datetime.now())/1000))

    #Power and Energy for grid values
    power = 0
    energy = 0
    for device in dt_evergi.DT_EVERGi_arrProduction_50:
        power = device.PV_rPower
        energy = 0

    payload = payload + ', "Grid":{"Power":' + str(power) + ', "Energy": ' + str(energy) + '},'

    #Add Production (Energymeters) to MQTT Message (We take the Transport ID as nr
    payload = payload + '"Production":['
    for device in dt_evergi.DT_EVERGi_arrProduction_50:
        power = device.PV_rPower
        payload = payload + ('{"nr":'+str(device.Conf_uiNr)+', "Power": '+str(power)+'},')
    # Remove last comma
    payload = payload[:-1]
    payload = payload + '],'


    # Nodes
    payload = payload + '"Node":['

    for device in dt_evergi.DT_EVERGi_arrProduction_50:
        power = device.PV_rPower
        current = [0, 0, 0]
        current[0] = device.PV_rCurrent1
        current[1] = device.PV_rCurrent2
        current[2] = device.PV_rCurrent3
        payload = payload + '{"nr":' + str(device.Conf_uiNr) + ', "Power": ' + str(power) + ', "Current": ['+ str(current[0]) +','+ str(current[1]) +','+ str(current[2]) +']},'
    # Remove last comma
    if payload[-1] == ',':
        payload = payload[:-1]
    payload = payload + '],'

    #payload = payload + '"{"nr":1, "Power": 6221, "Current": [9016,9016,9016]}'
    #payload = payload + ', {"nr":2, "Power": 4321, "Current": [6262,6262,6262]}],'

    # EVChargers:
    payload = payload + '"EVChargers":['
    for device in dt_evergi.DT_EVERGi_arrEVSE_100:

        soc1 = 0
        status1 = 0
        power1 = 0
        dc_voltage1 = 0
        dc_current1 = 0
        power_max1 = 999
        energy1= 0
        current1 = [0, 0, 0]
        soc2 = 0
        status2 = 0
        power2 = 0
        dc_voltage2 = 0
        dc_current2 = 0
        power_max2 = 999
        energy2 = 0
        current2 = [0, 0, 0]
        nr1 = 1
        nr2 = 2

        payload = payload + ('{"nr":' + str(nr1) + ', "Status": ' + str(status1) + ', "Power": ' + str(power1) + ', "Power_max": '+ str(power_max1) +', "Energy": ' + str(energy1) + ', "Current": ['+ str(current1[0]) +',' + str(current1[1]) + ','+ str(current1[2]) +'], "SOC": ' + str(soc1) + '},')
        payload = payload + ('{"nr":' + str(nr2) + ', "Status": ' + str(status2) + ', "Power": ' + str(power2) + ', "Power_max": '+ str(power_max2) +', "Energy": ' + str(energy2) + ', "Current": ['+ str(current2[0]) +',' + str(current2[1]) + ','+ str(current2[2]) +'], "SOC": ' + str(soc2) + '},')




        #payload = payload + '{"nr":1, "Status": 2,"Power": 6557, "Power_max": 8000, "Energy": 15665, "Current": [9503,9503,9503]},'
        #payload = payload + '{"nr":1, "Status": 2,"Power": 6557, "Power_max": 8000, "Energy": 15665, "Current": [9503,9503,9503], "SOC": 5423}'



    # Remove last comma
    if payload[-1] == ',':
        payload = payload[:-1]
    payload = payload + ']}'



    logging.info('Sending MQTT-Data to serverid' + str(1))
    publish_message(1, 'EVERGiEVSc/PLC-test/plc2sc', payload)


def datetime_to_unix_timestamp(dt):
    """
    shows datetime in unix timestamp
    :return: time in unix timestamp (in milliseconds sine 1st January 1970)
    """
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds() * 1000

def send_mqtt():
    while 1:
        send_mqtt_data()
        time.sleep(30)