# -------------------------------------------------------------
# treemap.py - Generates a treemap representation of the data
# July 2018 - Andrei Diaconu, Hrutvik Kanabar
# -------------------------------------------------------------
"""
Displays the collected data as a treemap

"""

__all__ = (
    'Treemap'
)

import subprocess
import os
import logging

from common import (
    file,
    util
)
from display.generic_display import GenericDisplay
from util.d3plus import d3IpyPlus as d3
from collect.IO import read

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class Treemap(GenericDisplay):
    def __init__(self, depth, inp, out):
        """
        Constructor for the Treemap.

        :param depth:
            The depth of Treemap. Should not be more than about 25, since the
            loading times increase too much
        :param inp:
            Input [Stack] file as a string
        :param out:
            Output file as a file object

        """
        self.depth = depth
        self.input = inp
        out.set_options("treemap", "html")
        self.output = str(out)

    @staticmethod
    @util.log(logger)
    def _generate_csv(in_file, out_file):
        """
        Creates a semicolon separated file from a stack parser output.
        The output format will be:
            - first line: Represents the columns (header); first column will
                          represent the value of the stack line; the rest of the
                          columns will be numbers from 1 to the maximum stack
                          depth, representing the groups we use for creating the
                          hierarchies;
            - next lines: values of the above columns, separated by semicolons;
                          the values for the groups will be the function at that
                          depth;
                          example: value;1;2;3 -- first row
                                   5;firefox;[unknown];libxul.so -- second row

        :param in_file: a collapsed stack produced by the stack parser; expects
                        an absolute path
        :param out_file: a semicolon separated file generated from the in_file;
                         expects an absolute path
        :raises ValueError: in case the file is not in an accepted format
        :returns max_depth: the maximum depth of the stack

        """
        max_depth = 0
        with read.Reader(str(in_file)) as (header, data):
            for line in data:
                cnt = line.count(';')
                # If we don't have any ';' characters raise error
                if cnt == 0:
                    raise ValueError("Invalid format of the file! Line that "
                                     "causes the problem {}".format(line))
                if max_depth < cnt:
                    max_depth = cnt

            # Number of fields in a line is 1 plus the number of ';' characters
            max_depth += 1

        with open(out_file, "w") as out_file:
            # Header of the csv; example: value;1;2;3;4;5...
            out_file.write("value;" +
                           ";".join([str(i) for i in
                                     range(1, max_depth + 1)]) +
                           "\n")

            with read.Reader(in_file) as (header, data):
                for line in data:
                    # We replace the only '#' character, that separates the
                    # weight from the callstack
                    call_stack = line.replace("#", ";", 1)
                    out_file.write(call_stack)

        return max_depth

    @util.Override(GenericDisplay)
    @util.log(logger)
    def show(self):
        """
        Displays the input stack as a treemap using the d3IpyPlus tool.

        Creates the ids and the columns that are passed in the treemap object,
        which is used to generate a html file that is to be displayed.
        """

        # Temp file for the csv file
        temp_file = str(file.TempFileName())
        max_depth = self._generate_csv(self.input, temp_file)

        # Generate the ids we use for the hierarchies and the columns of the
        # input file
        ids = [str(i) for i in range(1, max_depth + 1)]
        cols = ["value"] + ids

        data = d3.from_csv(temp_file, ';', columns=cols)
        tmap = d3.TreeMap(id=ids[0:self.depth], value="value", color="value",
                          legend=True, width=700)
        with open(str(self.output), "w") as out:
            out.write(tmap.dump_html(data))

        username = os.environ['SUDO_USER']
        subprocess.call(["su", "-", "-c", "firefox " +
                         str(self.output), username])
