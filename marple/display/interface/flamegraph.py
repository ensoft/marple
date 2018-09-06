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

import os
import subprocess
import collections
import logging

from marple.common import (
    file,
    util,
    data_io,
    paths
)
from marple.common.data_io import StackDatum
from marple.display.interface.generic_display import GenericDisplay
from typing import NamedTuple

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

    _DEFAULT_OPTIONS = DisplayOptions(coloring="hot")

    def __init__(self, data, out,
                 data_options=data_io.StackData.DEFAULT_OPTIONS,
                 display_options=_DEFAULT_OPTIONS):
        """
        Constructor for the flamegraph.

        :param data:
            A generator that returns the lines for the section we want to
            display as a flamegraph
        :param out:
            The output file where the image will be saved as an instance
            of the :class:`DisplayFileName`.
        :param data_options: object of the class specified in each of the `Data`
                             classes, containig various data options to be used
                             in the display class as labels or info
        :param display_options: display related options that are meant to make
                                the display option more customizable


        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        self.data = data
        # Setting the right extension and getting the path of the outp
        out.set_options("flamegraph", "svg")
        self.out_filename = str(out)

    @util.log(logger)
    def _read(self):
        """
        Read stack events from the self.data generator and parse each line to
        a StackDatum object

        :returns: a generator yielding StackDatum for each line read from
                  self.data
        """

        for line in self.data:
            yield StackDatum.from_string(line)

    @util.log(logger)
    def _make(self, stack_data):
        """
        Uses Brendan Gregg's flamegraph tool to convert data to flamegraph.

        :param stack_data:
            Generator for `StackDatum` objects.

        """
        temp_file = str(file.TempFileName())
        counts = collections.Counter()
        for stack in stack_data:
            new_counts = collections.Counter({stack.stack: stack.weight})
            counts += new_counts

        with open(temp_file, "w") as out:
            for stack, count in counts.items():
                out.write(";".join(stack) + " {}\n".format(count))

        with open(self.out_filename, "w") as out:
            if self.display_options.coloring:
                subprocess.Popen([FLAMEGRAPH_DIR, "--color=" +
                                  self.display_options.coloring,
                                  "--countname=" + self.data_options.weight_units,
                                  temp_file],
                                 stdout=out)
            else:
                subprocess.Popen([FLAMEGRAPH_DIR, temp_file], stdout=out)

        # Return counts to aid debugging
        return counts

    @util.log(logger)
    @util.Override(GenericDisplay)
    def show(self):
        """
        Creates the image and uses firefox to display the flamegraph.

        """
        # Generate data from the input file
        stack_generator = self._read()
        # Create a flamegraph svg based on the data
        self._make(stack_generator)
        # Open firefox
        username = os.environ['SUDO_USER']
        subprocess.call(["su", "-", "-c",  "firefox " + self.out_filename,
                         username])
