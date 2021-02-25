from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, send_from_directory, send_file
import os
import json
import time

import imghdr
from werkzeug.utils import secure_filename

#from tornado.platform import asyncio
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.web
import config as cfg
import ModbusClient
import tornado
from collections import OrderedDict
import datalogger
import osinterface
import re

stopprocess = False
import traceback
import subprocess
import serial
import calendar
import asyncio
import database
import logging

app = Flask(__name__)
config = OrderedDict()




@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.route('/fileuploads')
def fileuploads():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('fileupload.html', files=files, admin = loginadmin)

@app.route('/fileuploads', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or filename != 'config.json':
            return "Invalid file, please choose a valid config.json", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return '', 204

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

@app.route('/download')
def downloadFile ():
    path = "configuration/config.json"
    return send_file(path, as_attachment=True)
#----------------------This is the Main Page
@app.route('/index', methods=['GET', 'POST'])
def index():
    pythonswversion = "Can't read Python Version"
    webserverversion = "Can't read Webserver Version"


    config = cfg.Config.getConfig()

    if (request.method == 'POST') & (request.path == '/index') :
        cfg.Config.getInstance().eventcounter = 0;
    logging.info('Webserver request to open page "index"')

    exception = ''
    modemstatus = dict()
    deviceinformations = dict()



    #------------------------------ Read Gateway CPU Data Start ----------------------
    try:
        deviceinformations = osinterface.readdeviceinformations()
        cfg.Config.getInstance().read_version()
    except Exception:
        logging.error('Webserver: Unable to Read Deviceinformations from device: ' + str(traceback.format_exc()))

    pythonswversion = cfg.Config.getInstance().pythonswversion
    webserverversion = cfg.Config.getInstance().webserverversion
    gwarchitecture = deviceinformations['architecture']
    gwmodelname = deviceinformations['modelname']
    gwcpumaxmhz = deviceinformations['cpumaxmhz']
    gwcpuminmhz = deviceinformations['cpuminmhz']
    # ------------------------------ Read Gateway CPU Data End ----------------------

    # ------------------------------ Read Wlan0 config ------------------------------
    wlan0status = osinterface.readwlan0status()
    wlan0ipaddress = wlan0status['ipaddress']
    wlan0mask = wlan0status['mask']
    # ------------------------------ Read Wlan0 config ------------------------------

    # ------------------------------ Read eth0 config ------------------------------
    eth0status = osinterface.readeth0status()
    eth0ipaddress = eth0status['ipaddress']
    eth0mask = eth0status['mask']
    # ------------------------------ Read eth0 config ------------------------------

    try:
        eventcounter = cfg.Config.getInstance().eventcounter
    except:
        eventcounter = 'Error'






    parameter = {
                 'eventcounter': str(eventcounter),
                 'pythonswversion': str(pythonswversion),
                 'webserverversion': str(webserverversion),
                 'gwarchitecture': str(gwarchitecture),
                 'gwmodelname': str(gwmodelname),
                 'gwcpumaxmhz': str(gwcpumaxmhz),
                 'gwcpuminmhz': str(gwcpuminmhz),
                 'wlan0ipaddress': str(wlan0ipaddress),
                 'wlan0mask': str(wlan0mask),
                 'eth0ipaddress': str(eth0ipaddress),
                'eth0mask': str(eth0mask)
                }
    if (logindistributor or loginadmin):
        return render_template('index.html', parameter=parameter, admin = loginadmin)
    else:
        return do_admin_login()



conectivityparameter = {}
@app.route('/connectivity', methods=['GET', 'POST'])
def index2():
    global conectivityparameter
    if (request.method == 'POST'):
        try:
            if not 'networkID' in request.form:
                osinterface.console('zerotier-cli leave {0}'.format(conectivityparameter['vpnnetworkid']))
            else:
                osinterface.console('zerotier-cli join {0}'.format(request.form['networkID']))
                time.sleep(5)
        except Exception:
            logging.error('Webserver: Unable to Leave or Join Zerotier Network: ' + str(traceback.format_exc()))
    config = cfg.Config.getInstance()


    # ------------------------------ Read Wlan0 config ------------------------------
    wlan0status = osinterface.readwlan0status()
    wlan0ipaddress = wlan0status['ipaddress']
    wlan0mask = wlan0status['mask']
    # ------------------------------ Read Wlan0 config ------------------------------

    # ------------------------------ Read eth0 config ------------------------------
    eth0status = osinterface.readeth0status()
    eth0ipaddress = eth0status['ipaddress']
    eth0mask = eth0status['mask']
    # ------------------------------ Read eth0 config ------------------------------



#    try:
#        phonenumber = osinterface.readphonenumber()
#    except Exception as e:
#        datalogger.logData('Webserver: Unable to Read Phonenumber from device: ' + str(traceback.format_exc()))

    try:
        vpnstatus = osinterface.readvpnstatus()
    except Exception as e:
        logging.error('Webserver: Unable to Read vpnstatus from device: ' + str(traceback.format_exc()))



    conectivityparameter = {

                             'vpnipaddress': vpnstatus['ipaddress'],
                             'vpnsubnetmask': vpnstatus['mask'],
                             'vpnconnected': vpnstatus['connected'],
                             'vpnnodeid': vpnstatus['nodeid'],
                             'vpnversion': vpnstatus['version'],
                             'vpnnetworkid': vpnstatus['networkid'],
                             'vpnnetworkname': vpnstatus['networkname'],
                            'wlan0ipaddress': str(wlan0ipaddress),
                            'wlan0mask': str(wlan0mask),
                            'eth0ipaddress': str(eth0ipaddress),
                            'eth0mask': str(eth0mask)
                             }
    if (logindistributor or loginadmin):
        return render_template('connectivity.html', parameter=conectivityparameter, admin = loginadmin)
    else:
        return do_admin_login()



@app.route('/mobilesendpin',methods = ['GET', 'POST'])
def mobilesendpin():
   config = cfg.Config.getInstance()
   global conectivityparameter
   if ('sendpinresultfailed' in conectivityparameter):
       del conectivityparameter['sendpinresultfailed']
   if ('sendpinresultsuccess' in conectivityparameter):
       del conectivityparameter['sendpinresultsuccess']
   if request.method == 'POST':
       config.Pin = request.form['pin']

       try:
            sendpinresult = osinterface.console("mmcli -i 0 --pin="+config.Pin)
            config.StoreSettings()
            conectivityparameter['sendpinresultsuccess'] = sendpinresult
       except Exception as e:
            sendpinresult =  str(e)
            conectivityparameter['sendpinresultfailed'] = sendpinresult
   return render_template('connectivity.html', parameter=conectivityparameter, admin = loginadmin)


@app.route('/mobileatcommand',methods = ['GET', 'POST'])
def mobilesendat():
   global conectivityparameter
   if ('sendatresultfailed' in conectivityparameter):
       del conectivityparameter['sendatresultfailed']
   if ('sendatresultsuccess' in conectivityparameter):
       del conectivityparameter['sendatresultsuccess']
   if request.method == 'POST':
        atcommand = request.form['atcommand']
        if (atcommand == ''):
            conectivityparameter['sendatresultfailed'] = 'Please enter AT-command'
        else:
            try:
                answer = osinterface.sendatcommand(atcommand)

                conectivityparameter['sendatresultsuccess'] = 'AT-command successfully send'
                conectivityparameter['sendatanswer']=str(answer)
            except Exception as e:
                if ('sendatresultfailed' in conectivityparameter):
                    del conectivityparameter['sendatresultfailed']
                if ('sendatresultsuccess' in conectivityparameter):
                    del conectivityparameter['sendatresultsuccess']
                logging.error('Webserver: failed to send AT-command ' + str(traceback.format_exc()))
                conectivityparameter['sendatresultfailed'] = 'Failed to send AT-command'


   return render_template('connectivity.html', parameter=conectivityparameter, admin = loginadmin)

@app.route('/mobilesetapn',methods = ['GET', 'POST'])
def mobilesetapn():
   global conectivityparameter
   if ('sentapnfailed' in conectivityparameter):
       del conectivityparameter['sentapnfailed']
   if ('sentapnsuccess' in conectivityparameter):
       del conectivityparameter['sentapnsuccess']
   if request.method == 'POST':
        apn = request.form['apn']
        if (apn == ''):
            conectivityparameter['sentapnfailed'] = 'Please enter new APN'
        else:
            try:
                osinterface.changeapn(str(apn))
                conectivityparameter['sentapnsuccess'] = 'New APN successfully accepted'
            except Exception as e:
                conectivityparameter['sentapnfailed'] = str(e)

   return render_template('connectivity.html', parameter=conectivityparameter, admin = loginadmin)

@app.route('/mobilereset',methods = ['GET', 'POST'])
def mobilereset():
   global conectivityparameter
   if ('resetresultfailed' in conectivityparameter):
       del conectivityparameter['resetresultfailed']
   if ('resetresultsuccess' in conectivityparameter):
       del conectivityparameter['resetresultsuccess']
   if request.method == 'POST':
       try:
           osinterface.console('mmcli -m 0 --simple-disconnect')
           time.sleep(0.5)
           osinterface.console('ip link set ppp0 up')
       except Exception as e:
           logging.error('Webserver : Unable to reset moble connection ' + str(e))

   return render_template('connectivity.html', parameter=conectivityparameter, admin = loginadmin)

@app.route('/gatewayconfiguration')
def index3():
    with open('configuration/config.json') as json_data:
        cfg.Config.getInstance().configmodel = json.load(json_data)
    for readorder in cfg.Config.getInstance().configmodel['readorders']:
        for device in cfg.Config.getInstance().configmodel['devices']:
            if readorder['transportid'] == device['transportid']:
                if device.get('type', 'Modbus') == 'Bacnet':
                    readorder['fieldbustype'] = 'Bacnet'
                elif device.get('type', 'Modbus') == 'EthernetIP':
                    readorder['fieldbustype'] = 'EthernetIP'
                else:
                    readorder['fieldbustype'] = 'Modbus'
    if (loginadmin):
        return render_template('gatewayconfiguration.html', parameter=cfg.Config.getInstance().configmodel, admin = loginadmin)
    else:
        return do_admin_login()


@app.route('/modbus')
def index4():
    parameter = {}
    readparameter = {}
    response = dict()
    if (loginadmin):
        return render_template('modbus.html', parameter=parameter, parameter2=readparameter, response=response, admin = loginadmin)
    else:
        return do_admin_login()

@app.route('/latestreading')
def latestreadings():
    parameter = {}
    parameter['latestreadings'] = list()
    config = cfg.Config.getConfig()
    db_conn = database.connect("eh.db")
    for s in config['readorders']:
        readOrder = dict(s)
        reading = {}

        if ('nextwakeup' in readOrder) &('registerintervaltime' in readOrder) & ('latestreading' in readOrder):
            reading['timestamp'] = readOrder['nextwakeup'] + readOrder['registerintervaltime']
            reading['value'] = readOrder['latestreading']
            reading['tagname'] = readOrder['name']

            reading['history'] = database.get_daily_values(db_conn, reading['tagname'])
            if (reading['value'] != 65535):
                parameter['latestreadings'].append(reading)

    if (logindistributor or loginadmin):
        return render_template('latestreadings.html', parameter=parameter, admin = loginadmin)
    else:
        return do_admin_login()

showcontentlogfile = 1000;
@app.route('/showlog', methods = ['GET', 'POST'])
def index5():
    global showcontentlogfile
    showcontentlogfile = 1000;
    packagedir = os.path.dirname(
        os.path.abspath(__file__))  # get the Package directory, from there we get the subdirectoties
    directory = os.path.join(packagedir, 'unitdatabase')  # Subdirectory
    logfilename = os.path.join(directory, 'logdata.txt')

    if request.method == 'POST':            #The Post commes from the selection which content to show
        content = ""
    try:
        with open(logfilename, "r") as f:
            content = f.read()
            contentsplitline = content.splitlines()
            content = ""
            if (showcontentlogfile > len(contentsplitline)):
                showcontentlogfile = len(contentsplitline)
            for i in range(0, showcontentlogfile):
                content = content + str(contentsplitline[len(contentsplitline)-i-1]) + '\n'
    except Exception:
        logging.error('Webserver couldnt open logfile: ' + str(traceback.format_exc()))
    return render_template('showlog.html', content=content, admin = loginadmin)

@app.route('/showmore',methods = ['GET', 'POST'])
def showmore():
   global showcontentlogfile
   packagedir = os.path.dirname(
   os.path.abspath(__file__))  # get the Package directory, from there we get the subdirectoties
   directory = os.path.join(packagedir, 'unitdatabase')  # Subdirectory
   logfilename = os.path.join(directory, 'logdata.txt')


   if request.method == 'POST':
       content = ""
       try:
           showcontentlogfile = showcontentlogfile +1000
           with open(logfilename, "r") as f:
               content = f.read()
               contentsplitline = content.splitlines()
               content = ""
               if (showcontentlogfile > len(contentsplitline)):
                   showcontentlogfile = len(contentsplitline)
               for i in range(0, showcontentlogfile):
                   content = content + str(contentsplitline[len(contentsplitline) - i - 1]) + '\n'
       except Exception:
           logging.error('Webserver couldnt open logfile: ' + str(traceback.format_exc()))

   return render_template('showlog.html', content=content, admin = loginadmin)


loginadmin = False
logindistributor = False
@app.route('/', methods=['GET', 'POST'])
def do_admin_login():
    global loginadmin
    global logindistributor
    if request.method == 'POST':

        loginadmin = False
        logindistributor = False


        if request.form['password'] == '123456' and request.form['username'] == 'wiseenergy':
            loginadmin = True
            logindistributor = False
            return index()
        elif request.form['password'] == '123456' and request.form['username'] == 'admin':
            loginadmin = False
            logindistributor = True
            return index()
        else:
            return render_template('login.html', admin=loginadmin)

    if request.method == 'GET':
        return render_template('login.html', admin=loginadmin)




@app.route('/configure',methods = ['GET', 'POST'])
def configure():
   parameter = {}
   if request.method == 'POST':
        parameter = request.form['parameter']
        try:
            value = int(request.form['value'])
        except ValueError:
            value=''
        if (parameter != '' and value != ''):
            parameter = {'success': 'Parameter: ' + parameter + ' Value: ' + str(value) +' sent to the Device'}
        elif (value == ''):
            parameter = {'failed' : 'Please enter a valid value'}
   return render_template('gatewayconfiguration.html', parameter=parameter, admin = loginadmin)



@app.route('/modbussendalldata',methods = ['GET', 'POST'])
def modbussendalldata():
   readparameter = {}
   response = dict()
   parameter = {}
   config = cfg.Config.getInstance()

   if request.method == 'POST':
       config.lock.acquire()
       config.uploadalldata = True;
       config.lock.release()
       time.sleep(3)
       if (config.uploadalldata == False):
            parameter['modbusuploadregisterssuccess'] = 'Success'
       else:
            parameter['modbusuploadregistersfailed'] = 'Parameterupload failed, see Logfile for more informations'


   return render_template('modbus.html', parameter=parameter, parameter2=readparameter, response=response, admin = loginadmin)

@app.route('/modbuswriteform',methods = ['GET', 'POST'])
def modbuswrite():
   readparameter = {}
   response = dict()
   parameter = {}
   if request.method == 'POST':
        readparameter = {}
        response = dict()
        parameter = {}
        try:
            register = int(request.form['register'])
            value = int(request.form['value'])
            if request.form['transportid'] == "":
                transportid = 1
            else:
                transportid = int(request.form['transportid'])
        except ValueError:
            value=''
            register=''
        if (register != '' and value != ''):

            try:
                logging.debug('Webserver: Request to Write Holding Register: ' + request.form['register'] + ', value: ' + request.form['value'])
                config = cfg.Config.getConfig()
                cfg.Config.getInstance().lock.acquire()

                if ('serialPort' in config['devices'][transportid - 1]):
                    modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['serialPort']))
                    modbusClient.Parity = config['devices'][transportid - 1]['parity']
                    modbusClient.Baudrate = config['devices'][transportid - 1]['baudrate']
                    modbusClient.Stopbits = config['devices'][transportid - 1]['stopbits']
                if ('ipaddress' in config['devices'][transportid - 1]):
                    if (not ('port' in config['devices'][transportid - 1])):
                        config['devices'][transportid - 1]['port'] = 502
                    modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['ipaddress']),
                                                             int(config['devices'][transportid - 1]['port']))
                if ('unitidentifier' in config['devices'][transportid - 1]):
                    modbusClient.UnitIdentifier = config['devices'][transportid - 1]['unitidentifier']

                modbusClient.Timeout = 5
                modbusClient.connect()
                modbusClient.write_single_register(register-1,value)
                parameter = {'success': 'Value: ' + str(value) + ' successfully written to Holding Register: ' + str(register)}
            except Exception as e:
                parameter = {'failed': 'Unable to write value to Slave: '+ str(e)}
                logging.error('Webserver: Unable to write Registers to Modbus Slave: ' + str(e))
            finally:
                modbusClient.close()
                cfg.Config.getInstance().lock.release()
        elif (value == ''):
            parameter = {'failed' : 'Please enter a valid value'}
            logging.error('Webserver: Unable to write Registers to Modbus Slave, invalid value')
        elif (register == ''):
            parameter = {'failed' : 'Please enter a valid Register'}
            logging.error('Webserver: Unable to write Registers to Modbus Slave, invalid register')
   return render_template('modbus.html', parameter=parameter, parameter2=readparameter, response=response, admin = loginadmin)

