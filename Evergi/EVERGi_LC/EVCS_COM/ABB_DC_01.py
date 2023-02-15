import opc_ua, asyncio
import logging, traceback
class Evcs_abb_dc_01:
    def __init__(self):
        pass

    def evcs_abb_dc_01(self, cs, evse1, evse2):
        try:
            values_to_read = list()
            dict_element = dict()
            dict_element['address'] = 'ns=6;s=::Charger:ChargerView.SerialNr'
            dict_element['name'] = 'SerialNr'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:WD_Toggle'
            dict_element['name'] = 'Watchdog - toggle'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].Energy'
            dict_element['name'] = 'Energy to EV battery during charging session outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].State'
            dict_element['name'] = 'State outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].Cable'
            dict_element['name'] = 'True when charge cable is detected outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].SOC'
            dict_element['name'] = 'State of charge value of the EV battery outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].VehMaxAmp'
            dict_element['name'] = 'Vehicle max. Amp outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].VehMaxVolt'
            dict_element['name'] = 'Vehicle max. Volt outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].Volt'
            dict_element['name'] = 'DC voltage outlet 1'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[1].Amp'
            dict_element['name'] = 'DC current outlet 1'
            values_to_read.append(dict_element)

            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].Energy'
            dict_element['name'] = 'Energy to EV battery during charging session outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].State'
            dict_element['name'] = 'State outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].Cable'
            dict_element['name'] = 'True when charge cable is detected outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].SOC'
            dict_element['name'] = 'State of charge value of the EV battery outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].VehMaxAmp'
            dict_element['name'] = 'Vehicle max. Amp outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].VehMaxVolt'
            dict_element['name'] = 'Vehicle max. Volt outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].Volt'
            dict_element['name'] = 'DC voltage outlet 2'
            values_to_read.append(dict_element)
            dict_element['address'] = 'ns=6;s=::Charger:OutletsView[2].Amp'
            dict_element['name'] = 'DC current outlet 2'
            values_to_read.append(dict_element)

            asyncio.run(opc_ua.main('opc.tcp://' + cs.Conf_sAdress + ':' + str(cs.Conf_uiPort), '', '', values_to_read))
        except:
            logging.error('Unable to read from OPC-UA Server: ' + str(traceback.format_exc()))