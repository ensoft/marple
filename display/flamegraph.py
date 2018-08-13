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
from common.datatypes import StackData
from display.generic_display import GenericDisplay

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"

FLAMEGRAPH_DIR = DISPLAY_DIR + "util/flamegraph/flamegraph.pl"


class Flamegraph(GenericDisplay):
    def __init__(self, inp, out, coloring):
        """
        Constructor for the flamegraph.

        :param inp:
            The name of the [Stack] file to read data from
        :param out:
            The name of the image file that will be created.
        :param colouring:
            The colouring for the flamegraph as an argument string.
            As defined by Brendan Gregg's script, to go in the
            "--color=" option.
        """
        self.in_filename = inp
        out.set_options("treemap", "html")

        self.out_filename = str(out)
        self.colouring = coloring

    @util.log(logger)
    def _read(self):
        """
        Read stack events from a file in standard format.

        """
        with open(self.in_filename, "r") as inp:
            # Skip first line, header
            inp.readline()

            for line in inp.readlines():
                yield StackData.from_string(line)

    @util.log(logger)
    def _make(self, stack_data):
        """
        Uses Brendan Gregg's flamegraph tool to convert data to flamegraph.

        :param stack_data:
            Generator for `StackData` objects.

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
            if self.colouring:
                subprocess.Popen([FLAMEGRAPH_DIR, "--color=" + self.colouring,
                                  temp_file], stdout=out)
            else:
                subprocess.Popen([FLAMEGRAPH_DIR, temp_file], stdout=out)

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
