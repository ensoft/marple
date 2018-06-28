"""uses the middle level modules (mem, sched etc)"""
import argparse
import logging

logger = logging.getLogger(__name__)


def main(argv):
    args = args_parse(argv)
    if not (args.sched or args.lib or args.ipc or args.ipc or args.mem):
        print("At least one of the possible options needs to be specified!")
    if args.COMMAND == "collect":
        if args.sched:
            logger.info("recording scheduling data for {} seconds".format(args.t))
        if args.lib:
            logger.info("recording library loading data for {} seconds".format(args.t))
        if args.ipc:
            logger.info("recording ipc data for {} seconds".format(args.t))
        if args.mem:
            logger.info("recording memory data for {} seconds".format(args.t))
    elif args.COMMAND == "display":
        if args.sched:
            logger.info("displaying scheduling data")
        if args.lib:
            logger.info("displaying library loading data")
        if args.ipc:
            logger.info("displaying ipc scheduling data")
        if args.mem:
            logger.info("displaying mem scheduling data")


def args_parse(argv):
    """Parse the command line arguments"""

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
