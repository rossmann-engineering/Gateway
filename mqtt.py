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
            if str(mqttbroker.get('tls', 'false')) == 'True':
                self.clients[loopcounter]['instance'].tls_set(certfile=None,
                               keyfile=None,
                               cert_reqs=ssl.CERT_NONE)
            username = ''
            if 'username' in mqttbroker:
                username = mqttbroker['username']
            self.clients[loopcounter]['instance'].username_pw_set(mqttbroker['password'], username)


            while not internet_on():
                cfg.Config.getInstance().mqttconnectionlost = True
                logging.info('MQTT-Client - Wait for Internet connection available')
                time.sleep(2)
            try:
                db_conn = database.connect("eh.db", '')
                database.create_tables(db_conn)

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

                loopcounter = loopcounter + 1
            except:
                logging.error('Exception connecting to MQTT-Broker: ' + str(traceback.format_exc()))

    def on_connect(self, client, userdata, flags, rc):
        """ connect to mqtt """
        cfg.mqttconnectionlost = False
        config = cfg.Config.getConfig()
        client.subscribe(config['mqttbroker'][0]['subscribetopic'])
        #client.subscribe('v1/devices/me/attributes')
        pass

    def on_disconnect(self, client, userdata, rc):
        """ disconnect from mqtt """
        logging.info('Disconnected from MQTT-Broker')

        pass

    def on_message(self, client, userdata, msg):
        """ receive message from mqtt Broker """

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
    config = cfg.Config.getConfig()
    try:

        logging.info('Store Message to Database, ServerID ' + str(serverid) + ' Message: ' + payload)
        if len(payload) > 5:
            db_conn = database.connect("eh.db", config.get('databasetype', ''))
            database.add_message_queue(db_conn, datetime.datetime.now(), serverid, topic, payload)
            cfg.Config.getInstance().eventcounter = cfg.Config.getInstance().eventcounter + 1
    except:
        logging.error('Exception storing data in Database: ' + str(traceback.format_exc()))

    try:
        # check message queue for entries
        db_conn = database.connect("eh.db", config.get('databasetype', ''))
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
    """ send Thingsboard attributes """
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

        mqttbroker = dict(s)
        payload = '{"Time":' + str(int(datetime_to_unix_timestamp(datetime.datetime.now())/1000))

        #Power and Energy for grid values
        power = 0
        energy = 0
        for device in config['devices']:
            if (device.get('name', 'PQube3e power quality meter') == "PQube3e power quality meter"):
                for ro in config['readorders']:
                    if (device['transportid'] == ro['transportid']) & (device.get('name', 'PQube3e power quality meter') == "PQube3e power quality meter"):
                        if ro['name'] == 'Active Grid Power':
                            power = float(ro.get('value', 0))
                        elif ro['name'] == 'Active Grid Energy':
                            energy = float(ro.get('value', 0))

        payload = payload + ', "Grid":{"Power":' + str(power) + ', "Energy": ' + str(energy) + '},'

        #Add Production (Energymeters) to MQTT Message (We take the Transport ID as nr
        payload = payload + '"Production":['
        for device in config['devices']:
            for ro in config['readorders']:
                if (device['transportid'] == ro['transportid']) & (device.get('name', 'PQube3e power quality meter') == "PQube3e power quality meter"):
                    if (ro['name'] == 'Active Node Power'):
                        payload = payload + ('{"nr":'+str(device['transportid'])+', "Power": '+str(ro.get('value', 0))+'},')
        # Remove last comma
        payload = payload[:-1]
        payload = payload + '],'


        # Nodes
        payload = payload + '"Node":['

        for device in config['devices']:
            if device.get('name',
                       'EV charger eCharge4Drivers : ABB fast charger') == "PQube3e power quality meter":
                power = 0
                current = [0, 0, 0]
                for ro in config['readorders']:
                    if (device['transportid'] == ro['transportid']):
                        if (ro['name'] == 'Active Node Power'):
                            power = float(ro.get('value', 0))
                        if ro['name'] == 'Current L1':
                            current[0] = float(ro.get('value', 0))
                        if ro['name'] == 'Current L2':
                            current[1] = float(ro.get('value', 0))
                        if ro['name'] == 'Current L3':
                            current[2] = float(ro.get('value', 0))
                payload = payload + '{"nr":' + str(device['transportid']) + ', "Power": ' + str(power) + ', "Current": ['+ str(current[0]) +','+ str(current[1]) +','+ str(current[2]) +']},'
        # Remove last comma
        if payload[-1] == ',':
            payload = payload[:-1]
        payload = payload + '],'

        #payload = payload + '"{"nr":1, "Power": 6221, "Current": [9016,9016,9016]}'
        #payload = payload + ', {"nr":2, "Power": 4321, "Current": [6262,6262,6262]}],'

        # EVChargers:
        payload = payload + '"EVChargers":['
        for device in config['devices']:
            if device.get('name',
                       'EV charger eCharge4Drivers : ABB fast charger') == "EV charger eCharge4Drivers : ABB fast charger":
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
                for ro in config['readorders']:
                    if (device['transportid'] == ro['transportid']):


                        if (ro['name'] == 'State of charge value of the EV battery outlet 1'):
                            soc1 = float(ro.get('value', 0))
                            nr1 = ro.get('nr', 1)
                        if (ro['name'] == 'Status outlet 1'):
                            status1 = float(ro.get('value', 0))
                            nr1 = ro.get('nr', 1)
                        if (ro['name'] == 'DC voltage outlet 1'):
                            dc_voltage1 = float(ro.get('value', 0))
                            nr1 = ro.get('nr', 1)
                        if (ro['name'] == 'DC current outlet 1'):
                            dc_current1 = float(ro.get('value', 0))
                            current1[0] = dc_current1 / math.sqrt(3)
                            current1[1] = dc_current1 / math.sqrt(3)
                            current1[2] = dc_current1 / math.sqrt(3)
                            nr1 = ro.get('nr', 1)
                        if (ro['name'] == 'Energy to EV battery during charging session outlet 1'):
                            energy1 = float(ro.get('value', 0))
                            nr1 = ro.get('nr', 1)

                        if (ro['name'] == 'State of charge value of the EV battery outlet 2'):
                            soc2 = float(ro.get('value', 0))
                            nr2 = ro.get('nr', 1)
                        if (ro['name'] == 'Status outlet 2'):
                            status2 = float(ro.get('value', 0))
                            nr2 = ro.get('nr', 1)
                        if (ro['name'] == 'DC voltage outlet 2'):
                            dc_voltage2 = float(ro.get('value', 0))
                            nr2 = ro.get('nr', 1)
                        if (ro['name'] == 'DC current outlet 2'):
                            dc_current2 = float(ro.get('value', 0))
                            current2[0] = dc_current2 / math.sqrt(3)
                            current2[1] = dc_current2 / math.sqrt(3)
                            current2[2] = dc_current2 / math.sqrt(3)
                            nr2 = ro.get('nr', 1)
                        if (ro['name'] == 'Energy to EV battery during charging session outlet 2'):
                            energy2 = float(ro.get('value', 0))
                            nr2 = ro.get('nr', 1)



                payload = payload + ('{"nr":' + str(nr1) + ', "Status": ' + str(status1) + ', "Power": ' + str(power1) + ', "Power_max": '+ str(power_max1) +', "Energy": ' + str(energy1) + ', "Current": ['+ str(current1[0]) +',' + str(current1[1]) + ','+ str(current1[2]) +'], "SOC": ' + str(soc1) + '},')
                payload = payload + ('{"nr":' + str(nr2) + ', "Status": ' + str(status2) + ', "Power": ' + str(power2) + ', "Power_max": '+ str(power_max2) +', "Energy": ' + str(energy2) + ', "Current": ['+ str(current2[0]) +',' + str(current2[1]) + ','+ str(current2[2]) +'], "SOC": ' + str(soc2) + '},')



            if device.get('name',
                       'EV charger eCharge4Drivers : ABB fast charger') == "ABB Terra AC W22-T-RD-MC-0":
                soc = 0
                status = 0
                power = 0
                dc_voltage = 0
                dc_current = 0
                power_max = 999
                energy = 0
                current = [0, 0, 0]
                nr = 1
                for ro in config['readorders']:
                    if (device['transportid'] == ro['transportid']):
                        if (ro['name'] == 'Charging state'):
                            nr = ro.get('nr', 1)
                            status = float(ro.get('value', 0))
                        if (ro['name'] == 'Active Power'):
                            nr = ro.get('nr', 1)
                            power = float(ro.get('value', 0))
                        if (ro['name'] == 'Charging current phase 1'):
                            nr = ro.get('nr', 1)
                            current[0] = float(ro.get('value', 0))
                        if (ro['name'] == 'Charging current phase 2'):
                            nr = ro.get('nr', 1)
                            current[1] = float(ro.get('value', 0))
                        if (ro['name'] == 'Charging current phase 3'):
                            nr = ro.get('nr', 1)
                            current[2] = float(ro.get('value', 0))
                        if (ro['name'] == 'Energy delivered in charging session'):
                            nr = ro.get('nr', 1)
                            energy = float(ro.get('value', 0))



                payload = payload + ('{"nr":' + str(nr) + ', "Status": '+str(status)+', "Power": ' + str(power) + ', "Power_max": '+ str(power_max) +', "Energy": ' + str(energy) + ', "Current": ['+ str(current[0]) +',' + str(current[1]) + ','+ str(current[2]) +']},')



        #payload = payload + '{"nr":1, "Status": 2,"Power": 6557, "Power_max": 8000, "Energy": 15665, "Current": [9503,9503,9503]},'
        #payload = payload + '{"nr":1, "Status": 2,"Power": 6557, "Power_max": 8000, "Energy": 15665, "Current": [9503,9503,9503], "SOC": 5423}'



        # Remove last comma
        if payload[-1] == ',':
            payload = payload[:-1]
        payload = payload + ']}'



        logging.info('Sending MQTT-Data to serverid' + str(mqttbroker['serverid']))
        publish_message(mqttbroker['serverid'], mqttbroker['publishtopic'], payload)


