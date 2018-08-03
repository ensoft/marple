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

from common import file
from . import flamegraph
from . import heatmap
from . import treemap

logger = logging.getLogger('display.controller')
logger.setLevel(logging.DEBUG)


def _display(args):
    """
    Displaying part of the controller module.

    Deals with displaying data.

    :param args:
        Command line arguments for data-display
        Passed by main function

    """
    logger.info("Display function. "
                "Applying logic evaluating and applying input parameters")

    # Try to use the specified input file, otherwise use last one created
    input_filename = args.infile if args.infile is not None else \
        file.import_out_filename()
    # Use user output filename specified, otherwise create a unique one
    #   Do not let the user decide because they might overwrite the input!
    output_filename = args.outfile if args.outfile is not None else \
        file.find_unique_out_filename("display", ending=".svg")

    if args.cpu:
        # Stub
        raise NotImplementedError("display cpu data")
    elif args.disk:
        if args.n:
            labels = heatmap.AxesLabels(x='Time', x_units='seconds',
                                        y='Latency', y_units='ms',
                                        colorbar='No. accesses')
            logger.info("Creating heatmap.")
            hmap = heatmap.HeatMap(input_filename, labels,
                                   heatmap.DEFAULT_PARAMETERS)
            logger.info("Saving and displaying heatmap.")
            hmap.show()
            hmap.save(output_filename)
            logger.info("Exit heatmap methods.")
        else:
            flamegraph.make(input_filename, output_filename, colouring="io")
            flamegraph.show(output_filename)
    elif args.ipc:
        # Stub
        raise NotImplementedError("display ipc data")
    elif args.lib:
        # Stub
        raise NotImplementedError("display library data")
    elif args.mem:
        if args.n:
            raise NotImplementedError("display-numeric memory data")
        else:
            flamegraph.make(input_filename, output_filename, colouring="mem")
            flamegraph.show(output_filename)
    elif args.stack:
        if args.n:
            raise NotImplementedError("display-numeric stack data")
        elif args.t:
            logger.info("Creating treemap.")
            treemap.show(input_filename, output_filename + ".html")
            logger.info("Displayed treemap.")
        else:
            flamegraph.make(input_filename, output_filename)
            flamegraph.show(output_filename)



def _args_parse(argv):
    """
    Create a parser that parses the display command.

    Arguments that are created in the parser object:

        cpu: CPU scheduling data
        disk: disk I/O data
        ipc: ipc efficiency
        lib: library load times
        mem: memory allocation/ deallocation
        stack: stack tracing

        infile i: the filename of the file containing the input
        outfile o: the filename of the file that stores the output

        g: graphical representation of data (default)
        n: numerical representation of data


    :param argv:
        the arguments passed by the main function

    :return:
        an object containing the parsed command information

    Called by main when the program is started.

    """

    logger.info("Enter _args_parse function. Creates parser.")

    # Create parser object
    parser = argparse.ArgumentParser(prog="marple display",
                                     description="Display collected data "
                                     "in required format")

    # Add options for the modules
    module_display = parser.add_mutually_exclusive_group(required=True)

    module_display.add_argument("-c", "--cpu", action="store_true",
                                help="gather cpu scheduling events")
    module_display.add_argument("-d", "--disk", action="store_true",
                                help="monitor disk input/output")
    module_display.add_argument("-p", "--ipc", action="store_true",
                                help="trace inter-process communication")
    module_display.add_argument("-l", "--lib", action="store_true",
                                help="gather library load times")
    module_display.add_argument("-m", "--mem", action="store_true",
                                help="trace memory allocation/ deallocation")
    module_display.add_argument("-s", "--stack", action="store_true",
                                help="gather general call stack tracing data")

    # Add flag and parameter for displaying type in case of display
    type_display = parser.add_mutually_exclusive_group()
    type_display.add_argument("-g", action="store_true",
                              help="graphical representation as an image ("
                                   "default)")
    type_display.add_argument("-n", action="store_true",
                              help="numerical representation as a table")
    type_display.add_argument("-t", action="store_true",
                              help="treemap representation as an html")

    # Add flag and parameter for input filename
    filename = parser.add_argument_group()
    filename.add_argument("-i", "--infile", type=str,
                          help="Input file where collected data "
                               "to display is stored")

    # Add flag and parameter for output filename
    filename = parser.add_argument_group()
    filename.add_argument("-o", "--outfile", type=str,
                          help="Output file where the graph is stored")

    logger.info("Parsing input arguments")
    return parser.parse_args(argv)


def main(argv):
    """
    The main function of the controller.

    Calls the middle level modules according to options selected by user.

    :param argv:
        command line arguments from call in main

    """
    logger.info("Enter controller main function with arguments %s", str(argv))

    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate functions to display input
    _display(args)
