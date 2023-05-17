# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import datetime

# ---------------
# Twisted imports
# ---------------

import treq
from twisted.internet             import reactor, task, defer
from twisted.internet.defer       import inlineCallbacks
from zope.interface               import implementer

# ---------------------
# Third party libraries
# ---------------------

from pubsub import pub

#--------------
# local imports
# -------------

from tesslabel.utils import chop
from tesslabel.photometer.protocol.interface import IPhotometerControl


# -----------------------
# Module global variables
# -----------------------


# ----------------
# Module functions
# ----------------

def format_mac(mac):
    '''Formats MAC strings as returned from the device into well-known MAC format'''
    return ':'.join(map(''.join, zip(*[iter(mac)]*2)))

# ----------
# Exceptions
# ----------


# -------
# Classes
# -------

@implementer(IPhotometerControl)
class HTMLPhotometer:
    """
    Get the photometer by parsing the HTML photometer home page.
    Set the new ZP by using the same URL as the HTML form displayed for humans
    """
    CONFLICTIVE_FIRMWARE = ('Nov 25 2021 v 3.2',)

    GET_INFO = {
        # These apply to the /settings page 
        'mac'   : re.compile(r"MAC: ([0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2})"),       
        'firmware' : re.compile(r"Firmware v: (.+?)<br>"),  # Non-greedy matching until <br>
    }

    def __init__(self, addr, label, log, log_msg):
        self.log = log_msg
        self.addr = addr
        self.label = label
        log.info("{label:6s} Using {who} Info", label=self.label, who=self.__class__.__name__)

    # ---------------------
    # IPhotometerControl interface
    # ---------------------

    @inlineCallbacks
    def writeConfiguration(self, configuration, timeout):
        '''
        Writes Zero Point to the device. 
        Asynchronous operation
        '''
        label = self.label
        result = {}
        result['tstamp'] = datetime.datetime.now(datetime.timezone.utc)
        url = self._make_config_url()
        self.log.info("==> {label:6s} [HTTP GET] {url}", url=url, label=label)
        params = [('cons', '{0:0.2f}'.format(zero_point))]
        resp = yield treq.get(url, params=params, timeout=4)
        text = yield treq.text_content(resp)
        self.log.info("<== {label:6s} [HTTP GET] {url}", url=url, label=label)
        matchobj = self.GET_INFO['flash'].search(text)
        result['zp'] = float(matchobj.groups(1)[0])
        if not matchobj:
            self.log.error("{label:6s} ZP not written!", label=label)
        return(result)

    @inlineCallbacks
    def getPhotometerInfo(self, timeout):
        '''
        Get photometer information. 
        Asynchronous operation
        '''
        label = self.label
        result = {}
        result['tstamp'] = datetime.datetime.now(datetime.timezone.utc)
       
        url = self._make_state_url()
        self.log.info("==> {label:6s} [HTTP GET] {url}", label=label,url=url)
        resp = yield treq.get(url, timeout=timeout)
        text = yield treq.text_content(resp)
        self.log.info("<== {label:6s} [HTTP GET] {url}", label=label, url=url)
        matchobj = self.GET_INFO['mac'].search(text)
        if not matchobj:
            self.log.error("{label:6s} MAC not found!", label=label)
            raise ValueError("Old firmware doesn't show its MAC in the /settings page")
        result['mac'] = matchobj.groups(1)[0]
        matchobj = self.GET_INFO['firmware'].search(text)
        if not matchobj:
            self.log.error("{label:6s} Firmware not found!", label=label)
            raise ValueError("Old firmware doesn't show its version in the /settings page")
        result['firmware'] = matchobj.groups(1)[0]
        firmware = result['firmware']
        if firmware in self.CONFLICTIVE_FIRMWARE:
            pub.sendMessage('phot_firmware', role='test', firmware=firmware) 
        return(result)

    def onPhotommeterInfoResponse(self, line, tstamp):
        return False

    # --------------
    # Helper methods
    # --------------

    def _make_state_url(self):
        return f"http://{self.addr}/settings"

    def _make_save_url(self):
        return f"http://{self.addr}/setap" # Set A.P.


@implementer(IPhotometerControl)
class CLIPhotometer:

    """
    Get the photometer by sending commands through a line oriented interface (i.e a serial port).
    Set the new ZP by sending commands through a line oriented interface (i.e a serial port)
    """


    def __init__(self, label, log, log_msg):
        self.log = log_msg
        self.label = label
        self.parent = None
        self.read_deferred = None
        self.write_deferred = None
        log.info("{label:6s} Using {who} Info", label=self.label, who=self.__class__.__name__)

    def setParent(self, protocol):
        self.parent = protocol


    # ----------------------------
    # IPhotometerControl interface
    # ----------------------------

    def writeConfiguration(self, configuration, timeout):
        '''
        Writes Zero Point to the device. 
        Asynchronous operation
        '''
        return defer.fail(NotImplementedError("Can't write photometer information"))

   
    def getPhotometerInfo(self, timeout):
        '''
        Get photometer information. 
        Asynchronous operation
        '''
        return defer.fail(NotImplementedError("Can't get photometer info from command line interface"))


    def onPhotometerInfoResponse(self, line, tstamp):
        return False
      

@implementer(IPhotometerControl)
class DBasePhotometer:

    def __init__(self, config_dao, section, label, log, log_msg):
        self.log = log_msg
        self.config_dao = config_dao
        self.section = section
        self.label = label
        log.info("{label:6s} Using {who} Info", label=self.label, who=self.__class__.__name__)


    # ---------------------
    # IPhotometerControl interface
    # ---------------------

    def writeConfiguration(self, configuration, timeout):
        '''
        Writes Zero Point to the device. 
        Asynchronous operation
        '''
        return defer.fail(NotImplementedError("Can't write photometer to the database"))

   
    def getPhotometerInfo(self, timeout):
        '''
        Get photometer information. 
        Asynchronous operation
        '''
        return defer.fail(NotImplementedError("Can't get photometer info from database"))


    def onPhotometerInfoResponse(self, line, tstamp):
        return False



#---------------------------------------------------------------------
# --------------------------------------------------------------------
# --------------------------------------------------------------------


__all__ = [
    "HTMLPhotometer",
    "CLIPhotometer",
    "DBasePhotometer"
]