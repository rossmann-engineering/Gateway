import opc_ua, asyncio
import logging, traceback
class Evcs_abb_dc_01:
    def __init__(self):
        pass

    def evcs_abb_dc_01(self, cs, evse1, evse2):
        try:
            evse1.Conf_uiNr = cs.Conf_uiEVSEx_Nr_10[0]
            evse1.Conf_uiType = 1
            evse1.Conf_uiNodeNr = cs.Conf_uiNodeNr
            evse1.PV_xComm_ok = False

            evse2.Conf_uiNr = cs.Conf_uiEVSEx_Nr_10[1]
            evse2.Conf_uiType = 1
            evse2.Conf_uiNodeNr = cs.Conf_uiNodeNr
            evse2.PV_xComm_ok = False

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
            evse1.PV_xComm_ok = True
            evse2.PV_xComm_ok = True
            evse1.PV_rCurrent_max = next((item for item in values_to_read if item["name"] == "Vehicle max. Amp outlet 1"), dict())['value']
            evse2.PV_rCurrent_max = next((item for item in values_to_read if item["name"] == "Vehicle max. Amp outlet 2"), dict())['value']

            evse1.PV_rPower = next((item for item in values_to_read if item["name"] == "DC voltage outlet 1"), dict())['value'] * next((item for item in values_to_read if item["name"] == "DC current outlet 1"), dict())['value']
            evse2.PV_rPower = next((item for item in values_to_read if item["name"] == "DC voltage outlet 2"), dict())['value'] * next((item for item in values_to_read if item["name"] == "DC current outlet 2"), dict())['value']

            evse1.PV_rCurrentDC = next((item for item in values_to_read if item["name"] == "DC current outlet 1"), dict())['value']
            evse2.PV_rCurrentDC = next((item for item in values_to_read if item["name"] == "DC current outlet 2"), dict())['value']

            evse1.PV_rVoltageDC = next((item for item in values_to_read if item["name"] == "DC voltage outlet 1"), dict())['value']
            evse2.PV_rVoltageDC = next((item for item in values_to_read if item["name"] == "DC voltage outlet 2"), dict())['value']

            evse1.PV_rSOC = next((item for item in values_to_read if item["name"] == "DC voltage outlet 1"), dict())['value']
            evse2.PV_rSOC = next((item for item in values_to_read if item["name"] == "DC voltage outlet 2"), dict())['value']

            evse1.PV_rEnergy = next((item for item in values_to_read if item["name"] == "Energy to EV battery during charging session outlet 1"), dict())['value']
            evse2.PV_rEnergy = next((item for item in values_to_read if item["name"] == "Energy to EV battery during charging session outlet 2"), dict())['value']

        except:
            logging.error('Unable to read from OPC-UA Server: ' + str(traceback.format_exc()))