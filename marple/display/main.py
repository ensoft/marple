# -------------------------------------------------------------
# main.py - user interface, parses and applies display commands
# June-July 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies display commands

Handles interaction between the output modules (flamegraph, g2, etc.)
It calls the relevant functions for each command.

"""
__all__ = "main"

import argparse
import logging
import os

from marple.common import (
    file,
    util,
    config,
    consts,
    data_io,
)
from marple.display.interface import (
    heatmap,
    treemap,
    g2,
    flamegraph,
    stackplot,
    plotter
)

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


@util.log(logger)
def _select_mode(interface, datatype, args):
    """
    Function that selects the right display mode based on the interface and the
    datatype found in the header

    We first try to see if one of the cmd line arguments matches one of the
    possible display options for :param datatype; if not we try to use the
    option associated with the interface in the config file;
    We have chosen to use the interface and not the datatype so that the user
    can choose a more specific option; it is advisable to only use the config
    file, the args being only used for 'one of' situations

    :param interface:
        the type of the interface that produced the section;
        look at the consts module to see all the possibilities
    :param datatype:
        the datatype of the data in the section;
        look at the consts module to see all the possibilities
    :param args:
        terminal arguments as a dictionary

    :return:
        a consts.DisplayOptions specifing the display mode

    """
    # Create the dictionaries used in the selection step
    try:
        datatype_enum = consts.Datatypes(datatype)
    except ValueError as ve:
        raise ValueError("The datatype {} is not supported.".format(datatype)) \
            from ve

    # Determine possible ways to display the datatype
    possibilities = consts.display_dictionary[datatype_enum]

    for option in possibilities:
        # If options specified in the args, then use that option
        if args[option.value]:
            return option

    default = config.get_option_from_section(
        "DisplayInterfaces", interface)

    try:
        default_enum = consts.DisplayOptions(default)
    except ValueError as ve:
        raise ValueError(
            "The default value from the config ({}) was not recognised. "
            "Make sure the config values are within the accepted parameters."
            .format(default)) from ve

    if default_enum in possibilities:
        return consts.DisplayOptions(default_enum)
    else:
        raise ValueError(
            "No valid args or config values found for {}. Either "
            "add an arg in the terminal command or modify the "
            "config file".format(interface))


@util.log(logger)
def _args_parse(argv):
    """
    Create a parser that parses the display command.

    We create mutex groups for display options associated with the same
    datatype

    :param argv:
        the arguments passed by the main function

    :return:
        an object containing the parsed command information

    Called by main when the program is started.

    """

    # Create parser object
    parser = argparse.ArgumentParser(
        prog="marple --display",
        description="Display collected data in desired format")

    # List, entry selection, and data aggregation functionality
    meta = parser.add_mutually_exclusive_group()
    meta.add_argument("-l", "--list", action="store_true",
                      help="list available datasets in data file")

    meta.add_argument("-e", "--entry", nargs='*',
                            help="select dataset(s) from data file")
    meta.add_argument(
        "--noagg", action="store_true",
        help="if set, none of the sections in the file will be aggregated")

    # Group of the display options for displaying stacks
    stack_display = parser.add_mutually_exclusive_group()
    stack_display.add_argument(
        "-fg", "--" + consts.DisplayOptions.FLAMEGRAPH.value,
        action="store_true", help="display as flamegraph")
    stack_display.add_argument(
        "-tm", "--" + consts.DisplayOptions.TREEMAP.value,
        action="store_true", help="display as treemap")

    # Group of the display options for displaying events
    event_display = parser.add_mutually_exclusive_group()
    event_display.add_argument(
        "-g2", "--" + consts.DisplayOptions.G2.value,
        action="store_true", help="display as g2 image")
    event_display.add_argument(
        "-plt", "--" + consts.DisplayOptions.TCPPLOT.value,
        action="store_true", help="display as plot")

    # Group of the display options for displaying points
    point_display = parser.add_mutually_exclusive_group()
    point_display.add_argument(
        "-hm", "--" + consts.DisplayOptions.HEATMAP.value,
        action="store_true", help="display as heatmap")
    point_display.add_argument(
        "-sp", "--" + consts.DisplayOptions.STACKPLOT.value,
        action="store_true", help="display as stackplot")

    # Add flag and parameter for input filename
    filename = parser.add_argument_group()
    filename.add_argument(
        "-i", "--infile", type=str,
        help="Input file where collected data to display is stored")

    return parser.parse_args(argv)


def _list_directory_files(path):
    """
    Helper function that lists the contents of a directory

    :param path: the path of the directory as a string

    """
    # Get all files in dir
    files = [f for f in os.listdir(path)
             if os.path.isfile(os.path.join(path, f))]
    for f in files:
        # Now for each file we get its contents, based on the headers
        file_path = os.path.join(path, f)

        # Now some styles for the cmd line text
        red = '\033[91m'
        bold = '\033[1m'
        end = '\033[0m'
        print(bold + "File: " + red + file_path + end)
        with data_io.Reader(file_path) as reader:
            for header in reader.get_header_info_string():
                print(header)
        print()


@util.log(logger)
def main(argv):
    """
    The main function of the controller.

    Parses the cmd line arguments and displays either the sections in the
    provided file (args) or the last one created with their appropriate
    data options (options that are data specific, such as the label of
    the x axis for points) and the display options (display specific options,
    such as the maximum depth of a treemap)

    :param argv:
        command line arguments from call in main

    """

    # Parse arguments
    args = _args_parse(argv)

    # Set up input and output files
    if args.infile:
        path = os.path.expanduser(args.infile)

        # List directory contents if user has specified a dir
        if args.list and os.path.isdir(path):
            _list_directory_files(path)
            return

        # Otherwise continue as normal
        input_filename = file.DataFileName(given_name=args.infile)
    else:
        input_filename = file.DataFileName.import_filename()

    # Set up reader
    with data_io.Reader(input_filename) as reader:

        if args.list:
            headers = reader.get_header_info_string()
            for header in headers:
                print(header)
            return
        elif args.entry:
            entries = set(int(arg) for arg in args.entry)
            interfaces = {reader.get_interface_from_index(index)
                          for index in entries}
        else:
            interfaces = reader.get_all_interface_names()

        if args.noagg:
            # Get the aggregate section from the config file
            agg_groups = config.get_section('Aggregate')

            for agg_group in agg_groups:
                # Parse the string containing the interfaces into a list
                agg_interfaces = set(agg_group.replace(' ', '').split(','))

                if not agg_interfaces.issubset(interfaces):
                    continue  # skip when not all aggregates are in file
                else:
                    # We remove the aggregated interfaces from the list
                    # of interfaces since we display them here
                    interfaces = interfaces - agg_interfaces

                display_mode = agg_groups[agg_group]
                if display_mode == consts.DisplayOptions.TCPPLOT.value:
                    data_objs = reader.get_interface_data(*agg_interfaces)
                    visualiser = plotter.Plotter(*data_objs)
                    visualiser.show()
                else:
                    raise ValueError(
                        'Display mode {} does not support displaying aggregated'
                        ' data'.format(display_mode))

        # Display remaining interfaces
        data_objs = reader.get_interface_data(*interfaces)
        for data in data_objs:
            display_mode = _select_mode(data.interface.value,
                                        data.datatype, vars(args))
            try:
                visualiser = {
                    consts.DisplayOptions.G2: g2.G2,
                    consts.DisplayOptions.HEATMAP: heatmap.HeatMap,
                    consts.DisplayOptions.TREEMAP: treemap.Treemap,
                    consts.DisplayOptions.STACKPLOT: stackplot.StackPlot,
                    consts.DisplayOptions.FLAMEGRAPH: flamegraph.Flamegraph,
                    consts.DisplayOptions.TCPPLOT: plotter.Plotter
                }[display_mode]
            except KeyError as ke:
                raise KeyError("Unexpected display mode {}!".
                               format(display_mode)) from ke

            visualiser = visualiser(data)
            visualiser.show()
