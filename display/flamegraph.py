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

from common import file
from common.datatypes import StackData

DISPLAY_DIR = str(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__)))) + "/"

FLAMEGRAPH_DIR = DISPLAY_DIR + "util/flamegraph/flamegraph.pl"


def read(in_filename):
    """Read stack events from a file in standard format."""
    with open(in_filename, "r") as file:
        for line in file.readlines():
            yield StackData.from_string(line)


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
    temp_file = file.create_unique_temp_filename()
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


def show(image):
    """
    Uses firefox to display the flamegraph.

    :param image:
        The image file containing the flamegraph.

    """
    username = os.environ['SUDO_USER'] #@@@ TODO test this
    subprocess.call(["su", "-", "-c",  "firefox " + DISPLAY_DIR + image,
                     username])

