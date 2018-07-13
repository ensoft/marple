#!/usr/bin/env python3

# -------------------------------------------------------------
# main.py - Initiates the program
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Initiates the program.

Sets up logging, calls the appropriate controller (collect or display) and
deals with exceptions.

"""

import sys
import os
import logging

import collect.controller.main as collect_controller
import display.controller as display_controller
import common.output as output
from common import paths
from .common.exceptions import AbortedException

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

LOG_DIRECTORY = paths.VAR_DIR + "log/marple/"

# Check whether user is root, otherwise exit
if os.geteuid() != 0:
    exit("Error: You need to have root privileges to run marple.")

try:
    # Check if marple logging directory exists, else create one
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    # create a unique and descriptive logfile using timestamp and process id
    # in the standard linux log file directory
    logging.basicConfig(format="%(asctime)s %(name)-12s "
                               "%(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M",
                        filename=LOG_DIRECTORY + "marple" + str(os.getpid()) +
                                ".log",
                        filemode="w")

    # use marple log across the whole module
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
        # Call main function with command line arguments excluding argv[0]
        # (program name: marple) and argv[1] (function name: {collect,display})
        if len(sys.argv) < 2:
            output.print_("usage: marple COMMAND\n The COMMAND "
                          "can be either \"collect\" or \"display\"")
        elif sys.argv[1] == "collect":
            collect_controller.main(sys.argv[2:])
        elif sys.argv[1] == "display":
            display_controller.main(sys.argv[2:])
        else:
            output.print_("usage: marple COMMAND\n The COMMAND "
                          "can be either \"collect\" or \"display\"")

    except AbortedException:
        # If the user decides to abort
        exit("Aborted.")
    except NotImplementedError as nie:
        # if the requested function is not implemented, exit with an error
        exit("The command \"{}\" is currently not implemented. "
             "Please try a different command.".format(nie.args[0]))

    except FileExistsError as fee:
        # If the output filename requested by the user already exists
        exit("Error: A file with the name {} already exists. Please choose a "
             "unique filename.".format(fee.filename))
    except FileNotFoundError as fnfe:
        exit("Error: No file named {} found. Please choose a different "
             "filename or collect new data.".format(fnfe.filename))

    except Exception as ex:
        # If anything else goes wrong, handle it here
        output.error_("An unexpected error occurred. Check log for details",
                      str(ex))
        exit(1)