@app.route('/modbusreadform',methods = ['GET', 'POST'])
def modbusread():
   readparameter = {}
   response = dict()
   parameter = {}
   if request.method == 'POST':
        parameter = {}
        response = OrderedDict()

        try:
            logging.debug('Webserver: Request to Read '+request.form['dataarea'] +  ', starting Value:' + request.form['register'] + ', quantity: ' +request.form['quantity'])
            register = int(request.form['register'])
            quantity = int(request.form['quantity'])
            datatype = request.form['dataarea']
            if request.form['transportid'] == "":
                transportid = 1
            else:
                transportid = int(request.form['transportid'])
        except ValueError:
            register=''
            quantity=''
        if (register != '' and quantity != ''):
            try:
                config = cfg.Config.getConfig()
                cfg.Config.getInstance().lock.acquire()
                if ('serialPort' in config['devices'][transportid - 1]):
                    modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['serialPort']))
                    modbusClient.Parity = config['devices'][transportid - 1]['parity']
                    modbusClient.Baudrate = config['devices'][transportid - 1]['baudrate']
                    modbusClient.Stopbits = config['devices'][transportid - 1]['stopbits']
                if ('ipaddress' in config['devices'][transportid - 1]):
                    if (not ('port' in config['devices'][transportid - 1])):
                        config['devices'][transportid - 1]['port'] = 502
                    modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['ipaddress']),
                                                             int(config['devices'][transportid - 1]['port']))
                if ('unitidentifier' in config['devices'][transportid - 1]):
                    modbusClient.UnitIdentifier = config['devices'][transportid - 1]['unitidentifier']
                modbusClient.Timeout = 5
                modbusClient.connect()
                if (datatype == 'holdingregisters'):
                    registerValues = modbusClient.read_holdingregisters(register-1, quantity)
                else:
                    registerValues = modbusClient.read_inputregisters(register-1, quantity)
                for i in range(0, len(registerValues)):
                    response[str(register+i)] = str(registerValues[i])
                readparameter = {'success': 'Register successfully read from Modbus Slave'}

            except Exception as e:
                readparameter = {'failed': 'Unable to Read values from Slave: '+ str(e) }
                logging.error('Webserver: Unable to Read Registers from Modbus Slave: ' + str(traceback.format_exc()))
            finally:
                modbusClient.close()
                cfg.Config.getInstance().lock.release()

        elif (quantity == ''):
            readparameter = {'failed' : 'Please enter a quantity'}
            logging.error('Webserver: Unable to Read Registers from Modbus Slave, invalid Quantity')
        elif (register == ''):
            readparameter = {'failed' : 'Please enter a valid Register'}
            logging.error('Webserver: Unable to Read Registers from Modbus Slave, invalid Register value')
   return render_template('modbus.html', parameter=parameter, parameter2=readparameter, response=response, admin = loginadmin)


