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
from common.datatypes import EventDatum
from collect.IO import read
from typing import NamedTuple

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)
logger.setLevel(logging.DEBUG)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"


class G2(GenericDisplay):
    class DisplayOptions(NamedTuple):
        """
        Options:
            - track: pid or cpu, tells the g2 tool what to use as track
        """
        track: str
    _DEFAULT_OPTIONS = DisplayOptions(track="pid")

    def __init__(self, inp, data_options, display_options=_DEFAULT_OPTIONS):
        """
        Constructor for the g2.

        This display mode does not currently support an out file the g2 result
        cannot be saved

        :param inp:
            The input file that holds the data as an instance of the
            :class:`DataFileName`.
        :param data_options:
        :param display_options:
        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        self.inp = inp

    @staticmethod
    def _generate_events_from_file(file_descriptor):
        """
        Helper static method that yields EventDatum as we read the file
        :param file_descriptor: a file descriptor so we can extract the current
                                event from the file
        :returns: an EventDatum object parsed form the current line of the file

        """
        line = file_descriptor.readline()
        while line != "":
            yield EventDatum.from_string(line)
            line = file_descriptor.readline()

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Calls g2 to show a track separated graph

        The conversion for the MARPLE format happens here, a new CPEL file being
        created

        """
        tmp_cpel = file.TempFileName()
        with read.Reader(str(self.inp)) as (header, data):
            event_generator = self._generate_events_from_file(data)
            writer = CpelWriter(event_generator, self.display_options.track)

        writer.write(str(tmp_cpel))

        subprocess.call(["vpp/build-root/install-native/g2/bin/g2",
                         "--cpel-input", str(tmp_cpel)])
