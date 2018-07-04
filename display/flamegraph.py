# -------------------------------------------------------------
# flamegraph.py - interacts with the flame graph tool
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------
"""
Interacts with the flamegraph tool.

Issues a command to start the necessary scripts in Brendan Gregg's
Flamegraph tool.

"""


def make_flamegraph(filename):
    """

    :param filename:
        The name of the output file
    """
