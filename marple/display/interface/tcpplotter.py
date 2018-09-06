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
import enum

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


# class _MessageTypes(enum.Enum):
#     ACCEPT = 'A'
#     CONNECT = 'C'
#     CLOSE = 'X'


# TODO: Make wrapper class for drawing functions so you can modularize the
# TODO: radio button callbacks
class _TCPDDrawWidget(pg.GraphicsWindow):
    source_brush = pg.mkBrush('w')
    destination_brush = pg.mkBrush('w')
    color_dict = {
        'A': 'g',
        'C': 'b',
        'X': 'r'
    }

    def __init__(self, messages_gen, parent=None):
        """
        Initialises the window

        :param messages_gen: A generator that gives the TCP messages that we use
                             to populate the graph
        :param parent: parent of the window, should be left None

        """
        # Initialise superclass
        super().__init__(parent=parent)

        # We get the mapping form process names to values on the Y axis and
        # we partition the messages based on their type;
        # A dictionary of the form {'accept': (list_of_x, list_of_y), ...} is
        # produced, which is used when we need to redraw only particular types
        self.conn_partition_data, self.comm_to_y_map = \
            self._create_ymap_and_partition(messages_gen)

        # Max dimension for the x and y axes
        self.max_y = max(self.comm_to_y_map.values())
        all_messages = self.concat(self.conn_partition_data.values())
        self.max_x = max([message.time for message in all_messages])

        # Initial setup for the graph (draw the y axis, support lines), the
        # legend and the UI
        self._setup_graph()
        self._add_legend()
        self._add_UI()

        # We create the symbol and the symbol brushes lists so that we do not
        # have to create them everytime we redraw
        self.symbols = ['s', 'o'] * len(all_messages)
        self.symbol_brushes = [self.source_brush,
                               self.destination_brush] * len(all_messages)

    def _add_UI(self):
        """
        Function used during init that draws the UI elements (graph, buttons,
        text fields) the user interacts with

        """
        # We save the UI elements in a dictionary so that we can reference them
        # later (for example load text from a text filed)
        self.UI_dict = {}

        # Draw the UI elements in a resizable grid
        self.UI_elems_factory("check", "acc_check", "Show accept", 1, 0,
                              callback_function=lambda state: self.draw('A') if
                              state == 2 else self.empty_plot('A'))
        self.UI_elems_factory("check", "cls_check", "Show close", 1, 1,
                              callback_function=lambda state: self.draw('X') if
                              state == 2 else self.empty_plot('X'))
        self.UI_elems_factory("check", "con_check", "Show connect", 1, 2,
                              callback_function=lambda state: self.draw('C') if
                              state == 2 else self.empty_plot('C'))

        self.UI_elems_factory("text", "choices", "", 2, 0)
        self.UI_elems_factory("button", "display_choices", "Display Choices ("
                                                           "prefix match)",
                              2, 1,
                              callback_function=lambda: self.draw_selected_only(
                                  self.UI_dict['choices'].text()))
        self.UI_elems_factory("button", "clear_highlight",
                              "Clear highlight", 2, 2,
                              callback_function=lambda: self.empty_plot('H'))

    def _setup_graph(self):
        """
        Function used during init that sets up the actual graph

        We create the axis here, plots for each type of message + the plots
        for the support lines and the highlighted lines

        """
        graph_layout = self.addLayout(row=0, col=0, colspan=3)

        # Setup the plot container and the Y axis labels
        comm_axis = pg.AxisItem(orientation='left')
        comm_axis.setTicks([dict(enumerate(self.comm_to_y_map.keys())).items()])
        self.plot_container = self.addPlot(title="IPC (TCP Messages)",
                                           axisItems={'left': comm_axis})

        # The plots described above
        self.plots = {
            'A': self.plot_container.plot([], []),
            'X': self.plot_container.plot([], []),
            'C': self.plot_container.plot([], []),
            'lines': self.plot_container.plot([], []),
            'highlighted': self.plot_container.plot([], [])
        }
        graph_layout.addItem(self.plot_container)

        # We set the limits for the dispay viewbox (so we only have positive xs
        # and ys); we add one to add (or subtract) one so things don't get
        # clipped
        self.plot_container.vb.setLimits(xMin=-1, xMax=self.max_x + 1,
                                         yMin=-1, yMax=self.max_y + 1)

        # We draw the support lines
        ys = self.concat([[y, y] for y in range(0, self.max_y + 1)])
        xs = [0, self.max_x] * (self.max_y + 1)
        self.plots['lines'].setData(xs, ys,
                                    pen=pg.mkPen(255, 255, 255, 32),
                                    connect="pairs")

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
        legend.addItem(pg.PlotDataItem(pen=self.color_dict['A']),
                       "Accept")
        legend.addItem(pg.PlotDataItem(pen=self.color_dict['C']),
                       "Connect")
        legend.addItem(pg.PlotDataItem(pen=self.color_dict['X']),
                       "Close")
        legend.addItem(pg.PlotDataItem(pen='y'),
                       "Selected process")

    @staticmethod
    def concat(ll):
        """
        Helper function that converts a list of lists into a single list,
        perserving order
        :param ll: the list of lists to be concat'ed
        :return: a single list produced from the input
        """

        res = []
        for l in ll:
            for item in l:
                res.append(item)
        return res

    def empty_plot(self, plot_name):
        """
        Empties the specified plot
        :param plot_name: name of the plot to be emptied

        """
        if plot_name == 'A':
            self.plots['A'].setData([], [], symbol=[], symbolBrush=[])
        if plot_name == 'C':
            self.plots['C'].setData([], [], symbol=[], symbolBrush=[])
        if plot_name == 'X':
            self.plots['X'].setData([], [], symbol=[], symbolBrush=[])
        if plot_name == 'H':
            self.plots['highlighted'].setData([], [])

    def empty_all_plots(self):
        """
        Empties all plots (doesn't empty the support lines)

        """
        self.empty_plot('A')
        self.empty_plot('C')
        self.empty_plot('X')
        self.empty_plot('H')

    def UI_elems_factory(self, ui_elem, name, text, row, col, **kwargs):
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
        # Proxy that alows QT widgets to be put inside a graphics window
        proxy_elem = QtGui.QGraphicsProxyWidget()

        if ui_elem == 'check':
            new_elem = QtGui.QCheckBox(text)
            new_elem.stateChanged.connect(kwargs["callback_function"])
        elif ui_elem == 'text':
            new_elem = QtGui.QLineEdit(text)
        elif ui_elem == 'button':
            new_elem = QtGui.QPushButton(text)
            new_elem.clicked.connect(kwargs["callback_function"])
        proxy_elem.setWidget(new_elem)
        layout = self.addLayout(row=row, col=col)
        layout.addItem(proxy_elem)
        self.UI_dict[name] = new_elem

    def draw_selected_only(self, wanted_processes):
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
        self.UI_dict["acc_check"].setChecked(True)
        self.UI_dict["cls_check"].setChecked(True)
        self.UI_dict["con_check"].setChecked(True)

        # Parse the input into a list of regex patterns
        wanted_processes = wanted_processes.replace(' ', '').split(',')

        ys = []
        # Now for each type of message, select points that need to be displayed
        for mess_type in 'AXC':
            partition = self.conn_partition_data[mess_type]
            times = self.concat([[message.time] * 2 for message in partition])
            processes = self.concat([[message.source.comm,
                                      message.destination.comm]
                                     for message in partition])
            # 2 lists which when zipped they represent the points that need
            # to be drawn after the selection
            selected_times = []
            selected_processes = []

            # Now we go through all the points, two at a time since adjacent
            # points form lines (pairs source - destination), and chech if any
            # of them lie on a selected line; if this is true, then we draw
            # both of them
            for idx in range(0, len(times), 2):
                if check_regex(processes[idx], wanted_processes) or \
                   check_regex(processes[idx + 1], wanted_processes):
                    selected_times.extend(times[idx:idx+2])
                    selected_processes.extend(processes[idx:idx+2])
            num_selected_points = len(selected_times)

            # We need to save the ys of the lines to be highlighted
            # We do this by going only though the processes that matched (we
            # must create this list since selected_processes contains processes
            # that are there just because they are connected to a process that
            # matched)

            for y in list(
                filter(lambda proc: check_regex(proc, wanted_processes),
                       selected_processes)):
                ys.extend([self.comm_to_y_map[y], self.comm_to_y_map[y]])

            # Now we draw the markers and lines
            # The symbols and symbol brushes need to be lists, the i-th point's
            # style being defined by symbol[i] and symbolBrush[i]; the length
            # of both needs to be exactly the number of selected points
            # The connect keyword arg signals that point 2*i and 2*i+1 should be
            # connected
            self.plots[mess_type].setData(
                {'x': selected_times,
                 # With the ys we need to convert from process names to numbers
                 # on the y axis
                 'y': list(map(lambda process: self.comm_to_y_map[process],
                               selected_processes))},
                symbol=self.symbols[0:num_selected_points],
                pen=self.color_dict[mess_type],
                symbolBrush=self.symbol_brushes[0:num_selected_points],
                connect="pairs"
            )

        # In the end we draw the highlighted yellow lines
        self.plots['highlighted'].setData([0, self.max_x] * int(len(ys) / 2),
                                          ys, pen='y', connect="pairs")

    def draw(self, mess_type):
        """
        Draws all the messages of the provided type

        :param mess_type: the type of the messages to be drawn

        """
        self.empty_plot('H')

        partition = self.conn_partition_data[mess_type]
        times = self.concat([[message.time] * 2 for message in partition])
        processes = self.concat([[message.source.comm,
                                  message.destination.comm]
                                 for message in partition])
        num_points = len(times)

        # Now we draw the markers and lines
        # The symbols and symbol brushes need to be lists, the i-th point's
        # style being defined by symbol[i] and symbolBrush[i]; the length
        # of both needs to be exactly the number of selected points
        # The connect keyword arg signals that point 2*i and 2*i+1 should be
        # connected
        self.plots[mess_type].setData(
            {'x': times,
             # With the ys we need to convert from process names to numbers on
             # the y axis
             'y': list(map(lambda process: self.comm_to_y_map[process],
                           processes))},
            symbol=self.symbols[0:num_points],
            pen=self.color_dict[mess_type],
            symbolBrush=self.symbol_brushes[0:num_points],
            connect="pairs"
        )

    @staticmethod
    def _create_ymap_and_partition(messages_gen):
        """
        Method that returns a dictionary that represents the partition of
        the messages and the mapping between processes' names and y axis coords

        :param: messages_gen: generator that contains the TCP info
        :returns: a pair of dictionaries, as described above
        """
        comm_to_y_map = {}
        unique_ys = 0
        messages_partition = {'A': [],
                              'C': [],
                              'X': []}

        for event_datum in messages_gen:
            # Extract info
            msgtime = event_datum[0]
            msgtype = event_datum[1]
            source_pid = event_datum[2][0]
            source_comm = event_datum[2][1]
            source_port = event_datum[2][2]
            dest_pid = event_datum[2][3]
            dest_comm = event_datum[2][4]
            dest_port = event_datum[2][5]
            net_ns = event_datum[2][6]

            # Convert info to _TCPMessage
            source = _TCPPoint(source_pid, source_comm, source_port, net_ns)
            dest = _TCPPoint(dest_pid, dest_comm, dest_port, net_ns)
            message = _TCPMessage(source, dest, msgtime, msgtype)

            # Map source and dest if they have not been encountered
            # When we encounter a new process, we assign it an y coord equal to
            # the last one used + 1, so we only draw used lines (which will be
            # all the y lines between 0 and total number of unique processes)
            if source.comm not in comm_to_y_map.keys():
                comm_to_y_map[source.comm] = unique_ys
                unique_ys += 1

            if dest.comm not in comm_to_y_map.keys():
                comm_to_y_map[dest.comm] = unique_ys
                unique_ys += 1

            # Put message in the right partition
            if message.type == 'A':
                messages_partition['A'].append(message)
            elif message.type == 'C':
                messages_partition['C'].append(message)
            else:
                messages_partition['X'].append(message)
        return messages_partition, comm_to_y_map


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

        renderer = _TCPDDrawWidget(self.data_gen)
        pg.setConfigOptions(antialias=False)
        renderer.showMaximized()
        renderer.raise_()
        app.exec_()


