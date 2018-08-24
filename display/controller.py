# -------------------------------------------------------------
# controller.py - user interface, parses and applies display commands
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

from common import (
    file,
    util,
    config,
    consts,
    datatypes,
)
from display import (
    flamegraph,
    heatmap,
    treemap,
    g2,
    stackplot)
from collect.IO import read

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


@util.log(logger)
def _select_mode(interface, datatype, args):
    """
    Captures the common pattern of selecting the right display.

    :param interface_type: the type of the interface that produce the file;
                           can be:
                               - Scheduling Events
                               - Disk Latency/Time
                               - Malloc Stacks
                               - Memory leaks
                               - Memory/Time
                               - Call Stacks
    :param args: terminal arguments as a dictionary
    :returns display mode: an enums.DisplayOptions
                           specifing the display mode
    """
    # We create a config parser to read user setting from the config file
    config_parser = config.Parser()

    # Create the dictionaries used in the selection step
    try:
        datatype_enum = consts.Datatypes(datatype)
    except ValueError:
        raise ValueError("The file type {} is not supported".format(
            interface))

    # File type exists, we look in display_dictionary for the various ways
    # to display it
    possibilities = consts.display_dictionary[datatype_enum]

    for option in possibilities:
        if args[option.value]:
            return option
    else:
        # loop fell through without finding a factor (see python 3.7 doc 4.4)
        default = config_parser.get_option_from_section("DisplayInterfaces",
                                                        interface)
        try:
            default_to_enum = consts.InterfaceTypes(default)
        except ValueError:
            raise ValueError("The default value from the config could not be "
                             "converted to a enums.DisplayOptions enum. "
                             "Check that the values in the config correspond "
                             "with the enum values.")

        if default_to_enum in possibilities:
            return consts.DisplayOptions(default_to_enum)
        else:
            raise ValueError(
                "No valid args or config values found for {}. Either "
                "add an arg in the terminal command or modify the "
                "config file".format(interface))


@util.log(logger)
def _get_display_options(display_type):
    """
    Function that selects the specific options for the display_type of class
    `GenericDisplay`(does not have anything to do with the type of data that
    is in the file); example options: width of the display, name of the
    colorbar, depth of the treemap

    :param display_type: the datatype of the data in the file we read from
    :return: the options (if the user doesn't specify, the default is returned)

    """
    # We create a config parser to read user setting from the config file
    config_parser = config.Parser()

    if display_type == consts.DisplayOptions.TREEMAP:
        depth = config_parser.get_option_from_section("treemap", "depth",
                                                      typ="int")
        return treemap.Treemap.DisplayOptions(depth=depth)
    elif display_type == consts.DisplayOptions.STACKPLOT:
        top_processes = config_parser.get_option_from_section("stackplot",
                                                              "top", typ="int")
        return stackplot.StackPlot.DisplayOptions(top_processes=top_processes)
    elif display_type == consts.DisplayOptions.G2:
        track = config_parser.get_option_from_section("g2", "track")
        return g2.G2.DisplayOptions(track=track)
    elif display_type == consts.DisplayOptions.HEATMAP:
        figure_size = config_parser.get_option_from_section(
            "heatmap", "figure_size", typ="float")
        scale = config_parser.get_option_from_section(
            "heatmap", "scale", typ="float")
        y_res = config_parser.get_option_from_section(
            "heatmap", "y_res", typ="float")
        parameters = heatmap.GraphParameters(figure_size=figure_size,
                                             scale=scale,
                                             y_res=y_res)
        normalise = config_parser.get_option_from_section("heatmap", "y_res",
                                                          typ="bool")
        colorbar = "No. Accesses"
        return heatmap.HeatMap.DisplayOptions(colorbar, parameters, normalise)
    elif display_type == consts.DisplayOptions.FLAMEGRAPH:
        coloring = config_parser.get_option_from_section("flamegraph",
                                                         "coloring")
        return flamegraph.Flamegraph.DisplayOptions(coloring=coloring)