@app.route('/modbuscheckconnectivity',methods = ['GET', 'POST'])
def modbuscheckconnectivity():
   readparameter = {}
   response = dict()
   parameter = {}
   config = cfg.Config.getConfig()
   if request.method == 'POST':
        if ('serialPort' in config['devices'][0]):
            modbusClient = ModbusClient.ModbusClient(str(config['devices'][0]['serialPort']))
        if ('ipaddress' in config['devices'][0]):
            if (not ('port' in config['devices'][0])):
                config['devices'][0]['port'] = 502
            modbusClient = ModbusClient.ModbusClient(str(config['devices'][0]['ipaddress']),config['devices'][0]['port'])

        try:
            if request.form['transportid'] == "":
                transportid = 1
            else:
                transportid = int(request.form['transportid'])
            cfg.Config.getInstance().lock.acquire()


            if ('serialPort' in config['devices'][transportid - 1]):
                modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['serialPort']))
                modbusClient.Parity = config['devices'][transportid - 1]['parity']
                modbusClient.Baudrate = config['devices'][transportid - 1]['baudrate']
                modbusClient.Stopbits = config['devices'][transportid - 1]['stopbits']
            if ('ipaddress' in config['devices'][transportid - 1]):
                if (not ('port' in config['devices'][transportid - 1])):
                    config.Devices[transportid - 1]['port'] = 502
                modbusClient = ModbusClient.ModbusClient(str(config['devices'][transportid - 1]['ipaddress']),
                                                         int(config['devices'][transportid - 1]['port']))
            if ('unitidentifier' in config['devices'][transportid - 1]):
                modbusClient.UnitIdentifier = config['devices'][transportid - 1]['unitidentifier']

            modbusClient.Timeout = 5
            modbusClient.connect()
            modbusClient.read_inputregisters(214,1)
            parameter['modbuscheckconnectivitysuccess'] = 'Connection available'
        except Exception as e:
            parameter['modbuscheckconnectivityfailed'] = str(e)
        finally:
            if (modbusClient.is_connected()):
                modbusClient.close()
            cfg.Config.getInstance().lock.release()
   return render_template('modbus.html', parameter=parameter, parameter2=readparameter, response=response, admin = loginadmin)


