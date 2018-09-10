# -------------------------------------------------------------
# tcpplotter.py - plots tcp data
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Display option that can display ipc/tcp data as a line graph

"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets
import logging
import re
import typing
import functools

from marple.common import data_io
from marple.display.interface import generic_display

logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))

_all__ = (

)


class _TCPPoint(typing.NamedTuple):
    pid: str
    comm: str
    port: str
    net_ns: str


class _TCPMessage(typing.NamedTuple):
    source: _TCPPoint
    destination: _TCPPoint
    time: str
    type: str


# TODO: more general x axis
class _PlotterContainer:
    """
    Class that wraps the plot container, together with all its plots; makes it
    easier and more readable when we overwrite plots

    """
    source_brush = pg.mkBrush('w')
    destination_brush = pg.mkBrush('w')
    line_colors = [
        (0, 117, 220),
        (255, 0, 16),
        (43, 206, 72),
        (255, 164, 5),
        (148, 255, 181),
        (224, 255, 102),
        (240, 163, 255),
        (255, 255, 255)
    ]

    def __init__(self, processed_data, y_axis_ticks):
        """
        Initialises the class

        :param processed_data:
        :param y_axis_ticks:
        """
        def _create_map():
            ymap = {}
            unique_tracks = 0
            for event_type in processed_data.get_event_types():
                partition = processed_data.get_specific_partition(event_type)
                for event in partition:
                    if event.connected is not None:
                        for sd_pair in event.connected:
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
                        track = self._compose_track(event, "")
                        if track not in ymap.keys():
                            ymap[track] = unique_tracks
                            unique_tracks += 1
            return ymap

        def _assign_colors():
            colors = {}
            color_idx = 0
            for event_type in processed_data.get_event_types():
                if event_type not in colors:
                    colors[event_type] = self.line_colors[color_idx]
                    if color_idx < len(self.line_colors):
                        color_idx += 1

            return colors

        def _create_container_and_plots(ticks):
            plot_container = pg.PlotItem(title="IPC (TCP Messages)",
                                         labels={
                                             'left': ','.join(
                                                 self.y_axis_ticks),
                                             'bottom': 'time'},
                                         axisItems={'left': ticks})

            # Event specific plots
            event_plots = {}
            for event_type in self.processed_data.get_event_types():
                event_plots[event_type] = plot_container.plot([], [])

            # Support plots
            helper_plots = {
                'lines': plot_container.plot([], []),
                'highlight': plot_container.plot([], [])
            }
            return plot_container, event_plots, helper_plots

        def _create_ticks():
            ticks = pg.AxisItem(orientation='left')
            ticks.setTicks([dict(enumerate(self.tracks_ymap.keys())).items()])
            return ticks

        def _add_legend():
            """
            Function used during init that adds a legend in the top right corner
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
                    pen=pg.mkPen(color=self.line_colors[event_type], width=2)),
                    event_type)

            legend.addItem(pg.PlotDataItem(pen=pg.mkPen('y', width=2)),
                           "Selected process")

        self.processed_data = processed_data
        self.y_axis_ticks = y_axis_ticks
        self.tracks_ymap = _create_map()
        self.line_colors = _assign_colors()

        # Create ticks
        self.tick = _create_ticks()

        self.plot_container, self.event_plots, self.helper_plots = \
            _create_container_and_plots(self.tick)

        self.max_y = max(self.tracks_ymap.values())
        self.max_x = max(map(lambda event: event.time,
                             self.processed_data.get_all_events()))

        # We set the limits for the dispay viewbox (so we only have positive xs
        # and ys); we add one to add (or subtract) one so things don't get
        # clipped
        self.plot_container.vb.setLimits(xMin=-1, xMax=self.max_x + 1,
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
        return self.plot_container

    def get_plot_from_container(self, name):
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
        return ','.join([str(event.specific_datum[prefix + tick_track])
                         for tick_track in self.y_axis_ticks])

    def empty_plot(self, plot_name):
        """
        Empties the specified plot
        :param plot_name: name of the plot to be emptied

        """
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
        processes, times = [], []

        for event in partition:
            if event.connected is not None:
                for sd_pair in event.connected:
                    source_track = self._compose_track(event, sd_pair[0])
                    dest_track = self._compose_track(event, sd_pair[1])
                    processes.extend([source_track, dest_track])
                    times.extend([event.time, event.time])
            else:
                track = self._compose_track(event)
                processes.append(track)
                times.append(event.time)
        num_points = len(times)

        # We look at the first event to check if we have a partition that
        # needs connections
        if partition[0].connected is not None:
            connect = "pairs"
            pen = self.line_colors[event_type]
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
        # The symbols and symbol brushes need to be lists, the i-th point's
        # style being defined by symbol[i] and symbolBrush[i]; the length
        # of both needs to be exactly the number of selected points
        # The connect keyword arg signals that point 2*i and 2*i+1 should be
        # connected
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
    Class that deal with the various properties of the event data

    Provides different getters, for various fields
    """
    def __init__(self, events):
        """
        Initialises the class

        :param events: Events that we want processed
        """

        def process_data(events):
            """
            Helper method that partitions the events based on their type and gets
            all the properties present in them (so they can be filtered later)
            Properties will get their source - destination prefixed stripped so we
            can treat 'pid', 'source1_pid', 'dest1_pid' the same

            :param: the event we want to process
            :returns: a dictionary representing the partition and a set for the
                      properties
            """
            properties_set = set()
            event_partition = {}

            for event in events:
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

                if event.type not in event_partition:
                    event_partition[event.type] = [event]
                else:
                    event_partition[event.type].append(event)

            return event_partition, properties_set

        # Process the data using the above function
        self.event_partition, self.properties_set = process_data(events)

    # The following getter functions make it easier to interact with the
    # process data
    def get_specific_partition(self, event_type):
        return self.event_partition[event_type]

    def get_all_events(self):
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
        if prefix + property in event.specific_datum:
            return str(event.specific_datum[prefix + property])
        else:
            return None


