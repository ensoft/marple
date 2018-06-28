"""uses the middle level modules (mem, sched etc)"""
import argparse
import logging

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

    if args.COMMAND == "collect":
        collect(args)
    elif args.COMMAND == "display":
        display(args)


def collect(args):
    """
    Collection part of the controller module.

    Deals with data collection.
    :param args:
        Command line arguments for data-collection
        Passed by main function

    """
    if args.sched:
        # Stub
        logger.info("recording scheduling data for {} seconds".format(args.t))
    if args.lib:
        # Stub
        logger.info("recording library loading data for {} seconds".format(args.t))
    if args.ipc:
        # Stub
        logger.info("recording ipc data for {} seconds".format(args.t))
    if args.mem:
        # Stub
        logger.info("recording memory data for {} seconds".format(args.t))


def display(args):
    """
    Displaying part of the controller module.

    Deals with displaying data.

    :param args:
        Command line arguments for data-display
        Passed by main function

    """
    if args.sched:
        # Stub
        logger.info("displaying scheduling data")
    if args.lib:
        # Stub
        logger.info("displaying library loading data")
    if args.ipc:
        # Stub
        logger.info("displaying ipc scheduling data")
    if args.mem:
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

    # Add options for the modules, optional but at least one (checked in main)
    parser.add_argument("-s", "--sched", action="store_true", help="scheduler module")
    parser.add_argument("-l", "--lib", action="store_true", help="library module")
    parser.add_argument("-i", "--ipc", action="store_true", help="ipc module")
    parser.add_argument("-m", "--mem", action="store_true", help="memory module")

    # Add flag and parameter for time in case of collect
    time = parser.add_argument_group()
    time.add_argument("-t", type=int, help='time in seconds that data is collected')

    # Add flag and parameter for displaying type in case of display
    d_type = parser.add_mutually_exclusive_group(required=True)
    d_type.add_argument("-n", action="store_true", help="numerical representation")
    d_type.add_argument("-g", action="store_true", help="graphical representation")

    # Add string command parameter that specifies whether the action is collect or display
    parser.add_argument("COMMAND", type=str, help='The choices are: {collect, display}')

    logger.info("parsing input arguments")

    return parser.parse_args(argv)
