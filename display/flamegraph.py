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
logger.debug('Entered module: {}'.format(__name__))

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"

FLAMEGRAPH_DIR = DISPLAY_DIR + "util/flamegraph/flamegraph.pl"


class Flamegraph(GenericDisplay):
    def __init__(self, *args):
        """

        :param args[0] (in_filename):
            The name of the [Stack] file to read data from
        :param args[1] (out_filename):
            The name of the image file that will be created.
        :param args[2] (colouring):
            The colouring for the flamegraph as an argument string.
            As defined by Brendan Gregg's script, to go in the
            "--color=" option.
        """
        if len(args) != 3:
            raise Exception("Invalid number of parameters for the Flamegraph "
                            "class. The correct ones are, in this order, "
                            "in_filename, out_filename, colouring")
        self.in_filename = args[0]
        self.out_filename = args[1]
        self.colouring = args[2]

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

