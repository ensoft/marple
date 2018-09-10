# -------------------------------------------------------------
# main.py - user interface, parses and applies display commands
# June-July 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Controller script - user interface, parses and applies display commands

Handles interaction between the output modules (flamegraph, g2, etc.)
It calls the relevant functions for each command.

"""
import marple.common.data_io

__all__ = "main"

import argparse
import logging

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
def _get_data_options(datatype, data_options):
    """
    Function that returns the data options for a section whose data is of type
    `datatype`. Data options include x axis label, x axis units for
    points, weight label for stacks

    :param datatype: the datatype we get options for
    :param data_options: options we use to set up the DataOptions class
    :return: returns a `DataOptions` object, which should be  a class
             declared in each of the 'Data' objects in the common.datatypes
             module
    """

    if datatype == consts.Datatypes.STACK.value:
        weight_units = data_options['weight_units']
        return data_io.StackData.DataOptions(weight_units)
    elif datatype == consts.Datatypes.EVENT.value:
        return None
    elif datatype == consts.Datatypes.POINT.value:
        x_label = data_options['x_label']
        y_label = data_options['y_label']
        x_units = data_options['x_units']
        y_units = data_options['y_units']
        return data_io.PointData.DataOptions(x_label, y_label, x_units,
                                             y_units)
    else:
        raise ValueError("Invalid datatype")


@util.log(logger)
def _display(args):
    """
    Function that deals with matching the sections from the input file (either
    the given one or the last file created with marple --collect) with their
    appropriate display options. Here we also fetch both the data options
    (options that are data specific, such as the label of the x axis for points)
    and the display options (display specific options, such as the maximum
    depth of a treemap)

    :param args:
        Command line arguments
        Passed by main function

    """
    # Try to use the specified input file, otherwise use last one created
    if args.infile:
        input_filename = file.DataFileName(given_name=args.infile)
    else:
        input_filename = file.DataFileName.import_filename()

    # Use user output filename specified, otherwise create a unique one
    if args.outfile:
        output_filename = file.DisplayFileName(given_name=args.outfile)
    else:
        output_filename = file.DisplayFileName()

    # Read the metaheader
    metaheader = marple.common.data_io.read_metaheader(input_filename)
    # Initially all sections are to be displayed as standalones
    standalone_sections_set = set(metaheader['sections'].split(','))

    # Check if the no_agg flag is set. If it is, we skip
    if not args.no_agg:
        # We get the Aggregate section that contains all the sections that
        # will be displayed using one display mode (sections are identified
        # using the interface that was used to collect them)
        aggregates = config_parser.get_section('Aggregate')

        # We iterate through all the options in aggregates and display it
        # with the appropriate display mode
        for agg in aggregates:
            sections = agg.replace(' ', '').split(',')
            display_mode = aggregates[agg]
            datum_generator = data_io.read_multiple_sect(input_filename,
                                                         sections)

            # TODO: We skip options here, is this ok (think so since when we
            # TODO: have aggregates we lose some info)
            if display_mode == consts.DisplayOptions.TCPPLOT:
                display_object = tcpplotter.TCPPlotter(datum_generator)
            else:
                raise ValueError('Display mode {} does not support '
                                 'displaying aggregated '
                                 'data'.format(display_mode))

            # We have displayed the sections used at this step at least in
            # one aggregate, so we remove them from the `to be displayed as
            # standalone` set
            standalone_sections_set.difference(sections)

            # Display aggregates
            display_object.show()

    # Now we display the standalone sections
    for section in standalone_sections_set:
        # Data object (EventData etc) that encapsulates the actual data
        # and the header
        data_object = marple.common.data_io.read_section(input_filename,
                                                         section,
                                                         consts.data_separator)

        # We select the display option based on args or the config file,
        # and get the associated options with that display option
        display_for_interface = _select_mode(data_object.interface,
                                             data_object.datatype,
                                             vars(args))
        display_options = _get_display_options(display_for_interface)
        data_options = _get_data_options(data_object.data_options)

        # We know the display option, we have its specific options, we only
        # need to initialize the display object
        if display_for_interface is consts.DisplayOptions.G2:
            display_object = g2.G2(data_object.datum_generator,
                                   data_options,
                                   display_options)
        elif display_for_interface is consts.DisplayOptions.HEATMAP:
            display_object = heatmap.HeatMap(
                data_object.datum_generator, output_filename,
                data_options, display_options)
        elif display_for_interface is consts.DisplayOptions.TREEMAP:
            display_object = treemap.Treemap(
                data_object.datum_generator, output_filename,
                data_options, display_options)
        elif display_for_interface is consts.DisplayOptions.STACKPLOT:
            display_object = stackplot.StackPlot(
                data_object.datum_generator, data_options, display_options)
        elif display_for_interface is consts.DisplayOptions.FLAMEGRAPH:
            display_object = flamegraph.Flamegraph(
                data_object.datum_generator, output_filename,
                data_options, display_options)
        elif display_for_interface is consts.DisplayOptions.TCPPLOT:
            display_object = tcpplotter.TCPPlotter(
                data_object.datum_generator, data_options, display_options)
        else:
            raise ValueError("Unexpected display mode {}!".
                             format(display_for_interface))

        # Display it
        display_object.show()


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
    parser = argparse.ArgumentParser(prog="marple --display",
                                     description="Display collected data "
                                     "in required format")

    # Group of the display options for displaying stacks
    stack_display = parser.add_mutually_exclusive_group()
    stack_display.add_argument("-fg", "--" +
                               consts.DisplayOptions.FLAMEGRAPH.value,
                               action="store_true", help="display as flamegraph")
    stack_display.add_argument("-tm", "--" +
                               consts.DisplayOptions.TREEMAP.value,
                               action="store_true", help="display as treemap")

    # Group of the display options for displaying events
    event_display = parser.add_mutually_exclusive_group()
    event_display.add_argument("-g2", "--" +
                               consts.DisplayOptions.G2.value,
                               action="store_true", help="display as g2 image")
    event_display.add_argument("-tcp", "--" +
                               consts.DisplayOptions.TCPPLOT.value,
                               action="store_true", help="display as TCP plot")

    # Group of the display options for displaying points
    point_display = parser.add_mutually_exclusive_group()
    point_display.add_argument("-hm", "--" +
                               consts.DisplayOptions.HEATMAP.value,
                               action="store_true", help="display as heatmap")
    point_display.add_argument("-sp", "--" +
                               consts.DisplayOptions.STACKPLOT.value,
                               action="store_true", help="display as stackplot")

    parser.add_argument("--noagg", action="store_true",
                        help="if set, none of the sections in the file"
                             "will be aggregated")

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
    Parses the cmd line arguments and displays either the sections in the
    provided file (args) or the last one created

    :param argv:
        command line arguments from call in main

    """
    # Parse arguments
    args = _args_parse(argv)

    # Call the appropriate functions to display input
    _display(args)
