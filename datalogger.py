"""
Created on 12.01.2018

@author: Stefan Rossmann
"""
import csv
import logging
from logging.handlers import RotatingFileHandler
import config as cfg
import traceback
import datetime
import os, errno
import database
import mail
from logging import StreamHandler

try:
    os.makedirs('unitdatabase')
except OSError as e:
    pass
    #if e.errno != errno.EEXIST:
    #    raise

my_logger3 = logging.getLogger('MyMQTTPayloadLogger')
my_logger3.setLevel(logging.DEBUG)
my_logger3.propagate = False

# Add the log message handler to the logger
packagedir = os.path.dirname(
    os.path.abspath(__file__))  # get the Package directory, from there we get the subdirectoties
directory = os.path.join(packagedir, 'unitdatabase')  # Subdirectory

# Add the log message handler for the Payload logger
filename = os.path.join(directory, 'serveruploadMQTTlogdata.txt')

handler3 = logging.handlers.RotatingFileHandler(
    filename, maxBytes=20000000, backupCount=5)
formatter3 = logging.Formatter("%(asctime)s;%(message)s",
                               "%Y-%m-%d %H:%M:%S")
handler3.setFormatter(formatter3)
my_logger3.addHandler(handler3)


def logMQTTRegisterData(dataToWrite):
    """
    Stores the Payload send to Thingsboard via MQTT to the cloud
    :param Payload to store in file:
    :return:
    """
    try:
        # Set up a specific logger with our desired output level

        my_logger3.debug(dataToWrite)

        # print (dataToWrite)

    except:
        pass


def registerLogFileCSV():
    """
    gurke
    """
    try:
        config = cfg.Config.getConfig()
        maxfilesize = 1073741824 / 2  # 1 Gigabyte = 1073741824 bytes

        currentDateTime = datetime.datetime.now()
        currentDay = currentDateTime.day
        currentMonth = currentDateTime.month
        currentYear = currentDateTime.year

        yestardayDateTime = (datetime.datetime.now() - datetime.timedelta(days=1))
        yesterdayDay = yestardayDateTime.day
        yesterdayMonth = yestardayDateTime.month
        yestardayYear = yestardayDateTime.year

        packagedir = os.path.dirname(
            os.path.abspath(__file__))  # get the Package directory, from there we get the subdirectoties
        directory = os.path.join(packagedir, 'unitdatabase')
        directory = os.path.join(directory, 'csv')  # Subdirectory /csv
        filename = os.path.join(directory,
                                'registerlogdata' + str(currentYear) + str(currentMonth) + str(currentDay) + '.csv')
        # --------------------------Check path, create the path if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        if (__getDirSize(directory) > maxfilesize):  # Delete Files if max. size of directory is reached
            __deleteOldestFile(directory)

        # --------------------------Check if file exists, else create and write header
        if (not os.path.isfile(filename)):
            with open(filename, 'w') as csvfile:
                fieldnames = list()
                fieldnames.append('timestamp')
                for s in config['readorders']:
                    readorder = dict(s)
                    if ('logmodbusdata' in readorder):
                        if (readorder['logmodbusdata']):
                            fieldnames.append(readorder['name'])

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
                writer.writeheader()

            # ----------------------------------------------Check if yestardays File exist, if yes send if via mail start
            yestardayfilename = os.path.join(directory,
                                             'registerlogdata' + str(yestardayYear) + str(yesterdayMonth) + str(
                                                 yesterdayDay) + '.csv')
            if (os.path.isfile(yestardayfilename)):
                if config.get('emailregisterlogfiles', '') != '':
                    mail.send_mail(config['emailregisterlogfiles'], yestardayfilename)
            # ----------------------------------------------Check if yestardays File exist, if yes send if via mail end

        cfg.Config.getInstance().registerlogfilecounter = cfg.Config.getInstance().registerlogfilecounter + 1

        if (cfg.Config.getInstance().registerlogfilecounter >= config['loggingmultiplier']):
            cfg.Config.getInstance().registerlogfilecounter = 0
            with open(filename, 'a') as csvfile:
                writerows = dict()
                fieldnames = list()
                fieldnames.append('timestamp')
                writerows['timestamp'] = ('{0:%Y-%m-%dT%H:%M:%SZ}'.format(datetime.datetime.now()))
                for s in config['readorders']:
                    readorder = dict(s)
                    db_conn = database.connect(config.get('databasename', 'eh.db'))
                    database.add_daily_value(db_conn, readorder.get('serverid', list([1]))[0], readorder['name'],
                                             readorder.get('value', 0))
                    if ('logmodbusdata' in readorder):
                        if (readorder['logmodbusdata']):
                            fieldnames.append(readorder['name'])
                            if (
                                    'value' in readorder):  # We only write 65535 into the CSV if the value does not exist. Most of the case there is
                                # is a Register without readOrder
                                writerows[readorder['name']] = readorder['value']
                                db_conn = database.connect(config.get('databasename', 'eh.db'))
                                database.add_daily_value(db_conn, readorder.get('serverid', list([1]))[0],
                                                         readorder['name'], readorder['value'])
                            else:
                                writerows[readorder['name']] = 65535
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
                writer.writerow(writerows)

    except Exception as e:
        logging.error('Exception in writing CSV-Logdata: ' + str(traceback.format_exc()))


def __getDirSize(path):
    """
    gurke
    :param path: gurke
    :return: total size of gurke
    """
    totalsize = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            totalsize += os.path.getsize(fp)
    return totalsize


def __deleteOldestFile(path):
    """
    deletes the oldest files
    :param path: gurke
    """
    list_of_files = os.listdir(path)

    list_of_files.sort()
    os.remove((path + "//" + list_of_files[0]))
    logging.info('Folder size exceeded of CSV-Logdata Deleted File: ' + path + "//" + list_of_files[0])


class MailHandler(StreamHandler):
    """ classdocs """
    def __init__(self):
        """ gurke """
        StreamHandler.__init__(self)
        self.lastdtsend = None

    def emit(self, record):
        """ gurke """
        if self.lastdtsend == None:
            self.lastdtsend = datetime.datetime(year=1970, month=1, day=1)
        if (datetime.datetime.now() > (self.lastdtsend + datetime.timedelta(hours=1))):
            config = cfg.Config.getConfig()
            msg = self.format(record)
            if config.get('emailerrornotification', '') != '':
                mail.send_mail(config['emailerrornotification'], body='Gateway error: {0}'.format(msg))
            self.lastdtsend = datetime.datetime.now()