@app.route('/configurationform',methods = ['GET', 'POST'])
def configform():
   if request.method == 'POST':
        try:
            configuration = request.form
            config = cfg.Config.getConfig()

            config['basicinterval'] = float(configuration['basicinterval'])
            config['readinterval'] = float(configuration['readinterval'])
            config['loglevel'] = (configuration['loglevel'])
            config['emailregisterlogfiles'] = (configuration['emailregisterlogfiles'])
            config['emailerrornotification'] = (configuration['emailerrornotification'])
            config['emailfromaddress'] = (configuration['emailfromaddress'])
            config['smtphost'] = (configuration['smtphost'])
            config['smtpusername'] = (configuration['smtpusername'])
            config['smtppassword'] = (configuration['smtppassword'])
            config['smtpport'] = int(configuration['smtpport'])
            config['smtpenabletls'] = True if configuration['smtpenabletls'].lower() == 'true' else False
            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)
   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)




@app.route('/configurationformmqttservers',methods = ['GET', 'POST'])
def configformmqttservers():
   if request.method == 'POST':
        try:
            configuration = request.form
            config = cfg.Config.getConfig()
            for mqttbroker in config['mqttbroker']:
                for key, value in mqttbroker.items():
                    if (key == "serverid"):
                        mqttbroker[key] = int(configuration['serverid'+str(mqttbroker['serverid'])+'_'+key])
                    else:
                        mqttbroker[key] = configuration['serverid' + str(mqttbroker['serverid']) + '_' + key]

            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)
   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)

