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
import logging
import os

from common import (
    exceptions,
    file,
    output,
    util,
    datatypes,
    config,
    consts
)
from collect.interface import (
    perf,
    iosnoop,
    smem,
    ebpf)
from collect.IO import write

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


def _get_collecter_instance(interface_name, time, parser):
    """
    A helper function that returns an instance of the appropriate interface

    :param interface_name: the name of the interface we want an instance of
    :param time: the time used as an option for the collecter
    :param parser: a config parser used to fetch collecter related options other
                   than the time
    :returns: a collecter for the interface
    """
    collecter = None
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

    return collecter


@util.log(logger)
def _collect_and_store(args, parser):
    """
    Calls the relevant functions that user chose and stores output in file.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.

    """

    # Use user output filename specified, otherwise create a unique one
    if args.outfile is not None:
        if os.path.isfile(args.outfile):
            print("A file named {} already exists! Overwrite? ".format(
                args.outfile), end="")
            answer = input()
            if answer not in ("y", "yes"):
                raise exceptions.AbortedException
        filename = file.DataFileName(args.outfile)
    else:
        filename = file.DataFileName()
    # Save latest filename to temporary file for display module
    filename.export_filename()

    # Use user specified time for data collection, otherwise config value
    time = args.time if args.time is not None else parser.get_default_time()

    all_interface_instances = []
    interfaces_seen = set()
    config_parser = config.Parser()
    for interface in args.interfaces:
        if interface in consts.interfaces_argnames:
            if interface in interfaces_seen:
                continue
            interfaces_seen.union({interface})

            collecter = _get_collecter_instance(interface, time, parser)
            all_interface_instances.append(collecter.collect())
        else:
            # The interface is not a valid one, might be an alias
            if not config_parser.has_option("Aliases", interface):
                raise argparse.ArgumentError(message="Arguments not recognised",
                                             argument=args)

            alias_interfaces = config_parser.get_option_from_section(
                "Aliases", interface).split(',')
            for alias_interface in alias_interfaces:
                if alias_interface in alias_interfaces:
                    continue
                interfaces_seen.union({interface})

                collecter = _get_collecter_instance(alias_interface, time,
                                                    parser)
                all_interface_instances.append(collecter.collect())

    # For each pair (collecter, data) in all_data, we need to pass the
    # datum generator collecter provides to the data
    writer = write.Writer()
    writer.write(all_interface_instances, str(filename))

    output.print_("Done.")


@util.log(logger)
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

    # Create parser object
    parser = argparse.ArgumentParser(prog="marple collect",
                                     description="Collect performance data")

    # Add options for the modules
    options = parser.add_argument_group()
    options.add_argument("interfaces", nargs='+',
                         help="Modules to be used when tracking. Options "
                              "include: cpusched, disklat, ipc, lib,"
                              "mallocstacks, memtime, memleak. The user can "
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
def main(argv, parser):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        a list of command line arguments from call in main module
    :param parser:
        the parser that reads the config; it is passed around to avoid creating
        multiple parser objects
    """

    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate functions to collect input
    _collect_and_store(args, parser)
