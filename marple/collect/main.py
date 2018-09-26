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

__all__ = (
    "main",
)

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
    collection_time = parser.add_argument_group()
    collection_time.add_argument(
        "-t", "--time", type=int, help="specify the duration for data "
                                       "collection (in seconds).")

    return parser.parse_args(argv)


@util.log(logger)
def _get_collecters(subcommands, collection_time):
    """
    Calls the relevant functions that user chose and stores output in file.

    :param subcommands:
        The subcommands that tell which collecters to get
    :param collection_time:
        The time for collection


    """
    # Determine all arguments specifying collecter interfaces
    args_seen = set()
    for subcommand in subcommands:
        if subcommand in consts.interfaces_argnames:
            args_seen.add(subcommand)
        else:
            if not config.config.has_option("Aliases", subcommand):
                raise ValueError('One or more subcommands or aliases invalid!')
            # Look for aliases
            alias_args = set(config.get_option_from_section(
                "Aliases", subcommand).split(','))
            args_seen = args_seen.union(alias_args)

    return [_get_collecter_instance(arg, collection_time) for arg in args_seen]


def _get_collecter_instance(interface_name, collection_time):
    """
    A helper function that returns an instance of the appropriate interface

    :param interface_name:
        the name of the interface we want an instance of
    :param collection_time:
        the time used as an option for the collecter

    :returns:
        a collecter for the interface

    """
    interfaces = consts.InterfaceTypes
    interface = interfaces(interface_name)

    if interface is interfaces.SCHEDEVENTS:
        collecter = perf.SchedulingEvents(collection_time)
    elif interface is interfaces.DISKLATENCY:
        collecter = iosnoop.DiskLatency(collection_time)
    elif interface is interfaces.TCPTRACE:
        collecter = ebpf.TCPTracer(collection_time)
    elif interface is interfaces.MALLOCSTACKS:
        collecter = ebpf.MallocStacks(collection_time)
    elif interface is interfaces.MEMTIME:
        collecter = smem.MemoryGraph(collection_time)
    elif interface is interfaces.CALLSTACK:
        options = perf.StackTrace.Options(
            config.get_option_from_section("General", "frequency", "int"),
            config.get_option_from_section("General", "system_wide"))
        collecter = perf.StackTrace(collection_time, options)
    elif interface is interfaces.MEMLEAK:
        options = ebpf.Memleak.Options(
            config.get_option_from_section("General", "top_processes", "int"))
        collecter = ebpf.Memleak(collection_time, options)
    elif interface is interfaces.MEMEVENTS:
        collecter = perf.MemoryEvents(collection_time)
    elif interface is interfaces.DISKBLOCK:
        collecter = perf.DiskBlockRequests(collection_time)
    elif interface is interfaces.PERF_MALLOC:
        collecter = perf.MemoryMalloc(collection_time)
    else:
        raise NotImplementedError(interface_name)

    return collecter


async def _loading_bar(collection_time):
    """
    Function that displays a progress bar during collection

    We update the bar asynchronously every half a second, while collecting
    data.

    :param collection_time: the colelction time for the collectors
    """

    bar_width = 60
    for i in range(2 * collection_time + 1):
        progress = int((i / (2 * collection_time)) * bar_width)
        # \r - carriage return so that we overwrite the progress bar each
        #      time it is drawn
        # \033 - escape character so we can specify colors
        # [91m - red
        # [0m  - reset color to normal (from red)
        print("\r\033[91mProgress:\033[0m [{}] \033[91m{}%\033[0m".format(
            progress * "#" + (bar_width - progress) * " ",
            int(progress * 100 / bar_width)),
            end='', flush=True)
        await asyncio.sleep(0.5)
    print("")


@util.log(logger)
def _collect_results(collecters, collection_time):
    """
    Helper function that async collects all the data using the asyncio lib

    :param collecters: the collecter instances that we use to collect data
    :param collection_time: the collection time used by the collectors
    :return: the data gathered as a list of data objects

    """
    # Create event loop to collect and write data
    ioloop = asyncio.get_event_loop()

    # Begin async collection
    futures = tuple(collecter.collect() for collecter in collecters)
    results = ioloop.run_until_complete(
        asyncio.gather(*futures, _loading_bar(collection_time))
    )
    ioloop.close()

    results = results[:-1]  # Get rid of the loading bar, not relevant

    # Now, if a result has its `datum_generator` field None we know it errored
    errored = list(filter(lambda res: res.datum_generator is None,
                          results))
    not_errored = list(filter(lambda res: res.datum_generator is not None,
                              results))

    # We deal with the errored collecters
    if errored:
        print("Interfaces {} errored. No data collected for them. "
              "Check if the collection tools are installed "
              "correctly. Check the logs for more info about the errors.".
            format(','.join(map(lambda data: data.interface.value, errored)))
        )

    # Return only the unerrored results
    return not_errored


@util.log(logger)
def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user in the
    terminal.
    Uses asyncio to asynchronously collect data using the appropriate
    collectors.

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

    # Use user specified time for data collection, otherwise config value
    collection_time = args.time if args.time else config.get_default_time()

    # Get collecter interfaces
    collecters = _get_collecters(args.subcommands, collection_time)

    # Asynchronously collect everything
    results = _collect_results(collecters, collection_time)

    with marple.common.data_io.Writer(str(filename)) as writer:
        writer.write(results)

    output.print_("Done.")
