# -------------------------------------------------------------
# controller/main.py - user interface, parses and applies collect commands
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies collect commands

Handles interaction between the user and the middle level
functionality (mem, sched etc).
It calls the relevant functions for each command.

"""

import argparse
import logging
import os

from . import cpu
from . import stack
import common.output as output
import common.config as config
import common.file as file
import collect.converter.main as converter

COLLECTION_TIME = 10
COLLECTION_FREQUENCY = 99

logger = logging.getLogger('collect.controller.main')
logger.setLevel(logging.DEBUG)

__all__ = "main"


def _collect_and_store(args):
    """
    Collection part of the controller module.

    Deals with data collection.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.

    """
    logger.info("Collect function. "
                "Applying logic evaluating and applying input parameters")

    # Use the user specified filename if there is one,
    # otherwise create a unique one
    if args.file is None:
        filename = file.create_name()
        logger.info("Trying to generate default filename "
                    "as no filename was specified")
        i = 5
        while os.path.isfile(filename) and i > 0:
            filename = file.create_name()
            i -= 1

        if os.path.isfile(filename):
            output.error_("Unable to create a unique filename. "
                          "Please choose a filename and try again.",
                          "Failed to generate unique filename! Exiting! "
                          "Name: {}".format(filename))
            exit(1)
    else:
        filename = args.file

    if os.path.isfile(filename):
        logger.debug("File already exist. Filename: {}. Throwing exception"
                     .format(filename))
        raise FileExistsError

    # Use user specified time for data collection, otherwise standard value
    if args.time is None:
        time = config.get_default_time()
        if time is None:
            time = COLLECTION_TIME
        logger.info("Using default time {} s "
                    "as no time was specified".format(time))
    else:
        time = args.time

    # Use default frequency for data collection
    frequency = config.get_default_frequency()
    if frequency is None:
        frequency = COLLECTION_FREQUENCY
    logger.info("Using default frequency {} Hz ".format(frequency))

    if args.cpu:
        logger.info("Recording cpu scheduling data for {} seconds".format(time))
        generator = cpu.collect(time)
        converter.create_cpu_event_data(generator=generator, filename=filename)
    elif args.ipc:
        # Stub
        logger.info("Recording ipc data for {} seconds".format(time))
        _not_implemented("ipc")
    elif args.lib:
        # Stub
        logger.info("Recording library loading data "
                    "for {} seconds".format(time))
        _not_implemented("lib")
    elif args.mem:
        # Stub
        logger.info("Recording memory data for {} seconds".format(time))
        _not_implemented("mem")
    elif args.stack:
        # Stub
        logger.info("Recording stack data for {} seconds".format(time))
        generator = stack.collect(time, frequency)
        converter.create_stack_data(generator=generator, filename=filename)


def _not_implemented(name):
    """
    Displays error message and exits due to unimplemented functionality.

    Debugging function to give an error when something unfinished is called.

    :param name:
        name of the function that has not been implemented.

    """
    output.error_("The collect command \"{}\" is currently not implemented. "
                  "Please try a different command.".format(name),
                  "The collect function \"{}\" is not yet implemented. Exiting."
                  .format(name))


def _args_parse(argv):
    """
    Parses a collect command.

    Arguments that are created:

        cpu: CPU scheduling data
        ipc: ipc efficiency
        lib: library load times
        mem: memory allocation/ deallocation
        stack: stack tracing

        file f: the filename of the file that stores the output
        time t: time in seconds to record data

    :param argv:
        a list of arguments passed by the main function.

    :return:
        an object containing the parsed command information.

    Called by main when the program is started.

    """

    logger.info("Enter _args_parse function. Creates parser.")

    # Create parser object
    parser = argparse.ArgumentParser(prog="marple collect",
                                     description="Collect performance data")

    # Add options for the modules
    module_collect = parser.add_mutually_exclusive_group(required=True)

    module_collect.add_argument("-c", "--cpu", action="store_true",
                                help="cpu scheduling data")
    module_collect.add_argument("-i", "--ipc", action="store_true",
                                help="ipc efficiency")
    module_collect.add_argument("-l", "--lib", action="store_true",
                                help="library load times")
    module_collect.add_argument("-m", "--mem", action="store_true",
                                help="memory allocation/ deallocation")
    module_collect.add_argument("-s", "--stack", action="store_true",
                                help="stack tracing")

    # Add flag and parameter for filename
    filename = parser.add_argument_group()
    filename.add_argument("-f", "--file", type=str,
                          help="Output file where collected data is stored")

    # Add flag and parameter for time
    time = parser.add_argument_group()
    time.add_argument("-t", "--time", type=int,
                      help="time in seconds that data is collected")

    logger.info("Parsing input arguments")
    return parser.parse_args(argv)


def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        a list of command line arguments from call in main module

    """
    logger.info("Enter controller main function")

    # Parse arguments
    logger.info("Trying to parse input: {}".format(argv))
    args = _args_parse(argv)

    # Call the appropriate functions to collect input
    try:
        _collect_and_store(args)
    except FileExistsError:
        output.error_("A file with that name already exists. "
                      "Please choose a unique filename.",
                      "filename already exists")
        exit(1)
    except FileNotFoundError:
        output.error_("Error: No file with that name found. "
                      "Please choose a different filename or collect new data.",
                      "file not found")
        exit(1)
