# -------------------------------------------------------------
# IO/write.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak, Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

"""
Generic writer that saves data objects into a file. The format is header + data.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
__all__ = (
    'Writer',
)

import logging
import json

from common import util

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class Writer:
    @staticmethod
    @util.log(logger)
    def write(data, filename, header):
        """
        Writes to a file the contents of an iterator

        :param data: the data to be written, as a generator
        :param filename: the name of the file that data is going to be written
                         to
        :param header: a dictionary containing the header; should always
                       contain start and end times of the collect and the
                       datatype and interface used; can contain additional
                       fields
        """
        with open(filename, "w") as out:
            # We write the header of the file as the first line
            out.write(json.dumps(header) + '\n')

            for datum in data:
                out.write(str(datum) + "\n")


# class WriterCPEL(Writer):
#     @staticmethod
#     @util.log(logger)
#     @util.Override(Writer)
#     def write(sched_events, filename, header):
#         """
#         Saves the event data from the generator in a file in CPEL format.
#
#         :param sched_events:
#             An iterator of :class:`SchedEvent` objects.
#         :param filename:
#             The name of the file into which to store the output.
#         :param header: the header for the CPEL file; should be "CPEL"
#         """
#
#         cpel_writer = CpelWriter(sched_events)b
#         cpel_writer.write(filename)