"""
Controller script.

Handles interaction between the user and the middle level modules (mem, sched etc)

"""
import argparse
import logging
from src.modules import sched
from src.common import file, config

logger = logging.getLogger(__name__)


def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        command line arguments from call in main

    """
    args = args_parse(argv)

    if not (args.sched or args.lib or args.ipc or args.ipc or args.mem):
        logger.error("At least one of the possible options needs to be specified!")
        return

    # Use the user specified filename if there is one, otherwise create a unique one
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

    if args.COMMAND == "collect":
        collect(args, filename, time)

    elif args.COMMAND == "display":
        display(args, filename)


def collect(args, filename, time):
    """
    Collection part of the controller module.

    Deals with data collection.

    :param args:
        Command line arguments for data-collection.
        Passed by main function.
    :param filename:
        The location where the file is stored.
    :param time:
        The time in seconds for which to collect the data.

    """
    if args.sched:
        logger.info("recording scheduling data for {} seconds".format(time))
        sched.collect_all(time, filename)

    if args.lib:
        # Stub
        logger.info("recording library loading data for {} seconds".format(time))
    if args.ipc:
        # Stub
        logger.info("recording ipc data for {} seconds".format(time))
    if args.mem:
        # Stub
        logger.info("recording memory data for {} seconds".format(time))


def display(args, filename):
    """
    Displaying part of the controller module.

    Deals with displaying data.

    :param args:
        Command line arguments for data-display
        Passed by main function
    :param filename:
        The location where the file is stored.

    """

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


def args_parse(argv):
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
    parser = argparse.ArgumentParser(description='Collect and process performance data')

    module = parser.add_mutually_exclusive_group()

    # Add options for the modules, optional but at least one (checked in main)
    module.add_argument("-s", "--sched", action="store_true", help="scheduler module")
    module.add_argument("-l", "--lib", action="store_true", help="library module")
    module.add_argument("-i", "--ipc", action="store_true", help="ipc module")
    module.add_argument("-m", "--mem", action="store_true", help="memory module")

    # Add flag and parameter for displaying type in case of display
    d_type = parser.add_mutually_exclusive_group()
    d_type.add_argument("-n", action="store_true", help="numerical representation")
    d_type.add_argument("-g", action="store_true", help="graphical representation")

    # Add flag and parameter for time in case of collect
    time = parser.add_argument_group()
    time.add_argument("-t", "--time", type=int, help="time in seconds that data is collected")

    # Add flag and parameter for filename
    filename = parser.add_argument_group()
    filename.add_argument("-f", "--file", type=str, help="Output file where collected data is stored")

    # Add string command parameter that specifies whether the action is collect or display
    parser.add_argument("COMMAND", type=str, help='The choices are: {collect, display}')

    logger.info("parsing input arguments")

    return parser.parse_args(argv)
