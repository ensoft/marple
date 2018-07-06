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

import collect.controller.main as collect_controller
import display.controller as display_controller
import common.output as output

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

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

except PermissionError:
    # if setting up the logging fails there is something wrong with the system
    exit("Fatal Error: Failed to set up logging due to missing privileges "
         "to the log directory!\n Make sure you have root privileges and that "
         "you are allowed to access the log directory as root.")
except Exception as ex:
    # if setting up the logging fails there is something wrong with the system
    exit("Fatal Error: Failed to set up logging! {}".format(str(ex)))

if __name__ == "__main__":
    logger.info("Application started.")
    try:
        # Call main function with command line arguments
        # Excluding argv[0] (program name: leap)
        # and argv[1] (function name: {collect,display})
        if len(sys.argv) < 2:
            output.print_("usage: leap COMMAND\n The COMMAND "
                          "can be either \"collect\" or \"display\"")
        elif sys.argv[1] == "collect":
            collect_controller.main(sys.argv[2:])
        elif sys.argv[1] == "display":
            display_controller.main(sys.argv[2:])
        else:
            output.print_("usage: leap COMMAND\n The COMMAND "
                          "can be either \"collect\" or \"display\"")
    except Exception as ex:
        # If anything goes wrong, handle it here
        output.error_("An unexpected error occurred. Check log for details",
                      str(ex))
