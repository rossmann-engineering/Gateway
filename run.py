#!/usr/bin/env python
'''
Created on 28.10.2020

@author: Stefan Rossmann
'''

import time
import config as cfg
import sys
import execute_readorders
import datetime
import calendar
import webserver
import traceback
import threading
import mqtt
import logging
import os, errno
import pos_edge

# ------------------------- Initiate logging Start
try:
    os.makedirs('unitdatabase')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
logging.getLogger().setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler1 = logging.handlers.RotatingFileHandler(
    'unitdatabase/logdata.txt', maxBytes=2000000, backupCount=5)
logging.getLogger().addHandler(handler1)
formatter1 = logging.Formatter("%(asctime)s;%(message)s",
                               "%Y-%m-%d %H:%M:%S")
handler1.setFormatter(formatter1)
console = logging.StreamHandler()
logging.getLogger().addHandler(console)
# ------------------------- Initiate logging End


config = cfg.Config.getConfig()

#Write Softwareversion (commandline argument "writeswversion"
if (len(sys.argv) > 1):
    for i in range(1, len(sys.argv)):
        if (sys.argv[i] == 'writeswversion'):
            config.WritePythonSWVersion()

thread = threading.Thread(target=webserver.start, args=())
thread.start()

if (len(config['mqttbroker']) > 0):
    thread4 = threading.Thread(target=mqtt.Clients.getInstance, args=())
    thread4.start()

intervall = config['readinterval']
currentDateTime = datetime.datetime.now()
currentSecond = currentDateTime.second
currentMinute = currentDateTime.minute

resendhour = 1
resendminute = 0

timeInAbsoluteSeconds = calendar.timegm(time.gmtime())
nextWakeUp = (calendar.timegm(time.gmtime()) // intervall)*intervall +intervall
if (intervall > 60):

    nextWakeUp = ((timeInAbsoluteSeconds  // 60) * 60) + intervall
    nextWakeUp = ((nextWakeUp // 60) // (intervall // 60))* (intervall // 60) *60

myThreads = []


pos_edge_sendvalues = pos_edge.pos_edge()

execute_readorders.execute_readorders()
time.sleep(15)


oneshot = False


while (True):
    try:
        timeInAbsoluteSeconds = calendar.timegm(time.gmtime())
        currentDateTime = datetime.datetime.now()
        currentSecond = currentDateTime.second
        currentMinute = currentDateTime.minute
        currentHour = currentDateTime.hour

        #Send all True values at 00:30 every day -> we have to erase the "nextwakeup" element of each read order
        resendValues = False;
        if (pos_edge_sendvalues.GetPosEdge((currentHour == resendhour) and (currentMinute == resendminute))):
            #if (oneshot):
            resendValues = True
            logging.info('Resend all value at ' + str(resendhour) + ':' + str(resendminute))

        #Send all values from the Webserver Button
        if cfg.Config.getInstance().uploadalldata:
            resendValues = True
            logging.info('Resend all values request from Webserver')

        if (timeInAbsoluteSeconds >= nextWakeUp):
            nextWakeUp = nextWakeUp + intervall
            while (nextWakeUp < timeInAbsoluteSeconds):
                nextWakeUp = nextWakeUp + intervall
            print ('Woke up Read values: ' + str(datetime.datetime.now()))

            execute_readorders.execute_readorders()

        cfg.Config.getInstance().lock.acquire()
        send_value = False
        for i in range(0, len (config['readorders'])):
            readOrder = dict(config['readorders'][i])
            #Looking for the key "registerintervaltime", if not present: write "1"
            if not ('registerintervaltime' in readOrder):
                readOrder['registerintervaltime'] = 1


            readOrder['sendValue'] = False
            interval = readOrder['registerintervaltime']*config['basicinterval']

            #at 01:00 each day we upload all values -> reset the nextwakeup
            if (resendValues):
                if ('nextwakeup' in readOrder):
                    readOrder.pop('nextwakeup')


            #If the key "nextwakeup" doesn't exist it is the first startup -> Send values
            if (not 'nextwakeup' in readOrder):
                readOrder['nextwakeup'] = (calendar.timegm(time.gmtime()) // interval)*interval +interval

                if (interval > 60):

                    readOrder['nextwakeup'] = ((timeInAbsoluteSeconds  // 60) * 60) + interval
                    readOrder['nextwakeup'] = ((readOrder['nextwakeup'] // 60) // (interval // 60))* (interval // 60) *60

                #Send values at startup (13.05.2018)
                if ('value' in readOrder):
                    send_value = True
                    readOrder['sendValue'] = True
                    readOrder['oldvalue'] = 999999999.99
                    readOrder['latestreading'] = readOrder['value']  # This is only for the webserver

            else:
                if (timeInAbsoluteSeconds >= readOrder['nextwakeup']):
                    readOrder['nextwakeup'] = readOrder['nextwakeup'] + interval
                    while (readOrder['nextwakeup'] < timeInAbsoluteSeconds):
                        readOrder['nextwakeup'] = readOrder['nextwakeup'] + interval

                    # -----------------------If the transmissionmode is set to averagereading, then we write the averagevalue into the value element
                    if (('transmissionmode' in readOrder)):
                        if (readOrder['transmissionmode'] == 'averagereading'):
                            if ('averagevalues' in readOrder):
                                if len(readOrder['averagevalues']) > 0:
                                    readOrder['value'] = 0
                                    for j in range(0, len(readOrder['averagevalues'])):
                                        readOrder['value'] = readOrder['value'] + readOrder['averagevalues'][j]
                                    readOrder['value'] = readOrder['value']/len(readOrder['averagevalues'])
                                readOrder['averagevalues'] = list()




                    if (('value' in readOrder) & ('threshold' in readOrder) & ('oldvalue' in readOrder)):
                        if (((readOrder['value'] - readOrder['threshold']) >= readOrder['oldvalue']) | ((readOrder['value'] + readOrder['threshold']) <= readOrder['oldvalue']) | (readOrder['threshold'] == 0)):
                            readOrder['sendValue'] = True
                            send_value = True
                            readOrder['oldvalue'] = 999999999.99
                            readOrder['latestreading'] = readOrder['value']  # This is only for the webserver

                        else:
                            readOrder['sendValue'] = False

            #-------------------Check the alarm threshold - if the old value exceeds the alarmthreshold, this is outside the interval
            if (('value' in readOrder) & ('alarmthreshold' in readOrder)):
                if (not ('valueinalarm' in readOrder)):
                    readOrder['valueinalarm'] = False
                if ((readOrder['value'] >= readOrder['alarmthreshold']) & (readOrder['valueinalarm']== False)):
                    readOrder['sendValue'] = True
                    send_value = True
                    readOrder['valueinalarm'] = True
                    readOrder['latestreading'] = readOrder['value']  # This is only for the webserver
                if (readOrder['value'] < readOrder['alarmthreshold']):
                    readOrder['valueinalarm'] = False
            config['readorders'][i] = readOrder


        cfg.Config.getInstance().lock.release()
        if (send_value):
            if (len(config['mqttbroker']) > 0):
                thread5 = threading.Thread(target=mqtt.send_mqtt_data(), args=())
                thread5.start()


        if (cfg.Config.getInstance().uploadalldata & resendValues):
            cfg.Config.getInstance().uploadalldata = False



        time.sleep(0.5)
        oneshot = True

    except KeyboardInterrupt:
        logging.info('Thread Main stopped ')

        break;
    except Exception as e:
        logging.error('Exception in Main-Loop: ' + str(traceback.format_exc()))
        time.sleep(0.5)


webserver.stop = True
thread.join()
thread4.join()


