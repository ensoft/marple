# -------------------------------------------------------------
# perf.py - interacts with Brendan Gregg's iosnoop tool
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
from typing import NamedTuple
from io import StringIO

from common.datatypes import Datapoint
from collect.interface.collecter import Collecter
from common import util


logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))

ROOT_DIR = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__))))) + "/"

IOSNOOP_SCRIPT = ROOT_DIR + "util/perf-tools/iosnoop"


class DiskLatency(Collecter):
    class Options(NamedTuple):
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        sub_process = subprocess.Popen([IOSNOOP_SCRIPT, "-ts", str(self.time)],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        out, err = sub_process.communicate()

        logger.debug(err.decode())

        lines = StringIO(out.decode())

        # Skip two lines of header
        lines.readline()
        lines.readline()

        # Process rest of file
        for line in lines:
            values = line.split()
            if len(values) < 9:
                continue  # skip footer lines
            yield Datapoint(x=float(values[1]), y=float(values[8]),
                            info=values[3])
