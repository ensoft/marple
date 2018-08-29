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
import enum

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


# TODO: Tooltip for the unused data
# TODO: Add multiple colors to lines (search for Luke's answer on coloring
# TODO: discrete segments on the Google Forum)
class _TCPDDrawWidget(pg.GraphicsWindow):
    source_brush = pg.mkBrush('w')
    destination_brush = pg.mkBrush('w')
    accept_color = pg.mkColor('g')
    close_color = pg.mkColor('r')
    connect_color = pg.mkColor('b')

    def __init__(self, messages, comm_to_y_map, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.messages = messages
        self.comm_to_y_map = comm_to_y_map

        self._draw_background()
        self._draw_data()

    def _draw_background(self):
        comm_axis = pg.AxisItem(orientation='left')
        comm_axis.setTicks([dict(enumerate(self.comm_to_y_map.keys())).items()])
        self.plotter = self.addPlot(title="IPC (TCP Messages)",
                                    axisItems={'left': comm_axis})

        max_y = max(self.comm_to_y_map.values())
        max_time = max([message.time for message in self.messages])
        self.plotter.vb.setLimits(xMin=-1, xMax=max_time + 1, yMin=-1,
                                  yMax=max_y + 1)
        for y in range(0, max_y + 1):
            self.plotter.plot([0, max_time], [y, y],
                              pen=pg.mkPen(255, 255, 255, 32))

    def _draw_data(self):
        symbols = []
        for _ in range(0, len(self.messages)):
            symbols.extend(['s', 'o'])

        symbol_brushes = []
        for _ in range(0, len(self.messages)):
            symbol_brushes.extend([self.source_brush,
                                   self.destination_brush])

        xs = []
        ys = []
        line_colors = []
        for message in self.messages:
            xs.extend([message.time, message.time])
            ys.extend([self.comm_to_y_map[message.source.comm],
                       self.comm_to_y_map[message.destination.comm]])
            if message.type == 'A':
                color = self.accept_color
            elif message.type == 'C':
                color = self.connect_color
            else:
                color = self.close_color
            line_colors.append(color)

        self.plotter.plot({'x': xs, 'y': ys}, symbol=symbols,
                          pen='b', symbolBrush=symbol_brushes,
                          connect="pairs")

    def set_lines(self, x, y):
        symbols = []
        for i in range(0, int(len(x)/2)):
            symbols.extend(['s', 'o'])

        colors = []
        brush_sour = pg.mkBrush('g')
        brush_dest = pg.mkBrush('r')
        for i in range(0, int(len(x)/2)):
            colors.extend([brush_sour, brush_dest])
        self.plotDataLines.setData({'x':x, 'y':y}, symbol=symbols,
                                   pen='r', symbolBrush=colors)


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

        self.data = data_gen

    def _get_data_and_mapping(self):
        comm_to_y_map = {}
        unique_ys = 0
        messages = []

        for event_datum in self.data:
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

    def show(self):
        """
        Populates the graph and shows it in an interactive window

        """
        app = QtWidgets.QApplication([])

        messages, comm_to_y_map = self._get_data_and_mapping()

        renderer = _TCPDDrawWidget(messages, comm_to_y_map)
        pg.setConfigOptions(antialias=False)
        renderer.resize(800, 600)
        renderer.show()
        renderer.raise_()
        app.exec_()


import random

data = []
types = ['A', 'X', 'C']

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
