"""uses the middle level modules (mem, sched etc)"""
import argparse


def main(argv):
    args = args_parse(argv)
    if not (args.sched or args.lib or args.ipc or args.ipc or args.mem):
        print("At least one of the possible options needs to be specified!")
    if args.COMMAND == "collect":
        if args.sched:
            print("recording scheduling data for {} seconds".format(args.t))
    elif args.COMMAND == "display":
        if args.sched:
            print("displaying scheduling data")


def args_parse(argv):
    parser = argparse.ArgumentParser(description='Collect and process performance data')
    # collect = parser.add_mutually_exclusive_group('collect')
    parser.add_argument("-s", "--sched", action="store_true")
    parser.add_argument("-l", "--lib", action="store_true")
    parser.add_argument("-i", "--ipc", action="store_true")
    parser.add_argument("-m", "--mem", action="store_true")
    time = parser.add_argument_group()
    time.add_argument("-t", type=int, help='time in seconds that data is collected')
    parser.add_argument("COMMAND", type=str, help='The choices are: {collect, display}')
    # specific options

    return parser.parse_args(argv)
