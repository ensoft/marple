#!/usr/bin/env python3

# -------------------------------------------------------------
# main.py - Initiates the program
# June - August 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Initiates the program.

Sets up logging, calls the appropriate controller (collect or display) and
deals with exceptions.

"""
__all__ = ["main"]

import sys
import os
import logging

from collect.controller import main as collect_controller
from common import (
    exceptions,
    output,
    paths,
    config
)
from display import controller as display_controller

# use marple log across the whole module
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)


def main():

    # Check whether user is root, otherwise exit
    global logger
    if os.geteuid() != 0:
        exit("Error: You need to have root privileges to run marple.")

    # Make sure the directories marple accesses actually exist.
    # TODO: create config directory?
    paths.create_directories()
    parser = config.Parser()


    try:
        # create a unique and descriptive logfile using timestamp and process id
        # in the standard linux log file directory
        logging.basicConfig(format="%(asctime)s %(name)-12s "
                                   "%(levelname)-8s %(message)s",
                            datefmt="%m-%d %H:%M",
                            filename=paths.LOG_DIR + "marple" + str(os.getpid())
                                    + ".log",
                            filemode="w")

    except PermissionError:
        # if setting up the logging fails there is something wrong with the
        #   system
        exit("Fatal Error: Failed to set up logging due to missing privileges "
             "to the log directory!\n Make sure you have root privileges and "
             "that you are allowed to access the log directory as root.")

    except Exception as ex:
        # if setting up the logging fails there is something wrong with the
        #   system
        exit("Fatal Error: Failed to set up logging! {}".format(str(ex)))

    logger.info("Application started.")
    try:
        # Call main function with command line arguments excluding argv[0]
        # (program name: marple) and argv[1] (function name: {collect,display})
        if len(sys.argv) < 2:
            output.print_("usage: marple COMMAND\n The COMMAND "
                          "can be either \"collect\" or \"display\"")
        elif sys.argv[1] == "collect":
            collect_controller.main(sys.argv[2:], parser)
        elif sys.argv[1] == "display":
            display_controller.main(sys.argv[2:])
        else:
            output.print_("usage: marple COMMAND\n The COMMAND "
                          "can be either \"collect\" or \"display\"")
    except exceptions.AbortedException:
        # If the user decides to abort
        output.error_("Aborted.", "Execution was aborted by the user.")
        exit(1)
    except NotImplementedError as nie:
        # if the requested function is not implemented, exit with an error
        output.error_("The command \"{}\" is currently not implemented. "
                      "Please try a different command.".format(nie.args[0]),
                      "Exited with a NotImplementedError. Command: {}"
                      .format(nie.args[0]))
        exit(1)
    except FileExistsError as fee:
        # If the output filename requested by the user already exists
        output.error_("A file with the name {} already exists. Please "
                      "choose a unique filename.".format(fee.filename),
                      "Exited with a FileExistsError. File: {}".format(
                          fee.filename))
        exit(1)
    except FileNotFoundError as fnfe:
        # If no input file was found
        output.error_(" No file named {} found. Please choose a "
                      "different input file.".format(fnfe.filename),
                      "Exited with a FileNotFoundError. Filename: {}".format(
                          fnfe.filename))
        exit(1)
    except exceptions.NotSupportedException as nse:
        # If the target kernel does not meet the requirements
        output.error_("You need to have kernel {} or above for this "
                      "functionality".format(nse.required_kernel),
                      "Exited with NotSupportedError. Required Kernel: "
                      "{}".format(nse.required_kernel))
        exit(1)
    except IsADirectoryError as iade:
        # If user tried to save output under a name that is a directory name
        output.error_("Cannot use filename {}, because there is a directory "
                      "with that name. Please choose a different "
                      "filename".format(iade.filename),
                      "Exited with an IsADirectoryError.")
    except Exception as ex:
        # If anything else goes wrong, handle it here
        output.error_("An unexpected error occurred. Check log for details.",
                      str(ex))
        exit(1)


if __name__ == "__main__":
    main()
