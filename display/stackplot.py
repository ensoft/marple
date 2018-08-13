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
            The name of the file containing the csv data.

        """
        with open(filename, "r", encoding="utf-8") as file_:
            # Skip header line
            file_.readline()
            # Read the data, naming the columns X, Y, and INFO
            self.df = pd.read_csv(file_, names=["X", "Y", "INFO"],
                                  header=None)

        # Extract unique info fields and convert array to list
        i = np.unique(self.df.INFO)
        self.labels = ['{}'.format(_i) for _i in i]

        # Extract list of mem_sizes for labels
        self.mem_size = [self.df[self.df.INFO == _i].Y for _i in i]

    @util.log(logger)
    @util.Override(GenericDisplay)
    def show(self):
        # Create the plot
        plt.stackplot(np.unique(self.df.X), self.mem_size, labels=self.labels)

        # Set labels
        plt.xlabel('time/s')
        plt.ylabel('memory')

        # Set legend
        plt.legend(loc='upper left')

        plt.show()


if __name__ == "__main__":
    filename = "/tmp/stackplot.plt"
    with open(filename, "w") as file_:
        file_.writelines(io.StringIO("""
        [CSV]
        0,0,a
        0,0,b
        1,1,a
        1,1,b
        """.strip()))

    sp = StackPlot(filename)
    sp.show()
