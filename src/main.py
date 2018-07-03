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

DIRECTORY = "/var/log/leap/"


# Check whether user is root, otherwise exit
if os.geteuid() != 0:
    exit("Error: You need to have root privileges to run leap.")

# Check if leap logging directory exists, else create one
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

# create a unique and descriptive logfile using timiestamp and process id in the
# standard linux log file directory
logging.basicConfig(format="%(asctime)s %(name)-12s "
                           "%(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M",
                    filename=DIRECTORY + "leap" + str(os.getpid()) + ".log",
                    filemode="w")

# use leap log across the whole module
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    # Call main function with command line arguments
    # Excluding argv[0] (program name)
    logger.info("Application started.")
    controller.main(sys.argv[1:])
