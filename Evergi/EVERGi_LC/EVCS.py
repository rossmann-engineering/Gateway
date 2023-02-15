import logging
import time
import traceback

from Evergi.DT_EVERGi import DT_EVERGI
from Evergi.EVERGi_LC.EVCS_COM.ABB_AC_01 import *

def read_evcs():
    """
    Read Informations from chargers
    """
    while 1:
        dt_evergi = DT_EVERGI.getInstance()

        dt_evergi.DT_EVERGi_arrCS_50[1].PV_xComm_ok = False
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_sType = 'ABB AC 01'
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_sAdress = '192.168.71.12'
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiPort = 502
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiNodeNr = 1
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiEVSEx_Nr_10[0] = 1
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiWired = '123'

        for cs in dt_evergi.DT_EVERGi_arrCS_50:
            try:
                if cs.Conf_sType == 'ABB AC 01':
                    evcs_abb_ac_01(cs, dt_evergi.DT_EVERGi_arrEVSE_100[cs.Conf_uiEVSEx_Nr_10[0]])
            except Exception:
                logging.error('Exception reading from Chargers: ' + str(traceback.format_exc()))
                time.sleep(5)
