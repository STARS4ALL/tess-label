# ----------------------------------------------------------------------
# Copyright (c) 2022
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------


import os
import glob
import uuid
import datetime
import sqlite3

# ---------------
# Twisted imports
# ---------------

from twisted.application.service import Service
from twisted.logger import Logger
from twisted.enterprise import adbapi


from twisted.internet import reactor, task, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from tesslabel import SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR, TSTAMP_FORMAT, TSTAMP_SESSION_FMT
from tesslabel.logger import setLogLevel
from tesslabel.dbase import NAMESPACE, log 
from tesslabel.dbase.utils import create_database, create_schema
from tesslabel.dbase.dao import DataAccesObject

# ----------------
# Module constants
# ----------------

SQL_TEST_STRING = "SELECT COUNT(*) FROM config_t"


# ------------------------
# Module Utility Functions
# ------------------------

# SQLite has a default datetime.datetime adapter built in but
# we like to write in our own ISO format
def timestamp_adapter(tstamp):
    return tstamp.strftime(TSTAMP_FORMAT)

sqlite3.register_adapter(datetime.datetime, timestamp_adapter)

def getPool(*args, **kargs):
    '''Get connetion pool for sqlite3 driver (Twisted only)'''
    kargs['check_same_thread'] = False
    return adbapi.ConnectionPool("sqlite3", *args, **kargs)


def read_database_version(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "version";'
    cursor.execute(query)
    version = cursor.fetchone()[0]
    return version

def write_database_uuid(connection):
    guid = str(uuid.uuid4())
    cursor = connection.cursor()
    param = {'section': 'database','property':'uuid','value': guid}
    cursor.execute(
        '''
        INSERT INTO config_t(section,property,value) 
        VALUES(:section,:property,:value)
        ''',
        param
    )
    connection.commit()
    return guid

def make_database_uuid(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "uuid";'
    cursor.execute(query)
    guid = cursor.fetchone()
    if guid:
        try:
            uuid.UUID(guid[0])  # Validate UUID
        except ValueError:
            guid = write_database_uuid(connection)
        else:
            guid = guid[0]
    else:
        guid = write_database_uuid(connection)
    return guid


def read_configuration(connection):
     cursor = connection.cursor()
     cursor.execute("SELECT section, property, value FROM config_t ORDER BY section")
     return cursor.fetchall()

# --------------
# Module Classes
# --------------

class DatabaseService(Service):

    # Service name
    NAME = 'Database Service'

    def __init__(self, path, create_only=False, *args, **kargs):
        super().__init__(*args, **kargs)
        self.path = path
        self.getPoolFunc = getPool
        self.create_only = create_only

    #------------
    # Service API
    # ------------


    def startService(self):
        setLogLevel(namespace=NAMESPACE, levelStr='warn')

        connection, new_database = create_database(self.path)
        if new_database:
            log.warn("Created new database file at {f}",f=self.path)
        just_created, file_list = create_schema(connection, SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR, SQL_TEST_STRING)
        if just_created:
            for sql_file in file_list:
                log.warn("Populating data model from {f}", f=os.path.basename(sql_file))
        else:
            for sql_file in file_list:
                log.warn("Applying updates to data model from {f}", f=os.path.basename(sql_file))
        #levels  = read_debug_levels(connection)
        version = read_database_version(connection)
        guid    = make_database_uuid(connection)
        log.warn("Starting {service} on {database}, version = {version}, UUID = {uuid}", 
            database = self.path, 
            version  = version,
            service  = self.name,
            uuid     = guid,
        )
    
        # Remainder Service initialization
        super().startService() # se we can handle the 'running' attribute
        self._initial_config = read_configuration(connection)
        connection.commit()
        connection.close()
        if self.create_only:
            self.quit(exit_code=0)
        else:
            self.openPool()
            self.dao = DataAccesObject(self, self.pool)
            self.dao.version = version
            self.dao.uuid = guid


    @inlineCallbacks
    def stopService(self):
        log.info("Stopping {name}", name=self.name)
        self.closePool()
        try:
            reactor.stop()
        except Exception as e:
            log.failure("{e}",e=e)
        finally:
            yield super().stopService() # se we can handle the 'running' attribute

    # ---------------
    # OPERATIONAL API
    # ---------------    

    def setTestMode(self, test_mode):
        self.test_mode   = test_mode
    
    def getInitialConfig(self, section):
        '''For service startup, avoiding async code'''
        g = filter(lambda i: True if i[0] == section else False, self._initial_config)
        return dict(map(lambda i: (i[1], i[2]) ,g))

    # --------------
    # Event handlers
    # --------------



    # -------------
    # Helper methods
    # --------------

    

    # =============
    # Twisted Tasks
    # =============
   
        

      
    # ==============
    # Helper methods
    # ==============

    def openPool(self):
        # setup the connection pool for asynchronouws adbapi
        log.debug("Opening a DB Connection to {conn!s}", conn=self.path)
        self.pool  = self.getPoolFunc(self.path)
        log.debug("Opened a DB Connection to {conn!s}", conn=self.path)


    def closePool(self):
        '''setup the connection pool for asynchronouws adbapi'''
        log.debug("Closing a DB Connection to {conn!s}", conn=self.path)
        if self.pool:
            self.pool.close()
        self.pool = None
        log.debug("Closed a DB Connection to {conn!s}", conn=self.path)