class _UIElementManager:
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
            raise ValueError('Invalid ui elem type')

        # We save the element in the dictionary so we can reference it later
        self.ui_dict[name] = new_elem

    def get_ui_elem(self, name):
        if name in self.ui_dict:
            return self.ui_dict[name]
        else:
            raise KeyError("No element with the supplied name found")


class _PlotterWindow(pg.GraphicsWindow):
    """
    Class that only deals with the plotter window, creates layouts and puts
    things in them (not created here, external classes)

    """

    def __init__(self, generator_list, parent=None):
        """
        Initialises the window

        :param messages_gen: A generator that gives the TCP messages that we use
                             to populate the graph
        :param parent: parent of the window, should be left None

        """
        def events_from_generator_list():
            for generator in generator_list:
                for event in generator:
                    yield event

        # Initialise superclass
        super().__init__(parent=parent)

        # Process data, this data will remain unchanged (so we can filter
        # things from it)
        self.processed_data = _EventDataProcessor(events_from_generator_list())
        # We store the currently displayed data (which will change once we
        # filter)
        self.current_displayed_data = self.processed_data

        # Setup current graph
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
        def callback_check(state, event_type):
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
                                        self.empty_plot('highlight'))
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

    def _hide_unused_checkoxes(self):
        for event_type in self.processed_data.get_event_types():
            if event_type in self.current_displayed_data.get_event_types():
                hidden = False
            else:
                hidden = True
            self.ui_manager.get_ui_elem(event_type + "_check").setHidden(hidden)

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
            :return:
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
        # If the filter finds nothing, do nothing
        if len(filtered_events) == 0:
            QtGui.QMessageBox.warning(self, 'PyQt5 message',
                                      "No events found! No filtering applied "
                                      "(the data remained the same)")
            return

        filtered_data = _EventDataProcessor(filtered_events)
        new_plot_container = _PlotterContainer(filtered_data,
                                               ['comm', 'pid'])

        self.plot_layout.removeItem(self.current_plot.plot_container)
        self.plot_layout.addItem(new_plot_container.plot_container)
        self.current_plot = new_plot_container
        self.current_displayed_data = filtered_data
        self._hide_unused_checkoxes()


class TCPPlotter(generic_display.GenericDisplay):
    """
    Class that displays tcp data as a custom line graph"

    """
    class DisplayOptions(typing.NamedTuple):
        pass

    _DEFAULT_OPTIONS = DisplayOptions()

    def __init__(self, data_gen,
                 data_options=data_io.StackData.DEFAULT_OPTIONS,
                 display_options=_DEFAULT_OPTIONS):
        """
        Initializes the class

        :param data_gen:
            A generator that returns the lines for the section we want to
            display as a flamegraph
        :param data_options: object of the class specified in each of the `Data`
                             classes, containig various data options to be used
                             in the display class as labels or info
        :param display_options: display related options that are meant to make
                                the display option more customizable
        """
        # Initialise superclass
        super().__init__(data_options, display_options)

        self.data_gen = data_gen

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

import random
data = []
types = ['accept', 'close', 'connect']
for i in range(1, int(random.random() * 1000)):
    time = random.random() * 100
    s = int(random.random() * 100)
    d = int(random.random() * 100)
    data.append(data_io.EventDatum(time=time,
                                   type=types[random.randrange(0, 3)],
                                   connected=[("source_", "dest_")],
                                   specific_datum={
                                        "source_pid": s % 25,
                                        "source_comm": 'process' + str(s),
                                        "source_port": s % 25,
                                        "dest_pid": d % 25,
                                        "dest_comm": 'process' + str(d),
                                        "dest_port": d % 25,
                                        "net_ns": s+d}))

data.append(data_io.EventDatum(time=30,
                               type="new",
                               connected=None,
                               specific_datum={
                                    "pid": 32,
                                    "comm": 'newthing32',
                                    "dodo": 25,
                               }))

data.append(data_io.EventDatum(time=50,
                               type="old",
                               connected=None,
                               specific_datum={
                                    "pid": 32,
                                    "comm": 'newthing32',
                                    "dodo": 27,
                               }))

plot = TCPPlotter([data])
plot.show()