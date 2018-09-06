# -------------------------------------------------------------
# flamegraph.py - interacts with the flame g2 tool
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
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
from typing import NamedTuple

from marple.common import (
    file,
    util,
    data_io,
    config,
    output
)
from marple.display.interface.generic_display import GenericDisplay
from marple.display.tools.g2.cpel_writer import CpelWriter

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)
logger.setLevel(logging.DEBUG)


class G2(GenericDisplay):
    class DisplayOptions(NamedTuple):
        """
        Options:
            - track: pid or cpu, tells the g2 tool what to use as track
        """
        track: str
    _DEFAULT_OPTIONS = DisplayOptions(track="pid")

    def __init__(self, data, data_options=data_io.EventData.DEFAULT_OPTIONS,
                 display_options=_DEFAULT_OPTIONS):
        """
        Constructor for the g2.

        This display mode does not currently support an out file the g2 result
        cannot be saved

        :param data:
            A generator that returns the lines for the section we want to
            display using g2
        :param data_options: object of the class specified in each of the `Data`
                             classes, containig various data options to be used
                             in the display class as labels or info
        :param display_options: display related options that are meant to make
                                the display option more customizable
        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        self.data = data

    def _generate_events_from_file(self):
        """
        Helper static method that yields EventDatum as we consume the
        self.data generator that contains all the data in the section

        :returns: an EventDatum object parsed form the current line of the file

        """
        for line in self.data:
            yield data_io.EventDatum.from_string(line)

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Calls g2 to show a track separated graph

        The conversion for the MARPLE format happens here, a new CPEL file being
        created

        """
        tmp_cpel = file.TempFileName()
        g2_path = config.Parser().get_option_from_section('g2', 'path')
        g2_path = os.path.expanduser(g2_path)
        logger.info("G2 path: " + g2_path)

        # We create a generator that yields EventDatum from
        event_generator = self._generate_events_from_file()

        writer = CpelWriter(event_generator, self.display_options.track)
        writer.write(str(tmp_cpel))

        try:
            subprocess.call([g2_path, "--cpel-input", str(tmp_cpel)])
        except FileNotFoundError as fnfe:
            output.error_("G2 not found at {}. Check your config file?"
                          .format(fnfe.filename),
                          "Could not find G2 at {}, FileNotFoundError raised. "
                          "Change your config file to show the correct G2 path."
                          .format(fnfe.filename))
