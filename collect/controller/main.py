# -------------------------------------------------------------
# write.py - user interface, parses and applies collect commands
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies collect commands

Parses user input and calls to the appropriate functions (
cpu data collection, stack data collection, etc).

"""
__all__ = "main"

import argparse
import logging
import os

from common import (
    config,
    exceptions,
    file,
    output
)
from collect.controller import (
    cpu,
    disk_io,
    ipc,
    libs,
    mem,
    stack
)


# COLLECTION_TIME - int constant specifying the default data collection time
_COLLECTION_TIME = 10

logger = logging.getLogger('collect.controller.main')
logger.setLevel(logging.DEBUG)


def _collect_and_store(args):
    """
    Calls the relevant functions that user chose and stores output in file.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.

    """
    logger.info("Enter collect and store function. Applying logic evaluating "
                "and applying input parameters: %s"
                , args)

    # Use user output filename specified, otherwise create a unique one
    if args.outfile is not None:
        if os.path.isfile(args.outfile):
            print("A file named {} already exists! Overwrite? ".format(
                args.outfile), end="")
            answer = input()
            if answer not in ("y", "yes"):
                raise exceptions.AbortedException
        filename = args.outfile
    else:
        filename = file.find_unique_out_filename("collect", ending=".data")

    # Save latest filename to temporary file for display module
    file.export_out_filename(filename)

    # Use user specified time for data collection, otherwise standard value
    time = args.time if args.time is not None else config.get_default_time() \
        if config.get_default_time() is not None else _COLLECTION_TIME

    # Call appropriate function based on user input
    if args.cpu:
        cpu.sched_collect_and_store(time, filename)
    elif args.disk:
        disk_io.collect_and_store(time, filename)
    elif args.ipc:
        ipc.collect_and_store(time, filename)
    elif args.lib:
        libs.collect_and_store(time, filename)
    elif args.mem:
        mem.collect_and_store(time, filename)
    elif args.stack:
        stack.collect_and_store(time, filename)

    output.print_("Done.")


def _args_parse(argv):
    """
    Creates a parser that parses the collect command.

    Arguments that are created in the parser object:

        cpu: CPU scheduling data
        disk: disk I/O data
        ipc: ipc efficiency
        lib: library load times
        mem: memory allocation/ deallocation
        stack: stack tracing

        outfile o: the filename of the file that stores the output
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
                                help="gather cpu scheduling events")
    module_collect.add_argument("-d", "--disk", action="store_true",
                                help="monitor disk input/output")
    module_collect.add_argument("-p", "--ipc", action="store_true",
                                help="trace inter-process communication")
    module_collect.add_argument("-l", "--lib", action="store_true",
                                help="gather library load times")
    module_collect.add_argument("-m", "--mem", action="store_true",
                                help="trace memory allocation/ deallocation")
    module_collect.add_argument("-s", "--stack", action="store_true",
                                help="gather general call stack tracing data")

    # Add flag and parameter for filename
    filename = parser.add_argument_group()
    filename.add_argument("-o", "--outfile", type=str,
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
    logger.info("Enter controller main function with arguments %s", str(argv))

    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate functions to collect input
    _collect_and_store(args)