def _get_data_options(header):
    datatype = header['datatype']
    if datatype == "stack":
        weight_units = header['data_options']['weight_units']
        return datatypes.StackData.DataOptions(weight_units)
    elif datatype == "event":
        return None
    elif datatype == "point":
        x_label = header['data_options']['x_label']
        y_label = header['data_options']['y_label']
        x_units = header['data_options']['x_units']
        y_units = header['data_options']['y_units']
        return datatypes.PointData.DataOptions(x_label, y_label, x_units,
                                               y_units)


@util.log(logger)
def _display(args):
    """
    Displaying part of the controller module.

    Deals with displaying data by using the selection function. See the
    function for the selection criteria.

    :param args:
        Command line arguments for data-display
        Passed by main function

    """
    # Try to use the specified input file, otherwise use last one created
    if args.infile is not None:
        input_filename = file.DataFileName(given_name=args.infile)
    else:
        input_filename = file.DataFileName.import_filename()

    # Use user output filename specified, otherwise create a unique one
    # DO NOT let the user decide because they might overwrite the input!
    if args.outfile is not None:
        output_filename = file.DisplayFileName(given_name=args.outfile)
    else:
        output_filename = file.DisplayFileName()

    # We read the file header
    with read.Reader(str(input_filename)) as (file_header, _):
        header = file_header

    # We select the display method based on args and the config file, and get
    # the associated options with that mode (the options retrieved here
    # do not care about the interface type)
    display_for_interface = _select_mode(header['datatype'], vars(args))
    display_options = _get_display_options(display_for_interface)
    data_options = _get_data_options(header)

    # Match the mode with the appropriate display object, and alter some
    # interface specific options (the ones that are not in the config)
    if display_for_interface == consts.DisplayOptions.G2:
        display_object = g2.G2(input_filename, data_options, display_options)
    elif display_for_interface == consts.DisplayOptions.HEATMAP:
        display_object = heatmap.HeatMap(input_filename, output_filename,
                                         data_options, display_options)
    elif display_for_interface == consts.DisplayOptions.TREEMAP:
        display_object = treemap.Treemap(input_filename, output_filename,
                                         data_options, display_options)
    elif display_for_interface == consts.DisplayOptions.STACKPLOT:
        display_object = stackplot.StackPlot(input_filename, data_options,
                                             display_options)
    elif display_for_interface == consts.DisplayOptions.FLAMEGRAPH:
        display_object = flamegraph.Flamegraph(input_filename, output_filename,
                                               data_options, display_options)
    else:
        raise ValueError("Unexpected display mode {}!".
                         format(display_for_interface))

    # Display it
    display_object.show()


@util.log(logger)
def _args_parse(argv):
    """
    Create a parser that parses the display command.

    Arguments that are created in the parser object:
        fg: display with a flamegraph
        tm: display with a treemap
        g2: display with g2
        hm: display with heatmap
        sp: display with stackplot

        infile i: the filename of the file containing the input
        outfile o: the filename of the file that stores the output

    :param argv:
        the arguments passed by the main function

    :return:
        an object containing the parsed command information

    Called by main when the program is started.

    """

    # Create parser object
    parser = argparse.ArgumentParser(prog="marple display",
                                     description="Display collected data "
                                     "in required format")

    # Add flag and parameter for displaying type in case of display
    type_display = parser.add_mutually_exclusive_group()
    type_display.add_argument("-fg", "--flamegraph", action="store_true",
                              help="display as flamegraph")
    type_display.add_argument("-tm", "--treemap", action="store_true",
                              help="display as treemap")
    type_display.add_argument("-g2", "--g2", action="store_true",
                              help="display as g2 image")
    type_display.add_argument("-hm", "--heatmap", action="store_true",
                              help="display as heatmap")
    type_display.add_argument("-sp", "--stackplot", action="store_true",
                              help="display as stackplot")

    # Add flag and parameter for input filename
    filename = parser.add_argument_group()
    filename.add_argument("-i", "--infile", type=str,
                          help="Input file where collected data "
                               "to display is stored")

    # Add flag and parameter for output filename
    filename = parser.add_argument_group()
    filename.add_argument("-o", "--outfile", type=str,
                          help="Output file where the graph is stored")

    return parser.parse_args(argv)


@util.log(logger)
def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        command line arguments from call in main

    """
    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate functions to display input
    _display(args)
