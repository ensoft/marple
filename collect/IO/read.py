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

from common import util


logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class Reader:
    """
    Class that facilitates the reading of multi-section MARPLE files

    The format of a .marple file is:
    - Header1 (first line, json formatted)
    - Data1 (subsequent lines, ending with a new line)
    - Header2 (the line after the previous new line)
    - Data2
    - ...

    """

    @classmethod
    @util.log(logger)
    def read_header(cls, file_object):
        """
        Class method that parses the header of the file_object (its first line)
        The header MUST be a valid JSON, on a single line, otherwise an error
        will be thrown
        If the line we have just read is a blank line (''), the end of the
        document has been reached, and we return None

        :param: file_object: the file object whose header we want to parse
        :return: a dict representation of the header
        :raises: json.JSONDecodeError

        """
        header_str = file_object.readline()
        if header_str == "":
            # End of a file
            return None

        header_str = header_str.strip()
        try:
            header_dict = json.loads(header_str)
        except json.JSONDecodeError as jse:
            jse.msg = "Malformed JSON header!"
            raise jse
        return header_dict

    @classmethod
    @util.log(logger)
    def read_until_line(cls, file_object, stop_line):
        """
        Class method that lazily reads from file_object until the
        line (:param stop_line) or the end of the file is encountered (when
        the current line is '' this means we have reached the end of the file)

        :param file_object: the file object pointing where we want to start
                            reading from the file
        :param stop_line: the line that signals the ending of a section
        :return: a line from file_object

        """
        line = file_object.readline()
        while line != stop_line and line != '':
            yield line
            line = file_object.readline()
