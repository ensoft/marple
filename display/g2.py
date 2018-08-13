# -------------------------------------------------------------
# flamegraph.py - interacts with the flame g2 tool
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------
"""
Class that interacts with the g2 tool.

Implements the GenericDiaplay interface to display a track separated graph.

"""

__all__ = (
    "G2"
)

import logging
import os
import subprocess

from common import util
from common import file
from display.generic_display import GenericDisplay

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)
logger.setLevel(logging.DEBUG)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"


class G2(GenericDisplay):
    def __init__(self, cpel_file):
        """
        Constructor for the g2.

        :param cpel_filename:
            The name of the [CPEL] file to read data from

        """
        self.cpel_file = cpel_file

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Calls g2 to show a track separated graph

        The reading and writing to and from a temporaty file is a workaround
        to manage the file header

        :param cpel_data:
            The name of the CPEL file containing the data to be displayed.

        """
        tmp = file.TempFileName()
        with open(self.cpel_file, "rb") as read:
            read.readline()
            data = read.read()

        with open(str(tmp), "wb") as write:
            write.write(data)

        subprocess.call(["vpp/build-root/install-native/g2/bin/g2", "--cpel-input",
                         str(tmp)])
