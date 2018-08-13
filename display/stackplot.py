# -------------------------------------------------------------
# stackplot.py - Creates a stackplot from labelled coordinate data.
# June-July 2018 - Franz Nowak, Hrutvik
# -------------------------------------------------------------
"""
# stackplot.py - Creates a stackplot from labelled coordinate data.

Adds colours and legend and fills in between the lines.

"""
import logging

__all__ = ("StackPlot", )

import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt

from common import util

logger = logging.getLogger(__name__)


class StackPlot:
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
            df = pd.read_csv(file_)
        c = np.unique(df.C)
        labels = ['{}'.format(_c) for _c in c]
        args = [df[df.C == _c].B for _c in c]
        plt.stackplot(np.unique(df.A), args, labels=labels)
        plt.xlabel('time/s')
        plt.ylabel('memory/mB')
        plt.legend(loc='upper left')

    @util.log(logger)
    def show(self):
        plt.show()


if __name__ == "__main__":
    filename = "/tmp/stackplot.plt"
    with open(filename, "w") as file_:
        file_.writelines(io.StringIO("""
        A,B,C
        0,0,a
        0,0,b
        1,1,a
        1,1,b
        """.strip()))

    sp = StackPlot(filename)
    sp.show()
