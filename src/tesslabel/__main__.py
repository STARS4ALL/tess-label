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
import sys
import argparse

# ---------------
# Twisted imports
# ---------------

from twisted.internet import reactor
from twisted.application import service

#--------------
# local imports
# -------------

from tesslabel import __version__, get_status_code

import tesslabel.utils
from tesslabel.logger        import startLogging
from tesslabel.dbase.service import DatabaseService

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------


# ------------------------
# Module Utility Functions
# ------------------------

def mkendpoint(value):
    return tesslabel.utils.mkendpoint(value)

def createParser():
    global name
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='TESSLABEL GUI')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('-d', '--dbase',    type=str, required=True, action='store', metavar='<file path>', help='SQLite database to operate upon')
    parser.add_argument('-c', '--console',  action='store_true',  help='log to console.')
    parser.add_argument('-l', '--log-file', type=str, default=None, action='store', metavar='<file path>', help='log to file')
   
    # --------------------------
    # Create first level parsers
    # --------------------------

    subparser = parser.add_subparsers(dest='command')
    parser_gui  = subparser.add_parser('gui', help='graphical user interface options')
    parser_cli  = subparser.add_parser('cli', help='command line interface options')

    # -----------------------------------------------------------------------------------
    # Arguments for 'gui' command are not needed since they are handled by the GUI itself
    # -----------------------------------------------------------------------------------

    parser_gui.add_argument('-m','--messages', type=str, choices=["ref","test","both"], default=None, help='log photometer messages')

    # -----------------------------
    # Arguments for 'cli' command
    # -----------------------------
   
    group0 = parser_cli.add_mutually_exclusive_group()
    group0.add_argument('-t', '--test',    action='store_true',  default=False, help="Don't update database")
   
    return parser

# -------------------
# Booting application
# -------------------

options = createParser().parse_args(sys.argv[1:])

startLogging(
    console  = options.console,
    filepath = options.log_file
)

# --------------------
# Application assembly
# --------------------

application = service.Application("tesslabel")
dbaseService = DatabaseService(
    path        = options.dbase,
)
dbaseService.setName(DatabaseService.NAME)
dbaseService.setServiceParent(application)


if options.command == 'gui':
    from tesslabel.gui.service import GraphicalService
    guiService = GraphicalService(
        options = options,
    )
    guiService.setName(GraphicalService.NAME)
    guiService.setServiceParent(application)
elif options.command == 'cli':
    from tesslabel.cli.service      import CommandLineService
    batchService = CommandLineService(
        options = options,
    )
    batchService.setName(CommandLineService.NAME)
    batchService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()
sys.exit(get_status_code())
