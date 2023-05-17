# ----------------------------------------------------------------------
# Copyright (c) 2022
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------


# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger
from twisted.enterprise import adbapi


from twisted.internet import reactor, task, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

#--------------
# local imports
# -------------

from tesslabel import SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR

from tesslabel.logger import setLogLevel
from tesslabel.dbase import tables

# ----------------
# Module constants
# ----------------

NAMESPACE = 'dbase'

# -----------------------
# Module global variables
# -----------------------

log = Logger(NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------


# --------------
# Module Classes
# --------------

class DataAccesObject():

    def __init__(self, parent, pool, *args, **kargs):
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.parent = parent
        self.pool = pool
        self.start(*args)
        
       
    #------------
    # Service API
    # ------------

    def start(self, *args):
        log.info('Starting DAO')

        self.config = tables.ConfigTable(
            pool      = self.pool,
            log_level = 'info',
        )
        
        self.tess = tables.Table(
            pool                = self.pool, 
            table               = 'photometer',
            id_column           = 'rowid',
            natural_key_columns = ('mac',), 
            other_columns       = ('prefix','suffix','sensor','zero_point', 'freq_offset', 'interval','telnet_port','ssid','creation_date'),
            insert_mode         = tables.INSERT,
            log_level           = 'info',
        )
        

        
        