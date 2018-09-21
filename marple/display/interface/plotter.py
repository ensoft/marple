# -------------------------------------------------------------
# plotter.py - plots event data
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Visualiser that can display event data as a line graph

If the connect field of a datum is None, the event will be displayed as single
coloured triangles on the timeline, otherwise lines will connect sources and
destination based on the prefixes in the connected field (see the `EventDatum`
class from the module `common.data_io`
The UI is created automatically based on the properties specified in the
specific_datum field

Terminology:
    * ticks: the small lines that mark points on an axis (for example on the
             x axis there are ticks at 0, 1, 2, 3, 4, 5...
    * tracks: labels for the ticks on the y axis; in the case of events those
              can be composed from several properties (for example we can have
              have as labels the comm and pid of a process)
    * symbols: the markers used for events; for standalone events we have
               triangles (`t2`); for connected event we have square for the
               source (`s`) and circle for the destination (`o`)

"""

import colorsys
import functools
import itertools
import logging
import random
import re

import pyqtgraph as pg
from pyqtgraph import Qt as Qt

from marple.common import data_io
from marple.display.interface import generic_display

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', format(__name__))

_all__ = (
    "Plotter"
)


# TODO: more general x axis
class _PlotContainer:
    """
    Class that wraps the plot container from pyqtgraph, together with the plots

    Makes it easy to redraw the whole plot area when filtering and decouples
    the plot from the actual window

    """
    source_brush = pg.mkBrush('w')
    destination_brush = pg.mkBrush('w')
    # A list of easily distinguishable colours
    color_list = [
        (0, 0, 255),  # blue
        (0, 255, 0),  # green
        (255, 0, 0),  # red
        (255, 255, 0),  # yellow
        (0, 255, 255),  # cyan
        (225, 0, 255),  # violet
        (255, 255, 255)  # white
    ]

    def __init__(self, processed_data, y_axis_ticks):
        """
        Initialises the class

        :param processed_data: object of type `_EventDataProcessor`
        :param y_axis_ticks: list of strings, what the tracks on the y axis
                             represent; (eg. the list ['comm', 'pid']
                             will tell that on the y axis the tracks will be
                             of the form 'comm, pid')

        """
        self.processed_data = processed_data
        self.y_axis_ticks = y_axis_ticks
        self.tracks_ymap = self._create_map()
        self.color_map = self._assign_colors()
        self.tick = self._create_ticks()

        if len(self.tracks_ymap) == 0:
            raise ValueError("No data to be displayed in the plotter!")

        # Max y coord
        self.max_y = max(self.tracks_ymap.values())
        # Max x coord (max time) TODO: move to event processor
        self.max_x = max(map(lambda event: event.time,
                             self.processed_data.get_all_events()))

        self.plot_container, self.event_plots, self.helper_plots = \
            self._create_container_and_plots(self.tick)

        # We set the limits for the dispay viewbox (so we only have positive xs
        # and ys); we use the +-1000 so things don't get clipped
        # TODO: change +- here based on zoom
        self.plot_container.vb.setLimits(xMin=-10000, xMax=self.max_x + 10000,
                                         yMin=-1, yMax=self.max_y + 1)

        # Add legend
        self._add_legend()

    def _create_map(self):
        """
        Creates a map between the track names and the y axis

        The values on the y axis of the tracks are assigned in increasing order,
        starting from 0. When we encounter a track that was not seen before,
        assign it the next number on the y axis; if a track has been encountered
        before, we pass.

        :return: a dict described above
        """
        ymap = {}
        unique_tracks = 0
        for event in self.processed_data.get_all_events():
            # If the event is connected we need to check for new
            # tracks in both the source and the destination
            if event.connected is not None:
                for sd_pair in event.connected:
                    # sd_pair[0] is the prefix for the source
                    # properties, sd_pair[1] is the prefix for the
                    # destination properties
                    source_track = self._compose_track(event, sd_pair[0])
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

    def _assign_colors(self):
        """
        Method that creates a map between event types and colors.

        If the number of event types is greater that the number of hard coded
        colors, we generate random saturated colors that should be easily
        distinguishable.

        :return: a dict described above
        """
        colors = {}
        color_idx = 0
        for event_type in self.processed_data.get_event_types():
            if event_type not in colors:
                if color_idx < len(self.color_list):
                    colors[event_type] = self.color_list[color_idx]
                    color_idx += 1
                else:
                    # If every hard coded colour has been used
                    # Get a hsl color that is saturated and luminous
                    h, s, l = random.random(), \
                              0.5 + random.random() / 2.0, \
                              0.4 + random.random() / 5.0
                    # And convert it to rgb
                    r, g, b = [int(256 * i) for i in
                               colorsys.hls_to_rgb(h, l, s)]
                    colors[event_type] = (r, g, b)
        return colors

    def _create_container_and_plots(self, ticks):
        """
        Method that creates the plot container, sets up the event
        and helper plots, the axes labels and ticks.

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

        # For the support lines: one for each track, from 0 to the maximum y
        # value assigned during the mapping; the length of each line is the
        # maximum event time
        xs = [0, self.max_x] * (self.max_y + 1)
        # For y we must repeat each coord two times so we have a y coord for
        # both the dest and the source (horizontal line)
        ys = [y
              for t in range(0, self.max_y + 1)
              for y in [t, t]]
        helper_plots = {
            'lines': plot_container.plot(xs, ys,
                                         pen=pg.mkPen(255, 255, 255, 32),
                                         connect="pairs"),
            'highlight': plot_container.plot([], [])
        }
        return plot_container, event_plots, helper_plots

    def _create_ticks(self):
        """
        Method that creates the y axis ticks.

        :return: a `pyqtgraph.AxisItem` that has its ticks set to the event
                 tracks we have created in the mapping stage
        """
        ticks = pg.AxisItem(orientation='left')
        ticks.setTicks([dict(enumerate(self.tracks_ymap.keys())).items()])
        return ticks

    def _add_legend(self):
        """
        Helper function that adds a legend in the top right corner
        for the graph lines and symbols

        """
        # Numbers here make sure we position the legend in the top right corner
        legend = pg.LegendItem((0, 0), (0, 1))
        legend.setParentItem(self.plot_container)
        legend.addItem(pg.PlotDataItem(symbol='s'),
                       "Source")
        legend.addItem(pg.PlotDataItem(symbol='o'),
                       "Destination")

        # We add each event type with its colour
        for event_type in self.processed_data.get_event_types():
            legend.addItem(pg.PlotDataItem(
                pen=pg.mkPen(color=self.color_map[event_type], width=3)),
                event_type)

        legend.addItem(pg.PlotDataItem(pen=pg.mkPen('y', width=3)),
                       "Selected process")
# ---------------------------- Init end here

    def get_plot_container(self):
        """ Getter method that returns the plot container"""
        return self.plot_container

    def get_plot_from_container(self, name):
        """ Getter method that returns the plot with the specified name"""
        return self.plot_container[name]

    def _compose_track(self, event, prefix=""):
        """
        Helper method that composes the tracks by searching for the properties
        in `y_axis_ticks` in event.specific_datum.
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

    def draw_type(self, event_type):
        """
        Draws all the messages of the provided type

        :param event_type: the type of the messages to be drawn

        """
        self.empty_plot('highlight')

        partition = self.processed_data.get_specific_partition(event_type)
        # `processes` saves y coords, `times` saves x coords
        # processes[i] and times[i] are coords for the i-th point that is to
        # be drawn
        processes, times = [], []

        for event in partition:
            if event.connected is not None:
                for sd_pair in event.connected:
                    # For each source and destination we add the corresponding
                    # tracks to the y axis point list (`processes`)
                    source_track = self._compose_track(event, sd_pair[0])
                    dest_track = self._compose_track(event, sd_pair[1])
                    processes.extend([source_track, dest_track])

                    # We add the time twice, once for the source, once for the
                    # destination
                    times.extend([event.time, event.time])
            else:
                track = self._compose_track(event)
                processes.append(track)
                times.append(event.time)
        num_points = len(times)

        # We look at the first event of the partition to deduce if we have
        # a partition that draws lines or just points, and get the right
        # settings
        if partition[0].connected is not None:
            # We connect adjacent points ((source, dest), (source, dest), ...)
            connect = "pairs"
            # For the lines
            pen = self.color_map[event_type]
            # Symbols and brushes must alternate since we have a chain of
            # pairs (source, dest)
            symbol = ['s' if i % 2 == 0 else 'o' for i in range(num_points)]
            symbol_brushes = [self.source_brush if i % 2 == 0 else
                              self.destination_brush for i in range(num_points)]
        else:
            connect = None
            pen = None
            symbol = ['t2'] * num_points
            symbol_brushes = [pg.mkBrush(self.color_map[event_type])] * \
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
    Class that deal with processing the event data.

    Processes various properties of the event data so we separate the processing
    from drawing. Provides different getters, for various fields
    """
    def __init__(self, events):
        """
        Initialises the class

        :param events: An iterable representing the events
        """

        self.event_partition, self.properties_set, self.min_time = \
            self._process_data(events)

        # We normalise the times so they start at 0
        self._normalise()

    @staticmethod
    def _process_data(events):
        """
        Method that processes the data

        Functionality:
            * partitions the events based on their type (a partition for each
              type);
            * gets all the properties present in the specific_datum fields of
              the events(so they can be filtered later); properties that are in
              a `connected` event will get their source - destination prefixed
              stripped so we can treat 'pid', 'source1_pid', 'dest4_pid' the
              same

        :param: an iterable representing the events we want to process
        :return: a dictionary representing the partition, a set for the
                 properties and the min_time (used during normalisation)
        """
        properties_set = set()
        event_partition = {}

        min_time = None
        for event in events:
            # Determine mintime:
            min_time = min(min_time, event.time) if min_time is not None \
                                                 else event.time

            connected = event.connected
            if connected is not None:
                for prop in event.specific_datum.keys():
                    for sd_pair in connected:
                        source_prefix, dest_prefix = sd_pair[0], sd_pair[1]
                        match_src = re.match(source_prefix, prop)
                        match_dst = re.match(dest_prefix, prop)
                        # A property can belong to either the source or the
                        # destination
                        if match_src is not None:
                            # Source's prefix matched, its property
                            prop = prop[match_src.end():]
                        elif match_dst is not None:
                            # Dest's prefix matched, its property
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

    def _normalise(self):
        """
        Normalises the times in the events so they start at 0

        Method that subtracts the minimum time from all the event times so that
        they start at 0. Since the EventDatum is imutable we can't just change
        the time, so we create new events with the new times.

        """
        for partition in self.event_partition.values():
            for idx, event in enumerate(partition):
                partition[idx] = data_io.EventDatum(event.time - self.min_time,
                                                    event.type,
                                                    event.specific_datum,
                                                    event.connected)
    # ---------------------------------- Init finished

    # The following getter functions make it easier to interact with the
    # process data
    def get_specific_partition(self, event_type):
        """Getter that returns the events from the specified partition"""
        return self.event_partition[event_type]

    def get_all_events(self):
        """Getter that return all the events as a list"""
        events = []
        for event_subset in self.event_partition.values():
            for event in event_subset:
                events.append(event)
        return events

    def get_properties(self):
        """Geter that returns the properties set"""
        return self.properties_set

    def get_event_types(self):
        """Getter that returns the event_types"""
        return self.event_partition.keys()

    @staticmethod
    def get_property_value(event, property, prefix=""):
        """
        Method that return the value of a propery from the specific datum field.

        :param event: the event we want the property from
        :param property: the name of the property
        :param prefix: the prefix, if any, used to strip the source and
                       destination prefixes so we know 'source_pid' is the same
                       as 'pid'
        :return: the value of the property or None if it was not found
        """
        if prefix + property in event.specific_datum:
            return str(event.specific_datum[prefix + property])
        else:
            return None


class _UIElementManager:
    """
    Class that deals with the creation of new UI elements

    Provides a factory method; it keeps track of the created elements using a
    dictionary

    """
    def __init__(self):
        self.ui_dict = {}

    def new_ui_elem(self, ui_elem, name, text, **kwargs):
        """
        Factory function that creates UI elements.

        Creates elements and puts them in the UI dictionary (used for
        referencing them later)

        :param ui_elem: string representing the type of the UI element to
                        be added
        :param name: string representing the name of the UI element,
                     used as key for the dictionary
        :param text: text to be displayed on the UI element
        :param kwargs: additional parameters such as callback functions;

        """
        if ui_elem == 'check':
            new_elem = Qt.QtGui.QCheckBox(text)
            new_elem.stateChanged.connect(kwargs["callback_function"])
        elif ui_elem == 'text':
            new_elem = Qt.QtGui.QLineEdit(text)
        elif ui_elem == 'button':
            new_elem = Qt.QtGui.QPushButton(text)
            new_elem.clicked.connect(kwargs["callback_function"])
        elif ui_elem == 'group_box':
            new_elem = Qt.QtGui.QGroupBox(text)
            new_elem.setLayout(Qt.QtGui.QFormLayout())
        elif ui_elem == 'scroll_area':
            # Needs to be wrapped in a proxy object since this is the
            # element that actually gets put on the `pyqtgraph`.GraphicsWindow`,
            # and the window does not accept Qt widgets
            scroll_check = Qt.QtGui.QScrollArea()
            scroll_check.setWidget(kwargs['widget'])
            scroll_check.setWidgetResizable(True)
            scroll_check.setFixedHeight(kwargs['height'])
            new_elem = Qt.QtGui.QGraphicsProxyWidget()
            new_elem.setWidget(scroll_check)
        else:
            raise ValueError('Invalid UI elem type')

        # We save the element in the dictionary so we can refer it later
        self.ui_dict[name] = new_elem

    def get_ui_elem(self, name):
        """
        UI element getter function

        :param name: string representing the name of the UI object we want
        :return: the UI object
        """
        if name in self.ui_dict:
            return self.ui_dict[name]

        # Otherwise
        raise KeyError("No element with the supplied name found")


class _PlotterWindow(pg.GraphicsWindow):
    """
    Class that manages the window as a whole.

    It oversees the creation of the plotter window and the UI,
    their layouts, and what goes into them (using the classes above)

    """

    def __init__(self, event_generator, tracks, parent=None):
        """
        Initialises the window

        :param event_generator: A generator that gives the events that we
                                use to populate the graph
        :param parent: parent of the window, should be left None

        """
        super().__init__(parent=parent)

        # Process data, this data will remain unchanged (so we can filter
        # things from it)
        self.processed_data = _EventDataProcessor(event_generator)
        # We store the currently displayed data (changes when filtering)
        self.current_displayed_data = self.processed_data

        # Setup current graph
        # TODO: add a config option for the tracks
        self.current_plot = _PlotContainer(self.processed_data,
                                           tracks)

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
            # state here describes the state of the checkbox (2 means checked)
            return self.current_plot.draw_type(event_type) if state == 2 \
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
        Creates the layout and puts the right things in the right cells of the
        window grid

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
        Method that hides the checkboxes that are not relevant to the displayed
        data

        """
        for event_type in self.processed_data.get_event_types():
            hidden = event_type in \
                     self.current_displayed_data.get_event_types()
            self.ui_manager.get_ui_elem(event_type + "_check").setHidden(hidden)

    # TODO: Add highlighting
    def new_graph_from_filter(self, property, filters):
        """
        Redraws elements of the window in accordance with the displayed data.

        Redraws the plots so that they only contain the filtered data and
        dynamically updates the UI to reflect only the displayed data (however,
        the original data is still kept so we can filter on it later). The
        events that remain after the filtering are event that have the property
        `property` and at least one of the regex from `filter` matches it.

        :param property: the property we want to filter by as a string
        :param filters: the filters as comma separated regexes;

        """
        def check_match(to_match, regex_list):
            """
            Helper function that returns true if `to_match` matches with any
            of the regex patterns in `regex_list` (prefix match),
            false otherwise

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
                        # If any of the source or the destination have a propery
                        # that matches any of the filters, the event should be
                        # displayed
                        if s_value is \
                                not None and check_match(s_value, filters) or \
                           d_value is \
                                not None and check_match(d_value, filters):
                            filtered_events.append(event)

                else:
                    value = _EventDataProcessor.get_property_value(
                                event, property)
                    if value is not None and check_match(value, filters):
                        filtered_events.append(event)

        # If the filter finds nothing, do nothing and show an message box
        if not filtered_events:
            Qt.QtGui.QMessageBox.warning(self, 'PyQt5 message',
                                         "No events found! No filtering applied"
                                         " (the data remained the same)")
            return

        filtered_data = _EventDataProcessor(filtered_events)
        new_plot_container = _PlotContainer(filtered_data, tracks)

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
        # Since we accept aggregated data, we accept several data objects,
        # which we use to get a create one iterable that interates through all
        # the events from all data objects.
        super().__init__(*data)
        datum_generator = itertools.chain(*[d.datum_generator for d in data])
        self.data_gen = datum_generator

    def show(self):
        """
        Populates the graph and shows it in an interactive window

        """
        app = Qt.QtWidgets.QApplication([])

        renderer = _PlotterWindow(self.data_gen, ['comm', 'pid'])
        pg.setConfigOptions(antialias=False)
        renderer.showMaximized()
        renderer.raise_()
        app.exec_()
