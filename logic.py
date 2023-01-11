import logging
import traceback
import time
import opc_ua
import asyncio

import config as cfg
def run():
    logging.info('Thread Logic started')
    config = cfg.Config.getConfig()
    while 1:
        try:
            watchdog_from_plc = next((item for item in config['readorders'] if item["name"] == "Watchdog from PLC"), dict())
            watchdog_to_plc = next((item for item in config['readorders'] if item["name"] == "Watchdog to PLC"), dict())
            watchdog_to_plc['value'] = watchdog_from_plc.get('value', 0) * 100
            # Search for the Transport ID to write to
            for device in config['devices']:
                if device['transportid'] == watchdog_to_plc['transportid']:

                    asyncio.run(opc_ua.main('opc.tcp://' + device['ipaddress'] + ':' + device['port'], device['user'],
                                            device['password'], [watchdog_to_plc], write=True))

            time.sleep(5)
        except Exception:
            logging.error('Exception in Logic: ' + str(traceback.format_exc()))