def execute_write_order(payload):
    """
    {
    "EVChargers":[
    {"nr":1,
    "Current":6000,}, {"nr":2,
    "Current":7000,} ]
    }
    :param payload: message received from MQTT-Broker
    """
    d = json.loads(payload)
    if 'EVChargers' not in d:
        return
    config = cfg.Config.getConfig()
    # Search for matching RadOrder
    try:
        for charger in d['EVChargers']:
            for device in config['devices']:
                # Modbus Device
                if device.get('name',
                              'EV charger eCharge4Drivers : ABB fast charger') == "ABB Terra AC W22-T-RD-MC-0":
                    if charger['nr'] == device.get('nr', 1):
                        valueToWrite =  charger['Current'] * 1000
                        register = 16640
                        modbus_registers = ModbusClient.ConvertDoubleToTwoRegisters(valueToWrite)
                        modbus_client = ModbusClient.ModbusClient(device['ipaddress'], device['port'])
                        modbus_client.write_multiple_registers(register-1, modbus_registers)

                        logging.info(
                            'Write Order Executed Value: ' + str(valueToWrite) + " Register: " + str(register))
                if device.get('name',
                              'EV charger eCharge4Drivers : ABB fast charger') == "EV charger eCharge4Drivers : ABB fast charger":
                    if charger['nr'] == device.get('nr1', 1) | charger['nr'] == device.get('nr2', 1):
                        valueToWrite = charger['Current']
                        ro = next(
                            (item for item in config['readorders'] if item["name"] == "SetBudget"), dict())
                        ro['value'] = valueToWrite
                        asyncio.run(opc_ua.main('opc.tcp://' + device['ipaddress'] + ':' + str(device['port']), '',
                                                '', [ro], write=True))

    except Exception as e:
        logging.error('Exception Execute Write Order received from MQTT-Broker: ' + str(traceback.format_exc()))
        return


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
