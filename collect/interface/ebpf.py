# -------------------------------------------------------------
# ebpf.py - interacts with the eBPF tracing tool
# June - August 2018 - Franz Nowak, Andrei Diaconu
# -------------------------------------------------------------

"""
Interacts with the eBPF tracing tool

"""

from collect.interface.collecter import Collecter
import subprocess
import os
import logging
from common import util
from common import datatypes
from io import StringIO
import re

# TODO: no abs paths + move them to the paths module
MARPLE_DIR = "/home/andreid/PycharmProjects/marple/"
BCC_TOOLS_PATH = MARPLE_DIR + "util/bcc-tools/"

logger = logging.getLogger(__name__)
logger.debug('Entered module: {}'.format(__name__))


class MallocStacks(Collecter):
    """
    Class that interacts with Brendan Gregg's mallocstacks tools

    """
    def __init__(self, time):
        super().__init__(time)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        mall_subp = subprocess.Popen(["sudo", "python2",
                                      BCC_TOOLS_PATH + "mallocstacks.py", "-f",
                                      str(self.time)], stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
        out, err = mall_subp.communicate()

        logger.debug(err.decode())

        for line in StringIO(out.decode()):
            line = line.strip('\n')
            # We search for the first position where the pattern 'space
            # followed by digit' appears (we assume no process will have a
            # similar naming)
            space_pos = re.search(r' \d', line).start()

            # The weight starts right after the space and continues up to the
            # end of the line
            try:
                weight = int(line[space_pos + 1:])
                # The stack starts at the beginning of the line and ends just before
                # the space
                stack_list = tuple(line[:space_pos].split(';'))

                # Generator that yields StackData objects, constructed from the
                # current line
                yield datatypes.StackData(stack=stack_list, weight=weight)
            except ValueError:
                print(line)
