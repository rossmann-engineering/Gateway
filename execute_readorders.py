'''
Created on 28.10.2020

@author: Stefan Rossmann
'''
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

    config = cfg.Config.getInstance()

    config.lock.acquire()

    # Read Configuration (First store the last values
    _valuesList = list()
    _wakeupList = list()
    _oldvalueList = list()
    _lastpatchedList = list()
    _latestreading = list()
    _averagevaluesList = list()
    _valueinalarmList = list()

    for s in config.ReadOrders:
        _oldreadOrder = OrderedDict(s)
        if ('value' in _oldreadOrder):
            _valuesList.append(_oldreadOrder['value'])
        else:
            _valuesList.append(None)

        if ('nextwakeup' in _oldreadOrder):
            _wakeupList.append(_oldreadOrder['nextwakeup'])
        else:
            _wakeupList.append(None)

        if ('oldvalue' in _oldreadOrder):
            _oldvalueList.append(_oldreadOrder['oldvalue'])
        else:
            _oldvalueList.append(None)

        if ('lastpatchedvalue' in _oldreadOrder):
            _lastpatchedList.append(_oldreadOrder['lastpatchedvalue'])
        else:
            _lastpatchedList.append(None)

        if ('latestreading' in _oldreadOrder):
            _latestreading.append(_oldreadOrder['latestreading'])
        else:
            _latestreading.append(None)

        if ('averagevalues' in _oldreadOrder):
            _averagevaluesList.append(_oldreadOrder['averagevalues'])
        else:
            _averagevaluesList.append(None)

        if ('valueinalarm' in _oldreadOrder):
            _valueinalarmList.append(_oldreadOrder['valueinalarm'])
        else:
            _valueinalarmList.append(None)

        #else:
        #    _valuesList.append(0)
    # Read new configuration
    config.ReadConfig()
    _count = 0
    for s in config.ReadOrders:
        _readOrder = OrderedDict(s)
        if len(_valuesList) > _count:
            if (_valuesList[_count] is not None):
                _readOrder['value'] = _valuesList[_count]

        if len(_wakeupList) > _count:
            if (_wakeupList[_count] is not None):
                _readOrder['nextwakeup'] = _wakeupList[_count]

        if len(_oldvalueList) > _count:
            if (_oldvalueList[_count] is not None):
                _readOrder['oldvalue'] = _oldvalueList[_count]

        if len(_latestreading) > _count:
            if (_latestreading[_count] is not None):
                _readOrder['latestreading'] = _latestreading[_count]

        if len(_lastpatchedList) > _count:
            if (_lastpatchedList[_count] is not None):
                _readOrder['lastpatchedvalue'] = _lastpatchedList[_count]

        if len(_averagevaluesList) > _count:
            if (_averagevaluesList[_count] is not None):
                _readOrder['averagevalues'] = _averagevaluesList[_count]

        if len(_valueinalarmList) > _count:
            if (_valueinalarmList[_count] is not None):
                _readOrder['valueinalarm'] = _valueinalarmList[_count]
        config.ReadOrders[_count] = _readOrder
        _count = _count + 1




    inputRegisters = [[None for i in range(5)] for j in range (15000)]
    holdingRegisters = [[None for i in range(5)] for j in range (15000)]
    registerValues = list()
    retryCounter = 0        #This counter is to ensure  to try 3 times to read data from the Server
    for s in config.ModbusCommand:
        ModbusCommand = OrderedDict(s)
        functionCode = (ModbusCommand['functioncode'])
        startingAddress = (ModbusCommand['startingaddress'])
        quantity = (ModbusCommand['quantity'])
        if ('transportid' in ModbusCommand):
            transportid = (ModbusCommand['transportid'])
        else:
            transportid = 1


        #This is Modbus-RTU
        if ('serialPort' in config.Devices[transportid-1]):
            modbusClient = ModbusClient.ModbusClient(str(config.Devices[transportid-1]['serialPort']))
            modbusClient.Parity = config.Devices[transportid-1]['parity']
            modbusClient.Baudrate = config.Devices[transportid-1]['baudrate']
            modbusClient.Stopbits = config.Devices[transportid-1]['stopbits']
            if ('type' in config.Devices[transportid-1]):
                if (config.Devices[transportid - 1]['type'] == 'RS485'):
                    modbusClient.RS485 = True
        # This is Modbus-TCP
        if ('ipaddress' in config.Devices[transportid - 1]):
            if (not ('port' in config.Devices[transportid - 1])):
                config.Devices[transportid - 1]['port'] = 502
            modbusClient = ModbusClient.ModbusClient(str(config.Devices[transportid - 1]['ipaddress']), int(config.Devices[transportid - 1]['port']))
        if ('unitidentifier' in config.Devices[transportid - 1]):
            modbusClient.UnitIdentifier = config.Devices[transportid - 1]['unitidentifier']
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
                    for i in range(0, len (registerValues)):
                        inputRegisters[startingAddress+i+1][transportid-1] = registerValues[i]

                if (functionCode == 'Read Holding Registers'):
                    logging.debug('Request for Holding Registers, starting Value:' + str(startingAddress))
                    registerValues = modbusClient.read_holdingregisters(startingAddress, quantity)

                    logging.debug('Holding Registers received : ' + str(registerValues))

                    for i in range(0, len (registerValues)):
                        holdingRegisters[startingAddress+i+1][transportid-1] = registerValues[i]


                success = True
                time.sleep(0.01)

            except KeyboardInterrupt:
                break;

            except Exception as e:
                logging.error('Unable to read Registers from Modbus Slave: ' + str(traceback.format_exc()))
                traceback.print_exc()
                retryCounter = retryCounter +1

                time.sleep(1)
            finally:
                if ( modbusClient.is_connected()):
                    modbusClient.close()

        if (retryCounter >= 3):
            if (modbusClient.is_connected()):
                modbusClient.close()



    for i in range(0, len (config.ReadOrders)):
        readOrder = OrderedDict(config.ReadOrders[i])


        transportid = readOrder.get('transportid', 1)
        # Search for devices with the given transportid
        device = next(device for device in config.Devices if device['transportid'] == transportid)
        if device.get('type', 'modbus').lower() == 'bacnet' or device.get('type', 'modbus').lower() == 'ethernetip':
            continue


        if (not 'oldvalue' in readOrder):
            readOrder['oldvalue'] = 0.0
        if (not 'absolutethreshold' in readOrder):
            if (not 'relativethreshold' in readOrder):
                readOrder['threshold'] = 0
            else:
                if ('latestreading' in readOrder):
                    readOrder['threshold'] = readOrder['latestreading'] * readOrder['relativethreshold']/100.0
                    #If the Threshold is not equal 0 and Threshold is 0 we set it to a very short numbber 0.00001
                    if ((readOrder['threshold']) == 0) & (readOrder['relativethreshold'] > 0):
                        readOrder['threshold'] = 0.0001
                elif ('value' in readOrder):
                    readOrder['threshold'] = readOrder['value'] * readOrder['relativethreshold'] / 100.0
                    #If the Threshold is not equal 0 and Threshold is 0 we set it to a very short numbber 0.00001
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

            #-------------------------------------Read Input Registers----------------------------
            datatype = (readOrder['dataarea'])
            active = (readOrder['active'] == True)
            numberOfBits = (readOrder['bits'])
            if ((datatype == "Input Register")&(inputRegisters[register][transportid-1] != None )):
                if ('value' in readOrder):      #Check if Value already exists in dictionary
                    if (readOrder['oldvalue'] == 999999999.99):
                        readOrder['oldvalue'] =  readOrder['value']
                if ((readOrder['signed'] == True) & ((inputRegisters[register][transportid-1] & 0x8000) != 0)):
                    #inputRegisters[register] = (inputRegisters[register] & 0x7FFF) * -1
                    inputRegisters[register][transportid-1] = (((~inputRegisters[register][transportid-1])&0xffff) +1)*-1

                readOrder['value'] = 0xffff
                #if (active):   #removed 01.07.2018 to log the current data in the CSV File, even if "active" is set to false
                readOrder['value'] = inputRegisters[register][transportid-1] / (readOrder['multiplefactor']*1.0) if (readOrder['multiplefactor'] != 1) else inputRegisters[register][transportid-1]
                if (numberOfBits == 32):
                    readOrder['value'] =  ((inputRegisters[register][transportid-1]<<16) | (inputRegisters[(register+1)][transportid-1]))/ (readOrder['multiplefactor']*1.0)  if (readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else ((inputRegisters[register][transportid-1]<<16) | (inputRegisters[(register+1)][transportid-1]))
                if (numberOfBits == 64):    #64 bit only for double values -> multiplefactor ignored
                    readOrder['value'] =  ((inputRegisters[register][transportid-1] << 24) | (inputRegisters[(register+1)][transportid-1] << 32) | (inputRegisters[(register+2)][transportid-1] << 16) | (inputRegisters[(register+3)][transportid-1]))
                if ('swapregisters' in readOrder):
                    if (readOrder['swapregisters']):
                        readOrder['value'] = ((inputRegisters[register+1][transportid - 1] << 16) | (inputRegisters[(register)][transportid - 1])) / (readOrder['multiplefactor'] * 1.0) if (readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else ((inputRegisters[register + 1][transportid - 1] << 16) | (inputRegisters[(register)][transportid - 1]))
                        if numberOfBits == 64:  # 64 bit only for double values -> multiplefactor ignored
                            readOrder['value'] = ((inputRegisters[(register + 3)][transportid - 1] << 24) | (inputRegisters[(register + 2)][transportid - 1] << 32) | (inputRegisters[(register + 1)][transportid - 1] << 16) | (inputRegisters[register][transportid - 1]))

            # -------------------------------------Read Holding Registers----------------------------
            #config.ReadOrders[i] = readOrder
            if ((datatype == "Holding Register")&(holdingRegisters[register][transportid-1] != None )):
                if ('value' in readOrder):      #Check if Value already exists in dictionary
                    if ((readOrder['oldvalue']) == 999999999.99):
                        readOrder['oldvalue'] =  readOrder['value']
                if ((readOrder['signed'] == True) & ((holdingRegisters[register][transportid-1] & 0x8000) != 0)):
                    holdingRegisters[register][transportid-1] = (((~holdingRegisters[register][transportid-1]) & 0xffff) + 1) * -1
                readOrder['value'] = 0xffff
                #if (active):   #removed 01.07.2018 to log the current data in the CSV File, even if "active" is set to false
                readOrder['value'] =  holdingRegisters[(register)][transportid-1]  / readOrder['multiplefactor'] if (readOrder['multiplefactor'] != 1) else holdingRegisters[(register)][transportid-1]
                if (numberOfBits == 32):
                    readOrder['value'] = ((holdingRegisters[(register)][transportid-1]<<16) | (holdingRegisters[(register+1)][transportid-1])) / readOrder['multiplefactor']  if (readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else ((holdingRegisters[(register)][transportid-1]<<16) | (holdingRegisters[(register+1)][transportid-1]))
                if (numberOfBits == 64):    #64 bit only for double values
                    readOrder['value'] =  ((holdingRegisters[register][transportid-1] << 24) | (holdingRegisters[(register+1)][transportid-1] << 32) | (holdingRegisters[(register+2)][transportid-1] << 16) | (holdingRegisters[(register+3)][transportid-1]))
                if ('swapregisters' in readOrder):
                    if readOrder['swapregisters']:
                        readOrder['value'] = ((holdingRegisters[(register+1)][transportid - 1] << 16) | (holdingRegisters[(register)][transportid - 1])) / readOrder['multiplefactor'] if (readOrder['multiplefactor'] != 1 and 'datatype' not in readOrder) else ((holdingRegisters[(register + 1)][transportid - 1] << 16) | (holdingRegisters[(register)][transportid - 1]))
                        if numberOfBits == 64:  # 64 bit only for double values
                            readOrder['value'] = ((holdingRegisters[(register + 3)][transportid - 1] << 24) | (holdingRegisters[(register + 2)][transportid - 1] << 32) | (holdingRegisters[(register + 1)][transportid - 1] << 16) | (holdingRegisters[register][transportid - 1]))

            #------------------------Convert to Floating Point value if 'datatype' is float (32 bit) or double (64 bit)
            #https://stackoverflow.com/questions/33483846/how-to-convert-32-bit-binary-to-float
            if 'datatype' in readOrder and 'value' in readOrder:
                if readOrder['datatype'] == 'float' or readOrder['datatype'] == 'double':
                    f = int(str(readOrder['value']), 10)
                    readOrder['value'] = struct.unpack('f', struct.pack('I', f))[0]
                    if ('multiplefactor' in readOrder):
                        readOrder['value'] = readOrder['value'] / readOrder['multiplefactor']


            #-----------------------In this section we calculate the average value if the transmissionmode is set to averagereading
            if ('transmissionmode' in readOrder) & ('value' in readOrder):
                if (active & ('transmissionmode' in readOrder) & ('value' in readOrder) & (readOrder['value']!=0xffff)):
                    if (readOrder['transmissionmode'] == 'averagereading'):
                        if (not ('averagevalues' in readOrder)):
                            readOrder['averagevalues'] = list()
                        numberOfReadings = config.BasicInterval / config.ReadInterval
                        if (numberOfReadings < 1):
                            numberOfReadings = 1
                        readOrder['averagevalues'].append(readOrder['value'])
                        if (len(readOrder['averagevalues']) > numberOfReadings):
                            del(readOrder['averagevalues'][0])          #Delete the first entry of the list if the size exceeded the maximum size -> We wantg to ha ve only the latest readings

        config.ReadOrders[i] = readOrder


    execute_writeorders.execute_writeorders()


    #--------------------------Store data in LogFile
    datalogger.registerLogFileCSV()

    config.lock.release()


if __name__ == "__main__":
    f = int(str(45), 10)
    value = struct.unpack('f', struct.pack('I', 45))[0]
    print(value)
    print(type(value))
    