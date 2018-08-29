# -------------------------------------------------------------
# tcpplotter.py - plots tcp data
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Display option that can display ipc/tcp data as a line graph

"""

import matplotlib.pyplot as plt
import logging

import typing

from common import data_io
from display.interface import generic_display

logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))

_all__ = (

)

class TCPPlotter(generic_display.GenericDisplay):
    """
    Class that displays tcp data as a custom line graph"

    """
    class DisplayOptions(typing.NamedTuple):
        pass

    _DEFAULT_OPTIONS = DisplayOptions()

    def __init__(self, data,
                 data_options=data_io.StackData.DEFAULT_OPTIONS,
                 display_options=_DEFAULT_OPTIONS):
        """
        Initializes the class

        :param data:
            A generator that returns the lines for the section we want to
            display as a flamegraph
        :param data_options: object of the class specified in each of the `Data`
                             classes, containig various data options to be used
                             in the display class as labels or info
        :param display_options: display related options that are meant to make
                                the display option more customizable
        """
        self.data = data

    def _plot_draw(self):
        """
        Helper function that draws the points and lines in the plotter

        It first draws the timeline for each process and its label.
        Then we draw each source point and destination point and the line that
        connects them, coloured and labeled correctly
        """

        y_dict = {}
        crt_y_location = 0
        for event_datum in self.data:
            # We save all the data encoded in the event_datum
            time = event_datum[0]
            type = event_datum[1]
            source_pid = event_datum[2][0]
            source_comm = event_datum[2][1]
            source_port = event_datum[2][2]
            dest_pid = event_datum[2][3]
            dest_comm = event_datum[2][4]
            dest_port = event_datum[2][5]
            net_ns = event_datum[2][6]

            # If the current source_comm was not encountered before, add it
            # to the dict with it's corresponding y location and add its axline
            # crt_y_location represents the current y location where we can
            # draw a new process; starts from 0 and goes up
            if source_comm not in y_dict.keys():
                y_dict[source_comm] = crt_y_location
                plt.axhline(crt_y_location, color="darkgray")
                crt_y_location += 1

            # Same but now for dest_comm
            if dest_comm not in y_dict.keys():
                y_dict[dest_comm] = crt_y_location
                plt.axhline(crt_y_location, color="darkgray")
                crt_y_location += 1

            if type == 'A':
                color = 'g'
            elif type == 'C':
                color = 'b'
            else:
                color = 'r'
            plt.plot([time], [y_dict[source_comm]], color='black', marker="$S$")
            plt.plot([time], [y_dict[dest_comm]], color='black', marker="$D$")
            plt.plot([time, time], [y_dict[source_comm], y_dict[dest_comm]],
                     '{}-'.format(color), linewidth=1.0)

        y_int = [idx for idx in range(0, len(y_dict.keys()))]
        y_labels = [comm for comm in sorted(y_dict.keys())]
        plt.yticks(y_int, y_labels)

    def show(self):
        """
        Populates the graph and shows it in an interactive window

        """
        self._plot_draw()
        plt.show()


# TODO: https://bastibe.de/2013-05-30-speeding-up-matplotlib.html
# TODO: Add new
# import random
#
# data = []
# types = ['A', 'X', 'C']
# for i in range(1, int(random.random() * 100)):
#     time = random.random() * 100
#     s = int(random.random() * 100)
#     d = int(random.random() * 100)
#     data.append(data_io.EventDatum(time=time,
#                                    type=types[random.randrange(0, 3)],
#                                    specific_datum=(
#         None, 'process' + str(s), None, None, 'process' + str(d), None, None)))
#
# plot = TCPPlotter(data)
# plot.show()
