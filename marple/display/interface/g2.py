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
    consts,
    file,
    util,
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

    def __init__(self, data):
        """
        Constructor for the g2 display mode.

        :param data:
            An EventData object.

        """
        # Initialise the base class
        super().__init__(data)

        track = config.get_option_from_section(
            consts.DisplayOptions.G2.value, "track")
        self.display_options = self.DisplayOptions(track)

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Calls g2 to show a track separated graph

        The conversion for the MARPLE format happens here, a new CPEL file being
        created

        """
        tmp_cpel = str(file.TempFileName())
        g2_path = config.get_option_from_section('g2', 'path')
        g2_path = os.path.expanduser(g2_path)
        logger.info("G2 path: %s", g2_path)

        # We create a generator that yields EventDatum from
        event_generator = self.data.datum_generator
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
