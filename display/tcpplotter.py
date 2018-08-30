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

import typing
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
        def __init__(self, draw_func, conn_types):
            self.draw_func = draw_func
            self.conn_types = conn_types

        def draw(self):
            self.draw_func(self.conn_types)

    def __init__(self, messages_gen, parent=None):
        super().__init__(parent=parent)
        self.messages, self.comm_to_y_map = \
            self._create_comm_to_y_map(messages_gen)

        self.conn_partition_data = self._create_conn_partition()

        # We create the layout
        # First the ploting stuff
        tcp_graph_layout = self.addLayout(row=0, col=0, colspan=4)
        comm_axis = pg.AxisItem(orientation='left')
        comm_axis.setTicks([dict(enumerate(self.comm_to_y_map.keys())).items()])
        self.plot_container = self.addPlot(title="IPC (TCP Messages)",
                                           axisItems={'left': comm_axis})
        self.plots = {
            'A': self.plot_container.plot([], []),
            'X': self.plot_container.plot([], []),
            'C': self.plot_container.plot([], [])
        }
        tcp_graph_layout.addItem(self.plot_container)

        # Now the UI
        self.UI_dict = {}
        #Radio buttons for all the options
        options_group = QtGui.QButtonGroup(self)
        self.all = self.DrawMethodWrapper(self._draw, 'AXC')
        self.conn = self.DrawMethodWrapper(self._draw, 'C')
        self.acc = self.DrawMethodWrapper(self._draw, 'A')
        self.close = self.DrawMethodWrapper(self._draw, 'X')
        self._UI_elems_factory("radio", "all_radio", "Show all", 1, 0,
                               group=options_group,
                               callback_function=self.all.draw)
        self._UI_elems_factory("radio", "acc_radio", "Show accept", 1, 1,
                               group=options_group,
                               callback_function=self.close.draw)
        self._UI_elems_factory("radio", "cls_radio", "Show close", 1, 2,
                               group=options_group,
                               callback_function=self.conn.draw)
        self._UI_elems_factory("radio", "cnt_radio", "Show connect", 1, 3,
                               group=options_group,
                               callback_function=self.all.draw)
        self._UI_elems_factory("text", "choices", "", 2, 1)
        self._UI_elems_factory("button", "display_choices", "Display Choices",
                               2, 2, callback_function=self._empty_plots)

        self._draw_background()

        self.symbols = []
        for _ in range(0, len(self.messages)):
            self.symbols.extend(['s', 'o'])

        self.symbol_brushes = []
        for _ in range(0, len(self.messages)):
            self.symbol_brushes.extend([self.source_brush,
                                        self.destination_brush])

    def _empty_plots(self):
        self.plots['A'].setData([], [], symbol=[], symbolBrush=[])
        self.plots['C'].setData([], [], symbol=[], symbolBrush=[])
        self.plots['X'].setData([], [], symbol=[], symbolBrush=[])

    def _UI_elems_factory(self, type, name, text, row, col, **kwargs):
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
        self.UI_dict[name] = proxy_elem

    def _draw(self, types):
        self._empty_plots()

        for type in types:
            xs, ys = self.conn_partition_data[type]
            num_points = len(xs)
            self.plots[type].setData(
                {'x': xs, 'y': ys},
                symbol=self.symbols[0:num_points],
                pen=self.color_dict[type],
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

    def _draw_background(self):
        max_y = max(self.comm_to_y_map.values())
        max_time = max([message.time for message in self.messages])
        self.plot_container.vb.setLimits(xMin=-1, xMax=max_time + 1, yMin=-1,
                                         yMax=max_y + 1)
        for y in range(0, max_y + 1):
            self.plot_container.plot([0, max_time], [y, y],
                                     pen=pg.mkPen(255, 255, 255, 32))

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
            coords[1].extend([self.comm_to_y_map[message.source.comm],
                              self.comm_to_y_map[message.destination.comm]])

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
        renderer.resize(800, 600)
        renderer.show()
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
