import logging
import traceback

import config as cfg
def run():
    logging.info('Thread Logic started')
    config = cfg.Config.getConfig()
    while 1:
        try:
            watchdog_from_plc = next((item for item in config['readorders'] if item["name"] == "Watchdog from PLC"), dict())
            watchdog_to_plc = next((item for item in config['readorders'] if item["name"] == "Watchdog to PLC"), dict())
            watchdog_to_plc['value'] = watchdog_from_plc.get('value', 0) * 100

        except Exception:
            logging.error('Exception in Logic: ' + str(traceback.format_exc()))