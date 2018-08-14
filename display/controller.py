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
from enum import Enum

from common import (
    file,
    util,
    config
)
from display import (
    flamegraph,
    heatmap,
    treemap,
    g2,
    stackplot)


logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


# Both enums should match the values from the config files
class DisplayOptions(Enum):
    HEATMAP = "heatmap"
    STACKPLOT = "stackplot"
    FLAMEGRAPH = "flamegraph"
    TREEMAP = "treemap"
    G2 = "g2"


class FileTypes(Enum):
    CSV = '[CSV]'
    STACK = '[STACK]'
    CPEL = '[CPEL]'


# Display option for files
display_dictionary = {
    FileTypes.CSV: [DisplayOptions.HEATMAP, DisplayOptions.STACKPLOT],
    FileTypes.STACK: [DisplayOptions.FLAMEGRAPH, DisplayOptions.TREEMAP],
    FileTypes.CPEL: [DisplayOptions.G2]
}


@util.log(logger)
def _select_mode(file_type, args):
    """
    Captures the common pattern of selecting the right display.

    :param file_type: the type of the file; can be:
                        - [STACK]
                        - [CSV]
                        - [CPEL]
    :param args: terminal arguments as a dictionary
    :returns DisplayOptions(default_to_enum): an DisplayOptions specifing the
                                              display mode
    """
    # We create a config parser to read user setting from the config file
    config_parser = config.Parser()

    # Create the dictionaries used in the selection step
    try:
        file_type_enum = FileTypes(file_type)
    except ValueError:
        raise ValueError("The file type {} is not supported".format(file_type))

    # File type exists, we look in display_dictionary for the various ways
    # to display it
    if file_type_enum == FileTypes.CPEL:
        possibilities = display_dictionary[FileTypes.CPEL]
    elif file_type_enum == FileTypes.CSV:
        possibilities = display_dictionary[FileTypes.CSV]
    elif file_type_enum == FileTypes.STACK:
        possibilities = display_dictionary[FileTypes.STACK]

    for option in possibilities:
        if args[option.value]:
            return option
    else:
        # loop fell through without finding a factor (see python 3.7 doc 4.4)
        default = config_parser.get_option_from_section("Display",
                                                        file_type[1:-1])
        try:
            default_to_enum = DisplayOptions(default)
        except ValueError:
            raise ValueError("The default value from the config could not be "
                             "converted to a DisplayOptions enum. "
                             "Check that the values in the config correspond "
                             "with the enum values.")

        if default_to_enum in possibilities:
            return DisplayOptions(default_to_enum)
        else:
            raise ValueError(
                "No valid args or config values found for {}. Either "
                "add an arg in the terminal command or modify the "
                "config file".format(file_type))


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
        input_filename = str(file.DataFileName(args.infile))
    else:
        input_filename = str(file.DataFileName.import_filename())

    # Use user output filename specified, otherwise create a unique one
    # DO NOT let the user decide because they might overwrite the input!
    if args.outfile is not None:
        output_filename = file.DisplayFileName(given_name=args.outfile)
    else:
        output_filename = file.DisplayFileName()

    # We read the file header @TODO: Maybe add more functionality to the header
    with open(input_filename, "rb") as source:
        # Strip ending newline
        header = source.readline()[:-1]
        header = header.decode()

    # We select the display method based on args and the config file
    mode = _select_mode(header, vars(args))
    # Match the mode with the appropriate display object
    if mode == DisplayOptions.G2:
        display_object = g2.G2(input_filename)
    elif mode == DisplayOptions.HEATMAP:
        hm_labels = heatmap.AxesLabels(x='Time', x_units='seconds',
                                       y='Latency', y_units='ms',
                                       colorbar='No. accesses')
        display_object = heatmap.HeatMap(input_filename, output_filename,
                                         hm_labels, heatmap.DEFAULT_PARAMETERS,
                                         True)
    elif mode == DisplayOptions.TREEMAP:
        display_object = treemap.Treemap(25, input_filename, output_filename)
    elif mode == DisplayOptions.STACKPLOT:
        display_object = stackplot.StackPlot(input_filename)
    elif mode == DisplayOptions.FLAMEGRAPH:
        display_object = flamegraph.Flamegraph(input_filename,
                                               output_filename, None)
    else:
        raise ValueError("Unexpected display mode {}!".format(mode))

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
