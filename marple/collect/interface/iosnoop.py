# -------------------------------------------------------------
# iosnoop.py - interacts with Brendan Gregg's iosnoop tool
# July 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

"""
Interacts with the iosnoop tracing tool.

Calls iosnoop to collect disk latency data and format it.

"""
__all__ = (
    'DiskLatency',
)

import asyncio
import datetime
import logging
from io import StringIO
from typing import NamedTuple

from marple.collect.interface import collecter
from marple.common import data_io, util, paths, exceptions
from marple.common.consts import InterfaceTypes

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

IOSNOOP_SCRIPT = paths.MARPLE_DIR + "/collect/tools/perf-tools/iosnoop"


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
    async def _get_raw_data(self):
        """ Collect raw data asynchronously using iosnoop. """
        self.start_time = datetime.datetime.now()

        sub_process = await asyncio.create_subprocess_exec(
            IOSNOOP_SCRIPT, '-ts', str(self.time),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        out, err = await sub_process.communicate()

        self.end_time = datetime.datetime.now()
        if sub_process.returncode != 0:
            raise exceptions.SubprocessedErorred(err.decode())

        return StringIO(out.decode())

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def _get_generator(self, raw_data):
        """ Convert raw data to standard datatypes and yield it. """
        # Skip two lines of header
        raw_data.readline()
        raw_data.readline()

        # Process rest of file
        for line in raw_data:
            values = line.split()
            if len(values) < 9:
                continue  # skip footer lines
            yield data_io.PointDatum(x=float(values[1]), y=float(values[8]),
                                     info=values[3])

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def collect(self):
        """
        Collect data asynchronously using iosnoop.

        :return:
            a `data_io.PointData` object that encapsulates the collected
            data
        """
        try:
            raw_data = await self._get_raw_data()
        except exceptions.SubprocessedErorred as se:
            logger.error(str(se))
            return data_io.PointData(None, -1, -1,
                                     InterfaceTypes.DISKLATENCY, None)

        data = self._get_generator(raw_data)
        data_options = data_io.PointData.DataOptions(
            x_label="Time", y_label="Latency", x_units="s", y_units="ms")
        return data_io.PointData(data, self.start_time, self.end_time,
                                 InterfaceTypes.DISKLATENCY, data_options)
