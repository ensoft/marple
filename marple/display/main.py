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
import itertools

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
    tcpplotter
)

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

# We create a config parser to read user setting from the config file
config_parser = config.Parser()


@util.log(logger)
def _select_mode(interface, datatype, args):
    """
    Captures the common pattern of selecting the right display.

    We first try to see if one of the cmd line arguments matches one of the
    possible display options for :param:datatype; if not we try to use the
    option associated with the interface in the config file;

    We have chosen to use the interface and not the datatype so that the user
    can choose a more specific option; it is advisable to only use the config
    file, the args being only used for 'one of' situations

    :param interface: the type of the interface that produced the section;
                      look at the consts module to see all the possibilities
    :param datatype: the datatype of the data in the section;
                     look at the consts module to see all the possibilities
    :param args: terminal arguments as a dictionary

    :returns display mode: an consts.DisplayOptions
                           specifing the display mode

    """
    # Create the dictionaries used in the selection step
    try:
        datatype_enum = consts.Datatypes(datatype)
    except ValueError:
        raise ValueError("The datatype {} is not supported".format(datatype))

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
            default_to_enum = consts.DisplayOptions(default)
        except ValueError:
            raise ValueError("The default value from the config could not be "
                             "converted to a consts.DisplayOptions enum. "
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
def _get_display_options(display_option):
    """
    Function that selects the specific options for the :param:display_type
    of class `GenericDisplay`(does not have anything to do with the type of data
    that is in the section); example options: width of the display, name of the
    colorbar, depth of the treemap
    For a complete list of the various options for a display option, look at the
    implementation of the display classes
    !!! All options from the Options class must be included

    :param display_option: the display
    :return: the options: an object of type `GenericDisplay.DisplayOptions`,
                          which encapsulates the specific display options for
                          the display option

    """
    if display_option == consts.DisplayOptions.TREEMAP:
        depth = config_parser.get_option_from_section(
            consts.DisplayOptions.TREEMAP.value, "depth", typ="int")
        return treemap.Treemap.DisplayOptions(depth=depth)

    elif display_option == consts.DisplayOptions.STACKPLOT:
        top_processes = config_parser.get_option_from_section(
            consts.DisplayOptions.STACKPLOT.value, "top", typ="int")
        return stackplot.StackPlot.DisplayOptions(top_processes=top_processes)

    elif display_option == consts.DisplayOptions.G2:
        track = config_parser.get_option_from_section(
            consts.DisplayOptions.G2.value, "track")
        return g2.G2.DisplayOptions(track=track)

    elif display_option == consts.DisplayOptions.HEATMAP:
        figure_size = config_parser.get_option_from_section(
            consts.DisplayOptions.HEATMAP.value, "figure_size", typ="float")
        scale = config_parser.get_option_from_section(
            consts.DisplayOptions.HEATMAP.value, "scale", typ="float")
        y_res = config_parser.get_option_from_section(
            consts.DisplayOptions.HEATMAP.value, "y_res", typ="float")
        parameters = heatmap.GraphParameters(
            figure_size=figure_size, scale=scale, y_res=y_res)
        normalise = config_parser.get_option_from_section(
            consts.DisplayOptions.HEATMAP.value, "normalised", typ="bool")
        colorbar = "No. Occurences"
        return heatmap.HeatMap.DisplayOptions(colorbar, parameters, normalise)

    elif display_option == consts.DisplayOptions.FLAMEGRAPH:
        coloring = config_parser.get_option_from_section(
            consts.DisplayOptions.FLAMEGRAPH.value, "coloring")
        return flamegraph.Flamegraph.DisplayOptions(coloring=coloring)

    elif display_option == consts.DisplayOptions.TCPPLOT:
        return tcpplotter.TCPPlotter.DisplayOptions()

    else:
        raise ValueError("Invalid display mode")


@util.log(logger)
def _args_parse(argv):
    """
    Create a parser that parses the display command.

    Mutex groups of arguments that are created in the parser object (each
    group represents the display options for a datatype, each group is
    optional):
        Stack:
            fg: display with a flamegraph
            tm: display with a treemap

        Event:
            g2: display with g2

        Point:
            hm: display with heatmap
            sp: display with stackplot

        infile i: the filename of the file containing the input (optional)
        outfile o: the filename of the file that stores the output (optional)

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

    # List functionality
    list = parser.add_argument_group()
    list.add_argument("-l", "--list", action="store_true",
                      help="list available datasets in data file")

    # Data entry selection
    data_entry = parser.add_argument_group()
    data_entry.add_argument("-e", "--entry", nargs='*',
                            help="select dataset(s) from data file")

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
        "-tcp", "--" + consts.DisplayOptions.TCPPLOT.value,
        action="store_true", help="display as TCP plot")

    # Group of the display options for displaying points
    point_display = parser.add_mutually_exclusive_group()
    point_display.add_argument(
        "-hm", "--" + consts.DisplayOptions.HEATMAP.value,
        action="store_true", help="display as heatmap")
    point_display.add_argument(
        "-sp", "--" + consts.DisplayOptions.STACKPLOT.value,
        action="store_true", help="display as stackplot")

    # Data aggregation
    agg = parser.add_argument_group()
    agg.add_argument(
        "--noagg", action="store_true",
        help="if set, none of the sections in the file will be aggregated")

    # Add flag and parameter for input filename
    filename = parser.add_argument_group()
    filename.add_argument(
        "-i", "--infile", type=str,
        help="Input file where collected data to display is stored")

    # Add flag and parameter for output filename
    filename = parser.add_argument_group()
    filename.add_argument("-o", "--outfile", type=str,
                          help="Output file where the graph is stored")

    return parser.parse_args(argv)


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
        input_filename = file.DataFileName(given_name=args.infile)
    else:
        input_filename = file.DataFileName.import_filename()
    if args.outfile:
        output_filename = file.DisplayFileName(given_name=args.outfile)
    else:
        output_filename = file.DisplayFileName()

    # Set up reader
    with data_io.Reader(str(input_filename)) as reader:
        standalone_interfaces = reader.get_all_interface_names()

        if args.list:
            headers = reader.get_header_list()
            for header in headers:
                print(header)
            exit(0)

        if args.entry:
            entries = set(int(arg) for arg in args.entry)
            standalone_interfaces = {reader.get_interface_from_index(index)
                                     for index in entries}

        # Check if the no_agg flag is set
        if not args.noagg:
            # Get the aggregate section from the config file
            aggregates = config_parser.get_section('Aggregate')

            # Display aggregates with the correct display mode
            for agg in aggregates:
                agg_interfaces = set(agg.replace(' ', '').split(','))
                if not standalone_interfaces.issuperset(agg_interfaces):
                    continue

                display_mode = aggregates[agg]
                data_objs = reader.get_interface_data(*agg_interfaces)
                datum_generators = [data.datum_generator for data in data_objs]
                datum_generator = itertools.chain(*datum_generators)

                # TODO: We skip options here
                if display_mode == consts.DisplayOptions.TCPPLOT.value:
                    display_object = tcpplotter.TCPPlotter(datum_generator)
                else:
                    raise ValueError(
                        'Display mode {} does not support displaying aggregated'
                        ' data'.format(display_mode)
                    )

                # Remove displayed interfaces from standalone set
                standalone_interfaces = standalone_interfaces - agg_interfaces
                # Display aggregates
                display_object.show()

        # Now we display the standalone sections
        for interface in standalone_interfaces:
            data = next(reader.get_interface_data(interface))

            # We select the display option based on args or the config file,
            # and get the associated options with that display option
            display_for_interface = _select_mode(
                data.interface.value, data.datatype, vars(args))
            display_options = _get_display_options(display_for_interface)
            data_options = data.data_options

            # We know the display option, we have its specific options, we only
            # need to initialize the display object
            if display_for_interface is consts.DisplayOptions.G2:
                display_object = g2.G2(data.datum_generator,
                                       data_options,
                                       display_options)
            elif display_for_interface is consts.DisplayOptions.HEATMAP:
                display_object = heatmap.HeatMap(
                    data.datum_generator, output_filename,
                    data_options, display_options)
            elif display_for_interface is consts.DisplayOptions.TREEMAP:
                display_object = treemap.Treemap(
                    data.datum_generator, output_filename,
                    data_options, display_options)
            elif display_for_interface is consts.DisplayOptions.STACKPLOT:
                display_object = stackplot.StackPlot(
                    data.datum_generator, data_options, display_options)
            elif display_for_interface is consts.DisplayOptions.FLAMEGRAPH:
                display_object = flamegraph.Flamegraph(
                    data.datum_generator, output_filename,
                    data_options, display_options)
            elif display_for_interface is consts.DisplayOptions.TCPPLOT:
                display_object = tcpplotter.TCPPlotter(
                    data.datum_generator, data_options, display_options)
            else:
                raise ValueError("Unexpected display mode {}!".
                                 format(display_for_interface))

            # Display it
            display_object.show()
