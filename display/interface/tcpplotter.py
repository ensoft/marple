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
import random
import itertools
import functools

from common import data_io
from display.interface import generic_display

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
        (255, 204, 153),
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
                    for sd_pair in event.connected:
                        source_track = self._compose_track(
                            event.specific_datum, sd_pair[0])
                        dest_track = self._compose_track(
                            event.specific_datum, sd_pair[1])
                        if source_track not in ymap.keys():
                            ymap[source_track] = unique_tracks
                            unique_tracks += 1

                        if dest_track not in ymap.keys():
                            ymap[dest_track] = unique_tracks
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

        def _create_container_and_plots(self, ticks):
            plot_container = pg.PlotItem(title="IPC (TCP Messages)",
                                         labels={
                                             'left': ','.join(
                                                 self.y_axis_ticks),
                                             'bottom': 'time'},
                                         axisItems={'left': ticks})

            # Event specific plots
            event_plots = {}
            for event_type in self.processed_data.get_types():
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

        self.processed_data = processed_data
        self.y_axis_ticks = y_axis_ticks
        self.tracks_ymap = _create_map()
        self.line_colors = _assign_colors()
        self.plot_container, self.event_plots, self.helper_plots = \
            _create_container_and_plots()

        self.max_y = max(self.tracks_ymap.values())
        self.max_x = max(map(lambda event: event.time,
                             self.processed_data.get_all_events))

        # We set the limits for the dispay viewbox (so we only have positive xs
        # and ys); we add one to add (or subtract) one so things don't get
        # clipped
        self.plot_container.vb.setLimits(xMin=-1, xMax=self.max_x + 1,
                                         yMin=-1, yMax=self.max_y + 1)

        # Create ticks
        self.tick = _create_ticks()


        # We draw the support lines
        ys = self._concat([[y, y] for y in range(0, self.max_y + 1)])
        xs = [0, self.max_x] * (self.max_y + 1)
        self.helper_plots['lines'].setData(xs, ys,
                                           pen=pg.mkPen(255, 255, 255, 32),
                                           connect="pairs")

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

    def _compose_track(self, event_specfic_datum, prefix=""):
        return ','.join([str(event_specfic_datum[prefix + tick_track])
                         for tick_track in self.y_axis_ticks])






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
        self.event_partition, self.properties_set = self._process_data(events)

    def get_specific_partition(self, event_type):
        return self.event_partition[event_type]

    def get_all_events(self):
        for event_subset in self.event_partition.values():
            for event in event_subset:
                yield event

    def get_properties(self):
        return self.properties_set

    def get_event_types(self):
        return self.event_partition.keys()

    @staticmethod
    def get_property_value(self, event, property, prefix=""):
        if prefix + property in event.specific_datum:
            return str(event.specific_datum[prefix + property])
        else:
            return None

    def _process_data(self, events):
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

            if event.type not in event_partition:
                event_partition[event.type] = [event]
            else:
                event_partition[event.type].append(event)

        return event_partition, properties_set


