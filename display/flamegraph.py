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

from common import (
    file,
    util
)
from collect.IO import read
from common.datatypes import StackDatum
from display.generic_display import GenericDisplay
from typing import NamedTuple

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"

FLAMEGRAPH_DIR = DISPLAY_DIR + "util/flamegraph/flamegraph.pl"


class Flamegraph(GenericDisplay):
    class DisplayOptions(NamedTuple):
        """
        - coloring: can be hot (default), mem, io, wakeup, chain, java, js,
                    perl, red, green, blue, aqua, yellow, purple, orange
        """
        coloring: str

    _DEFAULT_OPTIONS = DisplayOptions(coloring="hot")

    def __init__(self, inp, out, data_options,
                 display_options=_DEFAULT_OPTIONS):
        """
        Constructor for the flamegraph.

        :param inp:
            The input file that holds the data as an instance of the
            :class:`DataFileName`.
        :param out:
            The output file where the image will be saved as an instance
            of the :class:`DisplayFileName`.
        :param data_options:
        :param display_options:


        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        # in_filename and out_filename File objects (see common.files)
        # We need to get their string representations (paths) and set the
        # right extension for the out file
        self.in_filename = str(inp)
        out.set_options("flamegraph", "svg")
        self.out_filename = str(out)

    @util.log(logger)
    def _read(self):
        """
        Read stack events from a file in standard format.

        """
        with read.Reader(self.in_filename) as (header, data):
            for line in data.readlines():
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
