# -------------------------------------------------------------
# IO/read.py - Reads a marple file
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Module reads a marple file

"""

__all__ = (
    'Reader',
)

import logging
import json

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class Reader:
    """
    Class that is used to read from marple files in a consistent way

    The format of a .marple file is:
    - Header (first line, json formatted)
    - Data (subsequent lines)

    """
    def __init__(self, file_name):
        """
        Initialising the reader object

        :param file_name: Name of the marple file to be used

        """
        self.file_name = file_name

    def __enter__(self):
        """
        Method that returns the resource to be managed
        :return: header as a dictioanry, data as a file descriptor (with the
                 header not included because we read it first)

        """
        self.open_file = open(self.file_name, "r")
        header_str = self.open_file.readline().strip()
        try:
            header_dict = json.loads(header_str)
        except json.JSONDecodeError as jse:
            jse.msg = "Invalid JSON header!"
            raise jse

        data = self.open_file
        return header_dict, data

    def __exit__(self, *args):
        """
        Cleanup method that closes the file

        """
        self.open_file.close()
