# -------------------------------------------------------------
# write.py - user interface, parses and applies collect commands
# June - August 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies collect commands

Parses user input and calls to the appropriate functions (
cpu data collection, stack data collection, etc).

"""
__all__ = "main"

import argparse
import asyncio
import logging
import os

from common import (
    exceptions,
    file,
    output,
    util,
    config,
    consts
)
from collect.interface import (
    perf,
    iosnoop,
    smem,
    ebpf
)
from collect.IO import write

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


@util.log(logger)
def main(argv, parser):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.
    Uses asyncio to asynchronously call collecters.

    :param argv:
        a list of command line arguments from call in main module
    :param parser:
        the parser that reads the config; it is passed around to avoid creating
        multiple parser objects
    """

    # Parse arguments
    args = _args_parse(argv)

    # Use user output filename specified, otherwise create a unique one
    if args.outfile:
        if os.path.isfile(args.outfile):
            output.print_("A file named {} already exists! Overwrite [y/n]? "
                          .format(args.outfile))
            if input() not in ("y", "yes"):
                raise exceptions.AbortedException
        filename = file.DataFileName(given_name=args.outfile)
    else:
        filename = file.DataFileName()

    # Save latest filename to temporary file for display module
    filename.export_filename()

    # Create event loop to collect and write data
    ioloop = asyncio.get_event_loop()
    # ioloop.set_debug(True)

    # Get collecter interfaces
    collecters = _get_collecters(args, parser)

    # Begin async collection
    futures = tuple(collecter.collect() for collecter in collecters)
    results = ioloop.run_until_complete(
        asyncio.gather(*futures)
    )

    # Write results
    for result in results:
        write.Writer.write(result, str(filename))

    # Cleanup
    ioloop.close()
    output.print_("Done.")


@util.log(logger)
def _args_parse(argv):
    """
    Creates a parser that parses the collect command.

    :param argv:
        a list of arguments passed by the main function.
    :return:
        an object containing the parsed command information.

    Called by main when the program is started.

    """

    # Create parser object
    parser = argparse.ArgumentParser(prog="marple collect",
                                     description="Collect performance data")

    # Add options for the modules
    options = parser.add_argument_group()
    options.add_argument("interfaces", nargs='+',
                         help="Modules to be used when tracking. Options "
                              "include: cpusched, disklat, ipc, lib,"
                              "mallocstacks, callstack, memtime, memleak, "
                              "memevents,"
                              " diskblockrq, perf_malloc. The user can "
                              "specify aliases for multiple such options in "
                              "the config file and use them here just like "
                              "with normal options")

    # Add flag and parameter for filename
    filename = parser.add_argument_group()
    filename.add_argument("-o", "--outfile", type=str,
                          help="Output file where collected data is stored")

    # Add flag and parameter for time
    time = parser.add_argument_group()
    time.add_argument("-t", "--time", type=int,
                      help="time in seconds that data is collected")

    return parser.parse_args(argv)


@util.log(logger)
def _get_collecters(args, parser):
    """
    Calls the relevant functions that user chose and stores output in file.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.

    """
    # Use user specified time for data collection, otherwise config value
    time = args.time if args.time else parser.get_default_time()

    # Determine all arguments specifying collecter interfaces
    args_seen = set()
    config_parser = config.Parser()
    for arg in args.interfaces:
        if arg in consts.interfaces_argnames:
            args_seen.add(arg)
        else:
            # The arg was not found, might be an alias
            if not config_parser.has_option("Aliases", arg):
                raise argparse.ArgumentError(message="Arguments not recognised",
                                             argument=args)
            alias_args = config_parser.get_option_from_section(
                "Aliases", arg).split(',')
            for alias_arg in alias_args:
                args_seen.add(alias_arg)

    return [_get_collecter_instance(arg, time, parser)
            for arg in args_seen]


def _get_collecter_instance(interface_name, time, parser):
    """
    A helper function that returns an instance of the appropriate interface

    :param interface_name: the name of the interface we want an instance of
    :param time: the time used as an option for the collecter
    :param parser: a config parser used to fetch collecter related options other
                   than the time
    :returns: a collecter for the interface
    """
    if interface_name == "cpusched":
        collecter = perf.SchedulingEvents(time)
    elif interface_name == "disklat":
        collecter = iosnoop.DiskLatency(time)
    elif interface_name == "ipc":
        collecter = ebpf.TCPTracer(time)
    elif interface_name == "lib":
        raise NotImplementedError("Lib not implemented")  # TODO
    elif interface_name == "mallocstacks":
        collecter = ebpf.MallocStacks(time)
    elif interface_name == "memtime":
        collecter = smem.MemoryGraph(time)
    elif interface_name == "callstack":
        options = perf.StackTrace.Options(parser.get_default_frequency(),
                                          parser.get_system_wide())
        collecter = perf.StackTrace(time, options)
    elif interface_name == "memleak":
        options = ebpf.Memleak.Options(10)
        collecter = ebpf.Memleak(time, options)
    elif interface_name == "memevents":
        collecter = perf.MemoryEvents(time)
    elif interface_name == "diskblockrq":
        collecter = perf.DiskBlockRequests(time)
    elif interface_name == "perf_malloc":
        collecter = perf.MemoryMalloc(time)
    else:
        raise NotImplementedError("{} not implemented!".format(interface_name))

    return collecter
