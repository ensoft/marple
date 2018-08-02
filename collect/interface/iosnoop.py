# -------------------------------------------------------------
# perf.py - interacts with Brendan Gregg's iosnoop tool
# July 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

"""
Interacts with the iosnoop tracing tool.

Calls iosnoop to collect data and format it.

"""
__all__ = ["collect_disk"]

import logging
import os
import subprocess

from common import output
from ..converter.datatypes import Datapoint

logger = logging.getLogger("collect.interface.iosnoop")
logger.setLevel(logging.DEBUG)

ROOT_DIR = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__))))) + "/"

IOSNOOP_SCRIPT = ROOT_DIR + "util/perf-tools/iosnoop"


def collect_disk(time):
    """
    Collect disk latency data using iosnoop.

    :param time:
        The time for which data should be collected.
    :param filename:
        The output file to which the data will be written.

    """
    logger.debug("Enter collect_disk - begin iosnoop tracing.")

    sub_process = subprocess.Popen([IOSNOOP_SCRIPT, "-ts", str(time)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

    for line in sub_process.stdout.readlines()[2:]:  # skip two lines of header
        values = line.decode().split()
        if len(values) < 9:
            continue # skip footer lines
        yield Datapoint(x=float(values[1]), y=float(values[8]), info=values[3])

    logger.debug("Done.")
    logger.debug(sub_process.stderr.read().decode())
    output.print_("Done.")
