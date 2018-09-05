#!/usr/bin/env python3

# -------------------------------------------------------------
# __main__.py - Initiates the program
# June - August 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Initiates the program.

Sets up logging, calls the appropriate controller (collect or display) and
deals with exceptions.

"""
__all__ = ["main"]

import argparse
import logging
import os
import sys
from datetime import datetime
import textwrap
import warnings
import traceback

from marple.common import (
    exceptions,
    output,
    paths,
    config,
    util
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
config_parser = config.Parser()


# Attempt to import collect and display - keep track of which are present
collect_exists, display_exists = True, True
warn = config_parser.get_option_from_section("General", "warnings", "bool")

try:
    from marple.collect import main as collect
except ImportError:
    if warn:
        msg = ("No data collection package detected - "
               "only data display package (marple -d/--display) may be used."
               " To suppress this warning, edit config.txt.")
        warnings.warn(RuntimeWarning(msg))
        logger.error(msg)
    collect_exists = False
    collect = None

try:
    from marple.display import main as display
except ImportError:
    if warn:
        msg = ("No data display package detected - "
               "only data collection package (marple -c/--collect) may be used."
               " To suppress this warning, edit config.txt")
        warnings.warn(RuntimeWarning(msg))
        logger.error(msg)
    display_exists = False
    display = None

# If neither is present, exit immediately
if not collect_exists and not display_exists:
    output.error_(
        "Fatal error: neither data collection nor data display packages found!",
        "User must have at least one of the data collection ('collect') "
        "and data display ('display') packages installed."
    )
    exit(1)


@util.log(logger)
def main():
    """ Run MARPLE """
    # Check whether user is root, otherwise exit
    if os.geteuid() != 0:
        output.error_("You must have root privileges to run MARPLE.\n",
                      "User was not root.")
        exit(1)

    paths.create_directories()  # Create required directories TODO config dir?
    setup_logger()  # Setup logging

    # Parse arguments
    parser = argparse.ArgumentParser(
        prog="marple",
        description="A Linux system profiling tool, which can collect data "
                    "and display it.", add_help=False)
    submodules = parser.add_mutually_exclusive_group(required=True)
    submodules.add_argument(
        "--collect", "-c", action='store_true',
        help="Collect profiling data and write to disk.")
    submodules.add_argument(
        "--display", "-d", action='store_true',
        help="Display profiling data stored on disk."
    )
    parsed, rest = parser.parse_known_args(sys.argv[1:])

    # Call relevant module
    global collect_exists, display_exists, config_parser
    try:
        if parsed.collect:
            if collect_exists:
                collect.main(rest, config_parser)
            else:
                raise ModuleNotFoundError(
                    name='common', path=(paths.MARPLE_DIR + '/__main__.py'))
        else:
            assert parsed.display
            if display_exists:
                display.main(rest)
            else:
                raise ModuleNotFoundError(
                    name='display', path=(paths.MARPLE_DIR + '/__main__.py'))

    except ModuleNotFoundError as mnfe:
        output.error_("Package {} does not exists on this system!"
                      .format(mnfe.name),
                      "Attempted to import '{}' in {}:\n"
                      .format(mnfe.name, mnfe.path) + traceback.format_exc())
        exit(1)
    except NotImplementedError as nie:
        # if the requested function is not implemented, exit with an error
        output.error_("The command \"{}\" is currently not implemented. "
                      "Please try a different command.".format(nie.args[0]),
                      "Exited with a NotImplementedError. Command: {}"
                      .format(nie.args[0]))
        exit(1)
    except FileExistsError as fee:  # TODO is this ever raised?
        # If the output filename requested by the user already exists
        output.error_("A file with the name {} already exists. Please "
                      "choose a unique filename.".format(fee.filename),
                      "Exited with a FileExistsError. File: {}".format(
                          fee.filename))
        exit(1)
    except FileNotFoundError as fnfe:
        # If no input file was found
        output.error_(" No file named {} found. Please choose a "
                      "different input file.".format(fnfe.filename),
                      "Exited with a FileNotFoundError. Filename: {}"
                      .format(fnfe.filename))
        exit(1)
    except exceptions.NotSupportedException as nse:
        # If the target kernel does not meet the requirements
        output.error_("You need to have kernel {} or above for this "
                      "functionality".format(nse.required_kernel),
                      "Exited with NotSupportedError. Required kernel: "
                      "{}".format(nse.required_kernel))
        exit(1)
    except IsADirectoryError as iade:
        # If user tried to save output under a name that is a directory name
        output.error_("Cannot use filename {}, because there is a directory "
                      "with that name. Please choose a different "
                      "filename".format(iade.filename),
                      "Exited with an IsADirectoryError.")
        exit(1)
    except Exception as ex:
        # If anything else goes wrong, handle it here
        output.error_("An unexpected error occurred. Check log for details.",
                      "\n" + traceback.format_exc())
        exit(1)


@util.log(logger)
def setup_logger():
    """ Create a log in paths.LOG_DIR """
    class LogFormatter(logging.Formatter):
        @util.Override(logging.Formatter)
        def format(self, record):
            header = super().format(record)
            original_msg = record.getMessage().split('\n')
            formatted_msg = ""
            line_length = 70
            for line in original_msg:
                if len(line) > line_length:
                    line = '\n'.join(textwrap.wrap(line, width=line_length,
                                                   break_long_words=False))
                formatted_msg = "\n".join((formatted_msg, line))

            indented_msg = textwrap.indent(formatted_msg, prefix="    ")

            return header + indented_msg

        @util.Override(logging.Formatter)
        def formatException(self, ei):
            return textwrap.indent(super().formatException(ei), prefix="    ")

    try:
        msg_format = '%(asctime)s - %(name)-25.25s - %(levelname)-8.8s'
        date_format = "%H:%M:%S"
        now = datetime.now()
        log_file = paths.LOG_DIR + now.strftime('%Y-%m-%d_%H:%M:%S') + ".log"
        level = logging.DEBUG

        handler = logging.FileHandler(log_file, mode='w')
        formatter = LogFormatter(fmt=msg_format, datefmt=date_format)
        handler.setFormatter(formatter)

        logging.basicConfig(level=level, handlers=[handler])
        logging.basicConfig()

    except PermissionError:
        output.error_(
            "Fatal error: failed to set up logging due to permissions.",
            "Ensure you have root privileges and can access the log directory"
            "as root.")
        exit(1)
    except Exception as ex:
        output.error_(
            "Fatal error: failed to set up logging.",
            str(ex))
        exit(1)


if __name__ == "__main__":
    main()
