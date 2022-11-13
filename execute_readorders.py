"""
Created on 28.10.2020

@author: Stefan Rossmann
"""
import config as cfg
import ModbusClient
import datalogger
import time
import traceback
from collections import OrderedDict
import struct
import execute_writeorders
import logging


def execute_readorders():
    """
    executes order read
    """
    config = cfg.Config.getConfig()

    cfg.Config.getInstance().lock.acquire()

    inputRegisters = [[None for i in range(5)] for j in range(15000)]
    holdingRegisters = [[None for i in range(5)] for j in range(15000)]
    registerValues = list()
    retryCounter = 0  # This counter is to ensure  to try 3 times to read data from the Server
    for s in config['modbuscommand']:
        ModbusCommand = OrderedDict(s)
        functionCode = (ModbusCommand['functioncode'])
        startingAddress = (ModbusCommand['startingaddress'])
        quantity = (ModbusCommand['quantity'])
        if ('transportid' in ModbusCommand):
            transportid = (ModbusCommand['transportid'])
        else:
            transportid = 1

        # This is Modbus-RTU
        if ('serialPort' in config['devices'][transportid - 1]):
            modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['serialPort']))
            modbusClient.Parity = config['devices'][transportid - 1]['parity']
            modbusClient.Baudrate = config['devices'][transportid - 1]['baudrate']
            modbusClient.Stopbits = config['devices'][transportid - 1]['stopbits']
            if ('type' in config['devices'][transportid - 1]):
                if (config['devices'][transportid - 1]['type'] == 'RS485'):
                    modbusClient.RS485 = True
        # This is Modbus-TCP
        if ('ipaddress' in config['devices'][transportid - 1]):
            if (not ('port' in config['devices'][transportid - 1])):
                config['devices'][transportid - 1]['port'] = 502
            modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['ipaddress']),
                                                     int(config['devices'][transportid - 1]['port']))
        if ('unitidentifier' in config['devices'][transportid - 1]):
            modbusClient.UnitIdentifier = config['devices'][transportid - 1]['unitidentifier']
        modbusClient.Timeout = 5
        success = False
        while (not success and retryCounter < 3):
            try:
                if (not modbusClient.is_connected()):
                    modbusClient.connect()
                if (functionCode == 'Read Input Registers'):
                    logging.debug('Request for Input Registers, starting Value:' + str(startingAddress))
                    registerValues = modbusClient.read_inputregisters(startingAddress, quantity)

                    logging.debug('Input Registers received : ' + str(registerValues))
                    for i in range(0, len(registerValues)):
                        inputRegisters[startingAddress + i + 1][transportid - 1] = registerValues[i]

                if (functionCode == 'Read Holding Registers'):
                    logging.debug('Request for Holding Registers, starting Value:' + str(startingAddress))
                    registerValues = modbusClient.read_holdingregisters(startingAddress, quantity)

                    logging.debug('Holding Registers received : ' + str(registerValues))

                    for i in range(0, len(registerValues)):
                        holdingRegisters[startingAddress + i + 1][transportid - 1] = registerValues[i]

                success = True
                time.sleep(0.01)

            except KeyboardInterrupt:
                break;

            except Exception as e:
                logging.error('Unable to read Registers from Modbus Slave: ' + str(traceback.format_exc()))
                traceback.print_exc()
                retryCounter = retryCounter + 1

                time.sleep(1)
            finally:
                if (modbusClient.is_connected()):
                    modbusClient.close()

        if (retryCounter >= 3):
            if (modbusClient.is_connected()):
                modbusClient.close()

    for i in range(0, len(config['readorders'])):
        readOrder = OrderedDict(config['readorders'][i])

        transportid = readOrder.get('transportid', 1)
        # Search for devices with the given transportid
        device = next(device for device in config['devices'] if device['transportid'] == transportid)
        if device.get('type', 'modbus').lower() == 'bacnet' or device.get('type', 'modbus').lower() == 'ethernetip':
            continue

        if (not 'oldvalue' in readOrder):
            readOrder['oldvalue'] = 0.0
        if (not 'absolutethreshold' in readOrder):
            if (not 'relativethreshold' in readOrder):
                readOrder['threshold'] = 0
            else:
                if ('latestreading' in readOrder):
                    readOrder['threshold'] = readOrder['latestreading'] * readOrder['relativethreshold'] / 100.0
                    # If the Threshold is not equal 0 and Threshold is 0 we set it to a very short numbber 0.00001
                    if ((readOrder['threshold']) == 0) & (readOrder['relativethreshold'] > 0):
                        readOrder['threshold'] = 0.0001
                elif ('value' in readOrder):
                    readOrder['threshold'] = readOrder['value'] * readOrder['relativethreshold'] / 100.0
                    # If the Threshold is not equal 0 and Threshold is 0 we set it to a very short numbber 0.00001
                    if ((readOrder['threshold']) == 0) & (readOrder['relativethreshold'] > 0):
                        readOrder['threshold'] = 0.0001
                else:
                    readOrder['threshold'] = 0
        else:
            readOrder['threshold'] = readOrder['absolutethreshold']

        if ('address' in readOrder):
            register = (readOrder['address'])
            if (not 'multiplefactor' in readOrder):
                readOrder['multiplefactor'] = 1

            # -------------------------------------Read Input Registers----------------------------
            datatype = (readOrder['dataarea'])
            active = (readOrder['active'] == True)
            numberOfBits = (readOrder['bits'])
            if ((datatype == "Input Register") & (inputRegisters[register][transportid - 1] != None)):
                if ('value' in readOrder):  # Check if Value already exists in dictionary
                    if (readOrder['oldvalue'] == 999999999.99):
                        readOrder['oldvalue'] = readOrder['value']
                if ((readOrder['signed'] == True) & ((inputRegisters[register][transportid - 1] & 0x8000) != 0)):
                    # inputRegisters[register] = (inputRegisters[register] & 0x7FFF) * -1
                    inputRegisters[register][transportid - 1] = (((~inputRegisters[register][
                        transportid - 1]) & 0xffff) + 1) * -1

                readOrder['value'] = 0xffff
                # if (active):   #removed 01.07.2018 to log the current data in the CSV File, even if "active" is set to false
                readOrder['value'] = inputRegisters[register][transportid - 1] / (
                            readOrder['multiplefactor'] * 1.0) if (readOrder['multiplefactor'] != 1) else \
                inputRegisters[register][transportid - 1]
                if (numberOfBits == 32):
                    readOrder['value'] = ((inputRegisters[register][transportid - 1] << 16) | (
                    inputRegisters[(register + 1)][transportid - 1])) / (readOrder['multiplefactor'] * 1.0) if (
                                readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else (
                                (inputRegisters[register][transportid - 1] << 16) | (
                        inputRegisters[(register + 1)][transportid - 1]))
                if (numberOfBits == 64):  # 64 bit only for double values -> multiplefactor ignored
                    readOrder['value'] = ((inputRegisters[register][transportid - 1] << 24) | (
                                inputRegisters[(register + 1)][transportid - 1] << 32) | (
                                                      inputRegisters[(register + 2)][transportid - 1] << 16) | (
                                          inputRegisters[(register + 3)][transportid - 1]))
                if ('swapregisters' in readOrder):
                    if (readOrder['swapregisters']):
                        readOrder['value'] = ((inputRegisters[register + 1][transportid - 1] << 16) | (
                        inputRegisters[(register)][transportid - 1])) / (readOrder['multiplefactor'] * 1.0) if (
                                    readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else (
                                    (inputRegisters[register + 1][transportid - 1] << 16) | (
                            inputRegisters[(register)][transportid - 1]))
                        if numberOfBits == 64:  # 64 bit only for double values -> multiplefactor ignored
                            readOrder['value'] = ((inputRegisters[(register + 3)][transportid - 1] << 24) | (
                                        inputRegisters[(register + 2)][transportid - 1] << 32) | (
                                                              inputRegisters[(register + 1)][transportid - 1] << 16) | (
                                                  inputRegisters[register][transportid - 1]))

            # -------------------------------------Read Holding Registers----------------------------
            # config.ReadOrders[i] = readOrder
            if ((datatype == "Holding Register") & (holdingRegisters[register][transportid - 1] != None)):
                if ('value' in readOrder):  # Check if Value already exists in dictionary
                    if ((readOrder['oldvalue']) == 999999999.99):
                        readOrder['oldvalue'] = readOrder['value']
                if ((readOrder['signed'] == True) & ((holdingRegisters[register][transportid - 1] & 0x8000) != 0)):
                    holdingRegisters[register][transportid - 1] = (((~holdingRegisters[register][
                        transportid - 1]) & 0xffff) + 1) * -1
                readOrder['value'] = 0xffff
                # if (active):   #removed 01.07.2018 to log the current data in the CSV File, even if "active" is set to false
                readOrder['value'] = holdingRegisters[(register)][transportid - 1] / readOrder['multiplefactor'] if (
                            readOrder['multiplefactor'] != 1) else holdingRegisters[(register)][transportid - 1]
                if (numberOfBits == 32):
                    readOrder['value'] = ((holdingRegisters[(register)][transportid - 1] << 16) | (
                    holdingRegisters[(register + 1)][transportid - 1])) / readOrder['multiplefactor'] if (
                                readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else (
                                (holdingRegisters[(register)][transportid - 1] << 16) | (
                        holdingRegisters[(register + 1)][transportid - 1]))
                if (numberOfBits == 64):  # 64 bit only for double values
                    readOrder['value'] = ((holdingRegisters[register][transportid - 1] << 24) | (
                                holdingRegisters[(register + 1)][transportid - 1] << 32) | (
                                                      holdingRegisters[(register + 2)][transportid - 1] << 16) | (
                                          holdingRegisters[(register + 3)][transportid - 1]))
                if ('swapregisters' in readOrder):
                    if readOrder['swapregisters']:
                        readOrder['value'] = ((holdingRegisters[(register + 1)][transportid - 1] << 16) | (
                        holdingRegisters[(register)][transportid - 1])) / readOrder['multiplefactor'] if (
                                    readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else (
                                    (holdingRegisters[(register + 1)][transportid - 1] << 16) | (
                            holdingRegisters[(register)][transportid - 1]))
                        if numberOfBits == 64:  # 64 bit only for double values
                            readOrder['value'] = ((holdingRegisters[(register + 3)][transportid - 1] << 24) | (
                                        holdingRegisters[(register + 2)][transportid - 1] << 32) | (
                                                              holdingRegisters[(register + 1)][
                                                                  transportid - 1] << 16) | (
                                                  holdingRegisters[register][transportid - 1]))

            # ------------------------Convert to Floating Point value if 'datatype' is float (32 bit) or double (64 bit)
            # https://stackoverflow.com/questions/33483846/how-to-convert-32-bit-binary-to-float
            if 'datatype' in readOrder and 'value' in readOrder:
                if readOrder['datatype'] == 'float' or readOrder['datatype'] == 'double':
                    f = int(str(readOrder['value']), 10)
                    readOrder['value'] = struct.unpack('f', struct.pack('I', f))[0]
                    if ('multiplefactor' in readOrder):
                        readOrder['value'] = readOrder['value'] / readOrder['multiplefactor']

            # -----------------------In this section we calculate the average value if the transmissionmode is set to averagereading
            if ('transmissionmode' in readOrder) & ('value' in readOrder):
                if (active & ('transmissionmode' in readOrder) & ('value' in readOrder) & (
                        readOrder['value'] != 0xffff)):
                    if (readOrder['transmissionmode'] == 'averagereading'):
                        if (not ('averagevalues' in readOrder)):
                            readOrder['averagevalues'] = list()
                        numberOfReadings = config['basicinterval'] / config['readinterval']
                        if (numberOfReadings < 1):
                            numberOfReadings = 1
                        readOrder['averagevalues'].append(readOrder['value'])
                        if (len(readOrder['averagevalues']) > numberOfReadings):
                            del (readOrder['averagevalues'][
                                0])  # Delete the first entry of the list if the size exceeded the maximum size -> We wantg to ha ve only the latest readings

        config['readorders'][i] = readOrder

    execute_writeorders.execute_writeorders()

    # --------------------------Store data in LogFile
    datalogger.registerLogFileCSV()

    cfg.Config.getInstance().lock.release()


if __name__ == "__main__":
    f = int(str(45), 10)
    value = struct.unpack('f', struct.pack('I', 45))[0]
    print(value)
    print(type(value))
