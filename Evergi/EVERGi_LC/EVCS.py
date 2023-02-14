import logging
import time
import traceback

from Evergi.DT_EVERGi import DT_EVERGI
import ModbusClient

def read_evcs():
    """
    Read Informations from chargers
    """
    while 1:
        dt_evergi = DT_EVERGI.getInstance()

        dt_evergi.DT_EVERGi_CS[1].PV_xComm_ok = False
        dt_evergi.DT_EVERGi_CS[1].Conf_sType = 'ABB AC 01'
        dt_evergi.DT_EVERGi_CS[1].Conf_sAdress = '192.168.71.12'
        dt_evergi.DT_EVERGi_CS[1].Conf_uiPort = 502
        dt_evergi.DT_EVERGi_CS[1].Conf_uiNodeNr = 1
        dt_evergi.DT_EVERGi_CS[1].Conf_uiEVSEx_Nr_10[0] = 1
        dt_evergi.DT_EVERGi_CS[1].Conf_uiWired = '123'
        for cs in dt_evergi.DT_EVERGi_CS:
            try:
                if cs.Conf_sType == 'ABB AC 01':
                    modbusClient = ModbusClient.ModbusClient(cs.Conf_sAdress, 502)
                    modbusClient.connect()
                    holding_registers1 = modbusClient.read_holdingregisters(16384, 30)
                    modbusClient.close()
            except Exception:
                logging.error('Exception reading from Chargers: ' + str(traceback.format_exc()))
                time.sleep(5)