@app.route('/configurationformdevices',methods = ['GET', 'POST'])
def configformdevices():
   if request.method == 'POST':
        try:
            configuration = request.form
            config = cfg.Config.getConfig()
            for device in config['devices']:
                for key, value in device.items():
                    if (key == "parity") or (key == "baudrate") or (key == "databits") or (key == "transportid") or (key == "unitidentifier") or (key == "stopbits"):
                        device[key] = int(configuration['transportid'+str(device['transportid'])+'_'+key])
                    else:
                        device[key] = configuration['transportid' + str(device['transportid']) + '_' + key]
            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)

   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)

@app.route('/adddevice',methods = ['GET', 'POST'])
def adddevice():
   if request.method == 'POST':
        try:
            configuration = request.form
            config = cfg.Config.getConfig()
            device = dict()
            device['transportid'] = int(configuration['newDeviceTransportId'])
            if (configuration['newDeviceFieldbus'] == 'ModbusRTU') or (configuration['newDeviceFieldbus'] == 'ModbusTCP'):
                device['unitidentifier'] = int(configuration['newDeviceUnitidentifier'])
                device['type'] = 'Modbus'
                device['identifier'] = configuration['newDeviceIdentifier']
            elif configuration['newDeviceFieldbus'] == 'Bacnet':
                device['type'] = 'Bacnet'
            elif configuration['newDeviceFieldbus'] == 'EthernetIP':
                device['type'] = 'EthernetIP'
                device['messagingtype'] = configuration['newDeviceCipMessagingType']
                if device['messagingtype'] == 'Implicit':
                    device['packetrate_to'] = configuration['newDeviceCipRequestedPacketRateTO']
                    device['packetrate_ot'] = configuration['newDeviceCipRequestedPacketRateOT']
                    device['instanceid_to'] = configuration['newDeviceCipInstanceIDTO']
                    device['instanceid_ot'] = configuration['newDeviceCipInstanceIDOT']
                    device['length_to'] = configuration['newDeviceCipLengthTO']
                    device['length_ot'] = configuration['newDeviceCipLengthOT']
                    device['realtimeformat_to'] = configuration['newDeviceCipRealTimeFormatTO']
                    device['realtimeformat_ot'] = configuration['newDeviceCipRealTimeFormatOT']
                    device['connectiontype_to'] = configuration['newDeviceCipConnectionTypeTO']
                    device['connectiontype_ot'] = configuration['newDeviceCipConnectionTypeOT']


            device['uid'] = configuration['newDeviceUID']
            if configuration['newDeviceFieldbus'] == 'ModbusRTU':
                device['baudrate'] = int(configuration['newDeviceBaudrate'])
                device['databits'] = int(configuration['newDeviceDatabits'])
                device['stopbits'] = int(configuration['newDeviceStopbits'])
                device['parity'] = int(configuration['newDeviceparity'])
                device['serialPort'] = configuration['newDeviceSerialPort']
            else:
                device['ipaddress'] = configuration['newDeviceIpAddress']
                device['port'] = int(configuration['newDevicePort'])

            config['devices'].append(device)
            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)

   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)

