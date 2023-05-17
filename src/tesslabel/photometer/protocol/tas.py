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

from twisted.logger               import Logger
from twisted.internet             import reactor

from twisted.internet.protocol    import ClientFactory
from twisted.protocols.basic      import LineOnlyReceiver
from twisted.internet.interfaces  import IPushProducer, IConsumer
from zope.interface               import implementer

#--------------
# local imports
# -------------

from tesslabel.logger       import setLogLevel as SetLogLevel
from tesslabel.photometer.protocol.interface import IPayloadDecoder, IPhotometerControl
from tesslabel.photometer.protocol.payload   import OldPayload, JSONPayload
from tesslabel.photometer.protocol.photinfo  import CLIPhotometer
from tesslabel.photometer.protocol.tessw     import TESSStreamProtocol


# -------
# Classes
# -------

class TESSProtocolFactory(ClientFactory):

    def __init__(self, model, log, namespace):
        self.model = model
        self.log = log
        self.log_msg = Logger(namespace=namespace)
        self.tcp_deferred = None

    def startedConnecting(self, connector):
        self.log.debug('Factory: Started to connect.')

    def clientConnectionLost(self, connector, reason):
        self.log.debug('Factory: Lost connection. Reason: {reason}', reason=reason)

    def clientConnectionFailed(self, connector, reason):
        self.log.debug('Factory: Connection failed. Reason: {reason}', reason=reason)

    def buildProtocol(self, addr):
        photinfo_obj = TASPhotometerInfo(
            label   = self.model,
            log     = self.log, 
            log_msg = self.log_msg
        )
        payload_obj  = JSONPayload(
            label   = self.model, 
            log     = self.log,
            log_msg = self.log_msg,
        )
        protocol     = TASStreamProtocol(
            factory      = self, 
            payload_obj  = payload_obj, 
            photinfo_obj = photinfo_obj, 
            label        = self.model
        )
        photinfo_obj.setParent(protocol)
        return protocol


class TASPhotometerInfo(CLIPhotometer):

    def __init__(self, label, log, log_msg):
        super().__init__(label, log, log_msg)
        self.SOLICITED_RESPONSES.append({
            'name'    : 'name',
            'pattern' : r'^TAS SN: (TAS\w{3})',       
        })
        self.SOLICITED_PATTERNS = [ re.compile(sr['pattern']) for sr in self.SOLICITED_RESPONSES ]



class TASStreamProtocol(TESSStreamProtocol):
    pass


__all__ = [
    "TESSProtocolFactory",
    "TASStreamProtocol",
]
