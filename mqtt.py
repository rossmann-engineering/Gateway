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
        config = cfg.Config.getConfig()
        cfg.Config.getInstance().mqttconnectionlost = True
        self.clients = list()

        # Contains the client instance (instance) and the server id (serverid)
        self.client = dict()
        loopcounter = 0
        for t in config['mqttbroker']:
            self.clients.append(dict())
            mqttbroker = dict(t)
            self.clients[loopcounter]['instance'] = mqtt.Client('client' + str(loopcounter))
            self.clients[loopcounter]['instance'].max_queued_messages_set(1)
            self.clients[loopcounter]['instance'].on_connect = self.on_connect
            self.clients[loopcounter]['instance'].on_disconnect = self.on_disconnect
            self.clients[loopcounter]['instance'].on_message = self.on_message
            self.clients[loopcounter]['instance'].on_publish = self.on_publish
            self.clients[loopcounter]['instance'].username_pw_set(mqttbroker['accesstoken'], '')
            while not internet_on():
                cfg.Config.getInstance().mqttconnectionlost = True
                logging.info('MQTT-Client - Wait for Internet connection available')
                time.sleep(2)
            try:
                if 'username' in mqttbroker and 'password' in mqttbroker:
                    self.clients[loopcounter]['instance'].username_pw_set(mqttbroker['username'],
                                                                          mqttbroker['password'])
                self.clients[loopcounter]['instance'].connect(mqttbroker['address'], int(mqttbroker['port']), 6000)
                logging.info('Initialize MQTT Client to Broker ' + str(mqttbroker['address']) + ', Port: ' + str(
                    mqttbroker['port']))
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
        """ connect to mqtt """
        cfg.mqttconnectionlost = False

        client.subscribe('v1/devices/me/rpc/request/+')
        client.subscribe('v1/devices/me/attributes')
        pass

    def on_disconnect(self, client, userdata, rc):
        """ disconnect from mqtt """
        logging.info('Disconnected from MQTT-Broker')

        pass

    def on_message(self, client, userdata, msg):
        """ receive message from mqtt gurke """

        logging.info('Message Received from MQTT Broker ' + str(msg.payload))
        requestId = msg.topic.replace('v1/devices/me/rpc/request/', '')
        is_rpc = False
        try:
            msg.payload, is_rpc = execute_rpc(msg.payload)
        except Exception:
            logging.error('Exception could not process RPC: ' + str(traceback.format_exc()))
        client.publish('v1/devices/me/rpc/response/' + requestId, msg.payload)
        if not is_rpc:
            execute_write_order(msg.payload)

    def on_publish(self, client, userdata, mid):
        """ publish to mqtt gurke """

        # DataLogger.logData('Publish successfully acknowledged mid: ' + str(mid))
        self.client['mid'] = mid


def internet_on():
    """
    connect to internet gurke
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
    publish message to gurke
    :param serverid: Server ID the Message refers to
    :param topic: topic gurke
    :param payload: message publish to topic
    """
    config = cfg.Config.getConfig()
    try:

        logging.info('Store Message to Database, ServerID ' + str(serverid) + ' Message: ' + payload)
        if len(payload) > 5:
            db_conn = database.connect("eh.db")
            database.add_message_queue(db_conn, datetime.datetime.now(), serverid, topic, payload)
            cfg.Config.getInstance().eventcounter = cfg.Config.getInstance().eventcounter + 1
    except:
        logging.error('Exception storing data in Database: ' + str(traceback.format_exc()))

    try:
        # check message queue for entries
        db_conn = database.connect("eh.db")
        datatosend = database.get_message_queue(db_conn, serverid)
        if len(datatosend) > 5:
            for t in Clients.getInstance().clients:
                logging.info('Message Queue exceeded max. size, trying to reconnect')
                # config.mqttconnectionlost = True
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
                    if not 'serverid' in client:  # That can happen if the client is not yet initialized
                        break
                    if client['serverid'] == serverid:
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
                                    cfg.Config.getInstance().mqttconnectionlost = False
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


