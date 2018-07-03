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
import logging

import controller.main as controller
import common.output as output

DIRECTORY = "/var/log/leap/"


# Check whether user is root, otherwise exit
if os.geteuid() != 0:
    exit("Error: You need to have root privileges to run leap.")

try:
    # Check if leap logging directory exists, else create one
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)

    # create a unique and descriptive logfile using timiestamp and process id
    # in the standard linux log file directory
    logging.basicConfig(format="%(asctime)s %(name)-12s "
                               "%(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M",
                        filename=DIRECTORY + "leap" + str(os.getpid()) + ".log",
                        filemode="w")

    # use leap log across the whole module
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
except Exception as ex:
    # if setting up the logging fails there is something wrong with the system
    exit("Fatal Error: Failed to set up logging! {}".format(str(ex)))

if __name__ == "__main__":
    logger.info("Application started.")
    try:
        # Call main function with command line arguments
        # Excluding argv[0] (program name)
        controller.main(sys.argv[1:])
    except Exception as ex:
        # If anything goes wrong, handle it here
        output.error_("An unexpected error occurred. Check log for details",
                      str(ex))
