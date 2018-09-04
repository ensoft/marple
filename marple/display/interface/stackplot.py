# -------------------------------------------------------------
# stackplot.py - Creates a stackplot from labelled coordinate data.
# June-July 2018 - Franz Nowak, Hrutvik
# -------------------------------------------------------------
"""
# stackplot.py - Creates a stackplot from labelled coordinate data.

Adds colours and legend and fills in between the lines.

"""

__all__ = ("StackPlot", )

import logging
from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np

from marple.common import util, data_io
from marple.display.interface.generic_display import GenericDisplay

logger = logging.getLogger(__name__)


class StackPlot(GenericDisplay):
    """
    The class representing stackplots.

    Takes a filename with CSV formatted data as input.
        To show the stack plot, use :func:`StackPlot.show`.

    """

    class DisplayOptions(NamedTuple):
        """
        - top_processes: the number of processes to be displayed in the
                         stackplot
        """
        top_processes: int

    _DEFAULT_DISPLAY_OPTIONS = DisplayOptions(top_processes=5)

    @util.log(logger)
    def __init__(self, data, data_options=data_io.PointData.DEFAULT_OPTIONS,
                 display_options=_DEFAULT_DISPLAY_OPTIONS):
        """
        Constructor, initialises the stackplot.

        There is no out file since currently we do not save an image of the
        output
        :param data:
            A generator that returns the lines for the section we want to
            display as a stackplot
        :param data_options: object of the class specified in each of the `Data`
                             classes, containig various data options to be used
                             in the display class as labels or info
        :param display_options: display related options that are meant to make
                                the display option more customizable

        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        # Read the data into a dict
        datapoints = {}
        for line in data:
            dp = data_io.PointDatum.from_string(line)
            if dp.x not in datapoints:
                datapoints[dp.x] = []
            datapoints[dp.x].append((dp.y, dp.info))

        # Collapse same labels at same x
        self._collapse_labels(datapoints)

        # Set of unique labels that will be displayed
        seen_labels = set()

        # Dict of x-coord to other points not in the top n at that x
        other = {}

        for x in datapoints:
            # Sort tuples at each time step by memory and take top elements
            data_descending = sorted(datapoints[x],
                                     key=lambda z: z[0],
                                     reverse=True)

            # Only keep first n at each time step
            datapoints[x] = data_descending[0:self.display_options
                                                  .top_processes]

            # Sum the rest of the values separately, as "other"
            if x not in other:
                try:
                    other[x] = np.sum(z[0] for z in
                                      data_descending[self.display_options
                                                          .top_processes:])
                except IndexError as ie:
                    raise IndexError("Not enough data to display stackplot "
                                     "with {} rows, use smaller number. {}"
                                     .format(self.display_options
                                                 .top_processes,
                                             ie.args))

            # Keep track of the labels that are in use in top n
            seen_labels = seen_labels.union(set(z[1] for z in datapoints[x]))

        # Insert the missing datapoints
        self._add_missing_datapoints(datapoints, seen_labels)

        # Sort again
        for x in datapoints:
            datapoints[x] = sorted(datapoints[x],
                                   key=lambda z: z[1],
                                   reverse=True)

        y_values_list = []
        # @@@ separate other and tuple_list into different for loops
        for index in range(len(seen_labels)+1):
            values = []
            for x, tuple_list in datapoints.items():
                if index == 0:
                    values.append(other[x])
                else:
                    values.append(tuple_list[index-1][0])
            y_values_list.append(values)

        labels_list = ["other"]
        for _, tuple_list in datapoints.items():
            for(_, label) in tuple_list:
                labels_list.append(label)
            break

        # Create the data to be plotted
        self.x_values = sorted(time for time in datapoints)
        self.y_values = np.stack(y_values_list)
        self.labels = labels_list

    @staticmethod
    def _collapse_labels(datapoints):
        """
        Collapses unique labels at each x-coordinate.

        Takes a dict representing a 2d graph with labels and makes the labels
            unique for each x coordinate by adding the y values for the same
            label. MODIFIES THE DICT PASSED AS AN ARGUMENT.

        :param datapoints:
            A dict with x-coordinates as keys and tuples of (y,label) as values.

        """
        # e.g.  in:     x1 -> (y1, label1), (y2, label2), (y3, label1)
        #       out:    x1 -> (y1+y3, label1), (y2, label2)

        for x in datapoints:
            # use dict to make labels at each x unique and add y's
            points = {}
            for (y, label) in datapoints[x]:
                if label not in points:
                    points[label] = y
                else:
                    points[label] += y

            # Convert back to list of tuples and modify the input dict
            datapoints[x] = [(y, label) for label, y in points.items()]

    @staticmethod
    def _add_missing_datapoints(datapoints, seen_labels):
        """
        Adds datapoints to the graph to make it plottable.

        Stackplot can only be plotted if there are the same number of (y,
        label) for each x, so add (0.0, label) where necessary, so that all
        seen labels exist at each x. MODIFIES THE DICT PASSED AS AN ARGUMENT.

        :param datapoints:
            A dict with x-coordinates as keys and tuples of (y,label) as values.
        :param seen_labels:
            The set of labels that need to exist at each x.

        """
        for x, data_tuple_list in datapoints.items():
            labels_at_key = set(tup[1] for tup in data_tuple_list)
            for _label in seen_labels - labels_at_key:
                datapoints[x].append((0.0, _label))

    @util.log(logger)
    @util.Override(GenericDisplay)
    def show(self):

        ax = plt.subplot(1, 1, 1)

        try:
            # Create the plot, ordering by time coordinates
            ax.stackplot(self.x_values, self.y_values, labels=self.labels)

        except KeyError as ke:
            raise KeyError("Not enough information to create a stackplot. "
                           "Need at least two samples. {}".format(ke.args))

        # Set legend, inverting the elements to have "other" at the bottom
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1])

        # @@@ Set labels passed as arguments (options)
        ax.set_xlabel(self.data_options.x_label + ' / ' +
                      self.data_options.x_units)
        ax.set_ylabel(self.data_options.y_label + ' / ' +
                      self.data_options.y_units)

        plt.show()