def execute_rpc(payload):
    """
    Payload which includes a RPC: {"method":"getValueTemperature"}
    :param payload: Payload received from topic v1/devices/me/rpc/request/{{requestid}}
    :return:Answer to send
    """
    config = cfg.Config.getConfig()
    response = payload
    is_rpc = False
    payload_dict = json.loads(payload)
    if 'rpcrequests' in config:
        for rpcrequest in config['rpcrequests']:
            if payload_dict.get('method', '') == rpcrequest['name']:
                is_rpc = True
                # look for a static value in the RPC definition
                if 'staticvalue' in rpcrequest:
                    response = rpcrequest['staticvalue']
                else:
                    # Look for a ReadOrder to return
                    for readorder in config['readorders']:
                        if rpcrequest.get('serverid', 1) in readorder['serverid']:
                            if readorder['name'] == rpcrequest['readorder']:
                                multiplefactor = rpcrequest.get('multiplefactor', 1)
                                if multiplefactor == 0:
                                    multiplefactor = 1
                                response = readorder.get('value', 0) / multiplefactor
                                break

        if is_rpc:
            logging.info('Returnvalue to RPC: {0}'.format(response))
    return response, is_rpc


def send_attributes():
    """ send attributes gurke """
    config = cfg.Config.getConfig()
    logging.info('Sending MQTT-Attributed...')
    for s in config['mqttbroker']:
        for u in config['devices']:
            mqttbroker = dict(s)
            logging.info('Sending MQTT-Attributes to serverid' + str(mqttbroker['serverid']))
            payload = '{'

            cfg.Config.getInstance().lock.acquire()
            # Send Readorders
            try:
                read_order_count = 0
                for t in config['attributes']:
                    attributes = dict(t)
                    active = (attributes.get('active', True) == True)
                    if 'serverid' in attributes:
                        serverids = attributes['serverid']
                    else:
                        serverids = [1]
                    if mqttbroker['serverid'] in serverids:
                        sendValue = True
                    else:
                        sendValue = False

                    if active & sendValue:
                        if read_order_count > 0:
                            payload = payload + ','
                        payload = payload + '"' + str(attributes['name']) + '":' + str(attributes['value'])
                        read_order_count = read_order_count + 1
            except Exception:
                logging.error('Exception send_mqtt_attributes to MQTT-Broker: ' + str(traceback.format_exc()))
            finally:
                cfg.Config.getInstance().lock.release()

            payload = payload + '}'
            if (read_order_count > 0) and 'attributetopic' in mqttbroker:
                publish_message(mqttbroker['serverid'], mqttbroker['attributetopic'], payload)


def send_mqtt_data(disconnected=False, connected=False):
    """
    send mqtt data
    :param disconnected: if true then disconnected from mqtt client
    :param connected: if true then connected to mqtt client
    """
    config = cfg.Config.getConfig()
    logging.info('Sending MQTT-Data...')
    for s in config['mqttbroker']:
        for u in config['devices']:
            mqttbroker = dict(s)
            payload = '{"ts":' + str(int(datetime_to_unix_timestamp(datetime.datetime.now())))

            payload = payload + ', "values":{'

            # This is the Message we send if the Modbus Device is not connected
            if disconnected:
                payload = payload + '"Modbus Connected":0'

            # This is the Message we send if the Modbus Device is connected
            if connected:
                payload = payload + '"Modbus Connected":1'

            if not connected and not disconnected:
                cfg.Config.getInstance().lock.acquire()
                # Send Readorders
                try:
                    read_order_count = 0
                    for t in config['readorders']:
                        readOrder = dict(t)
                        active = (readOrder['active'] == True)
                        if 'serverid' in readOrder:
                            serverids = readOrder['serverid']
                        else:
                            serverids = [1];
                        if ('sendValue' in readOrder) and (mqttbroker['serverid'] in serverids):
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
                    cfg.Config.getInstance().lock.release()

            payload = payload + '}}'
            if read_order_count > 0:
                logging.info('Sending MQTT-Data to serverid' + str(mqttbroker['serverid']))
                publish_message(mqttbroker['serverid'], mqttbroker['publishtopic'], payload)


