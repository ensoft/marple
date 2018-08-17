# -------------------------------------------------------------
# smem.py - interacts with the smem tool.
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Interacts with the smem tool.

Calls smem to collect memory data, format it, and has functions that create data
    object generators.

"""

__all__ = (
    "MemoryGraph",
)


import re
import subprocess
import time
from typing import NamedTuple

from collect.interface.collecter import Collecter
from common import datatypes, util


class MemoryGraph(Collecter):
    class Options(NamedTuple):
        """
        .. attribute:: mode:
            "name" or "pid" or "command", to decide the labelling

        """
        mode: str

    _DEFAULT_OPTIONS = Options(mode="name")

    @util.Override(Collecter)
    def __init__(self, time_, options=_DEFAULT_OPTIONS):
        super().__init__(time_, options)

    @util.Override(Collecter)
    def collect(self):
        """
        Collects sorted memory usage of a specific number of processes.

        :return:
            An iterator of :class: `DataPoint` objects.

        """
        # Dict for the datapoints to be collected
        datapoints = {}

        # Set the start time
        start_time = time.monotonic()
        current_time = 0.0

        while current_time < self.time:
            if self.options.mode == "name":
                out = subprocess.getoutput("smem -c \"name pss\" | tac")
            elif self.options.mode == "command":
                out = subprocess.getoutput("smem -c \"command pss\" | tac")
            else:
                raise ValueError(
                    "mode {} not supported.".format(self.options.mode))

            datapoints[current_time] = {}

            index = 0
            for line in out.split("\n"):
                if re.match("Name", line) is not None:
                    break

                match = re.match(r"\s*(?P<label>\S+(\s\S+)*)\s*"
                                 r"(?P<memory>\d+)", line)
                if match is None:
                    raise IOError("Invalid output format from smem: {}".format(
                        line))

                label = match.group("label")
                memory = int(match.group("memory"))

                if label in datapoints[current_time]:
                    memory += int(datapoints[current_time][label])
                else:
                    index += 1

                datapoints[current_time][label] = float(int(memory / 1024))

            # Update the clock
            current_time = time.monotonic() - start_time

        for key in datapoints:
            for lab in datapoints[key]:
                mem = datapoints[key][lab]
                yield datatypes.Datapoint(key, mem, lab)

    @staticmethod
    def _insert_datapoint(memory):
        """
        Converts a number in kilobytes into megabytes.

        :param memory:
            The amount of memory in kilobytes.
        :return:
            A float value to the nearest integer with the memory in megabytes.
        """
        return float(int(memory / 1024))


if __name__ == "__main__":
    mg=MemoryGraph(15)
    it=mg.collect()
    for i in it:
        print(i)