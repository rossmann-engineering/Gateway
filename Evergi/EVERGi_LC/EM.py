import struct
import logging
import time
import traceback

from Evergi.DT_EVERGi import DT_EVERGI
import ModbusClient

def read_em():
    """
    Reed Energymeters (Manually adjusted code)
    """
    dt_evergi = DT_EVERGI.getInstance()
    while 1:
        try:
            dt_evergi.DT_EVERGi_arrProduction_50[1].PV_xComm_ok = False
            modbusClient = ModbusClient.ModbusClient('192.168.68.132', 502)
            modbusClient.connect()
            holding_registers1 = modbusClient.read_holdingregisters(12152, 2)
            holding_registers2 = modbusClient.read_holdingregisters(11944, 6)
            modbusClient.close()
            dt_evergi.DT_EVERGi_arrProduction_50[1].Conf_uiNr = 1
            dt_evergi.DT_EVERGi_arrProduction_50[1].Conf_uiNodeNr = 1
            dt_evergi.DT_EVERGi_arrProduction_50[1].PV_rPower = ModbusClient.ConvertRegistersToFloat(holding_registers1)

            dt_evergi.DT_EVERGi_arrProduction_50[1].PV_rCurrent1 = ModbusClient.ConvertRegistersToFloat([holding_registers2[0], holding_registers2[1]])
            dt_evergi.DT_EVERGi_arrProduction_50[1].PV_rCurrent2 = ModbusClient.ConvertRegistersToFloat([holding_registers2[2], holding_registers2[3]])
            dt_evergi.DT_EVERGi_arrProduction_50[1].PV_rCurrent3 = ModbusClient.ConvertRegistersToFloat([holding_registers2[4], holding_registers2[5]])

            dt_evergi.DT_EVERGi_arrProduction_50[1].PV_xComm_ok = True
        except Exception:
            logging.error('Exception reading from Energy meter: ' + str(traceback.format_exc()))
            time.sleep(5)