def execute_write_order(payload):
    """
    Example Message:{"method":"setValue","params":true}
    or {"method":"toggle3","params":{"toggle3":1}
    :param payload: message received from MQTT-Broker
    """
    d = json.loads(payload)
    if 'method' not in d or 'params' not in d:
        return
    method = d['method']
    params = d['params']
    config = cfg.Config.getConfig()
    # Search for matching RadOrder
    cfg.Config.getInstance().lock.acquire()
    try:
        if (not isinstance(params,
                           dict)):  # Convert "params" to dictionary if Message Format: {"method":"setValue","params":true}
            converted_dict = dict()
            converted_dict[method] = params
            params = converted_dict
        for param in params:
            dict_key = param
            dict_value = params[param]
            for t in config['readorders']:
                readOrder = dict(t)
                if ('dataarea' in readOrder) & ('address' in readOrder):
                    if (readOrder['name'] == str(dict_key)) and (readOrder['dataarea'] == "Holding Register"):
                        if 'serialPort' in config['devices'][0]:
                            modbusClient = ModbusClient.ModbusClient(str(config.Devices[0]['serialPort']))
                        # This is Modbus-TCP
                        if 'ipaddress' in config['devices'][0]:
                            if not ('port' in config['devices'][0]):
                                config['devices'][0]['port'] = 502
                            modbusClient = ModbusClient.ModbusClient(str(config['devices'][0]['ipaddress']),
                                                                     int(config['devices'][0]['port']))
                        # if not isinstance(params, dict):      # Message Format: {"method":"setValue","params":true}
                        #    value = int(params)               # commented, because Message Format is converted at beginning
                        # else:                                 # Message Format: {"method":"toggle3","params":{"toggle3":1}
                        value = int(dict_value)
                        if 'staticvalue' in readOrder:
                            value = readOrder['staticvalue']
                        valueChanged = False
                        if 'value' in readOrder:
                            valueChanged = True  # (value != readOrder['value'])
                        else:
                            valueChanged = True
                        if valueChanged:
                            # This is Modbus-RTU
                            if 'serialPort' in config['devices'][0]:
                                modbusClient.Parity = (config['devices'][0]['parity'])
                                modbusClient.Baudrate = (config['devices'][0]['baudrate'])
                                modbusClient.Stopbits = (config['devices'][0]['stopbits'])
                            if 'ipaddress' in config['devices'][0]:
                                if not ('port' in config['devices'][0]):
                                    config['devices']['port'] = 502
                                modbusClient = ModbusClient.ModbusClient(
                                    str(config['devices'][0]['ipaddress']),
                                    int(config['devices'][0]['port']))
                            if 'unitidentifier' in config['devices'][0]:
                                modbusClient.UnitIdentifier = (config['devices'][0]['unitidentifier'])
                            if not modbusClient.is_connected():
                                modbusClient.connect()
                        register = (readOrder['address'])
                        if not ('multiplefactor' in readOrder):
                            readOrder['multiplefactor'] = 1
                        valueToWrite = int(round(value * readOrder['multiplefactor']))
                        modbusClient.write_single_register(register - 1, valueToWrite)
                        readOrder['value'] = value
                        logging.info(
                            'Write Order Executed Value: ' + str(valueToWrite) + " Register: " + str(register))
    except Exception as e:
        logging.error('Exception Execute Write Order received from MQTT-Broker: ' + str(traceback.format_exc()))
        return
    finally:
        cfg.Config.getInstance().lock.release()


def datetime_to_unix_timestamp(dt):
    """
    shows datetime in unix timestamp
    :return: time in unix timestamp (in milliseconds sine 1st January 1970)
    """
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds() * 1000


if __name__ == "__main__":
    # config = Config.Config.getInstance()
    # config.ReadConfig()
    client = mqtt.Client('client')
    client.connect('mqtt-dashboard.com', 1883, 6000)
    # send_mqtt_data()
    # dt = datetime.datetime(2016,1,1,12,0,0)
    # print (int(datetime_to_unix_timestamp(dt)))
    # execute_write_order('{"method":"Non-Saving Load","params":{"Non-Saving Load":50}}')
