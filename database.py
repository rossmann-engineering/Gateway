import json
import sqlite3
import logging
import datetime
import traceback
from uuid import uuid4
import config as cfg

config = cfg.Config.getConfig()

def connect(db_name, type=''):
    """
    Connect to database and return connection object
    :param db_name: database name (filename)
    :return: connection object
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    """
    Create database structure
    :param conn: connection object
    """
    try:
        cursor = conn.cursor()
        '''cursor.execute("""
            CREATE TABLE IF NOT EXISTS mqttuploads(
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                moment datetime NOT NULL,
                serverid INTEGER NOT NULL,
                topic text NOT NULL,
                payload text NOT NULL
            );""")'''
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS "tbl-meterdata" (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        partKey text NOT NULL,
                        epoch text NOT NULL,
                        meterTypeId INTEGER NOT NULL,
                        meterNameId INTEGER NOT NULL,
                        readTime text NOT NULL,
                        fActiveEnergy REAL,
                        rActiveEnergy REAL,
                        tActivePower REAL,
                        errorCode text,
                        serverid INTEGER NOT NULL,
                        transferred INTEGER
                    );""")

        conn.commit()
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dailycache(
                        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                        moment datextime NOT NULL,
                        serverid INTEGER NOT NULL,
                        tag text NOT NULL,
                        value float NOT NULL
                    );""")
        conn.commit()
        logging.info('database - table "mqttuploads" created"')
    except:
        logging.error('Exception creating table: ' + str(traceback.format_exc()))

def add_daily_value (conn, serverid, tag, value):
    """
    add daily value
    :param conn: connection object
    :param serverid: Server ID the Message refers to
    :param tag: datetime of reading
    :param value: daily value
    :return: update row ID
    """
    try:
        moment = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dailycache(moment,serverid,tag,value) VALUES(?,?,?,?)",
                       (moment, serverid, tag, value))
        conn.commit()
        cursor.execute("DELETE FROM dailycache WHERE moment < DATETIME('now', '-1 day')")
        conn.commit()
        rowid = cursor.lastrowid
        cursor.close()
        return rowid
    except:
        logging.error('Exception adding daily value to queue: ' + str(traceback.format_exc()))

def add_message_queue(conn, moment, serverid, payload, device):
    """
    Put Message in queue
    :param conn: connection object
    :param serverid: Server ID the Message refers to
    :param moment: datetime of reading
    :return: updated row ID
    """
    try:
        cursor = conn.cursor()
        dict_payload = json.loads(payload)
        cursor.execute("INSERT INTO \"tbl-meterdata\" (readTime,epoch,partKey,meterTypeId,meterNameId,fActiveEnergy,rActiveEnergy, tActivePower, errorCode, serverid, transferred) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (moment.strftime("%Y-%m-%d %H:%M:00"), moment.strftime("%Y-%m-%d %H:%M:00"),
                        1, device['meterTypeId'], device['meterNameId'], dict_payload['values']['fActiveEnergy'], dict_payload['values']['rActiveEnergy'], dict_payload['values']['tActivePower'],None, serverid, 0))
        conn.commit()
        rowid = cursor.lastrowid
        cursor.close()
        return rowid
    except:
        logging.error('Exception adding message to queue: ' + str(traceback.format_exc()))

def datetime_to_unix_timestamp(dt):
    """
    Converts Python Datetime to Unix Timestamp (Format used by Thingsboard)
    :param dt: Python Datetime
    :return: Unix Timestamp (Millseconds expired since 1st January 1970)
    """
    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

def get_daily_values(conn, tag, serverid):
    """
    get daily value
    :param conn: connection object
    :param tag: datetime of reading
    :param serverid: Server ID the Message refers to
    :return: value gurke
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, moment ,serverid ,tag,value FROM dailycache WHERE tag='"+str(tag)+ "' AND serverid=" + str(serverid) + " ORDER by rowid")
        data = cursor.fetchall()
        returnvalue = dict()
        value = list()
        moment = list()
        for element in data:
            value.append(element[4])
            moment.append((datetime.datetime.strptime(element[1],"%Y-%m-%d %H:%M:00")))
        returnvalue['value'] = value
        returnvalue['moment'] = moment
        cursor.close()
        return returnvalue
    except:
        logging.error('Exception getting dailyvalues: ' + str(traceback.format_exc()))

def get_message_queue(conn, serverid):
    """
    Retrieve first record from the database that needs to be sent
    :param conn: connection object
    :return: message data along with rowid
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, readTime,epoch,partKey,meterTypeId,meterNameId,fActiveEnergy,rActiveEnergy, tActivePower, errorCode, serverid, transferred FROM \"tbl-meterdata\" WHERE serverid="+str(serverid)+" ORDER by id")
        data = cursor.fetchall()
        returnvalue = list()
        for element in data:
            returnvalue.append(dict(element))

        cursor.close()
        return returnvalue
    except:
        logging.error('Exception getting message queue: ' + str(traceback.format_exc()))

def delete_message_queue(conn, rowid):
    """
    Remove recently uploaded message data from the database
    :param conn: connection object
    :param rowid: record identifier
    """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM \"tbl-meterdata\" WHERE id=?", (rowid, ))
        conn.commit()
        cursor.close()
    except:
        logging.error('Exception deleting row from queue: ' + str(traceback.format_exc()))

if __name__ == "__main__":
    db_conn = connect("db-meter-data", 'postgresql')
    create_tables(db_conn)
    #add_message_queue(db_conn, datetime.datetime.now(),5,"topic","hello mqtt")