@app.route('/addreadorder',methods = ['GET', 'POST'])
def addreadorder():
   if request.method == 'POST':
        try:
            configuration = request.form
            config = cfg.Config.getConfig()
            read_order = dict()
            read_order['name'] = configuration['newReadOrderName']
            read_order['active'] = True if configuration['newReadOrderEnableUpload'].lower() == 'true' else False
            read_order['transportid'] = int(configuration['newReadOrderTransportID'])
            server_ids_str = configuration['newReadOrderServerID']
            #Extract number from string
            server_ids = list()
            for s in re.findall(r'\d+', server_ids_str):
                server_ids.append(int(s))

            read_order['serverid'] = server_ids
            read_order['dataarea'] = configuration['newReadOrderDataArea']
            read_order['address'] = int(configuration['newReadOrderAddress'])
            read_order['bits'] = int(configuration['newReadOrderBits'])
            read_order['registerintervaltime'] = int(configuration['newReadOrderRegisterintervaltime'])
            read_order['absolutethreshold'] = float(configuration['newReadOrderAbsoluteThreshold'])
            read_order['relativethreshold'] = float(configuration['newReadOrderRelativeThreshold'])
            read_order['signed'] = True if configuration['newReadOrderSigned'].lower() == 'true' else False
            read_order['multiplefactor'] = float(configuration['newReadOrderMultiplefactor'])
            read_order['target'] = configuration['newReadOrderTarget']
            read_order['classid'] = configuration['newReadOrderCIPClassID']
            read_order['instanceid'] = configuration['newReadOrderCIPInstanceID']
            read_order['attributeid'] = configuration['newReadOrderCIPAttributeID']
            read_order['mask'] = configuration['newReadOrderCIPMask']
            read_order['startingbyte'] = configuration['newReadOrderCIPStartingByte']
            read_order['numberofbytes'] = configuration['newReadOrderCIPNumberOfBytes']

            config['readorders'].append(read_order)
            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)
   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)

