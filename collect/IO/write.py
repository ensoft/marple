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
    def write(data, filename):
        """
        Writes to a file the contents data from  list of `Data` objects

        :param data: a StackData, EventData, or PointData object
        :param filename: the name of the file that data is going to be written
                         to
        """
        with open(filename, "a") as out:
            # Write the header of the file as the first line
            out.write(json.dumps(data.header_to_dict()) + '\n')

            # Write data
            # out.writelines(data.datum_generator)
            for datum in data.datum_generator:
                out.write(str(datum) + "\n")

            out.write("\n")
