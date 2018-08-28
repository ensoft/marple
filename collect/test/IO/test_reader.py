# -------------------------------------------------------------
# IO/read.py - Reads a marple file
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Module that can read a marple file

"""

import unittest
import json

from unittest import mock
from io import StringIO

import common.data_io
from collect.IO import read


class ReaderTest(unittest.TestCase):
    """
    Class that tests the reader context manager used to open marple files
    """

    def test_normal_file(self):
        """
        Tests if under normal conditions the file object is consumed
        correctly and the results are consistent

        """
        file_header = "{\"start\": \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n" \
                    "11#12#13#14#15#16#17"
        file_object = StringIO(file_header + file_data)

        header = common.data_io.Reader.read_header(file_object)
        data = common.data_io.Reader.read_until_line(file_object, '\n')
        self.assertDictEqual(header, {"start": "2018-08-20 18:46:38.403129",
                                      "end": "2018-08-20 18:46:39.403129",
                                      "datatype": "Event Data",
                                      "interface": "Scheduling Events"})
        self.assertEqual([line for line in data],
                         ["1#2#3#4#5\n", "6#7#8#9#10\n",
                          "11#12#13#14#15#16#17"])

    def test_stops_correctly(self):
        """
        Tests if the data is being read until the separator and not beyond it

        """
        file_header = "{\"start\": \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n\n" \
                    "11#12#13#14#15#16#17"
        file_object = StringIO(file_header + file_data)

        header = common.data_io.Reader.read_header(file_object)
        data = common.data_io.Reader.read_until_line(file_object, '\n')
        self.assertDictEqual(header, {"start": "2018-08-20 18:46:38.403129",
                                      "end": "2018-08-20 18:46:39.403129",
                                      "datatype": "Event Data",
                                      "interface": "Scheduling Events"})
        self.assertEqual([line for line in data],
                         ["1#2#3#4#5\n", "6#7#8#9#10\n"])

    def test_bad_JSON(self):
        """
        Tests an invalid header (ie not in a JSON format)

        """
        file_header = "{\"start\" \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n" \
                    "11#12#13#14#15#16#17"
        file_object = StringIO(file_header + file_data)

        with self.assertRaises(json.JSONDecodeError):
            common.data_io.Reader.read_header(file_object)