class _PlotterWindow(pg.GraphicsWindow):
    """
    Class that only deals with the plotter window, creates layouts and puts
    things in them (not created here, external classes)

    """
    source_brush = pg.mkBrush('w')
    destination_brush = pg.mkBrush('w')

    def __init__(self, generator_list, parent=None):
        """
        Initialises the window

        :param messages_gen: A generator that gives the TCP messages that we use
                             to populate the graph
        :param parent: parent of the window, should be left None

        """
        # Initialise superclass
        super().__init__(parent=parent)
        self.tick_tracks = ["comm", "pid"]
        # We get the mapping form process names to values on the Y axis and
        # we partition the messages based on their type;
        # A dictionary of the form {'accept': (list_of_x, list_of_y), ...} is
        # produced, which is used when we need to redraw only particular types
        self.event_partition,\
            self.track_to_y_map, \
            self.properties_set, \
            self.type_colours = self._generate_datastruct(generator_list)

        # Max dimension for the x and y axes
        self.max_y = max(self.track_to_y_map.values())
        all_messages = self.concat(self.event_partition.values())
        self.max_x = max([message.time for message in all_messages])


        # Initial setup for the graph (draw the y axis, support lines), the
        # legend
        self._setup_graph()
        self._add_legend()

        # We save the UI elements in a dictionary so that we can reference them
        # later (for example load text from a text filed)
        self.UI_dict = {}
        self._add_UI()

        # We create the symbol and the symbol brushes lists so that we do not
        # have to create them everytime we redraw
        self.symbols = ['s', 'o'] * len(all_messages)
        self.symbol_brushes = [self.source_brush,
                               self.destination_brush] * len(all_messages)

    def callback_check(self, state, event_type):
        return self.draw(event_type) if state == 2 else self.empty_plot(
            event_type)

    def callback_filter(self, prop):
        return self.draw_selected_only(prop,
                                       self.UI_dict['regex_' + prop].text())

    def _add_UI(self):
        """
        Function used during init that draws the UI elements (graph, buttons,
        text fields) the user interacts with

        """
        check_layout = QtGui.QFormLayout()
        filter_layout = QtGui.QFormLayout()

        check_gb = QtGui.QGroupBox('Display / Hide')
        filter_gb = QtGui.QGroupBox('Filtering')

        # First draw the checkboxes
        for event_type in self.event_partition.keys():
            callback = functools.partial(self.callback_check, event_type=event_type)
            self.UI_elems_factory("check", event_type + "_check",
                                  "Show " + event_type,
                                  callback_function=callback)
            check_layout.addRow(self.UI_dict[event_type + "_check"])
        check_gb.setLayout(check_layout)

        # Now the filters
        for prop in self.properties_set:
            callback = functools.partial(self.callback_filter, prop)
            self.UI_elems_factory("text", "regex_" + prop, "")
            self.UI_elems_factory("button", "filter_" + prop,
                                  "Filter by {} (prefix match)".format(prop),
                                  callback_function=callback)
            filter_layout.addRow(self.UI_dict["regex_" + prop],
                                 self.UI_dict["filter_" + prop])
        # A clear highlight button
        self.UI_elems_factory("button", "clear_highlight",
                              "Clear highlight",
                              callback_function=lambda:self.empty_plot(
                                  'highlight'
                              ))
        filter_layout.addRow(self.UI_dict["clear_highlight"])
        filter_gb.setLayout(filter_layout)

        scroll_check = QtGui.QScrollArea()
        scroll_check.setWidget(check_gb)
        scroll_check.setWidgetResizable(True)
        scroll_check.setFixedHeight(200)
        layout = self.addLayout(row=1, col=0)
        proxy_elem = QtGui.QGraphicsProxyWidget()
        proxy_elem.setWidget(scroll_check)
        layout.addItem(proxy_elem)

        scroll_filter = QtGui.QScrollArea()
        scroll_filter.setWidget(filter_gb)
        scroll_filter.setWidgetResizable(True)
        scroll_filter.setFixedHeight(200)
        layout = self.addLayout(row=1, col=1)
        proxy_elem = QtGui.QGraphicsProxyWidget()
        proxy_elem.setWidget(scroll_filter)
        layout.addItem(proxy_elem)

    def _create_container_and_plots(self, ticks):
        self.plot_container = self.addPlot(title="IPC (TCP Messages)",
                                           labels={
                                               'left':
                                                   ','.join(self.tick_tracks),
                                               'bottom': 'time'},
                                           axisItems={'left': ticks})

        # Event specific plots
        self.event_plots = {}
        for event_type in self.event_partition.keys():
            self.event_plots[event_type] = self.plot_container.plot([], [])

        # Support plots
        self.helper_plots = {
            'lines': self.plot_container.plot([], []),
            'highlight': self.plot_container.plot([], [])
        }

        # We set the limits for the dispay viewbox (so we only have positive xs
        # and ys); we add one to add (or subtract) one so things don't get
        # clipped
        self.plot_container.vb.setLimits(xMin=-1, xMax=self.max_x + 1,
                                         yMin=-1, yMax=self.max_y + 1)

        # We draw the support lines
        ys = self.concat([[y, y] for y in range(0, self.max_y + 1)])
        xs = [0, self.max_x] * (self.max_y + 1)
        self.helper_plots['lines'].setData(xs, ys,
                                           pen=pg.mkPen(255, 255, 255, 32),
                                           connect="pairs")

    def _setup_graph(self):
        """
        Function used during init that sets up the actual graph

        We create the axis here, plots for each type of message + the plots
        for the support lines and the highlighted lines

        """
        self.graph_layout = self.addLayout(row=0, col=0, colspan=2)

        # Setup the plot container and the Y axis labels
        self.all_ticks = pg.AxisItem(orientation='left')
        self.all_ticks.setTicks([dict(enumerate(self.track_to_y_map.keys())).items()])

        self._create_container_and_plots(self.all_ticks)
        # Add plots to layout
        self.graph_layout.addItem(self.plot_container)





    def _add_legend(self):
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

        for item in self.event_partition.items():
            legend.addItem(pg.PlotDataItem(
                pen=pg.mkPen(color=self.type_colours[item[0]], width=2)),
                item[0])

        legend.addItem(pg.PlotDataItem(
            pen=pg.mkPen('y', width=2)),
            "Selected process")

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

        for event_type in self.event_partition.keys():
            self.empty_plot(event_type)

    def UI_elems_factory(self, ui_elem, name, text, **kwargs):
        """
        Factory function that creates UI elements and puts them in the UI
        dictionary (used for referencing them later)

        :param ui_elem: type of the UI element to be added
        :param name: name of the UI element, used as key for the dictionary
        :param text: text to be displayed on the UI element
        :param row: the row in the grid where the UI element is to be placed
        :param col: the col in the grid where the UI element is to be placed
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

        # We save the element in the dictionary so we can reference it later
        self.UI_dict[name] = new_elem

    def compose_track(self, event_specfic_datum, prefix=""):
        return ','.join([str(event_specfic_datum[prefix + tick_track])
                for tick_track in self.tick_tracks])


    def get_property_value(self, specific_datum, property, prefix=""):
        if prefix + property in specific_datum:
            return str(specific_datum[prefix + property])
        else:
            return None

    def draw_selected_only(self, property, filters):
        """
        Highlights the selected processes and displays only the markers
        for lines which have at least one end on a highlighted lines (easier
        for tracking)
        :param wanted_processes: the regex patterns used to find the wanted
                                 processes as alist of the form:
                                 regex1, regex2, ... (tolerant to whitespaces)

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

        self.empty_all_plots()
        for event_type in self.event_plots.keys():
            self.UI_dict[event_type + "_check"].setChecked(True)

        # Parse the input into a list of regex patterns
        filters = filters.replace(' ', '').split(',')

        # Now for each type of message, select points that need to be displayed
        event_dict = {}
        ymap = {}
        inc = 0
        for event_type in self.event_plots.keys():
            partition = self.event_partition[event_type]

            # 2 lists which when zipped they represent the points that need
            # to be drawn after the selection
            selected_times = []
            selected_processes = []

            # Now we go through all the points, two at a time since adjacent
            # points form lines (pairs source - destination), and chech if any
            # of them lie on a selected line; if this is true, then we draw
            # both of them
            for event in partition:
                if event.connected is not None:
                    for sd_pair in event.connected:
                        s_value = self.get_property_value(event.specific_datum,
                                                          property,
                                                          prefix=sd_pair[0])
                        d_value = self.get_property_value(event.specific_datum,
                                                          property,
                                                          prefix=sd_pair[1])
                        if s_value is not None and \
                                check_regex(s_value, filters) or d_value is \
                                not None and check_regex(d_value, filters):
                            selected_times.extend([event.time] * 2)
                            s_track = self.compose_track(
                                        event.specific_datum, sd_pair[0])
                            d_track =self.compose_track(
                                        event.specific_datum, sd_pair[1])
                            selected_processes.extend([s_track, d_track])
                            if s_track not in ymap:
                                ymap[s_track] = inc
                                inc += 1
                            if d_track not in ymap:
                                ymap[d_track] = inc
                                inc += 1

                else:
                    value = self.get_property_value(event.specific_datum,
                                                    property)
                    if value is not None:
                        selected_times.append(event.time)
                        track = self.compose_track(event.specific_datum)
                        selected_processes.append(track)
                        if track not in ymap:
                            ymap[track] = inc
                            inc += 1

            event_dict[event_type] = [selected_times, selected_processes]

        ticks = pg.AxisItem(orientation='left')
        ticks.setTicks(
            [dict(enumerate(ymap.keys())).items()])
        self.graph_layout.removeItem(self.plot_container)
        self._create_container_and_plots(ticks)
        self.graph_layout.addItem(self.plot_container)
        for event_type in event_dict.keys():
            num_selected_points = len(event_dict[event_type][0])
            self.event_plots[event_type].setData(
                {'x': event_dict[event_type][0],
                 # With the ys we need to convert from process names to numbers
                 # on the y axis
                 'y': list(map(lambda process: ymap[process],
                               event_dict[event_type][1]))},
                symbol=self.symbols[0:num_selected_points],
                pen=self.type_colours[event_type],
                symbolBrush=self.symbol_brushes[0:num_selected_points],
                connect="pairs"
            )

        # In the end we draw the highlighted yellow lines
        # self.plots['highlighted'].setData([0, self.max_x] * int(len(ys) / 2),
        #                                   ys, pen='y', connect="pairs")

    def draw(self, event_type):
        """
        Draws all the messages of the provided type

        :param event_type: the type of the messages to be drawn

        """
        self.empty_plot('highlight')

        partition = self.event_partition[event_type]
        processes, times = [], []
        for event in partition:
            for sd_pair in event.connected:
                source_track = self.compose_track(event.specific_datum,
                                                  sd_pair[0])
                dest_track = self.compose_track(event.specific_datum,
                                                sd_pair[1])
                processes.extend([source_track, dest_track])
                times.extend([event.time, event.time])
        num_points = len(times)

        # Now we draw the markers and lines
        # The symbols and symbol brushes need to be lists, the i-th point's
        # style being defined by symbol[i] and symbolBrush[i]; the length
        # of both needs to be exactly the number of selected points
        # The connect keyword arg signals that point 2*i and 2*i+1 should be
        # connected
        self.event_plots[event_type].setData(
            {'x': times,
             # With the ys we need to convert from process names to numbers on
             # the y axis
             'y': list(map(lambda process: self.track_to_y_map[process],
                           processes))},
            symbol=self.symbols[0:num_points],
            pen=self.type_colours[event_type],
            symbolBrush=self.symbol_brushes[0:num_points],
            connect="pairs"
        )

    def _generate_datastruct(self, generator_list):
        """
        Method that returns a dictionary that represents the partition of
        the messages and the mapping between processes' names and y axis coords

        :param: messages_gen: generator that contains the TCP info
        :returns: a pair of dictionaries, as described above
        """
        track_to_y_map = {}
        properties_set = set()
        unique_ys = 0
        event_partition = {}
        type_colours = {}
        color_idx = 0

        for generator in generator_list:
            for event in generator:
                # Extract info
                connected = event.connected

                if connected is not None:
                    for prop in event.specific_datum.keys():
                        for sd_pair in connected:
                            match_src = re.match(sd_pair[0], prop)
                            match_dst = re.match(sd_pair[1], prop)
                            if match_src is not None:
                                prop = prop[match_src.end():]
                            elif match_dst is not None:
                                prop = prop[match_dst.end():]
                            properties_set.add(prop)

                    for sd_pair in connected:
                        source_track = self.compose_track(
                            event.specific_datum, sd_pair[0])
                        dest_track = self.compose_track(
                            event.specific_datum, sd_pair[1])
                        if source_track not in track_to_y_map.keys():
                            track_to_y_map[source_track] = unique_ys
                            unique_ys += 1

                        if dest_track not in track_to_y_map.keys():
                            track_to_y_map[dest_track] = unique_ys
                            unique_ys += 1

                if event.type not in event_partition:
                    event_partition[event.type] = [event]
                else:
                    event_partition[event.type].append(event)

                if event.type not in type_colours:
                    type_colours[event.type] = self.dist_colors[color_idx]
                    if color_idx < len(self.dist_colors):
                        color_idx += 1

        return event_partition, track_to_y_map, properties_set, type_colours


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

plot = TCPPlotter([data])
plot.show()
