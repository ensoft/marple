#!/usr/bin/env python3

# -------------------------------------------------------------
# main.py - Initiates the program
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Initiates the program.

"""

import sys
import os
import datetime
import logging

from .controller import controller_main

# create a unique and descriptive logfile using timiestamp and process id in the
# standard linux log file directory
path = "/var/log/leap/" + datetime.date + datetime.time + os.getpid() + ".log"
logging.basicConfig(path)

# use leap log across the whole module
logger = logging.getLogger('leap-log')

if __name__ == "__main__":
    # Call main function with command line arguments
    # Excluding argv[0] (program name)
    controller_main.main(sys.argv[1:])
