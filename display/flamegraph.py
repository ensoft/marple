# -------------------------------------------------------------
# flamegraph.py - interacts with the flame graph tool
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------
"""
Interacts with the flamegraph tool.

Issues a command to start the necessary scripts in Brendan Gregg's
Flamegraph tool.

"""
import subprocess


def make(in_filename, out_filename):
    """
    Uses Brendan Gregg's flamegraph tool to convert data to flamegraph.

    :param in_filename:
        The name of the data file from which to create the image.
    :param out_filename:
        The name of the image file that will be created.

    """
    subprocess.call(["../util/flamegraph/flamegraph.pl", in_filename, ">",
                     out_filename])


def show(image):
    """
    Uses firefox to display the flamegraph.

    :param image:
        The image file containing the flamegraph.

    """
    subprocess.call(["firefox", image])

