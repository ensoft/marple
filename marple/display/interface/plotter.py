# -------------------------------------------------------------
# plotter.py - plots event data
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Display option that can display event data as a line graph

If the connect field of a datum is None, the event will be displayed as single
coloured triangles on the timeline, otherwise lines will connect sources and
destination based on the prefixes in the connect field
The UI is created automatically based on the properties specified in the
specific_datum field

"""

import colorsys
import functools
import itertools
import logging
import random
import re

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets

from marple.common import data_io
from marple.display.interface import generic_display

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', format(__name__))

_all__ = (
    "Plotter"
)


# TODO: more general x axis
class _PlotterContainer:
    """
    Class that wraps the plot container, together with all its plots; makes it
    easy to redraw the whole plot area when filtering

    """
    source_brush = pg.mkBrush('w')
    destination_brush = pg.mkBrush('w')
    # A list of easily distinguishable colours
    line_colors = [
        (0, 0, 255),
        (0, 255, 0),
        (255, 0, 0),
        (255, 255, 0),
        (0, 255, 255),
        (225, 0, 255),
        (255, 255, 255)
    ]

    def __init__(self, processed_data, y_axis_ticks):
        """
        Initialises the class

        :param processed_data: object of type `_EventDataProcessor`
        :param y_axis_ticks: list of strings, describing what the ticks
                             on the y axis should be (their names should
                             match with event properties)
        """
        def _create_map():
            """
            Helper method that creates a map between the track of each event
            (based on the ticks) and the y axis

            :return: a dict described above
            """
            ymap = {}
            unique_tracks = 0
            # We iterate through each event in each partition and assign its
            # track a y value
            for event_type in processed_data.get_event_types():
                partition = processed_data.get_specific_partition(event_type)
                for event in partition:
                    if event.connected is not None:
                        for sd_pair in event.connected:
                            # sd_pair[0] is the prefix for the source
                            # properties, sd_pair[1] is the prefix for the
                            # destination properties
                            source_track = self._compose_track(event,
                                                               sd_pair[0])
                            dest_track = self._compose_track(event, sd_pair[1])
                            if source_track not in ymap.keys():
                                ymap[source_track] = unique_tracks
                                unique_tracks += 1

                            if dest_track not in ymap.keys():
                                ymap[dest_track] = unique_tracks
                                unique_tracks += 1
                    else:
                        track = self._compose_track(event)
                        if track not in ymap.keys():
                            ymap[track] = unique_tracks
                            unique_tracks += 1
            return ymap

        def _assign_colors():
            """
            Helper method that creates a map between event types and colors

            If the number of event types is greater that the provided colors,
            we generate random saturated colors

            :return: a dict described above
            """
            colors = {}
            color_idx = 0
            for event_type in processed_data.get_event_types():
                if event_type not in colors:
                    if color_idx < len(self.line_colors):
                        colors[event_type] = self.line_colors[color_idx]
                        color_idx += 1
                    else:
                        # If every hard coded colour has been used,
                        h, s, l = random.random(), \
                                  0.5 + random.random() / 2.0, \
                                  0.4 + random.random() / 5.0
                        r, g, b = [int(256 * i) for i in
                                   colorsys.hls_to_rgb(h, l, s)]
                        colors[event_type] = (r, g, b)
            return colors

        def _create_container_and_plots(ticks):
            """
            Helper method that creates the plot container, sets up the event
            and helper plots, the axes labels and ticks

            :param ticks: The ticks to be used on the y axis
            :return: plot_container: a plot container as `pg.PlotItem`
                     event_plots: a dict that maps event types to the plots in
                                  the plot container
                     helper_plots: a dict that maps the helper plot labels
                                   to plots in the plot container
            """
            plot_container = pg.PlotItem(title="Events",
                                         labels={
                                             'left': ','.join(
                                                 self.y_axis_ticks),
                                             'bottom': 'time (ms)'},
                                         axisItems={'left': ticks})

            # Event plots init
            event_plots = {}
            for event_type in self.processed_data.get_event_types():
                event_plots[event_type] = plot_container.plot([], [])

            # Helper plots init
            helper_plots = {
                'lines': plot_container.plot([], []),
                'highlight': plot_container.plot([], [])
            }
            return plot_container, event_plots, helper_plots

        def _create_ticks():
            """
            Helper method that creates the y axis ticks

            :return: a `pg.AxisItem` that has its ticks set to the event tracks
                     we have created in the mapping stage
            """
            ticks = pg.AxisItem(orientation='left')
            ticks.setTicks([dict(enumerate(self.tracks_ymap.keys())).items()])
            return ticks

        def _add_legend():
            """
            Helper function that adds a legend in the top right corner
            for the graph lines and symbols

            """
            legend = pg.LegendItem((0, 0), (0, 1))
            legend.setParentItem(self.plot_container)
            legend.addItem(pg.PlotDataItem(symbol='s'),
                           "Source")
            legend.addItem(pg.PlotDataItem(symbol='o'),
                           "Destination")

            for event_type in self.processed_data.get_event_types():
                legend.addItem(pg.PlotDataItem(
                    pen=pg.mkPen(color=self.line_colors[event_type], width=3)),
                    event_type)

            legend.addItem(pg.PlotDataItem(pen=pg.mkPen('y', width=3)),
                           "Selected process")
        ######################

        self.processed_data = processed_data
        self.y_axis_ticks = y_axis_ticks
        self.tracks_ymap = _create_map()
        self.line_colors = _assign_colors()

        # Create ticks
        self.tick = _create_ticks()

        self.plot_container, self.event_plots, self.helper_plots = \
            _create_container_and_plots(self.tick)

        # Max y coord
        self.max_y = max(self.tracks_ymap.values())
        # Max x coord (max time)
        self.max_x = max(map(lambda event: event.time,
                             self.processed_data.get_all_events()))

        # We set the limits for the dispay viewbox (so we only have positive xs
        # and ys); we use the +-1000 so things don't get clipped
        # TODO: change +- here based on zoom
        self.plot_container.vb.setLimits(xMin=-10000, xMax=self.max_x + 10000,
                                         yMin=-1, yMax=self.max_y + 1)

        # We draw the support lines
        ys = list(self._concat([[y, y] for y in range(0, self.max_y + 1)]))
        xs = [0, self.max_x] * (self.max_y + 1)
        self.helper_plots['lines'].setData(xs, ys,
                                           pen=pg.mkPen(255, 255, 255, 32),
                                           connect="pairs")

        # Add legend
        _add_legend()

    def get_plot_container(self):
        """ Getter method that returns the plot container"""
        return self.plot_container

    def get_plot_from_container(self, name):
        """ Getter method that returns the plot with the specified name"""
        return self.plot_container[name]

    @staticmethod
    def _concat(ll):
        """
        Helper function that converts a list of lists into a single list,
        perserving order
        :param ll: the list of lists to be concat'ed
        :return: a single list produced from the input
        """
        for l in ll:
            for item in l:
                yield item

    def _compose_track(self, event, prefix=""):
        """
        Helper method that composes the tracks by searching for the properties
        in self.y_axis_tick in event.specific_datum.
        Example: when we call _compose_track(event, "source_") for the ticks
                 ['comm', 'pid'] (and suppose the event has fields
                 source_track: "abc", source_pid: 1) it will return "abc, 1"

        :param event: the event we want to create a track for
        :param prefix: the prefix used to extract the info for events that
                       display connections
        :return: the created track
        """
        return ','.join([str(event.specific_datum[prefix + tick_track])
                         for tick_track in self.y_axis_ticks])

    def empty_plot(self, plot_name):
        """
        Empties the specified plot
        :param plot_name: name of the plot to be emptied

        """
        # Special case for the helpe plot
        if plot_name == 'highlight':
            self.helper_plots['highlight'].setData([], [])
        else:
            self.event_plots[plot_name].setData([], [], symbol=[],
                                                symbolBrush=[])

    def empty_all_plots(self):
        """
        Empties all plots (doesn't empty the support lines)

        """
        self.empty_plot('highlight')

        for event_type in self.processed_data.get_event_types():
            self.empty_plot(event_type)

    def draw(self, event_type):
        """
        Draws all the messages of the provided type

        :param event_type: the type of the messages to be drawn

        """
        self.empty_plot('highlight')

        partition = self.processed_data.get_specific_partition(event_type)
        # processes saves y coords, times saves x coords
        # processes[i] and times[i] are coords for the i-th point that is to
        # be drawn
        processes, times = [], []

        for event in partition:
            if event.connected is not None:
                for sd_pair in event.connected:
                    # For each source and destination we add the corresponding
                    # tracks to the line lists
                    source_track = self._compose_track(event, sd_pair[0])
                    dest_track = self._compose_track(event, sd_pair[1])
                    processes.extend([source_track, dest_track])
                    times.extend([event.time, event.time])
            else:
                track = self._compose_track(event)
                processes.append(track)
                times.append(event.time)
        num_points = len(times)

        # We look at the first event of the partition to deduce if we have
        # a partition that draws lines or just points and get the right settings
        if partition[0].connected is not None:
            connect = "pairs"
            pen = self.line_colors[event_type]
            # Symbols and brushes must alternate since we have a chain of
            # pairs (source, dest)
            symbol = ['s' if i % 2 == 0 else 'o' for i in range(num_points)]
            symbol_brushes = [self.source_brush if i % 2 == 0 else
                              self.destination_brush for i in range(num_points)]
        else:
            connect = None
            pen = None

            symbol = ['t2'] * num_points
            symbol_brushes = [pg.mkBrush(self.line_colors[event_type])] * \
                             num_points

        # Now we draw the markers and lines
        self.event_plots[event_type].setData(
            {
                'x': times,
                # With the ys we need to convert from process names to numbers
                # on the y axis
                'y': list(map(lambda process: self.tracks_ymap[process],
                              processes))
            },
            symbol=symbol,
            pen=pen,
            symbolBrush=symbol_brushes,
            connect=connect,
            symbolSize=7
        )


class _EventDataProcessor:
    """
    Class that deal with processing the various properties of the event data so
    events are ready to be drawn

    Provides different getters, for various fields
    """
    def __init__(self, events):
        """
        Initialises the class

        :param events: Events that we want processed
        """

        def process_data(events):
            """
            Helper method that partitions the events based on their type and
            gets all the properties present in them (so they can be filtered
            later)
            Properties will get their source - destination prefixed stripped
            so we can treat 'pid', 'source1_pid', 'dest4_pid' the same

            :param: the events we want to process as a generator
            :returns: a dictionary representing the partition and a set for the
                      properties
            """
            properties_set = set()
            event_partition = {}

            min_time = None
            for event in events:
                # Determine mintime:
                if min_time is None:
                    min_time = event.time
                else:
                    min_time = min(min_time, event.time)

                # Extract info
                connected = event.connected

                if connected is not None:
                    for prop in event.specific_datum.keys():
                        for pair in connected:
                            source_prefix, dest_prefix = pair[0], pair[1]
                            match_src = re.match(source_prefix, prop)
                            match_dst = re.match(dest_prefix, prop)
                            if match_src is not None:
                                prop = prop[match_src.end():]
                            elif match_dst is not None:
                                prop = prop[match_dst.end():]
                            properties_set.add(prop)
                else:
                    for prop in event.specific_datum.keys():
                        properties_set.add(prop)

                # Add the event to either an existing partition or a new one
                if event.type not in event_partition:
                    event_partition[event.type] = [event]
                else:
                    event_partition[event.type].append(event)

            return event_partition, properties_set, min_time

        # Process the data using the above function
        self.event_partition, self.properties_set, self.min_time = \
            process_data(events)

        # We normalise the times so they start at 0
        self._normalise()

    def _normalise(self):
        """
        Helper function that normalises the times so they start at 0, by
        subtracting the minimum time from each of them

        """
        for partition in self.event_partition.values():
            for idx, event in enumerate(partition):
                # We replace the event datum from the partition with a new one,
                # whose time is normalised
                partition[idx] = data_io.EventDatum(event.time - self.min_time,
                                                    event.type,
                                                    event.specific_datum,
                                                    event.connected)

    # The following getter functions make it easier to interact with the
    # process data
    def get_specific_partition(self, event_type):
        return self.event_partition[event_type]

    def get_all_events(self):
        """
        :return: a list with all the events
        """
        events = []
        for event_subset in self.event_partition.values():
            for event in event_subset:
                events.append(event)
        return events

    def get_properties(self):
        return self.properties_set

    def get_event_types(self):
        return self.event_partition.keys()

    @staticmethod
    def get_property_value(event, property, prefix=""):
        """
        Helper function that retrieves the value of a property
        Used outside the class

        :param event: the event we want the property from
        :param property: the name of the property
        :param prefix: the prefix, if any, used to strip the source and
                       destination prefixes so we know 'source_pid' is the same
                       as 'pid'
        :return: the value of the property or None if it was not found
        """
        if prefix + property in event.specific_datum:
            return str(event.specific_datum[prefix + property])

        # Otherwise
        return None


class _UIElementManager:
    """
    Class that deals with the creation of new UI elements, and keeping track
    of them

    """
    def __init__(self):
        self.ui_dict = {}

    def new_ui_elem(self, ui_elem, name, text, **kwargs):
        """
        Factory function that creates UI elements and puts them in the UI
        dictionary (used for referencing them later)

        :param ui_elem: type of the UI element to be added
        :param name: name of the UI element, used as key for the dictionary
        :param text: text to be displayed on the UI element
        :param kwargs: additional parameters that are required by the UI,
                       such as callback functions

        """
        if ui_elem == 'check':
            new_elem = QtGui.QCheckBox(text)
            new_elem.stateChanged.connect(kwargs["callback_function"])
        elif ui_elem == 'text':
            new_elem = QtGui.QLineEdit(text)
        elif ui_elem == 'button':
            new_elem = QtGui.QPushButton(text)
            new_elem.clicked.connect(kwargs["callback_function"])
        elif ui_elem == 'group_box':
            new_elem = QtGui.QGroupBox(text)
            new_elem.setLayout(QtGui.QFormLayout())
        elif ui_elem == 'scroll_area':
            # Needs to be wrapped in a proxy object since this is the
            # element that actually gets put on the window, and the window does
            # not accept elements
            scroll_check = QtGui.QScrollArea()
            scroll_check.setWidget(kwargs['widget'])
            scroll_check.setWidgetResizable(True)
            scroll_check.setFixedHeight(kwargs['height'])
            new_elem = QtGui.QGraphicsProxyWidget()
            new_elem.setWidget(scroll_check)
        else:
            raise ValueError('Invalid UI elem type')

        # We save the element in the dictionary so we can refer it later
        self.ui_dict[name] = new_elem

    def get_ui_elem(self, name):
        """
        UI getter function

        :param name: name of the UI object we want
        :return: the UI object
        """
        if name in self.ui_dict:
            return self.ui_dict[name]

        # Otherwise
        raise KeyError("No element with the supplied name found")


class _PlotterWindow(pg.GraphicsWindow):
    """
    Class that that oversees the creation of the plotter window and the UI,
    their layouts, and what goes into them (using the classes above)

    """

    def __init__(self, event_generator, parent=None):
        """
        Initialises the window

        :param event_generator: A generator that gives the events that we
                                use to populate the graph
        :param parent: parent of the window, should be left None

        """
        # Initialise superclass
        super().__init__(parent=parent)

        # Process data, this data will remain unchanged (so we can filter
        # things from it)
        self.processed_data = _EventDataProcessor(event_generator)
        # We store the currently displayed data (changes when filtering)
        self.current_displayed_data = self.processed_data

        # Setup current graph
        # TODO: add a config option for the tracks
        self.current_plot = _PlotterContainer(self.current_displayed_data,
                                              ['comm', 'pid'])

        # Setup UI
        self.ui_manager = _UIElementManager()
        self._add_ui()

        # Manage the layout now that we have both the plot container and the
        # UI
        self._manage_layout()

    def _add_ui(self):
        """
        Function used during init that draws the UI elements (graph, buttons,
        text fields) the user interacts with

        """
        # The two callbacks functions here are used so that a new function
        # object is created each time we create a checkbox (for example the
        # scoping of lambdas in for loops makes them not usable in this case
        # since the lambdas get overwritten)
        def callback_check(state, event_type):
            # state here describes the state of the checkbox
            return self.current_plot.draw(event_type) if state == 2 \
                else self.current_plot.empty_plot(event_type)

        def callback_filter(prop):
            return self.new_graph_from_filter(prop,
                                              self.ui_manager
                                              .get_ui_elem('regex_' + prop)
                                              .text())

        self.ui_manager.new_ui_elem("group_box", "cb_select",
                                    "Display / hide event types")
        self.ui_manager.new_ui_elem("group_box", "cb_filter", "Filtering")

        # First draw the checkboxes
        for event_type in self.current_displayed_data.get_event_types():
            callback = functools.partial(callback_check, event_type=event_type)
            self.ui_manager.new_ui_elem("check", event_type + "_check",
                                        "Show " + event_type,
                                        callback_function=callback)
            self.ui_manager.get_ui_elem("cb_select").layout().addRow(
                self.ui_manager.get_ui_elem(event_type + "_check"))

        # Now the filters
        for prop in self.current_displayed_data.get_properties():
            callback = functools.partial(callback_filter, prop)
            self.ui_manager.new_ui_elem("text", "regex_" + prop, "")
            self.ui_manager.new_ui_elem("button", "filter_" + prop,
                                        "Filter by {} (prefix match)"
                                            .format(prop),
                                        callback_function=callback)
            self.ui_manager.get_ui_elem("cb_filter").layout().addRow(
                self.ui_manager.get_ui_elem("regex_" + prop),
                self.ui_manager.get_ui_elem("filter_" + prop))

        # A clear highlight button
        self.ui_manager.new_ui_elem("button", "clear_highlight",
                                    "Clear highlight",
                                    callback_function=lambda:
                                        self.current_plot.
                                            empty_plot('highlight'))
        self.ui_manager.get_ui_elem("cb_filter").layout().addRow(
            self.ui_manager.get_ui_elem("clear_highlight"))

        self.ui_manager.new_ui_elem("scroll_area", "scroll_select", "",
                                    widget=self.ui_manager.get_ui_elem(
                                        "cb_select"),
                                    height=200)

        self.ui_manager.new_ui_elem("scroll_area", "scroll_filter", "",
                                    widget=self.ui_manager.get_ui_elem(
                                        "cb_filter"),
                                    height=200)

    def _manage_layout(self):
        """
        Creates the layout and puts the right things in the right cells

        """
        self.plot_layout = self.addLayout(row=0, col=0, colspan=2)
        self.plot_layout.addItem(self.current_plot.plot_container)

        self.select_layout = self.addLayout(row=1, col=0)
        self.select_layout.addItem(self.ui_manager.get_ui_elem(
            "scroll_select"
        ))

        self.filter_layout = self.addLayout(row=1, col=1)
        self.filter_layout.addItem(self.ui_manager.get_ui_elem(
            "scroll_filter"
        ))

    def _hide_unused_checkboxes(self):
        """
        Hides the checkboxes that are not relevant for the currently displayed
        data

        """
        for event_type in self.processed_data.get_event_types():
            if event_type in self.current_displayed_data.get_event_types():
                hidden = False
            else:
                hidden = True
            self.ui_manager.get_ui_elem(event_type + "_check").setHidden(hidden)

    # TODO: Add highlighting
    def new_graph_from_filter(self, property, filters):
        """
        Highlights the selected processes and displays only the markers
        for lines which have at least one end on a highlighted lines (easier
        for tracking)
        :param property:
        :param filters:

        """
        def check_regex(to_match, regex_list):
            """
            Helper function that returns true if to_match matches with any
            of the regex patterns in regex_list, false otherwise

            :param to_match: text to be matched against the pattern list
            :param regex_list: regex pattern list
            :return: True if we have a match, False otherwise
            """
            for reg_ex in regex_list:
                if re.match(reg_ex, to_match):
                    return True
            return False

        for event_type in self.processed_data.get_event_types():
            self.ui_manager.get_ui_elem(event_type + "_check").setChecked(False)

        # Parse the input into a list of regex patterns
        filters = filters.replace(' ', '').split(',')

        # Now for each type of message, select points that need to be displayed
        filtered_events = []
        for partition in self.processed_data.event_partition.values():
            # Now we go through all the points, two at a time since adjacent
            # points form lines (pairs source - destination), and chech if any
            # of them lie on a selected line; if this is true, then we draw
            # both of them
            for event in partition:
                if event.connected is not None:
                    for sd_pair in event.connected:
                        s_value = _EventDataProcessor.get_property_value(
                                    event,
                                    property,
                                    prefix=sd_pair[0])
                        d_value = _EventDataProcessor.get_property_value(
                                    event,
                                    property,
                                    prefix=sd_pair[1])
                        if s_value is not None and \
                                check_regex(s_value, filters) or d_value is \
                                not None and check_regex(d_value, filters):
                            filtered_events.append(event)

                else:
                    value = _EventDataProcessor.get_property_value(
                                event, property)
                    if value is not None and check_regex(value, filters):
                        filtered_events.append(event)
        # If the filter finds nothing, do nothing and show an message box
        if not filtered_events:
            QtGui.QMessageBox.warning(self, 'PyQt5 message',
                                      "No events found! No filtering applied "
                                      "(the data remained the same)")
            return

        filtered_data = _EventDataProcessor(filtered_events)
        new_plot_container = _PlotterContainer(filtered_data,
                                               ['comm', 'pid'])

        # Update the data and the display
        self.plot_layout.removeItem(self.current_plot.plot_container)
        self.plot_layout.addItem(new_plot_container.plot_container)
        self.current_plot = new_plot_container
        self.current_displayed_data = filtered_data
        self._hide_unused_checkboxes()


class Plotter(generic_display.GenericDisplay):
    """
    Class that displays event data as a custom line graph"

    """

    def __init__(self, *data):
        """
        Initializes the class.

        """
        # Initialise superclass
        # TODO tidy this up - all display interfaces should have same approach
        super().__init__(*data)

        datum_generator = itertools.chain(*[d.datum_generator for d in data])
        self.data_gen = datum_generator

    def show(self):
        """
        Populates the graph and shows it in an interactive window

        """
        app = QtWidgets.QApplication([])

        renderer = _PlotterWindow(self.data_gen)
        pg.setConfigOptions(antialias=False)
        renderer.showMaximized()
        renderer.raise_()
        app.exec_()
