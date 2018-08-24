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
    Class that facilitates the reading of multi section MARPLE files

    The format of a .marple file is:
    - Header1 (first line, json formatted)
    - Data1 (subsequent lines, ending with a new line)
    - Header2 (the line after the previous new line)
    - Data2
    - ...

    """

    @classmethod
    def read_header(cls, file_object):
        """
        Class method that parses the header in the file_object (its first line)
        :param file_object: the file object whose header we want to parse
        :return: a dict representation of the header

        """
        header_str = file_object.readline().strip()
        if header_str == "":
            # End of a file
            return {}

        try:
            header_dict = json.loads(header_str)
        except json.JSONDecodeError as jse:
            jse.msg = "Invalid JSON header!"
            raise jse
        return header_dict

    @classmethod
    def read_until_line(cls, file_object, stop_line):
        """
        Class method that lazily reads sections from file_object; sections are
        separated by `line` is encountered (the line is skipped in the process)

        :param file_object: the file object pointing to the start of the section
        :param stop_line: the line that signals the ending of a section
        :return: a line from file_object

        """
        line = file_object.readline()
        while line != stop_line:
            yield line
            line = file_object.readline()
