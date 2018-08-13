# -------------------------------------------------------------
# controller.py - user interface, parses and applies display commands
# June-July 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies display commands

Handles interaction between the output modules (flamegraph, g2, etc.)
It calls the relevant functions for each command.

To add a new display mode:
    1)
    2)
    3)

"""
__all__ = "main"

import argparse
import logging

from common import (
    file,
    util,
    config
)
from display import (
    flamegraph,
    heatmap,
    treemap,
    g2)


logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

# Display option for
display_options = {
    '[CSV]': ['heatmap'],
    '[STACK]': ['flamegraph', 'treemap'],
    '[CPEL]': ['g2']
}


@util.log(logger)
def _select_mode(file_type, args, possib_dict):
    """
    Captures the common pattern of selecting the right display.
    The priority of selection: args have the highest priority, if any is
                               specified then we select that option; if the
                               arg option is specified, but unsupported, or no
                               arg is specified we look at the config file
                               preferences for the particular type of file; if
                               the option doesn't exist there we trow an error

    :param file_type: the type of the file; can be:
                        - [STACK]
                        - [CSV]
                        - [CPEL]
    :param args: terminal arguments as a dictionary
    :param posib_dict: a dictionary containing (key, value), where:
                            - key: name of the display option
                            - value: pair containing the function associated
                                     with the display option and the arguments
                                     it should be called with

    """
    # We create a config parser to read user setting from the config file
    config_parser = config.Parser()

    # If the file type is not recognized, throw error
    if file_type not in display_options:
        raise KeyError("The file type {} is not supported "
                        "yet".format(file_type))

    # We retrieve the possible display options for the particular file type
    options = display_options[file_type]
    # Flag to see if we encountered a cmd line argument, AND IT WAS A VALID
    # OPTION
    flag_args = False
    for option in options:
        # If the current option is in the dictionary, and it was specified in
        # the cmd line, we got a match
        if option in possib_dict and args[option]:
            flag_args = True
            display_class = possib_dict[option]
            display_class.show()
            break

    if not flag_args:
        # No matches for the cmd line args, we try the config file
        # We get the default option
        default = config_parser.get_option_from_section("Display",
                                                        file_type[1:-1])
        # If it is valid, we use it, otherwise we raise an error
        if default in possib_dict:
            display_class = possib_dict[default]
            display_class.show()
        else:
            raise Exception(
                "No valid args or config values found for {}. Either "
                "add an arg in the terminal command or modify the "
                "config file".format(file_type))

display_options = {
    '[CSV]': ['heatmap'],
    '[STACK]': ['flamegraph', 'treemap'],
    '[CPEL]': ['g2']
}


@util.log(logger)
def _select_mode(file_type, args, possib_dict):
    """
    Captures the common pattern of selecting the right display.

    :param file_type: the type of the file; can be:
                        - [STACK]
                        - [CSV]
                        - [CPEL]
    :param args: terminal arguments as a dictionary
    :param posib_dict: a dictionary containing (key, value), where:
                            - key: name of the display option
                            - value: pair containing the function associated
                                     with the display option and the arguments
                                     it should be called with

    """
    # We create a config parser to read user setting from the config file
    config_parser = config.Parser()

    if file_type not in display_options:
        raise KeyError("The file type {} is not supported "
                        "yet".format(file_type))

    options = display_options[file_type]
    flag_args = False
    for option in options:
        if option in possib_dict and args[option]:
            flag_args = True
            funct_pair = possib_dict[option]
    if flag_args:
        funct = funct_pair[0]
        arg = funct_pair[1]
        funct(*arg)
    else:
        default = config_parser.get_option_from_section("Display",
                                                        file_type[1:-1])
        if default in possib_dict:
            funct_pair = possib_dict[default]
            funct = funct_pair[0]
            arg = funct_pair[1]
            funct(*arg)
        else:
            raise Exception(
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

    # We read the file header
    with open(input_filename, "rb") as source:
        # Strip ending newline
        header = source.readline()[:-1]
        header = header.decode()

    # Create the dictionaries usde in the selection step
    if header == '[CPEL]':
        posib_dict = {
            'g2': g2.G2(input_filename)
        }
    elif header == '[CSV]':
        # We set the axes for the heatmap
        labels = heatmap.AxesLabels(x='Time', x_units='seconds',
                                    y='Latency', y_units='ms',
                                    colorbar='No. accesses')
        posib_dict = {
            'heatmap': heatmap.HeatMap(input_filename, output_filename,
                                       labels, heatmap.DEFAULT_PARAMETERS, True)
        }
    elif header == '[STACK]':
        posib_dict = {
            'treemap': treemap.Treemap(25, input_filename, output_filename),
            'flamegraph': flamegraph.Flamegraph(input_filename,
                                                output_filename, None)
        }
    else:
        raise Exception("File not supported!")

    # We select the display method based on args and the config file
    _select_mode(header, vars(args), posib_dict)

@util.log(logger)
def _args_parse(argv):
    """
    Create a parser that parses the display command.

    Arguments that are created in the parser object:
        fg: display with a flamegraph
        tm: display with a treemap
        g2: display with g2
        hm: display with heatmap

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
