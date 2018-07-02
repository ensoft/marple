# -------------------------------------------------------------
# controller.py - user interface, parses and applies commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies commands

Handles interaction between the user and the middle level
functionality (mem, sched etc).
It calls the relevant functions for each command.

"""

import argparse
import logging
import os
from . import sched
from ..common import file, config

logger = logging.getLogger('leap-log')

__all__ = "main"


def _collect(args):
    """
    Collection part of the controller module.

    Deals with data collection.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.

    """

    # Use the user specified filename if there is one,
    # otherwise create a unique one
    if args.file is None:
        filename = file.create_name()
        logger.info("Using default filename {} "
                    "as no filename was specified".format(filename))
    else:
        filename = args.file

    # Collect data for user specified amount of time, otherwise standard value
    if args.time is None:
        time = config.get_default_time()
        logger.info("Using default time {}s "
                    "as no time was specified".format(time))
    else:
        time = args.time

    if args.sched:
        logger.info("recording scheduling data for {} seconds".format(time))
        sched.collect_all(time, filename)

    if args.lib:
        # Stub
        logger.info("recording library loading data "
                    "for {} seconds".format(time))
    if args.ipc:
        # Stub
        logger.info("recording ipc data for {} seconds".format(time))
    if args.mem:
        # Stub
        logger.info("recording memory data for {} seconds".format(time))


def _display(args):
    """
    Displaying part of the controller module.

    Deals with displaying data.

    :param args:
        Command line arguments for data-display
        Passed by main function

    """
    # Use the user specified filename if there is one,
    # otherwise create a unique one
    if args.file is None:
        filename = file.create_name()
        logger.info("Using default filename {} "
                    "as no filename was specified".format(filename))
    else:
        filename = args.file

    if args.sched:
        # Stub
        logger.info("displaying scheduling data")
    elif args.lib:
        # Stub
        logger.info("displaying library loading data")
    elif args.ipc:
        # Stub
        logger.info("displaying ipc scheduling data")
    elif args.mem:
        # Stub
        logger.info("displaying mem scheduling data")


def _args_parse(argv):
    """
    Parse the command line arguments.

    Called by main when the program is started.

    Arguments that are created:

        sched: CPU scheduling data
        lib: library load times
        ipc: ipc efficiency
        mem: memory allocation/deallocation

        time t: time in seconds to record data

        -n: numerical representation of data
        -g: graphical representation of data

    """

    # Create parser object
    parser = argparse.ArgumentParser(prog="leap",
                                     description="Collect and display "
                                                 "performance data")

    # Create two sub-parsers for the two kinds of command, collect and display
    subparsers = parser.add_subparsers(dest="command")

    # ---------------
    
    # Collect Parser
    parser_collect = subparsers.add_parser("collect",
                                           help="Collect data to display")

    # Add options for the modules
    module_collect = parser_collect.add_mutually_exclusive_group(required=True)
    module_collect.add_argument("-s", "--sched", action="store_true",
                                help="scheduler module")
    module_collect.add_argument("-l", "--lib", action="store_true",
                                help="library module")
    module_collect.add_argument("-i", "--ipc", action="store_true",
                                help="ipc module")
    module_collect.add_argument("-m", "--mem", action="store_true",
                                help="memory module")

    # Add flag and parameter for filename
    filename = parser_collect.add_argument_group()
    filename.add_argument("-f", "--file", type=str,
                          help="Output file where collected data is stored")

    # Add flag and parameter for time
    time = parser_collect.add_argument_group()
    time.add_argument("-t", "--time", type=int,
                      help="time in seconds that data is collected")

    # Set default function
    parser_collect.set_defaults(func=_collect)

    # ---------------

    # Display Parser
    parser_display = subparsers.add_parser("display",
                                           help="Display collected data "
                                                "in required format")

    # Add options for the modules
    module_display = parser_display.add_mutually_exclusive_group(required=True)
    module_display.add_argument("-s", "--sched", action="store_true",
                                help="scheduler module")
    module_display.add_argument("-l", "--lib", action="store_true",
                                help="library module")
    module_display.add_argument("-i", "--ipc", action="store_true",
                                help="ipc module")
    module_display.add_argument("-m", "--mem", action="store_true",
                                help="memory module")

    # Add flag and parameter for displaying type in case of display
    type_display = parser_display.add_mutually_exclusive_group(required=True)
    type_display.add_argument("-n", action="store_true",
                              help="numerical representation")
    type_display.add_argument("-g", action="store_true",
                              help="graphical representation")

    # Add flag and parameter for filename
    filename = parser_display.add_argument_group()
    filename.add_argument("-f", "--file", type=str,
                          help="Input file where collected data "
                               "to display is stored")
    # Set default function
    parser_display.set_defaults(func=_display)

    # ---------------

    logger.info("parsing input arguments")

    return parser.parse_args(argv)


def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        command line arguments from call in main

    """
    # Check whether user is root, otherwise exit
    if os.geteuid() != 0:
        exit("You need to have root privileges to run leap.")

    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate function, either collect or display
    args.func(args)
