#!/usr/bin/env python
"""
Created on 28.10.2020

@author: Stefan Rossmann
"""

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
import datalogger
import logic
import Evergi.DT_EVERGi
import Evergi.EVERGi_LC.EM
import Evergi.EVERGi_LC.EVCS
import Evergi.EVERGi_LC.LoadBalancing
import Evergi.EVERGi_LC.MQTT
from Evergi.DT_EVERGi import DT_EVERGI
import database

DT_EVERGI.getInstance()
db_conn = database.connect("eh.db", '')
database.create_tables(db_conn)
time.sleep(1)
# ------------------------- Initiate logging Start
packagedir = os.path.dirname(
    os.path.abspath(__file__))  # get the Package directory, from there we get the subdirectoties
directory = os.path.join(packagedir, 'unitdatabase')  # Subdirectory

try:
    os.makedirs(directory)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise


filename = os.path.join(directory, 'logdata.txt')
logging.getLogger().setLevel(logging.INFO)
# Add the log message handler to the logger
handler1 = logging.handlers.RotatingFileHandler(
    filename, maxBytes=2000000, backupCount=5)
logging.getLogger().addHandler(handler1)
formatter1 = logging.Formatter("%(asctime)s;%(message)s",
                               "%Y-%m-%d %H:%M:%S")
handler1.setFormatter(formatter1)
console = logging.StreamHandler()
logging.getLogger().addHandler(console)

handler2 = datalogger.MailHandler()
handler2.setLevel(logging.ERROR)
logging.getLogger().addHandler(handler2)
handler2.setFormatter(formatter1)

logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('asyncua').setLevel(logging.CRITICAL)
# ------------------------- Initiate logging End



webserver_thread = threading.Thread(target=webserver.start, args=())
webserver_thread.start()

em_thread = threading.Thread(target=Evergi.EVERGi_LC.EM.read_em, args=())
em_thread.start()

evcs_thread = threading.Thread(target=Evergi.EVERGi_LC.EVCS.read_evcs, args=())
evcs_thread.start()

mqtt_thread = threading.Thread(target=Evergi.EVERGi_LC.MQTT.send_mqtt, args=())
mqtt_thread.start()
while 1:
    try:
        time.sleep(2)

    except KeyboardInterrupt:
        logging.info('Thread Main stopped ')
        break
    except Exception as e:
        logging.error('Exception in Main-Loop: ' + str(traceback.format_exc()))
        time.sleep(0.5)

webserver.stop = True
em_thread.join()
mqtt_thread.join()
