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
from collect.IO import read


@mock.patch('builtins.open')
class ReaderTest(unittest.TestCase):
    """
    Class that tests the reader context manager used to open marple files
    """

    def test_normal_file(self, open_mock):
        file_mock = open_mock
        file_header = "{\"start\": \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n" \
                    "11#12#13#14#15#16#17"
        file_mock.return_value = StringIO(file_header + file_data)

        with read.Reader("file") as (header, data):
            self.assertDictEqual(header, {"start": "2018-08-20 18:46:38.403129",
                                          "end": "2018-08-20 18:46:39.403129",
                                          "datatype": "Event Data",
                                          "interface": "Scheduling Events"})
            self.assertEqual(data.read(), file_data)

    def test_bad_JSON(self, open_mock):
        """
        Tests an invalid header (ie not in a JSON format)

        """
        file_mock = open_mock
        file_header = "{\"start\" \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n" \
                    "11#12#13#14#15#16#17"
        file_mock.return_value = StringIO(file_header + file_data)

        with self.assertRaises(json.JSONDecodeError):
            with read.Reader("file") as (header, data):
                something = 1
