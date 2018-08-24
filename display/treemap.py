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

import logging
import os
import subprocess
from typing import NamedTuple

from common import (
    file,
    util,
    consts
)
from display.generic_display import GenericDisplay
from util.d3plus import d3IpyPlus as d3

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


class Treemap(GenericDisplay):
    # @TODO: Add more options (look at how the treemap is initialised
    class DisplayOptions(NamedTuple):
        """
        Options:
            - depth: the maximum depth of the treemap (max number of elements
                     in a stack);
        """
        depth: int
    _DEFAULT_OPTIONS = DisplayOptions(depth=25)

    def __init__(self, data, out, data_options,
                 display_options=_DEFAULT_OPTIONS):
        """
        Constructor for the Treemap.

        :param data:
            A generator that returns the data for the section we want to
            display as a treemap
        :param out:
            The output file where the image will be saved as an instance
            of the :class:`DisplayFileName`.
        :param data_options:
        :param display_options:

        """
        # Initialise the base class
        super().__init__(data_options, display_options)

        # in_filename and out_filename File objects (see common.files)
        # We need to get their string representations (paths) and set the
        # right extension for the out file
        self.data = data
        out.set_options("treemap", "html")
        self.output = str(out)

    @util.log(logger)
    def _generate_csv(self, data, out_file):
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
                          example: bytes;1;2;3 -- first row
                                   5;firefox;[unknown];libxul.so -- second row

        :param data:
            A generator that returns the lines for the section we want to
            display as a stackplot
        :param out_file: a semicolon separated file generated from the in_file;
                         expects an absolute path
        :raises ValueError: in case the file is not in an accepted format
        :returns max_depth: the maximum depth of the stack

        """

        with open(out_file, "w") as out_file:
            # Header of the csv; example: value;1;2;3;4;5...
            out_file.write(self.data_options.weight_units + ";" +
                           ";".join([str(i) for i in
                                     range(1,
                                           self.display_options.depth + 1)]) +
                           "\n")

            for line in data:
                # If we don't have any ';' characters raise error
                if line.count(consts.separator) != 1:
                    raise ValueError(
                        "Invalid format of the file! Each line should "
                        "have the format weight#... Line that "
                        "causes the problem {}".format(line))

                # We replace the only '#' character, that separates the
                # weight from the callstack
                call_stack = line.strip().replace(consts.separator, ";", 1)
                sep = call_stack.split(';')
                out_file.write(';'.join(
                    sep[0:self.display_options.depth + 1]) + '\n')

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
        self._generate_csv(self.data, temp_file)
        # Generate the ids we use for the hierarchies and the columns of the
        # input file
        ids = [str(i) for i in range(1, self.display_options.depth + 1)]
        cols = [self.data_options.weight_units] + ids

        data = d3.from_csv(temp_file, ';', columns=cols)
        tmap = d3.TreeMap(id=ids[0:self.display_options.depth],
                          value=self.data_options.weight_units,
                          color=self.data_options.weight_units,
                          legend=True, width=700)
        with open(str(self.output), "w") as out:
            out.write(tmap.dump_html(data))

        username = os.environ['SUDO_USER']
        subprocess.call(["su", "-", "-c", "firefox " +
                         str(self.output), username])
