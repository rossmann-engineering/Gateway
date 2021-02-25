import subprocess
import os
import json
import datalogger
import traceback
import time
from subprocess import Popen, PIPE
import serial
import calendar
import config as cfg
import platform
import logging

def console (command):
    output = subprocess.check_output(command, shell = True)
    return output

def simpleconsole (command):
    os.system(command)

def readphonenumber():
    returnvalue = 'Error reading phone number'
    try:
        if (os.name != 'nt'):
            value = sendatcommand("AT+CNUM")
        else:
            file = open("atcnum.txt", "r")
            value = file.read()
        value = value.splitlines()
        for i in range(0, len(value)):
            if "CNUM" in value[i]:
                returnvalue = value[i].split(",")[1].replace('"', '')
    except Exception:
        logging.error('Webserver (osinterface): Unable to read Phonenumber (AT+CNUM): ' + str(traceback.format_exc()))

    finally:
        return returnvalue

def readdeviceinformations():
    '''
    Architecture:        aarch64
    Byte Order:          Little Endian
    CPU(s):              4
    On-line CPU(s) list: 0-3
    Thread(s) per core:  1
    Core(s) per socket:  4
    Socket(s):           1
    NUMA node(s):        1
    Vendor ID:           ARM
    Model:               4
    Model name:          Cortex-A53
    Stepping:            r0p4
    CPU max MHz:         1800.0000
    CPU min MHz:         1200.0000
    BogoMIPS:            16.00
    L1d cache:           unknown size
    L1i cache:           unknown size
    L2 cache:            unknown size
    NUMA node0 CPU(s):   0-3
    Flags:               fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid
    '''
    returnvalue = dict()
    try:
        returnvalue['architecture'] = "Value read error"
        returnvalue['vendor'] = "Value read error"
        returnvalue['modelname'] = "Value read error"
        returnvalue['cpumaxmhz'] = "Value read error"
        returnvalue['cpuminmhz'] = "Value read error"
        is_linux = False
        if (platform.system() == 'Linux'):
            is_linux = True
        if (is_linux):
            lscpu = console("lscpu")
        else:
            file = open("windowssimulation/lscpu.txt", "rb")
            lscpu = file.read()
        lscpu = str(lscpu, 'utf-8')
        lscpu = lscpu.splitlines()
        for i in range (0, len(lscpu)):
            if "Architecture" in lscpu[i]:
                returnvalue['architecture'] = lscpu[i].split(": ")[1].strip()
            if "Vendor ID" in lscpu[i]:
                returnvalue['vendor'] = lscpu[i].split(": ")[1].strip()
            if "Model name" in lscpu[i]:
                returnvalue['modelname'] = lscpu[i].split(": ")[1].strip()
            if "CPU max MHz" in lscpu[i]:
                returnvalue['cpumaxmhz'] = lscpu[i].split(": ")[1].strip()
            if "CPU min MHz" in lscpu[i]:
                returnvalue['cpuminmhz'] = lscpu[i].split(": ")[1].strip()
    except Exception:
        logging.error('Webserver (osinterface): Unable to read Deviceinformations (lscpu): ' + str(traceback.format_exc()))
    finally:
        return returnvalue


