# -------------------------------------------------------------
# controller.py - user interface, parses and applies display commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies display commands

Handles interaction between the output modules (flamegraph, g2, etc.)
It calls the relevant functions for each command.

"""
import os

__all__ = "main"

import argparse
import logging

from common import file, output
from . import flamegraph as flamegraph

logger = logging.getLogger('display.controller')
logger.setLevel(logging.DEBUG)


def _display(args):
    """
    Displaying part of the controller module.

    Deals with displaying data.

    :param args:
        Command line arguments for data-display
        Passed by main function

    """
    logger.info("Display function. "
                "Applying logic evaluating and applying input parameters")

    # Try to use the specified name, otherwise use last one created by collect
    input_filename = args.file if args.file is not None else \
        file.import_out_filename()
    output_filename = file.find_unique_out_filename("display", ending=".svg")

    if args.cpu:
        # Stub
        logger.info("Displaying cpu scheduling data")
        raise NotImplementedError("display cpu data")
    elif args.ipc:
        # Stub
        logger.info("Displaying ipc data")
        raise NotImplementedError("display ipc data")
    elif args.lib:
        # Stub
        logger.info("Displaying library loading data")
        raise NotImplementedError("display library data")
    elif args.mem:
        # Stub
        logger.info("Displaying memory allocation data")
        raise NotImplementedError("display memory data")
    elif args.stack:
        logger.info("Displaying stack tracing data")
        if args.n:
            raise NotImplementedError("display-numeric stack data")
        else:
            flamegraph.make(input_filename, output_filename)
            flamegraph.show(output_filename)


def _args_parse(argv):
    """
    Create a parser that parses the display command.

    Arguments that are created in the parser object:

        cpu: CPU scheduling data
        ipc: ipc efficiency
        lib: library load times
        mem: memory allocation/ deallocation
        stack: stack tracing

        file f: the filename of the file that stores the output

        -g: graphical representation of data (default)
        -n: numerical representation of data


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
    type_display = parser.add_mutually_exclusive_group()
    type_display.add_argument("-g", action="store_true",
                              help="graphical representation as an image ("
                                   "default)")
    type_display.add_argument("-n", action="store_true",
                              help="numerical representation as a table")

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
    logger.info("Enter controller main function with arguments {}".format(argv))

    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate functions to display input
    _display(args)

