# -------------------------------------------------------------
# stackplot.py - Creates a stackplot from labelled coordinate data.
# June-July 2018 - Franz Nowak, Hrutvik
# -------------------------------------------------------------
"""
# stackplot.py - Creates a stackplot from labelled coordinate data.

Adds colours and legend and fills in between the lines.

"""
import logging

from display.generic_display import GenericDisplay

__all__ = ("StackPlot", )

import numpy as np
import io
import matplotlib.pyplot as plt

from common import util

logger = logging.getLogger(__name__)


class StackPlot(GenericDisplay):
    """
    The class representing stackplots.

    Takes a filename with CSV formatted data as input.
        To show the stack plot, use :func:`StackPlot.show`.

    """
    @util.log(logger)
    def __init__(self, filename, number):
        """
        Constructor, initialises the stackplot.

        :param filename:
            The name of the file containing csv data in three columns.
        :param number:
            The number of elements per time step to display

        """

        with open(filename, "r", encoding="utf-8") as file_:
            # Skip header line
            file_.readline()
            # read the data into a dict
            datapoints = {}
            for line in file_:
                (x, y, label) = line.strip().split(",")
                x, y = float(x), float(y)
                if x not in datapoints:
                    datapoints[x] = []
                datapoints[x].append((y, label))

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
            datapoints[x] = data_descending[0:number]

            # Sum the rest of the values separately, as "other"
            if x not in other:
                try:
                    other[x] = np.sum(z[0] for z in data_descending[number:])
                except IndexError as ie:
                    raise IndexError("Not enough data to display stackplot "
                                     "with {} rows, use smaller number. {}"
                                     .format(number, ie.args))

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
        ax.set_xlabel('time/s')
        ax.set_ylabel('memory/MB')

        plt.show()


if __name__ == "__main__":
    fn = "/tmp/stackplot.plt"
    with open(fn, "w") as f:
        f.writelines(io.StringIO("""
        [CSV]
        0,0,other
        0,0,x
        0,1,x
        0,0,y
        1,0.5,x
        1,1,y
        1,2,other
        """.strip()))
        # @@@Test other as name

    sp = StackPlot(fn, 2)
    sp.show()
