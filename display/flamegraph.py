# -------------------------------------------------------------
# flamegraph.py - interacts with the flame graph tool
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------
"""
Interacts with the flamegraph tool.

Issues a command to start the necessary scripts in Brendan Gregg's
Flamegraph tool.

"""
import os
import subprocess
import collections
import logging

from common import (
    file,
    util
)
from common.datatypes import StackData

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"

FLAMEGRAPH_DIR = DISPLAY_DIR + "util/flamegraph/flamegraph.pl"


@util.log(logger)
def read(in_filename):
    """Read stack events from a file in standard format."""
    with open(in_filename, "r") as in_file:
        # Skip first line, header
        in_file.readline()
        for line in in_file.readlines():
            yield StackData.from_string(line)


@util.log(logger)
def make(stack_data, out_filename, colouring=None):
    """
    Uses Brendan Gregg's flamegraph tool to convert data to flamegraph.

    :param stack_data:
        Generator for :class:`StackData` objects.
    :param out_filename:
        The name of the image file that will be created.
    :param colouring:
        The colouring for the flamegraph as an argument string.
        As defined by Brendan Gregg's script, to go in the
        "--color=" option.

    """
    temp_file = str(file.TempFileName())
    counts = collections.Counter()
    for stack in stack_data:
        new_counts = collections.Counter({stack.stack: stack.weight})
        counts += new_counts

    with open(temp_file, "w") as out:
        for stack, count in counts.items():
            out.write(";".join(stack) + " {}\n".format(count))

    with open(out_filename, "w") as out:
        if colouring:
            subprocess.Popen([FLAMEGRAPH_DIR, "--color=" + colouring,
                              temp_file], stdout=out)
        else:
            subprocess.Popen([FLAMEGRAPH_DIR, temp_file], stdout=out)


@util.log(logger)
def show(image):
    """
    Uses firefox to display the flamegraph.

    :param image:
        The name of the image file containing the flamegraph.

    """
    username = os.environ['SUDO_USER'] #@@@ TODO test this
    subprocess.call(["su", "-", "-c",  "firefox " + image,
                     username])

