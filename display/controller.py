# -------------------------------------------------------------
# controller.py - user interface, parses and applies display commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies display commands

Handles interaction between the output modules (flamegraph, g2, etc.)
It calls the relevant functions for each command.

"""

import argparse
import logging
import os

import common.output as output

logger = logging.getLogger('display.controller')
logger.setLevel(logging.DEBUG)

__all__ = "main"


def _display(args):
    """
    Displaying part of the controller module.

    Deals with displaying data.

    :param args:
        Command line arguments for data-display
        Passed by main function

    """
    logger.info("Display function."
                "Applying logic evaluating and applying input parameters")

    # Try to use the specified name, otherwise throw exception
    filename = args.file
    if filename is None or not os.path.isfile(filename):
        logger.debug("File not found, throwing exception")
        raise FileNotFoundError

    if args.sched:
        # Stub
        logger.info("Displaying scheduling data")
        _not_implemented("sched")
    elif args.lib:
        # Stub
        logger.info("Displaying library loading data")
        _not_implemented("sched")
    elif args.ipc:
        # Stub
        logger.info("Displaying ipc scheduling data")
        _not_implemented("sched")
    elif args.mem:
        # Stub
        logger.info("Displaying mem scheduling data")
        _not_implemented("sched")


def _not_implemented(name):
    """
    Displays error message and exits due to unimplemented functionality.

    Debugging function to give an error when something unfinished is called.

    :param name:
        name of the function that has not been implemented.

    """
    output.error_("The display command \"{}\" is currently not implemented. "
                  "Please try a different command.".format(name),
                  "The display function \"{}\" is not yet implemented. Exiting."
                  .format(name))


def _args_parse(argv):
    """
    Parses a display command.

    Arguments that are created:

            sched: CPU scheduling data
            lib: library load times
            ipc: ipc efficiency
            mem: memory allocation/deallocation

            -n: numerical representation of data
            -g: graphical representation of data

    :param argv:
        the arguments passed by the main function

    :return:
        an object containing the parsed command information

    Called by main when the program is started.

    """

    logger.info("Enter _args_parse function. Creates parser.")

    # Create parser object
    parser = argparse.ArgumentParser(prog="leap display",
                                     description="Display collected data "
                                     "in required format")

    # -----
    # Add options for the modules
    module_display = parser.add_mutually_exclusive_group(required=True)
    module_display.add_argument("-s", "--sched", action="store_true",
                                help="scheduler module")
    module_display.add_argument("-l", "--lib", action="store_true",
                                help="library module")
    module_display.add_argument("-i", "--ipc", action="store_true",
                                help="ipc module")
    module_display.add_argument("-m", "--mem", action="store_true",
                                help="memory module")

    # Add flag and parameter for displaying type in case of display
    type_display = parser.add_mutually_exclusive_group(required=True)
    type_display.add_argument("-n", action="store_true",
                              help="numerical representation as a table")
    type_display.add_argument("-g", action="store_true",
                              help="graphical representation as an image")

    # Add flag and parameter for filename
    filename = parser.add_argument_group()
    filename.add_argument("-f", "--file", type=str,
                          help="Input file where collected data "
                               "to display is stored")

    logger.info("Parsing input arguments")
    return parser.parse_args(argv)


def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        command line arguments from call in main

    """
    logger.info("Enter controller main function")

    # Parse arguments
    logger.info("Trying to parse input: {}".format(argv))
    args = _args_parse(argv)

    # Call the appropriate functions to display input
    try:
        _display(args)
    except FileNotFoundError:
        output.error_("Error: No file with that name found. "
                      "Please choose a different filename or collect new data.",
                      "file not found")
        exit(1)
