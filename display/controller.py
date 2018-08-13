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
    config
)
from display import (
    flamegraph,
    heatmap,
    treemap,
    g2)


logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))

display_options = {
    '[CSV]': ['heatmap'],
    '[STACK]': ['flamegraph', 'treemap'],
    '[CPEL]': ['g2']
}


@util.log(logger)
def _gen_treemap(*args):
    #inp, out
    """
    Helper function that generates the treemap html file and shows it in the
    browser

    :param inp: input file
    :param out: output file, as DisplayFileName object

    """
    print(args)
    args[1].set_options("treemap", "html")
    treemap.show(args[0], str(args[1]))


# @util.log(logger)
# def _gen_flamegraph(*args):
#     #inp, out
#     """
#     Helper function that generates the flamegraph svg file and shows it in the
#     browser
#
#     :param input: input file
#     :param output: output file, as a DisplayFileName object
#
#     """
#     stacks = flamegraph.read(args[0])
#     args[1].set_options("flamegraph", "svg")
#     flamegraph.make(stacks, str(args[1]))
#     flamegraph.show(str(args[1]))


@util.log(logger)
def _gen_g2(*args):
    #inp
    """
    Helper function that generates the g2 representation
    :param input: the input filename

    """
    g2.show(args[0])


@util.log(logger)
def _gen_heatmap(*args):
    #inp, out, labels, params
    """
    Helper function that generates and displays the heatmap

    :param input: input file
    :param output: output file, as a DisplayFileName object
    :param labels: labels for the axes
    :param params: parameters for the heatmap, defaults to the defaults from
                   heatmap

    """
    hmap = heatmap.HeatMap(args[0], args[2], args[3])
    hmap.show()
    args[1].set_options("heatmap", "svg")
    hmap.save(str(args[1]))


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
        header = source.readline()[:-1]
        header = header.decode()

    if header == '[CPEL]':
        posib_dict = {
            'g2': (_gen_g2, [input_filename])
        }
    elif header == '[CSV]':
        # We set the axes for the heatmap
        labels = heatmap.AxesLabels(x='Time', x_units='seconds',
                                    y='Latency', y_units='ms',
                                    colorbar='No. accesses')
        posib_dict = {
            'heatmap': (_gen_heatmap, [input_filename, output_filename,
                                       labels, heatmap.DEFAULT_PARAMETERS])
        }
    elif header == '[STACK]':
        posib_dict = {
            'treemap': (_gen_treemap, [input_filename, output_filename]),
            'flamegraph': (_gen_flamegraph, [input_filename, output_filename])
        }
    else:
        raise Exception("File not supported!")

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