def readmodemstatus ():
    #DataLogger.logData('Webserver Read Modem Status (readmodemstatis())')
    returnvalue = dict()
    #Initialize Variables
    returnvalue['connected'] = 'Error Reading value'
    returnvalue['suspended'] = 'Error Reading value'
    returnvalue['interface'] = 'Error Reading value'
    returnvalue['iptimeout'] = 'Error Reading value'
    returnvalue['apn'] = 'Error Reading value'
    returnvalue['roaming'] ='Error Reading value'
    returnvalue['user'] = 'Error Reading value'
    returnvalue['password'] ='Error Reading value'
    returnvalue['iptype'] = 'Error Reading value'
    returnvalue['number'] = 'Error Reading value'
    returnvalue['ipv4method'] = 'Error Reading value'
    returnvalue['ipv4address'] = 'Error Reading value'
    returnvalue['ipv4prefix'] = 'Error Reading value'
    returnvalue['ipv4gateway'] = 'Error Reading value'
    returnvalue['ipv4dns'] = 'Error Reading value'
    returnvalue['duration'] = 0




    try:
        returnvalue['connected'] = "Value read error"
        returnvalue['suspended'] = "Value read error"
        returnvalue['interface'] = "Value read error"
        returnvalue['iptimeout'] = "Value read error"
        returnvalue['apn'] = "Value read error"
        returnvalue['roaming'] = "Value read error"
        returnvalue['user'] = "Value read error"
        returnvalue['password'] = "Value read error"
        returnvalue['iptype'] = "Value read error"
        returnvalue['number'] = "Value read error"
        returnvalue['ipv4method'] = "Value read error"
        returnvalue['ipv4address'] = "Value read error"
        returnvalue['ipv4prefix'] = "Value read error"
        returnvalue['ipv4gateway'] = "Value read error"
        returnvalue['ipv4dns'] = "Value read error"
        returnvalue['duration'] = 0
        if (os.name != 'nt'):
            for i in range(0, 20):
                try:
                    mmcli_b = console("mmcli -b "+str(i))


                    break
                except Exception:
                    pass
        else:
            file = open("mmcli_b_0.txt", "r")
            mmcli_b = file.read()
        mmcli_b = mmcli_b.splitlines()

        for i in range (0, len(mmcli_b)):
            if "connected" in mmcli_b[i]:
                returnvalue['connected'] = mmcli_b[i].split("'")[1]
            if "suspended" in mmcli_b[i]:
                returnvalue['suspended'] = mmcli_b[i].split("'")[1]
            if "interface" in mmcli_b[i]:
                returnvalue['interface'] = mmcli_b[i].split("'")[1]
            if "IP timeout" in mmcli_b[i]:
                returnvalue['iptimeout'] = mmcli_b[i].split("'")[1]
            if "apn" in mmcli_b[i]:
                returnvalue['apn'] = mmcli_b[i].split("'")[1]
            if "roaming" in mmcli_b[i]:
                returnvalue['roaming'] = mmcli_b[i].split("'")[1]
            if "user" in mmcli_b[i]:
                returnvalue['user'] = mmcli_b[i].split("'")[1]
            if "password" in mmcli_b[i]:
                returnvalue['password'] = mmcli_b[i].split("'")[1]
            if "IP type" in mmcli_b[i]:
                returnvalue['iptype'] = mmcli_b[i].split("'")[1]
            if "number" in mmcli_b[i]:
                returnvalue['number'] = mmcli_b[i].split("'")[1]
            if ("method" in mmcli_b[i]) & ("IPv4" in mmcli_b[i]):
                returnvalue['ipv4method'] = mmcli_b[i].split("'")[1]
            if "address" in mmcli_b[i]:
                returnvalue['ipv4address'] = mmcli_b[i].split("'")[1]
            if "prefix" in mmcli_b[i]:
                returnvalue['ipv4prefix'] = mmcli_b[i].split("'")[1]
            if "gateway" in mmcli_b[i]:
                returnvalue['ipv4gateway'] = mmcli_b[i].split("'")[1]
            if "dns" in mmcli_b[i]:
                returnvalue['ipv4dns'] = mmcli_b[i].split("'")[1]
            if "Duration" in mmcli_b[i]:
                returnvalue['duration'] = mmcli_b[i].split("'")[1]
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read values (mmcli -b 0): ' + str(traceback.format_exc()))


    #Initialize Variables
    returnvalue['manufacturer'] = 'Error Reading value'
    returnvalue['model'] = 'Error Reading value'
    returnvalue['revision'] = 'Error Reading value'
    returnvalue['hwrevision'] = 'Error Reading value'
    returnvalue['equipmentid'] = 'Error Reading value'
    returnvalue['powerstate'] = 'Error Reading value'
    returnvalue['accesstech'] = 'Error Reading value'
    returnvalue['signalquality'] = '0'
    returnvalue['imei'] = 'Error Reading value'
    returnvalue['operatorid'] = 'Error Reading value'
    returnvalue['operatorname'] = 'Error Reading value'
    returnvalue['subscription'] = 'Error Reading value'

    try:
        is_linux = False
        if (platform.system() == 'Linux'):
            is_linux = True
        if (is_linux):
            for i in range(0, 20):
                try:
                    mmcli_m = console("mmcli -m "+str(i))

                    break
                except Exception:
                    pass
        else:
            file = open("windowssimulation/mmcli -m 0.txt", "rb")
            mmcli_m = file.read()
        mmcli_m = str(mmcli_m, 'utf-8')
        mmcli_m = mmcli_m.splitlines()
        for i in range (0, len(mmcli_m)):
            if "manufacturer" in mmcli_m[i]:
                returnvalue['manufacturer'] = mmcli_m[i].split(":")[1]
            if "model" in mmcli_m[i]:
                returnvalue['model'] = mmcli_m[i].split(":")[1]
            if "revision" in mmcli_m[i]:
                returnvalue['revision'] = mmcli_m[i].split(":")[1]
            if "power state" in mmcli_m[i]:
                returnvalue['powerstate'] = mmcli_m[i].split(":")[1]
            if "signal quality:" in mmcli_m[i]:
                returnvalue['signalquality'] = mmcli_m[i].split(":")[1]
            if "imei" in mmcli_m[i]:
                returnvalue['imei'] = mmcli_m[i].split(":")[1]
            if "operator id" in mmcli_m[i]:
                returnvalue['operatorid'] = mmcli_m[i].split(":")[1]
            if "operator name" in mmcli_m[i]:
                returnvalue['operatorname'] = mmcli_m[i].split(":")[1]
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read values (mmcli -m 0): ' + str(traceback.format_exc()))


    #Send AT-Command to check Signal quality
    returnvalue['signalquality'] = '0'
    try:
        if (os.name != 'nt'):
            response = sendatcommand("AT+CSQ")
            response = response.splitlines()

            for i in range(0, len(response)):
                if "+CSQ" in response[i]:
                    returnvalue['signalquality'] = response[i].split(": ")[1].replace(',','.')
                    pass

    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read Signal quality (AT command AT+CSQ): ' + str(
            traceback.format_exc()))

    return returnvalue

