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

from common.datatypes import Datapoint
from collect.interface.interface import Interface
from common import util


logger = logging.getLogger("collect.interface.iosnoop")
logger.setLevel(logging.DEBUG)

ROOT_DIR = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(
              __file__))))) + "/"

IOSNOOP_SCRIPT = ROOT_DIR + "util/perf-tools/iosnoop"


class Disk(Interface):
    class Options(NamedTuple):
        pass

    _DEFAULT_OPTIONS = None

    @util.check_kernel_version("2.6")
    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)
        self.data_generator = None

    @util.Override(Interface)
    def collect(self):
        logger.info("Enter Disk.collect")

        sub_process = subprocess.Popen([IOSNOOP_SCRIPT, "-ts", str(self.time)],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        logger.debug(sub_process.stderr.read().decode())

        self.data_generator = (line.decode()
                               for line in sub_process.stdout.readlines())

    @util.Override(Interface)
    def get(self):
        logger.info("Enter Disk.get")

        # Skip over two lines of header
        next(self.data_generator)
        next(self.data_generator)

        # Process rest of file
        for line in self.data_generator:
            values = line.split()
            if len(values) < 9:
                continue  # skip footer lines
            yield Datapoint(x=float(values[1]), y=float(values[8]),
                            info=values[3])
