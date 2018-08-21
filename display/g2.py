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
from util.g2.cpel_writer import CpelWriter
from common.datatypes import EventData
from collect.IO import read

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)
logger.setLevel(logging.DEBUG)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"


class G2(GenericDisplay):
    def __init__(self, inp):
        """
        Constructor for the g2.

        :param inp:
            The name of the [CPEL] file to read data from

        """
        self.inp = inp

    @staticmethod
    def _generate_events_from_file(file_descriptor):
        line = file_descriptor.readline()
        while line != "":
            yield EventData.from_string(line)
            line = file_descriptor.readline()

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Calls g2 to show a track separated graph

        First we write the actual CPEL data (binary) in a temporary file using
        the [CPEL] format (CSV)
        after which we pass it to the g2 tool

        """
        tmp_cpel = file.TempFileName()
        with read.Reader(str(self.inp)) as (header, data):
            event_generator = self._generate_events_from_file(data)
            writer = CpelWriter(event_generator)

        writer.write(str(tmp_cpel))

        subprocess.call(["vpp/build-root/install-native/g2/bin/g2",
                         "--cpel-input", str(tmp_cpel)])
