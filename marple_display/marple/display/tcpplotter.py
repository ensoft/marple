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
from functools import partial

import typing
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

    class DrawMethodWrapper:
        def __init__(self, draw_func, **kwargs):
            self.draw_func = draw_func
            self.options_dict = kwargs

        def draw(self):
            if 'conn_types' in self.options_dict:
                self.draw_func(self.options_dict['conn_types'])
            if 'selected' in self.options_dict:
                self.draw_func(self.options_dict['selected']())


    def __init__(self, messages_gen, parent=None):
        super().__init__(parent=parent)
        self.messages, self.comm_to_y_map = \
            self._create_comm_to_y_map(messages_gen)

        self.conn_partition_data = self._create_conn_partition()
        self._setup_graph()
        self._add_legend()
        self._add_UI()

        self.symbols = ['s', 'o'] * len(self.messages)
        self.symbol_brushes = [self.source_brush, self.destination_brush] * \
                               len(self.messages)

    def _add_UI(self):
        # Now the UI
        self.UI_dict = {}
        # Radio buttons for all the options
        options_group = QtGui.QButtonGroup(self)
        self.all = self.DrawMethodWrapper(self.draw, conn_types='AXC')
        self.conn = self.DrawMethodWrapper(self.draw, conn_types='C')
        self.acc = self.DrawMethodWrapper(self.draw, conn_types='A')
        self.close = self.DrawMethodWrapper(self.draw, conn_types='X')
        self.UI_elems_factory("radio", "all_radio", "Show all", 1, 0,
                              group=options_group,
                              callback_function=self.all.draw)
        self.UI_elems_factory("radio", "acc_radio", "Show accept", 1, 1,
                              group=options_group,
                              callback_function=self.acc.draw)
        self.UI_elems_factory("radio", "cls_radio", "Show close", 1, 2,
                              group=options_group,
                              callback_function=self.close.draw)
        self.UI_elems_factory("radio", "cnt_radio", "Show connect", 1, 3,
                              group=options_group,
                              callback_function=self.conn.draw)

        self.UI_elems_factory("text", "choices", "", 2, 1)
        self.selected = self.DrawMethodWrapper(self.draw_selected_only,
                                               selected=self.UI_dict['choices'].text)
        self.UI_elems_factory("button", "display_choices", "Display Choices",
                              2, 2, callback_function=self.selected.draw)

    def _setup_graph(self):
        tcp_graph_layout = self.addLayout(row=0, col=0, colspan=4)
        comm_axis = pg.AxisItem(orientation='left')
        comm_axis.setTicks([dict(enumerate(self.comm_to_y_map.keys())).items()])
        self.plot_container = self.addPlot(title="IPC (TCP Messages)",
                                           axisItems={'left': comm_axis})
        self.plots = {
            'A': self.plot_container.plot([], []),
            'X': self.plot_container.plot([], []),
            'C': self.plot_container.plot([], []),
            'lines': self.plot_container.plot([], []),
            'highlighted': self.plot_container.plot([], [])
        }
        tcp_graph_layout.addItem(self.plot_container)

        max_y = max(self.comm_to_y_map.values())
        self.max_time = max([message.time for message in self.messages])
        self.plot_container.vb.setLimits(xMin=-1, xMax=self.max_time + 1,
                                         yMin=-1, yMax=max_y + 1)

        ys = []
        for y in range(0, max_y + 1):
            ys.extend([y, y])
        self.plots['lines'].setData([0, self.max_time] * (max_y + 1), ys,
                                    pen=pg.mkPen(255, 255, 255, 32),
                                    connect="pairs")

    def _add_legend(self):
        legend = pg.LegendItem((170, 0), (-1, 50))
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

    def empty_plots(self):
        self.plots['A'].setData([], [], symbol=[], symbolBrush=[])
        self.plots['C'].setData([], [], symbol=[], symbolBrush=[])
        self.plots['X'].setData([], [], symbol=[], symbolBrush=[])
        self.plots['highlighted'].setData([], [])

    def UI_elems_factory(self, type, name, text, row, col, **kwargs):
        proxy_elem = QtGui.QGraphicsProxyWidget()
        if type == 'radio':
            new_elem = QtGui.QRadioButton(text)
            new_elem.toggled.connect(kwargs["callback_function"])
            kwargs["group"].addButton(new_elem)
        elif type == 'text':
            new_elem = QtGui.QLineEdit(text)
        elif type == 'button':
            new_elem = QtGui.QPushButton(text)
            new_elem.clicked.connect(kwargs["callback_function"])
        proxy_elem.setWidget(new_elem)
        layout = self.addLayout(row=row, col=col)
        layout.addItem(proxy_elem)
        self.UI_dict[name] = new_elem

    # @TODO: Heavy refactor
    def draw_selected_only(self, wanted_processes):
        def check_regex(to_match, regex_list):
            for reg_ex in regex_list:
                if re.match(reg_ex, to_match):
                    return True
            return False

        self.empty_plots()
        wanted_processes = wanted_processes.replace(' ', '').split(',')

        ys = []
        for conn_type in 'AXC':
            times, processes = self.conn_partition_data[conn_type]
            selected_times = []
            selected_processes = []
            for idx in range(0, len(times), 2):
                if check_regex(processes[idx], wanted_processes) or \
                   check_regex(processes[idx + 1], wanted_processes):
                    selected_times.extend(times[idx:idx+2])
                    selected_processes.extend(processes[idx:idx+2])
            num_points = len(selected_times)

            for y in list(filter(lambda proc: check_regex(proc, wanted_processes), selected_processes)):
                ys.extend([self.comm_to_y_map[y], self.comm_to_y_map[y]])

            self.plots[conn_type].setData(
                {'x': selected_times,
                 'y': list(map(lambda process: self.comm_to_y_map[process],
                               selected_processes))},
                symbol=self.symbols[0:num_points],
                pen=self.color_dict[conn_type],
                symbolBrush=self.symbol_brushes[0:num_points],
                connect="pairs"
            )
        self.plots['highlighted'].setData(
            [0, self.max_time] * int(len(ys) / 2),
            ys,
            pen='y',
            connect="pairs")

    def draw(self, conn_types):
        self.empty_plots()

        for conn_type in conn_types:
            times, processes = self.conn_partition_data[conn_type]
            num_points = len(times)
            self.plots[conn_type].setData(
                {'x': times,
                 'y': list(map(lambda process: self.comm_to_y_map[process],
                               processes))},
                symbol=self.symbols[0:num_points],
                pen=self.color_dict[conn_type],
                symbolBrush=self.symbol_brushes[0:num_points],
                connect="pairs"
            )

    @staticmethod
    def _create_comm_to_y_map(messages_gen):
        comm_to_y_map = {}
        unique_ys = 0
        messages = []

        for event_datum in messages_gen:
            msgtime = event_datum[0]
            msgtype = event_datum[1]
            source_pid = event_datum[2][0]
            source_comm = event_datum[2][1]
            source_port = event_datum[2][2]
            dest_pid = event_datum[2][3]
            dest_comm = event_datum[2][4]
            dest_port = event_datum[2][5]
            net_ns = event_datum[2][6]

            source = _TCPPoint(source_pid, source_comm, source_port, net_ns)
            dest = _TCPPoint(dest_pid, dest_comm, dest_port, net_ns)
            message = _TCPMessage(source, dest, msgtime, msgtype)

            if source.comm not in comm_to_y_map.keys():
                comm_to_y_map[source.comm] = unique_ys
                unique_ys += 1

            if dest.comm not in comm_to_y_map.keys():
                comm_to_y_map[dest.comm] = unique_ys
                unique_ys += 1

            messages.append(message)
        return messages, comm_to_y_map

    def _create_conn_partition(self):
        xs = []
        ys = []
        conn_type_coords = {'A': ([], []),
                            'C': ([], []),
                            'X': ([], [])}
        for message in self.messages:
            xs.extend([message.time, message.time])
            ys.extend([self.comm_to_y_map[message.source.comm],
                       self.comm_to_y_map[message.destination.comm]])
            if message.type == 'A':
                coords = conn_type_coords['A']
            elif message.type == 'C':
                coords = conn_type_coords['C']
            else:
                coords = conn_type_coords['X']
            coords[0].extend([message.time, message.time])
            coords[1].extend([message.source.comm, message.destination.comm])

        return conn_type_coords


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
data.append(data_io.EventDatum(time=1,
                                   type=types[0],
                                   specific_datum=(
        None, 'process' + str(1), None, None, 'process' + str(3), None, None)))
data.append(data_io.EventDatum(time=2,
                                   type=types[1],
                                   specific_datum=(
        None, 'process' + str(3), None, None, 'process' + str(1), None, None)))
data.append(data_io.EventDatum(time=4,
                                   type=types[2],
                                   specific_datum=(
        None, 'process' + str(3), None, None, 'process' + str(1), None, None)))
data.append(data_io.EventDatum(time=10,
                                   type=types[2],
                                   specific_datum=(
        None, 'process' + str(5), None, None, 'process' + str(4), None, None)))
data.append(data_io.EventDatum(time=15,
                                   type=types[1],
                                   specific_datum=(
        None, 'process' + str(5), None, None, 'process' + str(4), None, None)))

# for i in range(1, int(random.random() * 100)):
#     time = random.random() * 100
#     s = int(random.random() * 100)
#     d = int(random.random() * 100)
#     data.append(data_io.EventDatum(time=time,
#                                    type=types[random.randrange(0, 3)],
#                                    specific_datum=(
#         None, 'process' + str(s), None, None, 'process' + str(d), None, None)))

plot = TCPPlotter(data)
plot.show()
