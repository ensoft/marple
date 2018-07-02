#!/usr/bin/env python3

# -------------------------------------------------------------
# controller.py - user interface, parses and applies commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Main script, initiates the program.

"""

import sys
import os
import datetime
import logging

from . import controller

path = "/var/log/leap/" + datetime.date + datetime.time + os.getpid() + ".log"

logging.basicConfig(path)
logger = logging.getLogger('leap-log')

if __name__ == "__main__":
    # Call main function with command line arguments
    # Excluding argv[0] (program name)
    controller.main(sys.argv[1:])
