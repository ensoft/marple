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


import asyncio
import datetime
import logging
import re
import subprocess
import time
from typing import NamedTuple

from marple.collect.interface import collecter
from marple.common import data_io, util
from marple.common.consts import InterfaceTypes

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class MemoryGraph(collecter.Collecter):
    """
    Collects sorted memory usage for a specific number of processes.

    """
    class Options(NamedTuple):
        """
        .. attribute:: mode:
            "name" or "pid" or "command", to decide the labelling

        """
        mode: str
        frequency: float

    _DEFAULT_OPTIONS = Options(mode="name", frequency=2.0)

    @util.Override(collecter.Collecter)
    def __init__(self, time_, options=_DEFAULT_OPTIONS):
        super().__init__(time_, options)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def _get_raw_data(self):
        """ Collect raw data asynchronously from smem """
        # Dict for the datapoints to be collected
        datapoints = {}

        # Set the start time
        start_time = time.monotonic()
        current_time = 0.0
        self.start_time = datetime.datetime.now()

        while current_time < self.time:
            if self.options.mode == "name":
                out = subprocess.getoutput("smem -c \"name pss\" | tac")
                # s = subprocess.Popen("smem -c \"name pss\" | tac",
                #                      stdout=subprocess.PIPE,
                #                      stderr=subprocess.PIPE)
                # out, err = s.communicate()
                # if err.decode():
                #     logger.error(err.decode())
            elif self.options.mode == "command":
                out = subprocess.getoutput("smem -c \"command pss\" | tac")
                # s = subprocess.Popen("smem -c \"command pss\" | tac",
                #                      stdout=subprocess.PIPE,
                #                      stderr=subprocess.PIPE)
                # out, err = s.communicate()
                # if err.decode():
                #     logger.error(err.decode())
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
                memory = float(match.group("memory"))

                if label in datapoints[current_time]:
                    memory += float(datapoints[current_time][label])
                else:
                    index += 1

                datapoints[current_time][label] = memory / 1024.0

            # Update the clock
            await asyncio.sleep(1.0 / self.options.frequency)
            current_time = time.monotonic() - start_time

        self.end_time = datetime.datetime.now()

        return datapoints

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def _get_generator(self, raw_data):
        """ Convert raw data to standard datatypes and yield them """
        for key in raw_data:
            for lab in raw_data[key]:
                mem = raw_data[key][lab]
                yield data_io.PointDatum(key, mem, lab)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def collect(self):
        """ Collect data asynchronously using smem """
        raw_data = await self._get_raw_data()
        data = self._get_generator(raw_data)
        return data_io.PointData(data, self.start_time, self.end_time,
                                 InterfaceTypes.MEMTIME, 'Time', 'seconds',
                                 'Memory', 'megabytes')

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
    it=asyncio.wait_for(mg.collect(), 60)
    for i in it:
        print(i)