@app.route('/addmodbuscommand',methods = ['GET', 'POST'])
def addmodbuscommand():
   if request.method == 'POST':
        try:
            configuration = request.form
            config = cfg.Config.getConfig()
            modbus_command = dict()
            modbus_command['transportid'] = int(configuration['newModbusCommandTransportID'])
            modbus_command['functioncode'] = configuration['newModbusCommandFunctioncode']
            modbus_command['startingaddress'] = int(configuration['newModbusCommandStartingAddress'])
            modbus_command['quantity'] = int(configuration['newModbusCommandQuantity'])
            config['modbuscommand'].append(modbus_command)
            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)
   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)


@app.route('/configurationformmodbuscommand',methods = ['GET', 'POST'])
def configformmodbuscommand():
   if request.method == 'POST':
        try:
            config = cfg.Config.getConfig()
            configuration = request.form
            selectedindex =  int(configuration['modbuscommands'])-1

            config['modbuscommand'][selectedindex]['functioncode'] = configuration['functioncode']
            config['modbuscommand'][selectedindex]['quantity'] = int(configuration['quantity'])
            config['modbuscommand'][selectedindex]['startingaddress'] = int(configuration['startingaddress'])
            cfg.Config.getInstance().write_config()
        except ValueError:
            pass
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)
   return redirect("/gatewayconfiguration", code=302)
   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)

