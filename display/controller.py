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
from . import flamegraph as flamegraph

logger = logging.getLogger('display.controller')
logger.setLevel(logging.DEBUG)

__all__ = "main"

OUT_DIR = "out/"
FLAME_IMAGE = OUT_DIR + "flame.svg"


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
    filename = OUT_DIR + args.file
    if filename is None or not os.path.isfile(os.fspath(filename)):
        logger.debug("File not found (filename={}), throwing "
                     "exception".format(filename))
        raise FileNotFoundError

    if args.cpu:
        # Stub
        logger.info("Displaying cpu scheduling data")
        _not_implemented("cpu")
    elif args.ipc:
        # Stub
        logger.info("Displaying ipc data")
        _not_implemented("ipc")
    elif args.lib:
        # Stub
        logger.info("Displaying library loading data")
        _not_implemented("lib")
    elif args.mem:
        # Stub
        logger.info("Displaying memory allocation data")
        _not_implemented("mem")
    elif args.stack:
        logger.info("Displaying stack tracing data")
        if args.n:
            _not_implemented("stack -n")
        else:
            flamegraph.make(filename, FLAME_IMAGE)
            flamegraph.show(FLAME_IMAGE)


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

        cpu: CPU scheduling data
        ipc: ipc efficiency
        lib: library load times
        mem: memory allocation/ deallocation
        stack: stack tracing

        file f: the filename of the file that stores the output

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
    parser = argparse.ArgumentParser(prog="marple display",
                                     description="Display collected data "
                                     "in required format")

    # -----
    # Add options for the modules
    module_display = parser.add_mutually_exclusive_group(required=True)

    module_display.add_argument("-c", "--cpu", action="store_true",
                                help="cpu scheduling data")
    module_display.add_argument("-i", "--ipc", action="store_true",
                                help="ipc efficiency")
    module_display.add_argument("-l", "--lib", action="store_true",
                                help="library load times")
    module_display.add_argument("-m", "--mem", action="store_true",
                                help="memory allocation/ deallocation")
    module_display.add_argument("-s", "--stack", action="store_true",
                                help="stack tracing")

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
    except FileNotFoundError as fnfe:
        output.error_("Error: No file with name {} found. "
                      "Please choose a different filename or collect new data."
                      .format(fnfe.filename),
                      "file not found error: {}".format(fnfe.filename))
        exit(1)
