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

import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt

from common import util

logger = logging.getLogger(__name__)


class StackPlot(GenericDisplay):
    """
    The class representing stackplots.

    Takes a filename with CSV formatted data as input.
        To show the heat map, use :func:`StackPlot.show`.

    """
    @util.log(logger)
    def __init__(self, filename):
        """
        Constructor, initialises the stackplot.

        :param filename:
            The name of the file containing csv data in three columns.

        """
        with open(filename, "r", encoding="utf-8") as file_:
            # Skip header line
            file_.readline()
            # Read the data into a DataFrame, naming the columns X, Y, and INFO
            self.df = pd.read_csv(file_, names=["X", "Y", "INFO"],
                                  header=None)

        # Extract unique info fields and convert array to list
        i = pd.unique(self.df.INFO)
        self.labels = ['{}'.format(_i) for _i in i]
        # self.labels.add("other")

        # Extract list of mem_sizes for labels
        self.mem_size = [self.df[self.df.INFO == _i].Y for _i in i]

    @staticmethod
    def _add_missing_datapoints(dataframe):
        """
        Adds datapoints to the CSV to make it plottable.

        :param dataframe:

        :return:
        """
        pass

    @staticmethod
    def _collapse_other():
        """

        :return:
        """
        pass

    @util.log(logger)
    @util.Override(GenericDisplay)
    def show(self):
        try:
            # Create the plot, ordering by time coordinates
            plt.stackplot(np.unique(self.df.X), self.mem_size[::-1],
                          labels=self.labels[::-1])
        except TypeError as te:
            raise TypeError("CSV seems to have missing or duplicate entries. {}"
                            .format(te.args))
        except KeyError as ke:
            raise KeyError("Too little information to create a stackplot. "
                           "Record for longer. {}".format(ke.args))

        # Set labels
        plt.xlabel('time/s')
        plt.ylabel('memory')

        # Set legend
        ax = plt.subplot(1, 1, 1)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1])

        plt.show()


if __name__ == "__main__":
    filename = "/tmp/stackplot.plt"
    with open(filename, "w") as file_:
        file_.writelines(io.StringIO("""
        [CSV]
        0,0,x
        0,0,y
        1,0.5,x
        1,1,y
        0,0,other
        1,2,other
        """.strip()))

    sp = StackPlot(filename)
    sp.show()
