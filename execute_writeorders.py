"""
Created on 13.11.2020

@author: Stefan Rossmann
"""
import config as cfg
import ModbusClient
import datalogger
import time
import traceback
from collections import OrderedDict
import struct


def execute_writeorders():
    """
    execute order write
    """
    config = cfg.Config.getConfig()

    for read_order in config['readorders']:
        if read_order.get('value', 0xFFFF) == 0xFFFF:
            continue
        if read_order.get('target', '') != '':
            # ----------------------------------Search for the Target Read-Order
            for target_readorder in config['readorders']:
                if read_order.get('target', '') == target_readorder['name']:
                    transportid = int(target_readorder.get('transportid', 1))
                    # ---------------------------------------------Serch for the Transport ID
                    for device in config['devices']:
                        if device['transportid'] == transportid:
                            address = target_readorder['address']
                            type = device.get('type', 'Modbus')
                            # ------------------------------------------------Modbus
                            if type == 'Modbus':
                                try:
                                    # This is Modbus-RTU
                                    if 'serialPort' in device:
                                        modbusClient = ModbusClient.ModbusClient(
                                            str(device['serialPort']))
                                        modbusClient.Parity = device['parity']
                                        modbusClient.Baudrate = device['baudrate']
                                        modbusClient.Stopbits = device['stopbits']
                                        if ('type' in device):
                                            if (device['type'] == 'RS485'):
                                                modbusClient.RS485 = True
                                    # This is Modbus-TCP
                                    if ('ipaddress' in device):
                                        if (not ('port' in device)):
                                            device['port'] = 502
                                        modbusClient = ModbusClient.ModbusClient(
                                            str(device['ipaddress']),
                                            int(device['port']))
                                    if ('unitidentifier' in device):
                                        modbusClient.UnitIdentifier = device['unitidentifier']
                                    modbusClient.Timeout = 5
                                    if (not modbusClient.is_connected()):
                                        modbusClient.connect()
                                    if (read_order['bits'] == 16):
                                        modbusClient.write_single_register(address - 1, int(round(
                                            read_order['value'] * read_order['multiplefactor'])))
                                    elif (read_order['bits'] == 32):
                                        registervalue = list([((int(
                                            read_order['value'] * read_order['multiplefactor']) & 0xFFFF0000) >> 16),
                                                              int(read_order['value'] * read_order[
                                                                  'multiplefactor']) & 0xFFFF])
                                        modbusClient.write_multiple_registers(address - 1, registervalue)
                                except Exception:
                                    datalogger.logData(
                                        'Unable to Write to Modbus Register : ' + str(traceback.format_exc()))
                                finally:
                                    modbusClient.close()

                            break;

                    break;
