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

# ---------------
# Twisted imports
# ---------------

from twisted.application.service import MultiService
from twisted.logger import Logger


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

from tesslabel                    import FULL_VERSION_STRING, TSTAMP_SESSION_FMT, TEST
from tesslabel                    import set_status_code
from tesslabel.utils              import chop
from tesslabel.logger             import setLogLevel
from tesslabel.dbase.service      import DatabaseService
from tesslabel.photometer.service import PhotometerService


# ----------------
# Module constants
# ----------------

NAMESPACE = 'batch'

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


class CommandLineService(MultiService):

    # Service name
    NAME = 'Command Line Service'

    def __init__(self, options):
        super().__init__()   
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self._cmd_options = vars(options)
        self._test_transport_method = None

    #------------
    # Service API
    # ------------

    def startService(self):
        # 'tesslabel' calzado a pelo poque parece que no se captura de la command line
        log.warn("tesslabel {full_version}",full_version=FULL_VERSION_STRING)
        self.dbaseServ = self.parent.getServiceNamed(DatabaseService.NAME)
        self.dbaseServ.setTestMode(self._cmd_options['test'])
        pub.subscribe(self.onPhotometerInfo, 'phot_info')
        pub.subscribe(self.onPhotometerOffline, 'phot_offline')
        self.photomServ = self.build()
        super().startService() # so we can handle the 'running' attribute

    def stopService(self):
        log.info("Stopping {name}", name=self.name)
        return super().stopService() # se we can handle the 'running' attribute

    # ---------------
    # OPERATIONAL API
    # ---------------

    @inlineCallbacks
    def quit(self, exit_code = 0):
        '''Gracefully exit Twisted program'''
        set_status_code(exit_code)
        yield self.parent.stopService()

    def onPhotometerOffline(self, role):
        set_status_code(1)
        reactor.callLater(1, self.parent.stopService)

    @inlineCallbacks
    def onPhotometerInfo(self, role, info):
        label = TEST if role == 'test' else REF
        if info is None:
            log.warn("[{label}] No photometer info available. Is it Connected?", label=label)
        else:
            log.info("[{label}] Role         : {value}", label=label, value=info['role'])
            log.info("[{label}] Model        : {value}", label=label, value=info['model'])      
            log.info("[{label}] MAC          : {value}", label=label, value=info['mac'])
            log.info("[{label}] Firmware     : {value}", label=label, value=info['firmware'])
        if role == 'test' and self._cmd_options['dry_run']:
            log.info('Dry run. Will stop here ...') 
            set_status_code(0)
            yield self.parent.stopService()
        elif role == 'test' and self._cmd_options['write_zero_point'] is not None:
            result = yield self.testPhotometer.writeZeroPoint(self._cmd_options['write_zero_point'])
            set_status_code(0)
            yield self.parent.stopService()


    
    # ==============
    # Helper methods
    # ==============

    def build(self):
        section   = 'device'
        prefix    = TEST
        options = self.dbaseServ.getInitialConfig(section)
        options['model']        = options['model'].upper()
        options['old_proto']    = int(options['old_proto'])
        options['log_level']    = 'info' # A capón de momento
        options['log_messages'] = 'warn'
        options['config_dao']   = self.dbaseServ.dao.config
        proto, addr, port = chop(options['endpoint'], sep=':')
        self._test_transport_method = proto
        service = PhotometerService(options, False)
        service.setName(prefix + ' ' + PhotometerService.NAME)
        service.setServiceParent(self)
        return service
    
