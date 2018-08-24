# -------------------------------------------------------------
# ebpf.py - interacts with the eBPF tracing tool
# June - August 2018 - Franz Nowak, Andrei Diaconu
# -------------------------------------------------------------

"""
Interacts with the eBPF tracing tool

"""

__all__ = (
    "MallocStacks",
    "Memleak"
)

from collect.interface.collecter import Collecter
import subprocess
import logging
import datetime
from common import util
from common import datatypes
from io import StringIO
from typing import NamedTuple

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

    class Options(NamedTuple):
        """ No options for this collecter class. """
        pass

    _DEFAULT_OPTIONS = None

    def __init__(self, time, options=_DEFAULT_OPTIONS):
        """
        Initialize the collecter

        """
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def get_generator(self):
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

            # Generator that yields StackDatum objects, constructed from the
            # current line
            yield datatypes.StackDatum(stack=stack_list,
                                       weight=_to_kilo(weight))

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        # Start and end times for the collection
        start = datetime.datetime.now()
        end = start + datetime.timedelta(0, self.time)
        start = str(start)
        end = str(end)

        return datatypes.StackData(self.get_generator, start, end, "kilobytes",
                                   "Malloc Stacks")


class Memleak(Collecter):
    """
    Class that interacts with the memleak tool.

    """

    class Options(NamedTuple):
        """
        Options to use in the collection.
            - top_stacks: how many stacks to be displayed

        """
        top_stacks: int

    _DEFAULT_OPTIONS = Options(top_stacks=10)

    def __init__(self, time, options = _DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(Collecter)
    def get_generator(self):
        """
        Collects all the top 'top_stacks' stacks with outstanding allocations

        The memleak.py script places an ebpf program in kernel memory that
        places UProbes in all the userspace allocation and deallocation
        functions in the kernel. This program keeps track, using hashtables,
        of every stack's current allocated memory. If, by the end of a sleep
        period of 'time' seconds, there are stacks that haven't freed all the
        memory, the script prints them in a StackLine format
        (weight#name1;name2;name3;...) that is retrieved via stdout and
        processed here.

        :return: a generator of 'StackDatum' objects

        """
        mall_subp = subprocess.Popen(["sudo", "python",
                                      BCC_TOOLS_PATH + "memleak.py",
                                      "-t", str(self.time),
                                      "-T", str(self.options.top_stacks)],
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
        out, err = mall_subp.communicate()

        logger.debug(err.decode())

        # TODO: Currently same as mallocstacks' collect, will probably change
        # TODO: If not put them in one function
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

            # Generator that yields StackDatum objects, constructed from the
            # current line
            yield datatypes.StackDatum(stack=stack_list,
                                       weight=_to_kilo(weight))

    @util.log(logger)
    @util.Override(Collecter)
    def collect(self):
        # Start and end times for the collection
        start = datetime.datetime.now()
        end = start + datetime.timedelta(0, self.time)
        start = str(start)
        end = str(end)

        return datatypes.StackData(self.get_generator, start, end, "kilobytes",
                                   "Memory Leaks")