import random

data = []
types = ['A', 'X', 'C']
# data.append(data_io.EventDatum(time=1,
#                                    type=types[0],
#                                    specific_datum=(
#         None, 'process' + str(1), None, None, 'process' + str(3), None, None)))
# data.append(data_io.EventDatum(time=2,
#                                    type=types[1],
#                                    specific_datum=(
#         None, 'process' + str(3), None, None, 'process' + str(1), None, None)))
# data.append(data_io.EventDatum(time=4,
#                                    type=types[2],
#                                    specific_datum=(
#         None, 'process' + str(3), None, None, 'process' + str(1), None, None)))
# data.append(data_io.EventDatum(time=10,
#                                    type=types[2],
#                                    specific_datum=(
#         None, 'process' + str(5), None, None, 'process' + str(4), None, None)))
# data.append(data_io.EventDatum(time=15,
#                                    type=types[1],
#                                    specific_datum=(
#         None, 'process' + str(5), None, None, 'process' + str(4), None, None)))

for i in range(1, int(random.random() * 100)):
    time = random.random() * 100
    s = int(random.random() * 100)
    d = int(random.random() * 100)
    data.append(data_io.EventDatum(time=time,
                                   type=types[random.randrange(0, 3)],
                                   specific_datum=(
        None, 'process' + str(s), None, None, 'process' + str(d), None, None)))

plot = TCPPlotter(data)
plot.show()
