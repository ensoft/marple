# -------------------------------------------------------------
# iosnoop.py - interacts with Brendan Gregg's iosnoop tool
# July 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

"""
Interacts with the iosnoop tracing tool.

Calls iosnoop to collect data and format it.

"""
__all__ = (
    'Disk'
)

import logging
import os
import subprocess
import datetime
from typing import NamedTuple
from io import StringIO

from common import datatypes
from collect.interface import collecter
from common import util


logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

ROOT_DIR = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__))))) + "/"

IOSNOOP_SCRIPT = ROOT_DIR + "util/perf-tools/iosnoop"


class DiskLatency(collecter.Collecter):
    """ Collect disk latency data using iosnoop. """

    class Options(NamedTuple):
        """ No options for this collecter class. """
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        """ Initialise the collecter (see superclass). """
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def get_generator(self):
        """ Collect data using iosnoop and yield it. """
        sub_process = subprocess.Popen([IOSNOOP_SCRIPT, "-ts", str(self.time)],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        out, err = sub_process.communicate()

        logger.error(err.decode())

        lines = StringIO(out.decode())

        # Skip two lines of header
        lines.readline()
        lines.readline()

        # Process rest of file
        for line in lines:
            values = line.split()
            if len(values) < 9:
                continue  # skip footer lines
            yield datatypes.PointDatum(x=float(values[1]), y=float(values[8]),
                                       info=values[3])

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def collect(self):
        # Start and end times for the collection
        start = datetime.datetime.now()
        end = start + datetime.timedelta(0, self.time)
        start = str(start)
        end = str(end)

        return datatypes.PointData(self.get_generator, start, end,
                                   'Disk Latency/Time', 'Time', 'Latency',
                                   'seconds', 'ms')
