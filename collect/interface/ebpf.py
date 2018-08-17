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


def _to_kilo(num):
    """
    Helper function, transforms from bytes to kilobytes
    :param num: number of bytes
    :return: closest into to the actual number of kilobytes

    """
    return int(num / 1000)

class MallocStacks(Collecter):
    """
    Class that interacts with Brendan Gregg's mallocstacks tools

    """
    def __init__(self, time):
        super().__init__(time)

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        """
        Collects memory stacks where the weight is the number of kilobytes
        :return:

        """
        mall_subp = subprocess.Popen(["sudo", "python",
                                      BCC_TOOLS_PATH + "mallocstacks.py", "-f",
                                      str(self.time)], stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
        out, err = mall_subp.communicate()

        logger.debug(err.decode())

        for line in StringIO(out.decode()):
            line = line.strip('\n')
            # We find the first #, marking the ending of the weight
            hash_pos = line.find('#')

            # The weight starts right after the space and continues up to the
            # first occurence of #
            try:
                weight = int(line[0:hash_pos])
            except ValueError:
                raise ValueError("The weight {} is not a number!",
                                 line[0:hash_pos])

            # The stack starts after the first hash
            stack_list = tuple(line[hash_pos + 1:].split('#'))

            # Generator that yields StackData objects, constructed from the
            # current line
            yield datatypes.StackData(stack=stack_list,
                                      weight=_to_kilo(weight))