@app.route('/configurationformreadorders',methods = ['GET', 'POST'])
def configformreadorders():
   if request.method == 'POST':
        try:
            config = cfg.Config.getConfig()
            configuration = request.form
            for s in range(0, len(config['readorders'])):
            #for s in config.ReadOrders:
                #ReadOrder = dict(s)
                name = (config['readorders'][s]['name'])
                if (name == configuration['name']):

                    config['readorders'][s]['address'] = int(configuration['address'])
                    if ('transportid' in configuration):
                        if configuration['transportid'] != "":
                            config['readorders'][s]['transportid'] = int(configuration['transportid'])
                    if ('registerintervaltime' in configuration):
                        if configuration['registerintervaltime'] != "":
                            config['readorders'][s]['registerintervaltime'] = int(configuration['registerintervaltime'])
                    if ('absolutethreshold' in configuration):
                        if configuration['absolutethreshold'] != "":
                            config['readorders'][s]['absolutethreshold'] = int(configuration['absolutethreshold'])
                    if ('relativethreshold' in configuration):
                        if configuration['relativethreshold'] != "":
                            config['readorders'][s]['relativethreshold'] = int(configuration['relativethreshold'])
                    if ('parameter' in configuration):
                        if configuration['parameter'] != "":
                            config['readorders'][s]['parameter'] = bool(configuration['parameter'])
                    if ('signed' in configuration):
                        if configuration['signed'] != "":
                            if (str(configuration['signed']).lower() == 'true'):
                                config['readorders'][s]['signed'] = True
                            else:
                                config['readorders'][s]['signed'] = False
                    if ('interval' in configuration):
                        if configuration['interval'] != "":
                            config['readorders'][s]['interval'] = int(configuration['interval'])
                    if ('multiplefactor' in configuration):
                        if configuration['multiplefactor'] != "":
                            config['readorders'][s]['multiplefactor'] = int(configuration['multiplefactor'])
                    if ('transmissionmode' in configuration):
                        if configuration['transmissionmode'] != "":
                            config['readorders'][s]['transmissionmode'] = (configuration['transmissionmode'])
                    if ('type' in configuration):
                        if configuration['type'] != "":
                            config['readorders'][s]['type'] = int(configuration['type'])
                    if ('active' in configuration):
                        if (str(configuration['active']).lower() == 'true'):
                            config['readorders'][s]['active'] = True
                        else:
                            config['readorders'][s]['active'] = False
                    if ('serverid' in configuration):
                        if configuration['serverid'] != "":
                            serverids = configuration['serverid'].replace("[","").replace("]", "").split(',')

                            config['readorders'][s]['serverid'] = list()
                            for serverid in serverids:
                                config['readorders'][s]['serverid'].append(int(serverid))


                    config['readorders'][s]['multiplefactor'] = int(configuration['multiplefactor'])
                    if 'bits' in configuration:
                        if (configuration['bits'].isdigit()):
                            config['readorders'][s]['bits'] = int(configuration['bits'])
                    if 'dataarea' in configuration:
                        config['readorders'][s]['dataarea'] = configuration['dataarea']
                    if 'target' in configuration:
                        config['readorders'][s]['target'] = configuration['target']
                    cfg.Config.getInstance().write_config()


        except ValueError:
            logging.error('Value Error Webserver while transfering ReadOrders: ' + str(traceback.format_exc()))
        except Exception:
            logging.error('Error Webserver while transfering ReadOrders: ' + str(traceback.format_exc()))
   with open('configuration/config.json') as json_data:
       d = json.load(json_data)

   #return render_template('gatewayconfiguration.html', parameter=d, admin = loginadmin)
   return redirect("/gatewayconfiguration", code=302)


#if __name__ == '__main__':
#    app.secret_key = os.urandom(12)
#    app.run('0.0.0.0', 5000)
def start():
    if not os.path.exists('configuration'):
        os.makedirs('configuration')
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.config['UPLOAD_EXTENSIONS'] = ['.json']
    app.config['UPLOAD_PATH'] = 'configuration'
    app.secret_key = os.urandom(12)
    sockets = tornado.netutil.bind_sockets(5000)
    #tornado.process.fork_processes(0)
    asyncio.set_event_loop(asyncio.new_event_loop())
    http_server = HTTPServer(WSGIContainer(app))
    http_server.add_sockets(sockets)
    app.debug = False
    logging.info('Thread Webserver started')

    tornado.ioloop.PeriodicCallback(askstop, 1000).start()

    tornado.ioloop.IOLoop.instance().start()



    #http_server = WSGIServer(('0.0.0.0', 5000), app.wsgi_app)
    #http_server.serve_forever()


stop = False
def askstop():
    global stop
    if stop:
        tornado.ioloop.IOLoop.instance().stop()
        logging.info('Thread Webserver stopped')

