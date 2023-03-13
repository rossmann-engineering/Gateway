import logging
import time
import traceback
import database

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
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_sAdress = '192.168.178.178'#'192.168.71.12'
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiPort = 502
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiNodeNr = 1
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiEVSEx_Nr_10[1] = 1
        dt_evergi.DT_EVERGi_arrCS_50[1].Conf_uiWired = '123'

        """
        dt_evergi.DT_EVERGi_arrCS_50[2].PV_xComm_ok = False
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_sType = 'ABB DC 01'
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_sAdress = '192.168.71.49'
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_uiPort = 4840
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_uiNodeNr = 1
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_uiEVSEx_Nr_10[1] = 2
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_uiEVSEx_Nr_10[2] = 3
        dt_evergi.DT_EVERGi_arrCS_50[2].Conf_uiWired = '123'
        """

        try:
            for cs in dt_evergi.DT_EVERGi_arrCS_50:

                if cs.Conf_sType == 'ABB AC 01':
                    dt_evergi.DT_EVERGi_arrEVSE_100[cs.Conf_uiEVSEx_Nr_10[0]].abb_ac_01.evcs_abb_ac_01(cs, dt_evergi.DT_EVERGi_arrEVSE_100[cs.Conf_uiEVSEx_Nr_10[0]])
                if cs.Conf_sType == 'ABB DC 01':
                    dt_evergi.DT_EVERGi_arrEVSE_100[cs.Conf_uiEVSEx_Nr_10[0]].abb_dc_01.evcs_abb_dc_01(cs,
                                                                                                       dt_evergi.DT_EVERGi_arrEVSE_100[
                                                                                                           cs.Conf_uiEVSEx_Nr_10[
                                                                                                               0]], dt_evergi.DT_EVERGi_arrEVSE_100[
                                                                                                           cs.Conf_uiEVSEx_Nr_10[
                                                                                                               0]])

        except Exception:
            logging.error('Exception reading from Chargers: ' + str(traceback.format_exc()))

        finally:
            time.sleep(5)

        # Add values to Database
        try:
            db_conn = database.connect("eh.db", '')
            for device in dt_evergi.DT_EVERGi_arrEVSE_100:
                if device.Conf_uiNr != 0:
                    database.add_daily_value(db_conn, 1, 'PV_uiState' + str(device.Conf_uiNr), device.PV_uiState)
                    database.add_daily_value(db_conn, 1, 'PV_rPower' + str(device.Conf_uiNr), device.PV_rPower)
                    database.add_daily_value(db_conn, 1, 'PV_rPower_max' + str(device.Conf_uiNr), device.PV_rPower_max)
                    database.add_daily_value(db_conn, 1, 'PV_rEnergy' + str(device.Conf_uiNr), device.PV_rEnergy)
                    database.add_daily_value(db_conn, 1, 'PV_rCurrent1' + str(device.Conf_uiNr), device.PV_rCurrent1)
                    database.add_daily_value(db_conn, 1, 'PV_rCurrent2' + str(device.Conf_uiNr), device.PV_rCurrent2)
                    database.add_daily_value(db_conn, 1, 'PV_rCurrent3' + str(device.Conf_uiNr), device.PV_rCurrent3)
                    database.add_daily_value(db_conn, 1, 'PV_rCurrent_max' + str(device.Conf_uiNr), device.PV_rCurrent_max)
                    database.add_daily_value(db_conn, 1, 'PV_rCurrentDC' + str(device.Conf_uiNr), device.PV_rCurrentDC)
                    database.add_daily_value(db_conn, 1, 'PV_rVoltageDC' + str(device.Conf_uiNr), device.PV_rVoltageDC)
                    database.add_daily_value(db_conn, 1, 'PV_rSOC' + str(device.Conf_uiNr), device.PV_rSOC)
                    database.add_daily_value(db_conn, 1, 'PV_xComm_ok' + str(device.Conf_uiNr), device.PV_xComm_ok)
                    database.add_daily_value(db_conn, 1, 'SPSc_rCurrent' + str(device.Conf_uiNr), device.SPSc_rCurrent)
                    database.add_daily_value(db_conn, 1, 'SPSc_uiComm' + str(device.Conf_uiNr), device.SPSc_uiComm)
                    database.add_daily_value(db_conn, 1, 'Help_SP_rCurrent_dev' + str(device.Conf_uiNr), device.Help_SP_rCurrent_dev)
            db_conn.close()

        except Exception:
            logging.error('Exception adding values to database: ' + str(traceback.format_exc()))


