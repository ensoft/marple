# -------------------------------------------------------------
# flamegraph.py - interacts with the flame graph tool
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------
"""
Class that interacts with the flamegraph tool.

Implements the GenericDiaplay interface to display an image of a flamegraph.

"""

__all__ = (
    "Flamegraph"
)

import collections
import logging
import os
import subprocess
from typing import NamedTuple

from marple.common import (
    config,
    consts,
    file,
    util,
    paths
)
from marple.display.interface.generic_display import GenericDisplay

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

FLAMEGRAPH_DIR = paths.MARPLE_DIR + "/display/tools/flamegraph/flamegraph.pl"


class Flamegraph(GenericDisplay):
    class DisplayOptions(NamedTuple):
        """
        - coloring: can be hot (default), mem, io, wakeup, chain, java, js,
                    perl, red, green, blue, aqua, yellow, purple, orange
        """
        coloring: str

    def __init__(self, data):
        """
        Constructor for the flamegraph.

        :param data:
            A generator that returns the data for the section we want to
            display as a flamegraph

        """
        # Initialise the base class
        super().__init__(data)

        coloring = config.get_option_from_section(
            consts.DisplayOptions.FLAMEGRAPH.value, "coloring")
        self.display_options = self.DisplayOptions(coloring)

    @util.log(logger)
    def _make(self, data):
        """
        Uses Brendan Gregg's flamegraph tool to convert data to flamegraph.

        :param data:
            A StackData object.

        """
        stacks_temp_file = str(file.TempFileName())
        counts = collections.Counter()

        stack_data = data.datum_generator
        for stack in stack_data:
            new_counts = collections.Counter({stack.stack: stack.weight})
            counts += new_counts

        with open(stacks_temp_file, "w") as out:
            for stack, count in counts.items():
                out.write(";".join(stack) + " {}\n".format(count))

        self.svg_temp_file = str(file.TempFileName())

        with open(self.svg_temp_file, "w") as out:
            if self.display_options.coloring:
                subprocess.Popen(
                    [FLAMEGRAPH_DIR, "--color=" + self.display_options.coloring,
                     "--countname=" + self.data_options.weight_units,
                     stacks_temp_file], stdout=out)
            else:
                subprocess.Popen([FLAMEGRAPH_DIR, stacks_temp_file], stdout=out)

        # Return counts to aid debugging
        return counts

    @util.log(logger)
    @util.Override(GenericDisplay)
    def show(self):
        """
        Creates the image and uses firefox to display the flamegraph.

        """
        # Create a flamegraph svg based on the data
        self._make(self.data)

        # Open firefox
        username = os.environ['SUDO_USER']
        subprocess.call(
            ["su", "-", "-c",  "firefox " + self.svg_temp_file, username])
