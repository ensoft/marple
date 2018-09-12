# -------------------------------------------------------------
# main.py - user interface, parses and applies collect commands
# June - August 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies collect commands

Parses user input and calls to the appropriate functions (
cpu data collection, stack data collection, etc).

"""
import marple.common.data_io

__all__ = "main"

import argparse
import asyncio
import logging
import os
import textwrap

from marple.common import (
    file,
    output,
    util,
    config,
    consts
)
from marple.collect.interface import (
    perf,
    iosnoop,
    smem,
    ebpf
)

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


@util.log(logger)
def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.
    Uses asyncio to asynchronously call collecters.

    :param argv:
        a list of command line arguments from call in main module

    """

    # Parse arguments
    args = _args_parse(argv)

    # Use user output filename specified, otherwise create a unique one
    if args.outfile:
        if os.path.isfile(args.outfile):
            output.print_("A file named {} already exists! Overwrite [y/n]? "
                          .format(args.outfile))
            if input() not in ("y", "yes", "Y"):
                output.error_("Aborted.\n",
                              "User aborted collect due to file overwrite.")
                exit(1)
        filename = file.DataFileName(given_name=args.outfile)
    else:
        filename = file.DataFileName()

    # Save latest filename to temporary file for display module
    filename.export_filename()

    # Get collecter interfaces
    collecters = _get_collecters(args)

    # Create event loop to collect and write data
    ioloop = asyncio.get_event_loop()
    # ioloop.set_debug(True)

    # Create function to display loading bar when collecting
    async def loading_bar():
        bar_width = 60

        time = args.time if args.time else config.get_default_time()
        for i in range(2 * time + 1):
            progress = int((i / (2 * time)) * bar_width)
            print("\r\033[91mProgress:\033[0m [{}] \033[91m{}%\033[0m".format(
                progress * "#" + (bar_width - progress) * " ",
                int(progress * 100 / bar_width)),
                end='', flush=True)
            await asyncio.sleep(0.5)
        print("")

    # Begin async collection
    futures = tuple(collecter.collect() for collecter in collecters)
    results = ioloop.run_until_complete(
        asyncio.gather(*futures, loading_bar())
    )

    # Write results
    with marple.common.data_io.Writer(str(filename)) as writer:
        writer.write(results[:-1])

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
    parser = argparse.ArgumentParser(
        prog="marple --collect", description="Collect performance data.",
        formatter_class=argparse.RawTextHelpFormatter, epilog="\n\n")

    # Add options for the modules
    options = parser.add_argument_group()

    user_groups = config.get_section('Aliases').items()

    user_groups_help = [name + ": " + interfaces
                        for name, interfaces in user_groups]

    subcommand_help = (
            "interfaces to use for data collection.\n\n"
            "When multiple interfaces are specified, they will all be used "
            "to collect data simultaneously.\n"
            "Users can also define their own groups of interfaces using "
            "the config file.\n\n"
            "Built-in interfaces are:\n"
            ">" + ", ".join(consts.interfaces_argnames) + "\n"
            "Current user-defined groups are:\n"
            ">" + "\n>".join(user_groups_help)
    )

    line_length = 55
    wrapped = ""
    for line in subcommand_help.split('\n'):
        if len(line) > line_length:
            line = '\n'.join(textwrap.wrap(line, width=line_length,
                                           break_long_words=False))
        if line.startswith(">"):
            line = textwrap.indent(line[1:], prefix="    ")
        wrapped = '\n'.join((wrapped, line)).lstrip()

    options.add_argument(
        "subcommands", nargs='+',
        choices=consts.interfaces_argnames + [name for name, _ in user_groups],
        metavar="subcommand",
        help=wrapped
    )

    filename_help = (
        "specify the data output file.\n\n"
        "By default this will create a "
        "directory named 'marple_out' in the current working directory, "
        "and files will be named by date and time.\n"
        "Specifying a file name "
        "will write to the 'marple_out' directory - pass in a path "
        "to override the save location too."
    )
    wrapped = ""
    for line in filename_help.split('\n'):
        if len(line) > line_length:
            line = '\n'.join(textwrap.wrap(line, width=line_length,
                                           break_long_words=False))
        wrapped = '\n'.join((wrapped, line)).lstrip()

    # Add flag and parameter for filename
    filename = parser.add_argument_group()
    filename.add_argument(
        "-o", "--outfile", type=str, help=wrapped)

    # Add flag and parameter for time
    time = parser.add_argument_group()
    time.add_argument(
        "-t", "--time", type=int, help="specify the duration for data "
                                       "collection (in seconds).")

    return parser.parse_args(argv)


@util.log(logger)
def _get_collecters(args):
    """
    Calls the relevant functions that user chose and stores output in file.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.

    """
    # Use user specified time for data collection, otherwise config value
    time = args.time if args.time else config.get_default_time()

    # Determine all arguments specifying collecter interfaces
    args_seen = set()
    for arg in args.subcommands:
        if arg in consts.interfaces_argnames:
            args_seen.add(arg)
        else:
            assert config.config.has_option("Aliases", arg)
            # Look for aliases
            alias_args = set(config.get_option_from_section(
                "Aliases", arg).split(','))
            args_seen = args_seen.union(alias_args)

    return [_get_collecter_instance(arg, time)
            for arg in args_seen]


def _get_collecter_instance(interface_name, time):
    """
    A helper function that returns an instance of the appropriate interface

    :param interface_name:
        the name of the interface we want an instance of
    :param time:
        the time used as an option for the collecter

    :returns:
        a collecter for the interface

    """
    interfaces = consts.InterfaceTypes
    interface = interfaces(interface_name)

    assert interface in interfaces

    if interface is interfaces.SCHEDEVENTS:
        collecter = perf.SchedulingEvents(time)
    elif interface is interfaces.DISKLATENCY:
        collecter = iosnoop.DiskLatency(time)
    elif interface is interfaces.TCPTRACE:
        collecter = ebpf.TCPTracer(time)
    # elif interface is interfaces.LIB:
    #     raise NotImplementedError("Lib not implemented")  # TODO
    elif interface is interfaces.MALLOCSTACKS:
        collecter = ebpf.MallocStacks(time)
    elif interface is interfaces.MEMTIME:
        collecter = smem.MemoryGraph(time)
    elif interface is interfaces.CALLSTACK:
        options = perf.StackTrace.Options(
            config.get_option_from_section("General", "frequency", "int"),
            config.get_option_from_section("General", "system_wide"))
        collecter = perf.StackTrace(time, options)
    elif interface is interfaces.MEMLEAK:
        options = ebpf.Memleak.Options(10)  # TODO CHANGE HARDCODED
        collecter = ebpf.Memleak(time, options)
    elif interface is interfaces.MEMEVENTS:
        collecter = perf.MemoryEvents(time)
    elif interface is interfaces.DISKBLOCK:
        collecter = perf.DiskBlockRequests(time)
    elif interface is interfaces.PERF_MALLOC:
        collecter = perf.MemoryMalloc(time)
    else:
        raise NotImplementedError("{} not implemented!".format(interface_name))

    return collecter
