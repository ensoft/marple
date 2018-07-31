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

logger = logging.getLogger("collect.interface.iosnoop")
logger.setLevel(logging.DEBUG)

ROOT_DIR = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__))))) + "/"

IOSNOOP_SCRIPT = ROOT_DIR + "util/perf-tools/iosnoop"


def collect_disk(time, filename):
    """
    Collect disk latency data using iosnoop.

    :param time:
        The time for which data should be collected.
    :param filename:
        The output file to which the data will be written.

    """
    logger.debug("Enter collect_disk - begin iosnoop tracing.")

    with open(filename, "w") as out:
        sub_process = subprocess.Popen([IOSNOOP_SCRIPT, "-ts", str(time)], stdout=out,
                                       stderr=subprocess.PIPE)
    logger.debug("Done.")
    logger.debug(sub_process.stderr.read().decode())
    output.print_("Done.")