def gwReboot():
    """
    Reboots the Gateway using the console command "reboot"
    """
    try:
        if (os.name != 'nt'):
            console("reboot")

    except Exception as e:
        logging.error(
            'Error while rebooting (reboot): ' + str(traceback.format_exc()))

def sendatcommand(command):
    """
    Sends AT comands to the 3G Modem. The USB Modem has to be connected to ttyACM3
    :param command: The AT commad that has to be send
    :return: Answer from Modem
    """
    port  = "/dev/ttyUSB2"
    #find serial port
    #for i in range(0, 5):
    #    try:
    #        answer = osinterface.console("info /dev/ttyACM"+str(i)+" & udevadm info -a /dev/ttySCM"+str(i)+" | grep ATTRS{product}")
    #        answer = answer.splitlines()
    #        for j in range(0, len(answer)):
    #            if "SIM5360" in answer[j]:
    #                port = "/dev/ttyUSB"+str(i)
    #    except Exception:
    #        pass

    data = ''
    cfg.Config.getInstance().atcommandlock.acquire()
    try:
        ser = serial.Serial(port, timeout=0.2,write_timeout=1,  baudrate=9600, xonxoff=False, rtscts=False, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        if (not ser.is_open):
                ser.open()

        timeInAbsoluteSeconds = calendar.timegm(time.gmtime())


        while (((timeInAbsoluteSeconds + 5) > calendar.timegm(time.gmtime())) and len(data)<2):
            try:
                ser.flushInput()
                ser.flushOutput()
                cmd = (str(command)+"\r").encode('utf-8')


                ser.write(cmd)
                ser.flush()
                    # data = self.ser.read(50)

                data = str(ser.read(1000), 'utf-8')
                logging.info('Response to AT-Command from Modem: '+data);

            except Exception:
                logging.error('Unable to send AT command' + str(
                    traceback.format_exc()))
        #print data
        #DataLogger.logData('Send AT Command, Received Answer: ' + str(data))
    except Exception:
        logging.error('Unable to send AT command' + str(
            traceback.format_exc()))
    finally:
        cfg.Config.getInstance().atcommandlock.release()
    return data.replace('\n', '<br>')





def readvpnstatus ():
    # The output of platform.system() is as follows:
    # Linux: Linux
    # Mac: Darwin
    # Windows: Windows
    is_linux = False
    if (platform.system() == 'Linux'):
        is_linux = True
    returnvalue = dict();
    returnvalue['ipaddress'] = 'error'
    returnvalue['mask'] = 'error'
    returnvalue['nodeid'] = 'error'
    returnvalue['version'] = 'error'
    returnvalue['connected'] = 'false'
    returnvalue['networkid'] = 'error'
    returnvalue['networkname'] = 'error'

    try:
        if is_linux:
            # First determine the interface
            ifconfig = console("ifconfig")
            ifconfig = str(ifconfig, 'utf-8')
            ifconfig = ifconfig.splitlines()
            for i in range(0, len(ifconfig)):
                if ifconfig[i].startswith("zt"):
                    networkname = ifconfig[i].split(':')[0]
                    break
            ifconfig = console("ifconfig "+str(networkname))


        else:
            file = open("windowssimulation/ifconfig zt0.txt", "rb")
            ifconfig = file.read()
        ifconfig = str(ifconfig, 'utf-8')
        ifconfig = ifconfig.splitlines()
        firstline = ifconfig[1].split("  ")
        for i in range(0, len(firstline)):
            if "inet" in firstline[i]:
                returnvalue['ipaddress'] = firstline[i].split("inet")[1].strip()
            if "netmask" in firstline[i]:
                returnvalue['mask'] = firstline[i].split("netmask")[1].strip()
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read vpn values (ifconfig_zt0): ' + str(traceback.format_exc()))

    try:
        zerotier = ""
        if is_linux:
            zerotier = console("sudo zerotier-cli -j info")
        else:
            file = open("windowssimulation/zerotier-cli -j info.txt", "rb")
            zerotier = file.read()
        zerotier = str(zerotier, 'utf-8')
        zerotier = zerotier.splitlines()
        for i in range(0, len(zerotier)):
            if '"version"' in zerotier[i]:
                returnvalue['version'] = zerotier[i].split(":")[1].strip().replace(',', '').replace('"', '')
            if "address" in zerotier[i]:
                returnvalue['nodeid'] = zerotier[i].split(":")[1].strip().replace(',', '').replace('"', '')
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read vpn values (zerotier-cli -j info): '  + str(traceback.format_exc()))

    try:
        networks = ""
        if is_linux:
            networks = console("zerotier-cli listnetworks")
        else:
            file = open("windowssimulation/zerotier-cli listnetworks.txt", "rb")
            networks = file.read()
        networks = str(networks, 'utf-8')
        networks = networks.splitlines()

        for network in networks:
            if ':' in network:
                returnvalue['networkid'] = network.split(" ")[2]
                returnvalue['networkname'] = network.split(" ")[3]
                if 'OK' in network:
                    returnvalue['connected'] = 'true'
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read vpn values (zerotier-cli listnetworks): '  + str(traceback.format_exc()))



    return returnvalue


def readzerotiernetwork():
    #zerotier-cli listnetworks
    #200 listnetworks <nwid> <name> <mac> <status> <type> <dev> <ZT assigned ips>
    #200 listnetworks c7c8172af1f100cc EH-Gateways ce:ec:e8:62:62:db OK PRIVATE zt5u46mkr5 fc36:3917:e6ec:1993:48cc:0000:0000:0001/40,10.147.17.142/24
    returnvalue = dict();
    returnvalue['networkid'] = 'error'
    returnvalue['networkname'] = 'error'
    returnvalue['networkip'] = 'error'
    try:
        if (os.name != 'nt'):
            # First determine the interface
            zerotiercli = console("zerotier-cli listnetworks")



        else:
            file = open("windowssimulation/zerotier-cli listnetworks.txt", "r")
            zerotiercli = file.read()
        zerotiercli = zerotiercli.splitlines()
        returnvalue['networkid'] = zerotiercli[1].split(' ')[2]
        returnvalue['networkname'] = zerotiercli[1].split(' ')[3]
        returnvalue['networkip'] = zerotiercli[1].split(' ')[7]

    except Exception as e:
        logging.error('Unable to read Zerotier Networkname (zerotier-cli listnetworks): ' + str(traceback.format_exc()))
    return returnvalue

def readeth0status():
    returnvalue = dict();
    returnvalue['ipaddress'] = 'no IP-Address'
    returnvalue['mask'] = 'No Mask'
    try:
        is_linux = False
        if (platform.system() == 'Linux'):
            is_linux = True
        if (is_linux):
            ifconfig = console("ifconfig eth0")
        else:
            file = open("windowssimulation/ifconfig eth0.txt", "rb")
            ifconfig = file.read()
        ifconfig = str(ifconfig, 'utf-8')
        ifconfig = ifconfig.splitlines()
        firstline = ifconfig[1].split("  ")
        for i in range(0, len(firstline)):
            if "inet" in firstline[i]:
                returnvalue['ipaddress'] = firstline[i].split("inet")[1].strip()
            if "netmask" in firstline[i]:
                returnvalue['mask'] = firstline[i].split("netmask")[1].strip()
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read eth0 values (ifconfig eth0): ' + str(traceback.format_exc()))
    return returnvalue

def readwlan0status():
    returnvalue = dict();
    returnvalue['ipaddress'] = 'no IP-Address'
    returnvalue['mask'] = 'No Mask'
    try:
        is_linux = False
        if (platform.system() == 'Linux'):
            is_linux = True
        if (is_linux):
            ifconfig = console("ifconfig wlan0")
        else:
            file = open("windowssimulation/ifconfig wlan0.txt", "rb")
            ifconfig = file.read()
        ifconfig = str(ifconfig, 'utf-8')
        ifconfig = ifconfig.splitlines()
        firstline = ifconfig[1].split("  ")
        for i in range(0, len(firstline)):
            if "inet" in firstline[i]:
                returnvalue['ipaddress'] = firstline[i].split("inet")[1].strip()
            if "netmask" in firstline[i]:
                returnvalue['mask'] = firstline[i].split("netmask")[1].strip()
    except Exception as e:
        logging.error('Webserver (osinterface): Unable to read wlan0 values (ifconfig eth1): ' + str(traceback.format_exc()))
    return returnvalue